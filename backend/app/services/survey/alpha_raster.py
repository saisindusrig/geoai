"""Vector-to-alpha rasterization aligned to survey DEM/ortho grid."""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from app.services.storage import save_file
from app.services.survey.project_helpers import ensure_project_crs

try:
    import rasterio
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
except ImportError:
    rasterio = None
    rasterize = None
    from_bounds = None

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db.models import EngineeringLayer, Project, SurveyDataset


def generate_alpha_raster(
    db: Session,
    project: Project,
    *,
    road_width_m: float = 7.0,
    dem_dataset: SurveyDataset | None = None,
) -> dict:
    if rasterio is None:
        raise RuntimeError("rasterio is required for alpha raster generation")

    from app.db.models import EngineeringLayer, SurveyDataset

    epsg = ensure_project_crs(project)
    layers = (
        db.query(EngineeringLayer)
        .filter(EngineeringLayer.project_id == project.id)
        .all()
    )
    if not dem_dataset:
        dem_dataset = (
            db.query(SurveyDataset)
            .filter(SurveyDataset.project_id == project.id, SurveyDataset.kind.in_(["dem", "orthomosaic"]))
            .order_by(SurveyDataset.created_at.desc())
            .first()
        )

    shapes = []
    for layer in layers:
        if layer.geom_geojson is None:
            continue
        geom = shape(layer.geom_geojson)
        if layer.layer_type == "road_centerline":
            buf = geom.buffer(road_width_m / 2.0 if layer.width_m is None else layer.width_m / 2.0)
            shapes.append((mapping(buf), 255))
        elif layer.layer_type in ("road_edge", "construction_zone", "mask_source", "parcel"):
            shapes.append((mapping(geom), 255))

    if not shapes:
        raise ValueError("No vector layers to rasterize")

    if dem_dataset and dem_dataset.metadata_json and dem_dataset.metadata_json.get("bounds"):
        bounds = dem_dataset.metadata_json["bounds"]
        width = dem_dataset.metadata_json.get("width", 512)
        height = dem_dataset.metadata_json.get("height", 512)
        transform = from_bounds(*bounds, width, height)
    else:
        union = unary_union([shape(s[0]) for s in shapes])
        minx, miny, maxx, maxy = union.bounds
        pad = 10.0
        bounds = (minx - pad, miny - pad, maxx + pad, maxy + pad)
        width = height = 512
        transform = from_bounds(*bounds, width, height)

    mask = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
    )

    png_buf = io.BytesIO()
    try:
        from PIL import Image

        Image.fromarray(mask).save(png_buf, format="PNG")
    except ImportError:
        # Minimal PNG without PIL — store raw GeoTIFF only
        png_buf = None

    tif_buf = io.BytesIO()
    with rasterio.open(
        tif_buf,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=mask.dtype,
        crs=f"EPSG:{epsg}",
        transform=transform,
    ) as dst:
        dst.write(mask, 1)

    key_tif = f"projects/{project.id}/exports/alpha_map.tif"
    url_tif = save_file(key_tif, tif_buf.getvalue(), "image/tiff")
    url_png = None
    if png_buf:
        key_png = f"projects/{project.id}/exports/alpha_map.png"
        url_png = save_file(key_png, png_buf.getvalue(), "image/png")

    return {
        "alpha_tif_url": url_tif,
        "alpha_png_url": url_png,
        "bounds": list(bounds),
        "crs_epsg": epsg,
        "width": width,
        "height": height,
    }

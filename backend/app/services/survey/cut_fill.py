"""Cut/fill volumes from survey DEM vs design surface — survey-grade only."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.services.survey.constants import SURVEY_DEM_MAX_PIXEL_M
from app.core.config import settings
from app.services.survey.project_helpers import ensure_project_crs, require_survey_tier

try:
    import rasterio
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
except ImportError:
    rasterio = None

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db.models import Project


def compute_cut_fill(
    db: Session,
    project: Project,
    *,
    design_elevation_m: float | None = None,
    road_width_m: float = 7.0,
) -> dict:
    require_survey_tier(project, "survey_grade")
    if design_elevation_m is None:
        raise ValueError("An explicit design elevation and resolved vertical reference are required")

    from app.db.models import EngineeringLayer, SurveyDataset
    from shapely.geometry import mapping, shape

    if rasterio is None:
        raise RuntimeError("rasterio required for survey cut/fill")

    dem = (
        db.query(SurveyDataset)
        .filter(SurveyDataset.project_id == project.id, SurveyDataset.kind == "dem")
        .order_by(SurveyDataset.created_at.desc())
        .first()
    )
    if not dem or not dem.storage_key:
        raise ValueError("Survey DEM required for cut/fill")
    if dem.pixel_size_m and dem.pixel_size_m > SURVEY_DEM_MAX_PIXEL_M:
        raise ValueError(f"DEM resolution {dem.pixel_size_m}m exceeds survey-grade limit {SURVEY_DEM_MAX_PIXEL_M}m")

    local = Path(settings.LOCAL_STORAGE_DIR) / dem.storage_key
    if not local.exists():
        raise ValueError("DEM file missing from storage")

    ensure_project_crs(project)
    layers = (
        db.query(EngineeringLayer)
        .filter(EngineeringLayer.project_id == project.id, EngineeringLayer.layer_type == "road_centerline")
        .all()
    )

    with tempfile.NamedTemporaryFile(suffix=".tif") as tmp:
        tmp.write(local.read_bytes())
        tmp.flush()
        with rasterio.open(tmp.name) as ds:
            existing = ds.read(1).astype(float)
            transform = ds.transform
            cell_area = abs(transform.a * transform.e)
            nodata = ds.nodata
            if nodata is not None:
                existing = np.where(existing == nodata, np.nan, existing)

            design = np.full_like(existing, design_elevation_m if design_elevation_m is not None else np.nanmean(existing))

            if layers:
                shapes = []
                for layer in layers:
                    if layer.geom_geojson is None:
                        continue
                    geom = shape(layer.geom_geojson)
                    width = layer.width_m or road_width_m
                    shapes.append((mapping(geom.buffer(width / 2.0)), 1))
                if shapes:
                    mask = rasterize(shapes, out_shape=existing.shape, transform=transform, fill=0, dtype=np.uint8)
                    design = np.where(mask > 0, design, existing)

            delta = design - existing
            valid = ~np.isnan(existing) & ~np.isnan(design)
            cut = float(np.nansum(np.where((delta < 0) & valid, -delta, 0)) * cell_area)
            fill = float(np.nansum(np.where((delta > 0) & valid, delta, 0)) * cell_area)

    return {
        "cut_m3": round(cut, 2),
        "fill_m3": round(fill, 2),
        "net_m3": round(fill - cut, 2),
        "cell_area_m2": cell_area,
        "vertical_rmse_m": dem.rmse_v_m,
        "volume_uncertainty_m3": None,
        "uncertainty_status": "UNKNOWN",
        "dem_dataset_id": dem.id,
        "accuracy_tier": project.accuracy_tier,
        "disclaimer": "Volumes computed from imported survey DEM only — not from satellite basemap.",
    }

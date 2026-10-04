"""Terrain and road mesh GLB export from survey DEM + vectors."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import trimesh
from shapely.geometry import LineString, shape

from app.core.config import settings
from app.services.storage import save_file
from app.services.survey.project_helpers import ensure_project_crs

try:
    import rasterio
except ImportError:
    rasterio = None

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db.models import Project


def _dem_height_grid(dem_path: bytes, decimate: int = 4) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp.write(dem_path)
        path = tmp.name
    try:
        with rasterio.open(path) as ds:
            data = ds.read(1, out_shape=(
                max(2, ds.height // decimate),
                max(2, ds.width // decimate),
            ))
            bounds = ds.bounds
            return data.astype(float), (bounds.left, bounds.bottom, bounds.right, bounds.top)
    finally:
        Path(path).unlink(missing_ok=True)


def export_terrain_glb(db: Session, project: Project) -> str:
    from app.db.models import SurveyDataset

    dem = (
        db.query(SurveyDataset)
        .filter(SurveyDataset.project_id == project.id, SurveyDataset.kind == "dem")
        .order_by(SurveyDataset.created_at.desc())
        .first()
    )
    if not dem or not dem.storage_key:
        raise ValueError("No survey DEM available for terrain mesh")

    from app.core.config import settings

    local = Path(settings.LOCAL_STORAGE_DIR) / dem.storage_key
    if local.exists():
        dem_bytes = local.read_bytes()
    else:
        raise ValueError("DEM file not found in storage; re-import survey DEM")

    heights, bounds = _dem_height_grid(dem_bytes)
    h, w = heights.shape
    minx, miny, maxx, maxy = bounds
    xs = np.linspace(minx, maxx, w)
    ys = np.linspace(miny, maxy, h)
    xx, yy = np.meshgrid(xs, ys)
    zz = np.nan_to_num(heights, nan=0.0)

    vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    faces = []
    for i in range(h - 1):
        for j in range(w - 1):
            a = i * w + j
            b = a + 1
            c = a + w
            d = c + 1
            faces.append([a, c, b])
            faces.append([b, c, d])

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    key = f"projects/{project.id}/exports/terrain.glb"
    return save_file(key, buf.getvalue(), "model/gltf-binary")


def export_roads_glb(db: Session, project: Project, default_width_m: float = 7.0) -> str:
    from app.db.models import EngineeringLayer, SurveyDataset

    ensure_project_crs(project)
    layers = (
        db.query(EngineeringLayer)
        .filter(
            EngineeringLayer.project_id == project.id,
            EngineeringLayer.layer_type.in_(["road_centerline", "road_edge"]),
        )
        .all()
    )
    if not layers:
        raise ValueError("No road engineering layers")

    dem = (
        db.query(SurveyDataset)
        .filter(SurveyDataset.project_id == project.id, SurveyDataset.kind == "dem")
        .first()
    )
    dem_heights = None
    dem_bounds = None
    if dem and dem.storage_key:
        local = Path(settings.LOCAL_STORAGE_DIR) / dem.storage_key
        if local.exists():
            dem_heights, dem_bounds = _dem_height_grid(local.read_bytes(), decimate=8)

    meshes: list[trimesh.Trimesh] = []
    for layer in layers:
        if layer.geom_geojson is None:
            continue
        geom = shape(layer.geom_geojson)
        if layer.layer_type == "road_centerline" and isinstance(geom, LineString):
            width = layer.width_m or default_width_m
            poly = geom.buffer(width / 2.0)
            coords = np.array(poly.exterior.coords)
            z = np.zeros(len(coords))
            if dem_heights is not None and dem_bounds is not None:
                minx, miny, maxx, maxy = dem_bounds
                h, w = dem_heights.shape
                for i, (x, y) in enumerate(coords[:, :2]):
                    col = int((x - minx) / max(maxx - minx, 1e-6) * (w - 1))
                    row = int((y - miny) / max(maxy - miny, 1e-6) * (h - 1))
                    z[i] = dem_heights[row, col]
            verts = np.column_stack([coords[:, 0], coords[:, 1], z])
            faces = [[0, i, i + 1] for i in range(1, len(verts) - 1)]
            if faces:
                meshes.append(trimesh.Trimesh(vertices=verts, faces=faces))

    if not meshes:
        raise ValueError("Could not build road mesh from layers")

    combined = trimesh.util.concatenate(meshes)
    buf = io.BytesIO()
    combined.export(buf, file_type="glb")
    key = f"projects/{project.id}/exports/roads.glb"
    return save_file(key, buf.getvalue(), "model/gltf-binary")

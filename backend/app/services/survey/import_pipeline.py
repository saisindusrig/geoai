"""Import GeoJSON, Shapefile, GeoTIFF, GCP CSV into PostGIS + MinIO."""

from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EngineeringLayer, GroundControlPoint, SurveyDataset
from app.services.geospatial.crs import reproject_geojson, wgs84_to_project
from app.services.storage import save_file
from app.services.survey.constants import DATASET_KINDS, ENGINEERING_LAYER_TYPES, GCP_SOURCES
from app.services.survey.project_helpers import ensure_project_crs, sync_layer_postgis

try:
    import geopandas as gpd
except ImportError:
    gpd = None

try:
    import rasterio
except ImportError:
    rasterio = None

try:
    import laspy
except ImportError:
    laspy = None

try:
    import ezdxf
except ImportError:
    ezdxf = None


def _parse_capture_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip()[:19], fmt)
        except ValueError:
            continue
    return None


def ingest_geojson_layer(
    db: Session,
    project,
    geojson: dict,
    layer_type: str,
    name: str,
    *,
    source: str | None = None,
    width_m: float | None = None,
    survey_dataset_id: int | None = None,
    accuracy_tier: str = "gis_grade",
) -> EngineeringLayer:
    if layer_type not in ENGINEERING_LAYER_TYPES:
        raise ValueError(f"Invalid layer_type: {layer_type}")
    epsg = ensure_project_crs(project)
    geom = geojson.get("geometry") if geojson.get("type") == "Feature" else geojson
    if geom is None:
        raise ValueError("No geometry in GeoJSON")
    geom_project = reproject_geojson(geom, 4326, epsg)
    geom_wgs84 = geom if geom.get("coordinates") else reproject_geojson(geom_project, epsg, 4326)
    layer = EngineeringLayer(
        project_id=project.id,
        survey_dataset_id=survey_dataset_id,
        layer_type=layer_type,
        name=name,
        width_m=width_m,
        source=source,
        accuracy_tier=accuracy_tier,
        crs_epsg=epsg,
        geom_geojson=geom_project,
        geom_wgs84_geojson=geom_wgs84,
        properties_json=geojson.get("properties") if geojson.get("type") == "Feature" else {},
    )
    db.add(layer)
    db.flush()
    sync_layer_postgis(db, layer, epsg)
    return layer


def ingest_geojson_file(
    db: Session,
    project,
    content: bytes,
    layer_type: str,
    name: str,
    **kwargs: Any,
) -> EngineeringLayer:
    data = json.loads(content.decode("utf-8"))
    if data.get("type") == "FeatureCollection":
        features = data.get("features") or []
        if not features:
            raise ValueError("Empty FeatureCollection")
        last = None
        for i, feat in enumerate(features):
            last = ingest_geojson_layer(
                db, project, feat, layer_type, name if i == 0 else f"{name} ({i + 1})", **kwargs
            )
        return last  # type: ignore[return-value]
    return ingest_geojson_layer(db, project, data, layer_type, name, **kwargs)


def ingest_shapefile_zip(
    db: Session,
    project,
    content: bytes,
    layer_type: str,
    name: str,
    **kwargs: Any,
) -> list[EngineeringLayer]:
    if gpd is None:
        raise RuntimeError("geopandas is required for Shapefile import")
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "upload.zip"
        zpath.write_bytes(content)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(tmp)
        shps = list(Path(tmp).rglob("*.shp"))
        if not shps:
            raise ValueError("No .shp found in zip")
        gdf = gpd.read_file(shps[0])
        if gdf.crs is None:
            raise ValueError("CRS metadata is missing; identify the source CRS before importing")
        gdf = gdf.to_crs(epsg=4326)
        layers: list[EngineeringLayer] = []
        for i, row in gdf.iterrows():
            feat = json.loads(gdf.loc[[i]].to_json())["features"][0]
            layers.append(
                ingest_geojson_layer(
                    db,
                    project,
                    feat,
                    layer_type,
                    name if len(gdf) == 1 else f"{name} feature {i}",
                    **kwargs,
                )
            )
        return layers


def ingest_geotiff(
    db: Session,
    project,
    content: bytes,
    kind: str,
    name: str,
    *,
    source: str | None = None,
    capture_date: str | None = None,
    rmse_h_m: float | None = None,
    rmse_v_m: float | None = None,
) -> SurveyDataset:
    if kind not in ("orthomosaic", "dem"):
        raise ValueError("GeoTIFF import supports orthomosaic or dem only")
    if rasterio is None:
        raise RuntimeError("rasterio is required for GeoTIFF import")
    epsg = ensure_project_crs(project)
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp.write(content)
        tpath = tmp.name
    try:
        with rasterio.open(tpath) as ds:
            if ds.crs is None:
                raise ValueError("GeoTIFF CRS is missing; resolve metadata before importing")
            crs_epsg = ds.crs.to_epsg()
            transform = ds.transform
            pixel_size = abs(transform.a) if transform.a else None
            meta = {
                "width": ds.width,
                "height": ds.height,
                "bounds": list(ds.bounds),
                "crs": str(ds.crs) if ds.crs else None,
            }
    finally:
        Path(tpath).unlink(missing_ok=True)

    key = f"projects/{project.id}/survey/{kind}/{name.replace(' ', '_')}.tif"
    url = save_file(key, content, "image/tiff")
    ds_row = SurveyDataset(
        project_id=project.id,
        kind=kind,
        name=name,
        storage_key=key,
        source=source,
        capture_date=_parse_capture_date(capture_date),
        crs_epsg=crs_epsg or epsg,
        pixel_size_m=pixel_size,
        rmse_h_m=rmse_h_m,
        rmse_v_m=rmse_v_m,
        accuracy_tier="gis_grade",
        metadata_json={**meta, "file_url": url},
    )
    db.add(ds_row)
    db.flush()
    return ds_row


def ingest_gcp_csv(db: Session, project, content: bytes) -> list[GroundControlPoint]:
    epsg = ensure_project_crs(project)
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[GroundControlPoint] = []
    for row in reader:
        name = (row.get("name") or row.get("Name") or row.get("id") or "GCP").strip()
        source = (row.get("source") or row.get("Source") or "manual").strip().upper()
        if source not in GCP_SOURCES:
            source = "manual"
        lng = float(row.get("lng") or row.get("lon") or row.get("longitude") or row.get("Longitude"))
        lat = float(row.get("lat") or row.get("latitude") or row.get("Latitude"))
        e = row.get("easting_m") or row.get("easting") or row.get("Easting")
        n = row.get("northing_m") or row.get("northing") or row.get("Northing")
        if e is not None and n is not None:
            easting, northing = float(e), float(n)
        else:
            easting, northing = wgs84_to_project(lng, lat, epsg)
        gcp = GroundControlPoint(
            project_id=project.id,
            name=name,
            source=source,
            lng=lng,
            lat=lat,
            ellipsoid_h_m=_float_or_none(row.get("ellipsoid_h_m") or row.get("height")),
            easting_m=easting,
            northing_m=northing,
            orthometric_h_m=_float_or_none(row.get("orthometric_h_m") or row.get("ortho_h")),
            horizontal_accuracy_m=_float_or_none(row.get("horizontal_accuracy_m") or row.get("h_acc")),
            vertical_accuracy_m=_float_or_none(row.get("vertical_accuracy_m") or row.get("v_acc")),
        )
        db.add(gcp)
        rows.append(gcp)
    db.flush()
    return rows


def _float_or_none(v: Any) -> float | None:
    if v is None or v == "":
        return None
    return float(v)


def ingest_las_laz(
    db: Session,
    project,
    content: bytes,
    filename: str,
    name: str,
    *,
    source: str | None = None,
) -> SurveyDataset:
    if laspy is None:
        raise RuntimeError("laspy is required for LAS/LAZ import")
    epsg = ensure_project_crs(project)
    key = f"projects/{project.id}/survey/lidar/{Path(filename).stem}.laz"
    url = save_file(key, content, "application/octet-stream")
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(content)
        tpath = tmp.name
    try:
        las = laspy.read(tpath)
        meta = {
            "point_count": int(las.header.point_count),
            "x_min": float(las.header.x_min),
            "x_max": float(las.header.x_max),
            "y_min": float(las.header.y_min),
            "y_max": float(las.header.y_max),
            "z_min": float(las.header.z_min),
            "z_max": float(las.header.z_max),
            "file_url": url,
        }
    finally:
        Path(tpath).unlink(missing_ok=True)
    ds_row = SurveyDataset(
        project_id=project.id,
        kind="lidar",
        name=name,
        storage_key=key,
        source=source,
        crs_epsg=epsg,
        accuracy_tier="visual",
        metadata_json={**meta, "processing_state": "REFERENCE_ONLY", "terrain_activation_supported": False, "vertical_reference": "UNKNOWN"},
    )
    db.add(ds_row)
    db.flush()
    return ds_row


def ingest_dxf(
    db: Session,
    project,
    content: bytes,
    name: str,
    layer_type: str = "road_centerline",
    **kwargs: Any,
) -> list[EngineeringLayer]:
    if ezdxf is None:
        raise RuntimeError("ezdxf is required for DXF import")
    epsg = ensure_project_crs(project)
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(content)
        tpath = tmp.name
    try:
        doc = ezdxf.readfile(tpath)
    finally:
        Path(tpath).unlink(missing_ok=True)
    msp = doc.modelspace()
    layers: list[EngineeringLayer] = []
    idx = 0
    for entity in msp:
        etype = entity.dxftype()
        coords: list[list[float]] = []
        if etype == "LINE":
            coords = [[entity.dxf.start.x, entity.dxf.start.y], [entity.dxf.end.x, entity.dxf.end.y]]
        elif etype == "LWPOLYLINE":
            coords = [[p[0], p[1]] for p in entity.get_points("xy")]
        elif etype == "POLYLINE":
            coords = [[v.dxf.location.x, v.dxf.location.y] for v in entity.vertices]
        else:
            continue
        if len(coords) < 2:
            continue
        geom_local = {"type": "LineString", "coordinates": coords}
        geom_wgs84 = reproject_geojson(geom_local, epsg, 4326)
        layer = EngineeringLayer(
            project_id=project.id,
            layer_type=layer_type,
            name=f"{name} {idx}",
            source="dxf",
            accuracy_tier="gis_grade",
            crs_epsg=epsg,
            geom_geojson=geom_local,
            geom_wgs84_geojson=geom_wgs84,
            **{k: v for k, v in kwargs.items() if k in ("width_m", "survey_dataset_id")},
        )
        db.add(layer)
        db.flush()
        sync_layer_postgis(db, layer, epsg)
        layers.append(layer)
        idx += 1
    if not layers:
        raise ValueError("No supported entities (LINE/LWPOLYLINE) in DXF")
    return layers


def ingest_osm_context(db: Session, project, geojson: dict, name: str = "OSM context") -> EngineeringLayer:
    return ingest_geojson_layer(
        db,
        project,
        geojson,
        "utility",
        name,
        source="osm",
        accuracy_tier="visual",
    )

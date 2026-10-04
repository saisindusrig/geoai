"""Survey Mode API — imports, GCP, validation, CRS, cut/fill."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.disclaimer import DISCLAIMER
from app.core.security import get_current_user_id
from app.db.models import (
    AccuracyReport,
    EngineeringLayer,
    GroundControlPoint,
    Project,
    SurveyDataset,
    TerrainDataset,
    TerrainDatasetVersion,
)
from app.services.survey.terrain_activation import activate_terrain
from app.db.session import IS_POSTGRES, get_db
from app.services.geospatial.crs import crs_label, estimate_utm_epsg
from app.services.survey.constants import VISUAL_BASEMAP_WARNING
from app.services.survey.cut_fill import compute_cut_fill
from app.services.survey.gcp_adjustment import compute_gcp_adjustment, layer_metadata_badge, run_validation
from app.services.survey.import_pipeline import (
    ingest_dxf,
    ingest_gcp_csv,
    ingest_geotiff,
    ingest_geojson_file,
    ingest_las_laz,
    ingest_osm_context,
    ingest_shapefile_zip,
)
from app.services.survey.project_helpers import ensure_project_crs, require_postgis
from app.services.survey.legacy_sync import sync_legacy_geometry

router = APIRouter(prefix="/api/projects/{project_id}/survey", tags=["survey"])


class GcpCreate(BaseModel):
    name: str
    source: str = "manual"
    lng: float
    lat: float
    ellipsoid_h_m: float | None = None
    easting_m: float | None = None
    northing_m: float | None = None
    orthometric_h_m: float | None = None
    horizontal_accuracy_m: float | None = None
    vertical_accuracy_m: float | None = None
    map_derived_e_m: float | None = None
    map_derived_n_m: float | None = None


class OffsetApply(BaseModel):
    offset_e_m: float
    offset_n_m: float
    offset_h_m: float = 0.0


class SurveyModeToggle(BaseModel):
    enabled: bool


class CutFillRequest(BaseModel):
    design_elevation_m: float | None = None
    road_width_m: float = 7.0

class TerrainCreate(BaseModel):
    name: str
    kind: str = "SURVEY_TERRAIN"

class TerrainActivate(BaseModel):
    expected_revision: int | None = None

@router.post("/terrain-datasets")
def create_terrain_dataset(project_id: int, payload: TerrainCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    dataset = TerrainDataset(project_id=project_id, name=payload.name, kind=payload.kind, created_by=user_id)
    db.add(dataset); db.flush()
    version = TerrainDatasetVersion(terrain_dataset_id=dataset.id, project_id=project_id, version=1)
    db.add(version); db.commit()
    return {"dataset_id": dataset.id, "version_id": version.id, "version": 1}

@router.post("/terrain-datasets/{dataset_id}/versions/{version_id}/activate")
def activate_terrain_version(project_id: int, dataset_id: int, version_id: int, payload: TerrainActivate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    try:
        active = activate_terrain(db, project_id=project_id, dataset_id=dataset_id, version_id=version_id, actor_user_id=user_id, expected_revision=payload.expected_revision)
        db.commit()
    except ValueError as exc:
        db.rollback(); raise HTTPException(422, str(exc))
    return {"dataset_id": active.terrain_dataset_id, "version_id": active.terrain_version_id, "revision": active.revision}


def _dataset_out(d: SurveyDataset) -> dict:
    return {
        "id": d.id,
        "kind": d.kind,
        "name": d.name,
        "storage_key": d.storage_key,
        "source": d.source,
        "capture_date": d.capture_date.isoformat() if d.capture_date else None,
        "crs_epsg": d.crs_epsg,
        "crs_label": crs_label(d.crs_epsg) if d.crs_epsg else None,
        "pixel_size_m": d.pixel_size_m,
        "rmse_h_m": d.rmse_h_m,
        "rmse_v_m": d.rmse_v_m,
        "accuracy_tier": d.accuracy_tier,
        "metadata_json": d.metadata_json,
        "created_at": d.created_at,
    }


def _layer_out(layer: EngineeringLayer) -> dict:
    return {
        "id": layer.id,
        "layer_type": layer.layer_type,
        "name": layer.name,
        "width_m": layer.width_m,
        "geom_wgs84_geojson": layer.geom_wgs84_geojson,
        "properties_json": layer.properties_json,
        "metadata": layer_metadata_badge(layer),
        "created_at": layer.created_at,
    }


@router.get("/status")
def survey_status(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    project = get_owned_project(project_id, db, user_id)
    return {
        "postgis_available": IS_POSTGRES,
        "survey_mode_enabled": project.survey_mode_enabled,
        "accuracy_tier": project.accuracy_tier or "visual",
        "engineering_crs_epsg": project.engineering_crs_epsg,
        "visual_warning": VISUAL_BASEMAP_WARNING,
        "disclaimer": DISCLAIMER,
    }


@router.post("/mode")
def toggle_survey_mode(
    project_id: int,
    payload: SurveyModeToggle,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if payload.enabled:
        require_postgis()
    project = get_owned_project(project_id, db, user_id)
    project.survey_mode_enabled = payload.enabled
    if payload.enabled:
        ensure_project_crs(project)
        sync_legacy_geometry(db, project)
    db.commit()
    return {"survey_mode_enabled": project.survey_mode_enabled, "engineering_crs_epsg": project.engineering_crs_epsg}


@router.get("/crs")
def get_crs(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    epsg = ensure_project_crs(project)
    db.commit()
    lng = project.origin_lng or project.center_lng or 0
    lat = project.origin_lat or project.center_lat or 0
    return {
        "engineering_crs_epsg": epsg,
        "crs_label": crs_label(epsg),
        "origin_lng": lng,
        "origin_lat": lat,
        "auto_utm_epsg": estimate_utm_epsg(lng, lat),
    }


@router.post("/import")
async def import_survey_data(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    file: UploadFile = File(...),
    format: str = Form(...),
    layer_type: str = Form("road_centerline"),
    name: str = Form("Import"),
    kind: str = Form("vector"),
    source: str | None = Form(None),
    capture_date: str | None = Form(None),
    rmse_h_m: float | None = Form(None),
    rmse_v_m: float | None = Form(None),
):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    content = await file.read()
    fmt = format.lower().strip()

    try:
        if fmt in ("geojson", "json"):
            layer = ingest_geojson_file(db, project, content, layer_type, name, source=source)
            db.commit()
            return {"type": "layer", "layer": _layer_out(layer)}
        if fmt in ("shapefile", "shp", "zip"):
            layers = ingest_shapefile_zip(db, project, content, layer_type, name, source=source)
            db.commit()
            return {"type": "layers", "layers": [_layer_out(l) for l in layers]}
        if fmt in ("geotiff", "tif", "tiff"):
            ds = ingest_geotiff(
                db, project, content, kind if kind in ("dem", "orthomosaic") else "dem", name,
                source=source, capture_date=capture_date, rmse_h_m=rmse_h_m, rmse_v_m=rmse_v_m,
            )
            db.commit()
            return {"type": "dataset", "dataset": _dataset_out(ds)}
        if fmt == "gcp_csv":
            gcps = ingest_gcp_csv(db, project, content)
            db.commit()
            return {"type": "gcps", "count": len(gcps)}
        if fmt in ("las", "laz"):
            ds = ingest_las_laz(db, project, content, file.filename or "cloud.laz", name, source=source)
            db.commit()
            return {"type": "dataset", "dataset": _dataset_out(ds)}
        if fmt == "dxf":
            layers = ingest_dxf(db, project, content, name, layer_type=layer_type)
            db.commit()
            return {"type": "layers", "layers": [_layer_out(l) for l in layers]}
        raise HTTPException(422, f"Unsupported format: {format}")
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e


@router.post("/import/osm-context")
def import_osm_context(
    project_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    layer = ingest_osm_context(db, project, payload, name="OSM context")
    db.commit()
    return _layer_out(layer)


@router.get("/datasets")
def list_datasets(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    rows = db.query(SurveyDataset).filter(SurveyDataset.project_id == project_id).all()
    return [_dataset_out(d) for d in rows]


@router.get("/layers")
def list_layers(
    project_id: int,
    layer_type: str | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    q = db.query(EngineeringLayer).filter(EngineeringLayer.project_id == project_id)
    if layer_type:
        q = q.filter(EngineeringLayer.layer_type == layer_type)
    return [_layer_out(l) for l in q.all()]


@router.post("/gcp")
def add_gcp(
    project_id: int,
    payload: GcpCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    epsg = ensure_project_crs(project)
    from app.services.geospatial.crs import wgs84_to_project

    e = payload.easting_m
    n = payload.northing_m
    if e is None or n is None:
        e, n = wgs84_to_project(payload.lng, payload.lat, epsg)
    gcp = GroundControlPoint(
        project_id=project.id,
        name=payload.name,
        source=payload.source,
        lng=payload.lng,
        lat=payload.lat,
        ellipsoid_h_m=payload.ellipsoid_h_m,
        easting_m=e,
        northing_m=n,
        orthometric_h_m=payload.orthometric_h_m,
        horizontal_accuracy_m=payload.horizontal_accuracy_m,
        vertical_accuracy_m=payload.vertical_accuracy_m,
        map_derived_e_m=payload.map_derived_e_m,
        map_derived_n_m=payload.map_derived_n_m,
    )
    db.add(gcp)
    db.commit()
    db.refresh(gcp)
    return {"id": gcp.id, "name": gcp.name}


@router.get("/gcp")
def list_gcp(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    rows = db.query(GroundControlPoint).filter(GroundControlPoint.project_id == project_id).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "source": g.source,
            "lng": g.lng,
            "lat": g.lat,
            "easting_m": g.easting_m,
            "northing_m": g.northing_m,
            "horizontal_accuracy_m": g.horizontal_accuracy_m,
            "vertical_accuracy_m": g.vertical_accuracy_m,
        }
        for g in rows
    ]


@router.get("/gcp/adjustment")
def gcp_adjustment(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    gcps = db.query(GroundControlPoint).filter(GroundControlPoint.project_id == project_id).all()
    return compute_gcp_adjustment(project, gcps)


@router.post("/gcp/apply-offset")
def apply_gcp_offset(
    project_id: int,
    payload: OffsetApply,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    project.offset_e_m = payload.offset_e_m
    project.offset_n_m = payload.offset_n_m
    project.offset_h_m = payload.offset_h_m
    db.commit()
    return {
        "offset_e_m": project.offset_e_m,
        "offset_n_m": project.offset_n_m,
        "offset_h_m": project.offset_h_m,
    }


@router.post("/validate")
def validate_survey(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    report = run_validation(db, project)
    db.commit()
    return report


@router.get("/accuracy-reports")
def list_accuracy_reports(
    project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
):
    get_owned_project(project_id, db, user_id)
    rows = (
        db.query(AccuracyReport)
        .filter(AccuracyReport.project_id == project_id)
        .order_by(AccuracyReport.created_at.desc())
        .limit(10)
        .all()
    )
    return [{"id": r.id, "tier_result": r.tier_result, "passed": r.passed, "report": r.report_json, "created_at": r.created_at} for r in rows]


@router.post("/cut-fill")
def survey_cut_fill(
    project_id: int,
    payload: CutFillRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    try:
        return compute_cut_fill(
            db, project,
            design_elevation_m=payload.design_elevation_m,
            road_width_m=payload.road_width_m,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

"""Owned, versioned engineering evidence and explicit placement operations."""
from datetime import datetime, timezone
from typing import Literal
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user_id
from app.db.session import get_db, IS_POSTGRES
from app.db.models import (ActiveTerrainConfiguration, EngineeringAnalysis, EngineeringAuditEvent,
    GroundSample, ModelPlacement, ModelRevision, ProjectMapPreferences, SurveyControlPoint,
    SurveyValidationRun, SurveyCheckpointResidual, TerrainDatasetVersion, TerrainDataset, SavedCameraView)
from app.services.survey.engineering_evidence import checkpoint_statistics, readiness
from app.services.survey.ground_resolver import resolve_ground
from app.services.survey.engineering_analysis import alignment_profile

router = APIRouter(prefix="/api/projects/{project_id}/engineering", tags=["engineering"])


class StrictPayload(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class PointInput(StrictPayload):
    name: str = Field(min_length=1, max_length=255)
    role: Literal["ADJUSTMENT", "VALIDATION_CHECKPOINT"]
    coordinates: tuple[float, float, float]
    horizontal_crs: str = Field(min_length=1)
    vertical_reference: str = Field(min_length=1)


class ResidualInput(StrictPayload):
    checkpoint_id: int
    observed: tuple[float, float, float] | None = None
    horizontal_crs: str
    vertical_reference: str
    excluded: bool = False
    exclusion_reason: str | None = None


class ValidationInput(StrictPayload):
    terrain_version_id: int
    checkpoints: list[ResidualInput] = Field(max_length=10000)


class PlacementInput(StrictPayload):
    placement_mode: Literal["GROUND_RELATIVE", "ABSOLUTE"]
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    elevation: float
    heading_deg: float = 0
    elevation_offset: float = 0
    anchor_locked: bool = True
    vertical_reference: dict
    accepted_ground_sample_id: int | None = None


class SampleInput(StrictPayload):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class TerrainVersionInput(StrictPayload):
    horizontal_crs_code: str = Field(pattern=r"^EPSG:\d+$")
    vertical_reference: Literal["ELLIPSOIDAL", "ORTHOMETRIC", "LOCAL_DATUM"]
    datum_name: str = Field(min_length=1)
    unit: Literal["METRE", "FOOT", "US_SURVEY_FOOT"]
    coverage_geojson: dict
    cesium_ion_asset_id: int = Field(gt=0)
    source: str = Field(min_length=1)
    capture_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class ProfileInput(StrictPayload):
    model_revision_id: int
    station_interval_m: Literal[10, 20, 50] = 20
    proposed_elevation_m: float | None = None


@router.post("/analyses/profile")
def calculate_profile(project_id: int, payload: ProfileInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    project = get_owned_project(project_id, db, user_id)
    if db.get_bind().dialect.name != "postgresql":
        raise HTTPException(503, "Profile analysis requires authoritative PostGIS terrain; SQLite supports visual context only")
    revision = db.query(ModelRevision).filter_by(id=payload.model_revision_id, project_id=project_id).one_or_none()
    if not revision:
        raise HTTPException(404, "Model revision not found")
    if not project.alignment_geojson or project.alignment_geojson.get("type") != "LineString":
        raise HTTPException(422, "A project alignment is required")
    active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).one_or_none()
    if not active:
        raise HTTPException(422, "Activate a resolved terrain version before analysis")
    if not project.engineering_crs_epsg:
        raise HTTPException(422, "Resolve a metric project CRS before calculating chainage")
    stations = db.execute(text("""
        WITH line AS (SELECT ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:alignment),4326),:crs) AS geom),
        length AS (SELECT geom, ST_Length(geom) AS metres FROM line),
        stations AS (SELECT geom, metres, LEAST(n * :interval,metres) AS chainage
          FROM length CROSS JOIN LATERAL generate_series(0,CEIL(metres/:interval)::integer) n WHERE metres > 0)
        SELECT chainage, ST_X(ST_Transform(ST_LineInterpolatePoint(geom,chainage/metres),4326)) AS longitude,
               ST_Y(ST_Transform(ST_LineInterpolatePoint(geom,chainage/metres),4326)) AS latitude FROM stations
        ORDER BY chainage
    """), {"alignment": json.dumps(project.alignment_geojson), "interval": payload.station_interval_m, "crs": project.engineering_crs_epsg}).mappings().all()
    if len(stations) > 10000:
        raise HTTPException(422, "Alignment exceeds the analysis station limit")
    rows = []
    for station in stations:
        sample = resolve_ground(db, project_id, station["longitude"], station["latitude"])
        rows.append({"chainage_m": station["chainage"], "longitude": station["longitude"], "latitude": station["latitude"],
            "ground_elevation_m": sample["elevation"], "proposed_elevation_m": payload.proposed_elevation_m,
            "source": sample["source"], "terrain_version_id": sample["terrain_version_id"], "sample_status": sample["status"], "sampled_at": sample["sampled_at"]})
    profile = alignment_profile(rows)
    status = "VALID" if profile and all(r["sample_status"] == "VALID" for r in profile) else "UNKNOWN"
    result = {"stations": profile, "uncertainty": "UNKNOWN", "measurement_class": "SURVEY-DERIVED", "earthwork_authoritative": False,
        "horizontal_crs": "EPSG:4326", "proposed_surface": "Explicit constant elevation" if payload.proposed_elevation_m is not None else "UNKNOWN"}
    analysis = EngineeringAnalysis(project_id=project_id, model_revision_id=revision.id, terrain_version_id=active.terrain_version_id,
        analysis_type="PROFILE", algorithm_version="alignment-profile/1", status=status, result_json=result, actor_user_id=user_id)
    db.add(analysis); db.flush()
    audit(db, project_id, user_id, "analysis.profile", after={"analysis_id": analysis.id, "model_revision_id": revision.id, "status": status}, terrain_version_id=active.terrain_version_id)
    db.commit()
    return {"id": analysis.id, "status": status, **result}


@router.get("/analyses")
def analyses(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    rows = db.query(EngineeringAnalysis).filter_by(project_id=project_id).order_by(EngineeringAnalysis.id.desc()).limit(100).all()
    return [{"id": r.id, "type": r.analysis_type, "status": r.status, "model_revision_id": r.model_revision_id, "terrain_version_id": r.terrain_version_id,
        "constraint_versions": r.constraint_versions_json, "dependencies": r.dependency_ids_json, "algorithm_version": r.algorithm_version, "timestamp": r.created_at.isoformat(), "actor": r.actor_user_id, "result": r.result_json} for r in rows]


@router.get("/revisions/{revision_id}/spatial-manifest")
def spatial_manifest(project_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    revision = db.query(ModelRevision).filter_by(id=revision_id, project_id=project_id).one_or_none()
    if not revision:
        raise HTTPException(404, "Model revision not found")
    placement = get_placement(project_id, revision_id, db, user_id)["placement"]
    site = evidence(project_id, db, user_id)
    result = {"manifest_version": 1, "project_id": project_id, "model_revision_id": revision_id, "placement": placement,
        "horizontal_crs": site["evidence"]["horizontal_crs"], "vertical_reference": site["evidence"]["vertical_reference"],
        "units": "METRE", "local_axis_convention": "EAST_NORTH_UP", "readiness": site["readiness"], "validation": site["evidence"]["validation"],
        "terrain": site["evidence"]["terrain"], "timestamp": datetime.now(timezone.utc).isoformat()}
    audit(db, project_id, user_id, "export.spatial_manifest", after={"model_revision_id": revision_id, "readiness": site["readiness"]})
    db.commit()
    return result


class CameraInput(StrictPayload):
    name: str = Field(min_length=1, max_length=100)
    position: tuple[float, float, float]
    heading: float
    pitch: float
    roll: float
    target: tuple[float, float, float] | None = None
    projection: Literal["PERSPECTIVE", "ORTHOGRAPHIC"]


class MapPreferencesInput(StrictPayload):
    preset: Literal["ENGINEERING", "REALISTIC", "SUN_STUDY", "SURVEY_QA"]
    quality: Literal["PERFORMANCE", "BALANCED", "HIGH_DETAIL"]
    shadows: Literal["OFF", "BALANCED", "HIGH"]
    utc: str
    timeZone: str

    @field_validator("utc")
    @classmethod
    def valid_utc(cls, value):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("UTC timestamp requires a timezone")
        return parsed.astimezone(timezone.utc).isoformat()

    @field_validator("timeZone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Unknown IANA timezone")
        return value


@router.get("/map-preferences")
def map_preferences(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = db.query(ProjectMapPreferences).filter_by(project_id=project_id).one_or_none()
    return {"preferences": row.preferences_json if row else None}


@router.put("/map-preferences")
def save_map_preferences(project_id: int, payload: MapPreferencesInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = db.query(ProjectMapPreferences).filter_by(project_id=project_id).one_or_none()
    if row is None:
        row = ProjectMapPreferences(project_id=project_id)
        db.add(row)
    row.preferences_json = payload.model_dump()
    db.commit()
    return {"saved": True}


@router.get("/camera-views")
def camera_views(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    return [{"id": row.id, "name": row.name, **row.camera_json} for row in db.query(SavedCameraView).filter_by(project_id=project_id).all()]


@router.post("/camera-views")
def save_camera_view(project_id: int, payload: CameraInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = SavedCameraView(project_id=project_id, name=payload.name, camera_json=payload.model_dump(exclude={"name"}))
    db.add(row); db.commit()
    return {"id": row.id}


@router.post("/terrain-datasets/{dataset_id}/versions")
def create_version(project_id: int, dataset_id: int, payload: TerrainVersionInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    dataset = db.query(TerrainDataset).filter_by(id=dataset_id, project_id=project_id).with_for_update().one_or_none()
    if not dataset:
        raise HTTPException(404, "Terrain dataset not found")
    coverage = payload.coverage_geojson
    if coverage.get("type") not in ("Polygon", "MultiPolygon"):
        raise HTTPException(422, "Coverage must be a WGS84 Polygon or MultiPolygon")
    polygons = [coverage.get("coordinates", [])] if coverage["type"] == "Polygon" else coverage.get("coordinates", [])
    try:
        for polygon in polygons:
            if not polygon:
                raise ValueError()
            for ring in polygon:
                if len(ring) < 4 or ring[0] != ring[-1] or any(len(p) != 2 or not -180 <= p[0] <= 180 or not -90 <= p[1] <= 90 for p in ring):
                    raise ValueError()
        if not polygons:
            raise ValueError()
        datetime.strptime(payload.capture_date, "%Y-%m-%d")
    except (ValueError, TypeError, IndexError):
        raise HTTPException(422, "Invalid coverage coordinates or capture date")
    if db.get_bind().dialect.name == "postgresql":
        valid = db.execute(text("SELECT ST_IsValid(ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))"), {"geometry": json.dumps(coverage)}).scalar()
        if not valid:
            raise HTTPException(422, "Coverage is not a valid PostGIS geometry")
    latest = db.query(TerrainDatasetVersion).filter_by(terrain_dataset_id=dataset_id).order_by(TerrainDatasetVersion.version.desc()).first()
    resolved = payload.vertical_reference == "ELLIPSOIDAL" and payload.unit == "METRE"
    row = TerrainDatasetVersion(project_id=project_id, terrain_dataset_id=dataset_id, version=(latest.version + 1 if latest else 1),
        processing_state="READY" if resolved else "METADATA_REQUIRED", horizontal_crs_type="WGS84_GEOGRAPHIC" if payload.horizontal_crs_code == "EPSG:4326" else "PROJECTED",
        horizontal_crs_code=payload.horizontal_crs_code, source_unit=payload.unit,
        vertical_reference_json={"type": payload.vertical_reference, "datumName": payload.datum_name, "unit": payload.unit, "source": payload.source, "captureDate": payload.capture_date},
        vertical_resolution_state="RESOLVED" if resolved else "UNSUPPORTED", coverage_geojson=coverage, cesium_ion_asset_id=payload.cesium_ion_asset_id)
    db.add(row); db.flush()
    audit(db, project_id, user_id, "terrain.version.created", after={"dataset_id": dataset_id, "version_id": row.id, **payload.model_dump()}, terrain_version_id=row.id)
    db.commit()
    return {"id": row.id, "version": row.version, "state": row.processing_state, "activation_block": None if resolved else "Verified unit/datum conversion is required; no conversion is assumed"}


@router.get("/terrain-datasets")
def terrain_datasets(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).one_or_none()
    rows = db.query(TerrainDatasetVersion).filter_by(project_id=project_id).order_by(TerrainDatasetVersion.id.desc()).all()
    return {"active_version_id": active.terrain_version_id if active else None, "versions": [{"id": r.id, "dataset_id": r.terrain_dataset_id, "version": r.version,
        "state": r.processing_state, "horizontal_crs": r.horizontal_crs_code, "vertical_reference": r.vertical_reference_json,
        "unit": r.source_unit, "coverage": r.coverage_geojson, "ion_asset_id": r.cesium_ion_asset_id, "validation_status": r.validation_state} for r in rows]}


@router.post("/ground-samples")
def ground_sample(project_id: int, payload: SampleInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    result = resolve_ground(db, project_id, payload.longitude, payload.latitude)
    row = GroundSample(project_id=project_id, longitude=payload.longitude, latitude=payload.latitude,
        elevation=result["elevation"], status=result["status"], source=result["source"],
        terrain_dataset_id=result["terrain_dataset_id"], terrain_version_id=result["terrain_version_id"],
        vertical_reference_json=result["vertical_reference"], failure_reason=result["failure_reason"], sampled_at=datetime.now(timezone.utc))
    db.add(row); db.flush()
    audit(db, project_id, user_id, "terrain.sampled", after={"sample_id": row.id, **result}, terrain_version_id=row.terrain_version_id)
    db.commit()
    return {"id": row.id, **result, "project_id": project_id, "readiness": "SPATIAL_READY" if row.status == "VALID" else "VISUAL_REFERENCE"}


@router.get("/ground-samples/{sample_id}")
def sample_provenance(project_id: int, sample_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = db.query(GroundSample).filter_by(id=sample_id, project_id=project_id).one_or_none()
    if not row:
        raise HTTPException(404, "Sample not found")
    return {"project_id": project_id, "sample_id": row.id, "longitude": row.longitude, "latitude": row.latitude, "elevation": row.elevation,
        "terrain_dataset_id": row.terrain_dataset_id, "terrain_version_id": row.terrain_version_id, "vertical_reference": row.vertical_reference_json,
        "horizontal_crs": "EPSG:4326", "source": row.source, "status": row.status, "sampled_at": row.sampled_at,
        "calculation_version": "ground-sample/1", "failure_reason": row.failure_reason}


def version_for_project(db, project_id, version_id):
    version = db.query(TerrainDatasetVersion).filter_by(id=version_id, project_id=project_id).one_or_none()
    if not version:
        raise HTTPException(404, "Terrain version not found")
    return version


def audit(db, project_id, user_id, action, before=None, after=None, terrain_version_id=None):
    db.add(EngineeringAuditEvent(project_id=project_id, actor_user_id=user_id, action=action,
        before_json=before, after_json=after, terrain_version_id=terrain_version_id))


@router.post("/control-points")
def create_control(project_id: int, payload: PointInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = SurveyControlPoint(project_id=project_id, name=payload.name, role=payload.role,
        reference_json={"coordinates": payload.coordinates, "horizontal_crs": payload.horizontal_crs, "vertical_reference": payload.vertical_reference})
    db.add(row); db.flush()
    audit(db, project_id, user_id, "checkpoint.created", after={"id": row.id, **payload.model_dump()})
    db.commit()
    return {"id": row.id}


@router.post("/validation-runs")
def validate_checkpoints(project_id: int, payload: ValidationInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    version = version_for_project(db, project_id, payload.terrain_version_id)
    if len({p.checkpoint_id for p in payload.checkpoints}) != len(payload.checkpoints):
        raise HTTPException(422, "Duplicate checkpoint identifiers")
    points = []
    for observation in payload.checkpoints:
        point = db.query(SurveyControlPoint).filter_by(id=observation.checkpoint_id, project_id=project_id).one_or_none()
        if not point:
            raise HTTPException(404, "Checkpoint not found for this project")
        reference = point.reference_json
        if observation.excluded and not observation.exclusion_reason:
            raise HTTPException(422, "Checkpoint exclusion requires a reason")
        points.append({"id": point.id, "role": point.role, "observed": observation.observed or [], "reference": reference["coordinates"],
            "same_reference": observation.horizontal_crs == reference["horizontal_crs"] and observation.vertical_reference == reference["vertical_reference"],
            "excluded": observation.excluded, "exclusion_reason": observation.exclusion_reason})
    result = checkpoint_statistics(points)
    result.update(terrain_version_id=version.id, algorithm_version="independent-xyz/1", calculated_at=datetime.now(timezone.utc).isoformat())
    passed = result["valid_count"] >= 3 and result["invalid_count"] == 0 and result["horizontal_rmse_m"] <= .05 and result["vertical_rmse_m"] <= .1
    run = SurveyValidationRun(project_id=project_id, terrain_version_id=version.id, algorithm_version="independent-xyz/1",
        actor_user_id=user_id, status="VALID" if passed else "WARNING", result_json=result)
    db.add(run); db.flush()
    for residual in result["residuals"]:
        db.add(SurveyCheckpointResidual(validation_run_id=run.id, checkpoint_id=residual["checkpoint_id"], status=residual["status"], result_json=residual))
    audit(db, project_id, user_id, "validation.executed", after={"run_id": run.id, "status": run.status}, terrain_version_id=version.id)
    db.commit()
    return {"id": run.id, "status": run.status, **result}


@router.get("/evidence")
def evidence(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    project = get_owned_project(project_id, db, user_id)
    active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).one_or_none()
    version = version_for_project(db, project_id, active.terrain_version_id) if active else None
    run = db.query(SurveyValidationRun).filter_by(project_id=project_id, terrain_version_id=version.id).order_by(SurveyValidationRun.id.desc()).first() if version else None
    raster_available = False
    if IS_POSTGRES and version:
        raster_table = db.execute(text("SELECT to_regclass('engineering_terrain_rasters')")).scalar()
        if raster_table:
            raster_available = bool(db.execute(text("SELECT EXISTS(SELECT 1 FROM engineering_terrain_rasters WHERE project_id=:project AND terrain_version_id=:version)"), {"project": project_id, "version": version.id}).scalar())
    states = {
        "horizontal_crs": {"status": "VALID" if version and version.horizontal_crs_code else "MISSING", "value": version.horizontal_crs_code if version else None},
        "vertical_reference": {"status": "VALID" if version and version.vertical_resolution_state == "RESOLVED" else "MISSING", "value": version.vertical_reference_json if version else None},
        "units": {"status": "VALID" if version and version.source_unit != "UNKNOWN" else "MISSING", "value": version.source_unit if version else None},
        "terrain": {"status": "VALID" if version and version.processing_state == "READY" else "MISSING", "dataset_id": active.terrain_dataset_id if active else None, "version_id": version.id if version else None},
        "coverage": {"status": "VALID" if version and version.coverage_geojson else "MISSING", "value": version.coverage_geojson if version else None},
        "validation": {"status": run.status if run else "MISSING", "value": run.result_json if run else None, "date": run.created_at.isoformat() if run else None},
        "spatial_backend": {"status": "VALID" if IS_POSTGRES else "UNSUPPORTED", "value": "PostGIS" if IS_POSTGRES else "SQLite — reference only"},
        "authoritative_raster": {"status": "VALID" if raster_available else "MISSING", "value": "Accepted terrain raster" if raster_available else "Renderer terrain alone is insufficient for server-side survey validation"},
    }
    ready = readiness(dict(terrain_available=bool(version), imagery_available=True,
        horizontal_crs_resolved=states["horizontal_crs"]["status"] == "VALID", vertical_reference_resolved=states["vertical_reference"]["status"] == "VALID",
        units_resolved=states["units"]["status"] == "VALID", coverage_verified=states["coverage"]["status"] == "VALID",
        survey_authoritative=IS_POSTGRES and raster_available, validation_status=run.status if run else "MISSING", checkpoint_statistics=run.result_json if run else {}))
    return {"project_id": project.id, "readiness": ready, "evidence": states, "measurement_class": "SURVEY-DERIVED" if ready == "SURVEY_READY" else "VISUAL"}


@router.put("/placements/{revision_id}")
def put_placement(project_id: int, revision_id: int, payload: PlacementInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    revision = db.query(ModelRevision).filter_by(id=revision_id, project_id=project_id).one_or_none()
    if not revision:
        raise HTTPException(404, "Model revision not found")
    if payload.vertical_reference.get("type") != "ELLIPSOIDAL":
        raise HTTPException(422, "Convert the anchor to a resolved ellipsoidal reference before placement")
    sample = None
    if payload.placement_mode == "GROUND_RELATIVE":
        sample = db.query(GroundSample).filter_by(id=payload.accepted_ground_sample_id, project_id=project_id).one_or_none()
        active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).one_or_none()
        if not sample or sample.status != "VALID" or sample.elevation is None or not active or sample.terrain_version_id != active.terrain_version_id:
            raise HTTPException(422, "A current, valid ground sample is required")
        if abs(sample.longitude - payload.longitude) > 1e-8 or abs(sample.latitude - payload.latitude) > 1e-8:
            raise HTTPException(422, "Ground sample does not match the anchor")
        if sample.vertical_reference_json != payload.vertical_reference:
            raise HTTPException(422, "Ground sample vertical reference does not match the anchor")
    placement = db.query(ModelPlacement).filter_by(project_id=project_id, model_revision_id=revision_id).one_or_none()
    before = {"longitude": placement.anchor_longitude, "latitude": placement.anchor_latitude, "elevation": placement.anchor_elevation} if placement else None
    if not placement:
        placement = ModelPlacement(project_id=project_id, model_revision_id=revision_id)
        db.add(placement)
    placement.placement_mode = payload.placement_mode
    placement.height_reference = "TERRAIN" if sample else "ELLIPSOID"
    placement.anchor_longitude, placement.anchor_latitude = payload.longitude, payload.latitude
    placement.anchor_elevation = sample.elevation if sample else payload.elevation
    placement.elevation_resolution = "RESOLVED"
    placement.elevation_provenance_json = {"source": "ACCEPTED_SAMPLE" if sample else "USER_PROVIDED",
                                         "ground_sample_id": sample.id if sample else None}
    placement.anchor_heading_deg = payload.heading_deg % 360
    placement.elevation_offset, placement.anchor_locked = payload.elevation_offset, payload.anchor_locked
    placement.anchor_vertical_reference_json = payload.vertical_reference
    placement.accepted_ground_sample_id = sample.id if sample else None
    placement.terrain_dataset_id = sample.terrain_dataset_id if sample else None
    placement.terrain_version_id = sample.terrain_version_id if sample else None
    placement.placement_state = "VALID"
    audit(db, project_id, user_id, "placement.accepted", before=before, after=payload.model_dump(), terrain_version_id=placement.terrain_version_id)
    db.commit()
    return {"id": placement.id, "status": placement.placement_state, "anchor_elevation": placement.anchor_elevation}


@router.get("/placements/{revision_id}")
def get_placement(project_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = db.query(ModelPlacement).filter_by(project_id=project_id, model_revision_id=revision_id).one_or_none()
    if not row:
        return {"placement": None}
    return {"placement": {"mode": row.placement_mode, "status": row.placement_state, "longitude": row.anchor_longitude,
        "latitude": row.anchor_latitude, "elevation": row.anchor_elevation if row.elevation_resolution == "RESOLVED" else None, "offset": row.elevation_offset,
        "elevation_resolution": row.elevation_resolution, "elevation_provenance": row.elevation_provenance_json,
        "legacy_display_elevation": row.anchor_elevation if row.elevation_resolution == "LEGACY_UNRESOLVED" else (row.elevation_provenance_json or {}).get("previous_value") if row.elevation_resolution == "UNKNOWN" else None,
        "heading": row.anchor_heading_deg, "locked": row.anchor_locked, "vertical_reference": row.anchor_vertical_reference_json,
        "terrain_version_id": row.terrain_version_id, "ground_sample_id": row.accepted_ground_sample_id}}


@router.get("/log")
def engineering_log(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    rows = db.query(EngineeringAuditEvent).filter_by(project_id=project_id).order_by(EngineeringAuditEvent.id.desc()).limit(200).all()
    return [{"id": r.id, "actor": r.actor_user_id, "action": r.action, "before": r.before_json, "after": r.after_json, "terrain_version_id": r.terrain_version_id, "timestamp": r.created_at.isoformat()} for r in rows]

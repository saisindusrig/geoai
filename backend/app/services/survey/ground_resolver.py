"""Authoritative survey samples use PostGIS; SQLite cannot emulate them."""
import json
from sqlalchemy import text
from app.db.models import ActiveTerrainConfiguration, TerrainDatasetVersion, TerrainDataset
from app.services.survey.engineering_evidence import sample_result


def resolve_ground(db, project_id: int, longitude: float, latitude: float) -> dict:
    unknown = lambda reason: sample_result(longitude=longitude, latitude=latitude, height=None, failure_reason=reason)
    if db.get_bind().dialect.name != "postgresql":
        return unknown("UNSUPPORTED: authoritative terrain sampling requires PostgreSQL/PostGIS")
    active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).one_or_none()
    if not active:
        return unknown("No active project terrain; world terrain is visual context only")
    version = db.query(TerrainDatasetVersion).filter_by(id=active.terrain_version_id, project_id=project_id).one_or_none()
    if not version or version.processing_state != "READY" or version.vertical_resolution_state != "RESOLVED":
        return unknown("Terrain processing or vertical reference is unresolved")
    coverage = db.execute(text("SELECT ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(:coverage),4326), ST_SetSRID(ST_MakePoint(:lng,:lat),4326))"),
        {"coverage": json.dumps(version.coverage_geojson), "lng": longitude, "lat": latitude}).scalar()
    if not coverage:
        result = unknown("Outside accepted survey coverage; public terrain is contextual")
        result["status"] = "OUTSIDE_COVERAGE"
        return result
    height = db.execute(text("""
        SELECT ST_Value(rast, 1, ST_Transform(ST_SetSRID(ST_MakePoint(:lng,:lat),4326),ST_SRID(rast)), true)
        FROM engineering_terrain_rasters
        WHERE project_id=:project AND terrain_version_id=:version
        AND ST_Intersects(rast,ST_Transform(ST_SetSRID(ST_MakePoint(:lng,:lat),4326),ST_SRID(rast)))
        ORDER BY id LIMIT 1
        """), {"lng": longitude, "lat": latitude, "project": project_id, "version": version.id}).scalar()
    dataset = db.get(TerrainDataset, active.terrain_dataset_id)
    return sample_result(longitude=longitude, latitude=latitude, height=height,
        source=dataset.kind, dataset_id=dataset.id, version_id=version.id,
        vertical_reference=version.vertical_reference_json,
        failure_reason="NoData cell or raster is unavailable")

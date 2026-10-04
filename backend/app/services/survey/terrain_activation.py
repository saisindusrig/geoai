"""Atomic active-terrain selection; geometry is never changed here."""
from sqlalchemy.orm import Session
from app.db.models import ActiveTerrainConfiguration, AuditLog, GroundSample, ModelPlacement, TerrainDatasetVersion, EngineeringAnalysis, EngineeringAuditEvent, StructureGroundCheck

def activate_terrain(db: Session, *, project_id: int, dataset_id: int, version_id: int, actor_user_id: int, expected_revision: int | None = None):
    version = db.query(TerrainDatasetVersion).filter_by(id=version_id, project_id=project_id, terrain_dataset_id=dataset_id).with_for_update().one_or_none()
    if not version:
        raise ValueError("Terrain version was not found for this project")
    if version.processing_state != "READY":
        raise ValueError("Terrain version must be READY before activation")
    if version.horizontal_crs_type == "UNKNOWN" or version.vertical_resolution_state != "RESOLVED" or version.source_unit == "UNKNOWN":
        raise ValueError("Terrain CRS, vertical reference, and units must be resolved before activation")
    if version.cesium_ion_asset_id is None:
        raise ValueError("Terrain version requires a Cesium ion asset before activation")
    if not version.coverage_geojson or not version.vertical_reference_json:
        raise ValueError("Terrain coverage and vertical reference metadata are required")
    active = db.query(ActiveTerrainConfiguration).filter_by(project_id=project_id).with_for_update().one_or_none()
    if active and expected_revision is not None and active.revision != expected_revision:
        raise ValueError("Active terrain changed; reload and try again")
    previous = active.terrain_version_id if active else None
    if previous == version_id:
        return active
    if active is None:
        active = ActiveTerrainConfiguration(project_id=project_id, terrain_dataset_id=dataset_id, terrain_version_id=version_id, activated_by=actor_user_id)
        db.add(active)
    else:
        active.terrain_dataset_id, active.terrain_version_id, active.activated_by, active.revision = dataset_id, version_id, actor_user_id, active.revision + 1
    placements = db.query(ModelPlacement).filter_by(project_id=project_id).all()
    for placement in placements:
        changed = previous != version_id
        if not changed:
            continue
        if placement.placement_mode == "GROUND_RELATIVE":
            placement.placement_state = "REVIEW_REQUIRED"
        db.query(GroundSample).filter_by(placement_id=placement.id).filter(GroundSample.source != "NONE").update({"status": "STALE"}, synchronize_session=False)
    db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.terrain_version_id != version_id).update({"status": "STALE"}, synchronize_session=False)
    db.query(StructureGroundCheck).filter_by(project_id=project_id).update({"status": "STALE"}, synchronize_session=False)
    db.add(EngineeringAuditEvent(project_id=project_id, actor_user_id=actor_user_id, action="terrain.activated", terrain_version_id=version_id, before_json={"version_id": previous}, after_json={"version_id": version_id, "dataset_id": dataset_id}))
    db.add(AuditLog(user_id=actor_user_id, project_id=project_id, action="terrain.activated", entity_type="terrain_dataset_version", entity_id=str(version_id), metadata_json={"previous_version_id": previous, "dataset_id": dataset_id, "revision": active.revision}))
    db.flush()
    return active

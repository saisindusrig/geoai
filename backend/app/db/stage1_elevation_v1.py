"""Conservative, audited migration classifier. Never guesses from zero alone."""
from datetime import datetime, timezone
import sqlalchemy as sa


def backfill(connection):
    metadata = sa.MetaData()
    placements = sa.Table("model_placements", metadata, autoload_with=connection)
    revisions = sa.Table("model_revisions", metadata, autoload_with=connection)
    samples = sa.Table("ground_samples", metadata, autoload_with=connection)
    audit = sa.Table("audit_logs", metadata, autoload_with=connection)
    for row in connection.execute(sa.select(placements)).mappings().all():
        if row["elevation_provenance_json"] is not None:
            continue
        value = row["anchor_elevation"]
        revision = connection.execute(sa.select(revisions.c.document_json).where(
            revisions.c.id == row["model_revision_id"], revisions.c.project_id == row["project_id"])).scalar() or {}
        sample = connection.execute(sa.select(samples).where(samples.c.id == row["accepted_ground_sample_id"],
            samples.c.project_id == row["project_id"])).mappings().first()
        valid_sample = bool(sample and sample["source"] != "NONE" and sample["status"] in {"VALID", "STALE"}
            and sample["elevation"] is not None and sample["elevation"] == value
            and sample["longitude"] == row["anchor_longitude"] and sample["latitude"] == row["anchor_latitude"]
            and sample["vertical_reference_json"] and sample["vertical_reference_json"] == row["anchor_vertical_reference_json"])
        # Explicitly accepted placement is evidence of a recorded altitude, NOT
        # a claim of survey accuracy or engineering readiness.
        accepted = connection.execute(sa.select(audit.c.id).where(
            audit.c.project_id == row["project_id"], audit.c.action == "placement.accepted",
            audit.c.entity_id == str(row["id"]))).scalar()
        recorded = value is not None and bool(row["anchor_vertical_reference_json"]) and bool(accepted)
        explicit_unknown = revision.get("metadata", {}).get("elevation_known") is False
        if valid_sample or recorded:
            state, reason = "RESOLVED", "ACCEPTED_SAMPLE" if valid_sample else "ACCEPTED_PLACEMENT"
        elif value is None:
            state, reason = "UNKNOWN", "NULL_ELEVATION"
        elif value == 0 and explicit_unknown and row["legacy_placement"] and not row["anchor_vertical_reference_json"]:
            state, reason, value = "UNKNOWN", "EXPLICIT_LEGACY_UNKNOWN_DEFAULT", None
        else:
            state, reason = "LEGACY_UNRESOLVED", "PRESERVED_WITHOUT_SUFFICIENT_PROVENANCE"
        provenance = {"migration": "009", "reason": reason, "previous_value": row["anchor_elevation"],
                      "ground_sample_id": row["accepted_ground_sample_id"] if valid_sample else None}
        connection.execute(placements.update().where(placements.c.id == row["id"]).values(
            anchor_elevation=value, elevation_resolution=state, elevation_provenance_json=provenance))
        connection.execute(audit.insert().values(project_id=row["project_id"], action="placement.elevation_migrated",
            entity_type="model_placement", entity_id=str(row["id"]), metadata_json=provenance | {"resolution": state},
            created_at=datetime.now(timezone.utc)))

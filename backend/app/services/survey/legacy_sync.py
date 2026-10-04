"""Sync legacy GeoJSON boundary/alignment into engineering_layers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import EngineeringLayer, Project
from app.services.survey.import_pipeline import ingest_geojson_layer


def sync_legacy_geometry(db: Session, project: Project) -> None:
    existing_types = {
        row[0]
        for row in db.query(EngineeringLayer.layer_type)
        .filter(EngineeringLayer.project_id == project.id)
        .all()
    }
    if project.boundary_geojson and "parcel" not in existing_types:
        ingest_geojson_layer(
            db,
            project,
            {"type": "Feature", "geometry": project.boundary_geojson, "properties": {}},
            "parcel",
            "Project boundary",
            source="legacy_boundary",
            accuracy_tier="visual",
        )
    if project.alignment_geojson and "road_centerline" not in existing_types:
        ingest_geojson_layer(
            db,
            project,
            {"type": "Feature", "geometry": project.alignment_geojson, "properties": {}},
            "road_centerline",
            "Project alignment",
            source="legacy_alignment",
            accuracy_tier="visual",
        )

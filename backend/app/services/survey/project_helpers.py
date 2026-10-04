"""Survey project helpers — CRS setup, PostGIS gate, layer sync."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import text

from app.db.session import IS_POSTGRES
from app.services.geospatial.crs import estimate_utm_epsg, reproject_geojson, wgs84_to_project

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db.models import EngineeringLayer, Project

POSTGIS_REQUIRED_MSG = (
    "Survey Mode requires PostgreSQL with PostGIS. "
    "Start Docker services (docker compose up -d) and set DATABASE_URL to the PostGIS instance."
)


def require_postgis() -> None:
    if not IS_POSTGRES:
        raise HTTPException(503, POSTGIS_REQUIRED_MSG)


def ensure_project_crs(project: Project) -> int:
    if project.engineering_crs_epsg:
        return project.engineering_crs_epsg
    lng = project.center_lng or project.origin_lng or 77.5946
    lat = project.center_lat or project.origin_lat or 12.9716
    epsg = estimate_utm_epsg(lng, lat)
    project.engineering_crs_epsg = epsg
    project.origin_lng = lng
    project.origin_lat = lat
    return epsg


def wgs84_geom_to_project(geojson_wgs84: dict, project_epsg: int) -> dict:
    return reproject_geojson(geojson_wgs84, 4326, project_epsg)


def sync_layer_postgis(db: Session, layer: EngineeringLayer, project_epsg: int) -> None:
    if not IS_POSTGRES or layer.geom_geojson is None:
        return
    db.execute(
        text(
            """
            UPDATE engineering_layers
            SET geom = ST_SetSRID(ST_GeomFromGeoJSON(:gj), :srid)
            WHERE id = :id
            """
        ),
        {"gj": json.dumps(layer.geom_geojson), "srid": project_epsg, "id": layer.id},
    )


def tier_at_least(current: str, required: str) -> bool:
    from app.services.survey.constants import TIER_RANK

    return TIER_RANK.get(current, 0) >= TIER_RANK.get(required, 0)


def require_survey_tier(project: Project, minimum: str = "survey_grade") -> None:
    if not tier_at_least(project.accuracy_tier or "visual", minimum):
        raise HTTPException(
            403,
            f"This operation requires accuracy tier '{minimum}' or higher. "
            f"Current tier: '{project.accuracy_tier or 'visual'}'. "
            "Import survey DEM/ortho, add GCPs, and run validation.",
        )

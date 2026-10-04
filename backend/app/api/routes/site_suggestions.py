"""Site suggestion API — server-side heuristics with analysis context."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.project_catalog import project_type_family
from app.core.disclaimer import DISCLAIMER
from app.core.security import get_current_user_id
from app.db.models import SiteAnalysis
from app.db.session import get_db
from app.services.geospatial import spatial_analysis

router = APIRouter(prefix="/api/projects/{project_id}/site-suggestions", tags=["site-suggestions"])


class SiteSuggestionRequest(BaseModel):
    lng: float | None = None
    lat: float | None = None


def _client_style_suggestions(lng: float, lat: float, project_type: str, roads: list) -> list[dict]:
    """Mirror frontend heuristics for API parity."""
    family = project_type_family(project_type)
    suggestions: list[dict] = []
    if family == "building":
        presets = [
            (60, 45, "Compact plot", "Mid-rise massing (~2,700 m²)"),
            (100, 80, "Standard campus", "Institutional / commercial block"),
            (150, 120, "Large footprint", "Warehouse or multi-block"),
        ]
        for i, (w, h, label, reason) in enumerate(presets):
            ring = _rectangle(lng, lat, w, h)
            area = spatial_analysis.polygon_metrics({"type": "Polygon", "coordinates": [ring]})["area_sqm"]
            suggestions.append(
                {
                    "id": f"api-bld-{i}",
                    "label": label,
                    "reason": reason,
                    "score": 92 if 2000 < area < 15000 else 75,
                    "kind": "boundary",
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                }
            )
    elif family in ("flyover", "road", "pipeline"):
        lengths = [400, 600, 800] if family != "pipeline" else [300, 500, 700]
        for i, length in enumerate(lengths):
            line = _line_from_center(lng, lat, length, 90 if i % 2 else 0)
            suggestions.append(
                {
                    "id": f"api-align-{i}",
                    "label": f"{length} m corridor",
                    "reason": f"Aligned {'E–W' if i % 2 else 'N–S'} corridor",
                    "score": 88 - i * 3,
                    "kind": "alignment",
                    "geometry": line,
                }
            )
    return suggestions[:6]


def _rectangle(lng: float, lat: float, width_m: float, height_m: float) -> list:
    dlat = height_m / 111320
    dlng = width_m / (111320 * max(0.3, abs(__import__("math").cos(__import__("math").radians(lat)))))
    return [
        [lng - dlng / 2, lat - dlat / 2],
        [lng + dlng / 2, lat - dlat / 2],
        [lng + dlng / 2, lat + dlat / 2],
        [lng - dlng / 2, lat + dlat / 2],
        [lng - dlng / 2, lat - dlat / 2],
    ]


def _line_from_center(lng: float, lat: float, length_m: float, bearing_deg: float) -> dict:
    import math

    br = math.radians(bearing_deg)
    dlat = (length_m / 2) * math.cos(br) / 111320
    dlng = (length_m / 2) * math.sin(br) / (111320 * max(0.3, abs(math.cos(math.radians(lat)))))
    return {
        "type": "LineString",
        "coordinates": [[lng - dlng, lat - dlat], [lng + dlng, lat + dlat]],
    }


def _building_clashes(suggestion_geom: dict, buildings: list) -> list[str]:
    if suggestion_geom.get("type") != "Polygon":
        return []
    clashes = spatial_analysis.find_intersections(suggestion_geom, buildings)
    return [f"Overlaps {c.get('name', c.get('category', 'building'))}" for c in clashes]


@router.post("")
def suggest_sites(
    project_id: int,
    payload: SiteSuggestionRequest | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    payload = payload or SiteSuggestionRequest()
    lng = payload.lng if payload.lng is not None else (project.center_lng or 77.5946)
    lat = payload.lat if payload.lat is not None else (project.center_lat or 12.9716)

    analysis = (
        db.query(SiteAnalysis)
        .filter(SiteAnalysis.project_id == project_id)
        .order_by(SiteAnalysis.created_at.desc())
        .first()
    )
    roads = []
    buildings = []
    if analysis:
        roads = (analysis.nearby_roads_json or {}).get("features", [])
        buildings = (analysis.existing_buildings_json or {}).get("features", [])

    suggestions = _client_style_suggestions(lng, lat, project.project_type, roads)
    for s in suggestions:
        s["building_clashes"] = _building_clashes(s["geometry"], buildings)

    return {"suggestions": suggestions, "disclaimer": DISCLAIMER}

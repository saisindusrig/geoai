"""Safe, constrained bridge-concept planning backed by Nebius Token Factory."""

from __future__ import annotations

import json
import math
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings


class GeoPoint(BaseModel):
    lng: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)
    elevation_m: float | None = Field(default=None, ge=-500, le=9000)


class SiteContext(BaseModel):
    start: GeoPoint
    end: GeoPoint
    crossing: Literal["waterway", "road", "terrain", "unknown"] = "unknown"
    terrain_slope_pct: float = Field(default=0, ge=0, le=100)
    nearby_buildings: int = Field(default=0, ge=0, le=10000)
    nearby_roads: int = Field(default=0, ge=0, le=10000)

    @property
    def span_m(self) -> float:
        """Haversine distance. Visual context only, never a survey measurement."""
        radius_m = 6_371_000
        lat1, lat2 = math.radians(self.start.lat), math.radians(self.end.lat)
        d_lat = lat2 - lat1
        d_lng = math.radians(self.end.lng - self.start.lng)
        a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
        return max(1.0, 2 * radius_m * math.asin(math.sqrt(a)))


class BridgeSpec(BaseModel):
    bridge_type: Literal["pedestrian_bridge"] = "pedestrian_bridge"
    structure_type: Literal["steel_truss", "steel_girder"] = "steel_girder"
    width_m: float = Field(default=4, ge=2, le=8)
    deck_elevation_m: float = Field(default=5, ge=2.5, le=15)
    supports: int = Field(default=2, ge=0, le=8)
    deck_material: Literal["concrete"] = "concrete"
    structure_material: Literal["steel"] = "steel"
    railings: bool = True
    stages: list[Literal["foundation", "supports", "steel", "deck", "finished"]] = [
        "foundation", "supports", "steel", "deck", "finished"
    ]


class BridgePlan(BaseModel):
    summary: str = Field(min_length=10, max_length=600)
    spec: BridgeSpec
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    warnings: list[str] = Field(default_factory=list, max_length=8)
    explanation: str = Field(min_length=10, max_length=1200)


ConstructionType = Literal["bridge", "flyover", "building", "road", "pipeline", "dam"]


class ConstructionSpec(BaseModel):
    project_type: ConstructionType
    width_m: float = Field(ge=2, le=80)
    length_m: float = Field(ge=10, le=2000)
    height_m: float = Field(ge=1, le=150)
    supports: int = Field(ge=0, le=80)
    style: str = Field(min_length=3, max_length=120)
    stages: list[Literal["site", "foundation", "structure", "finish"]]


class ConstructionPlan(BaseModel):
    summary: str = Field(min_length=10, max_length=600)
    spec: ConstructionSpec
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    warnings: list[str] = Field(default_factory=list, max_length=8)
    explanation: str = Field(min_length=10, max_length=1200)


_CONSTRUCTION_DEFAULTS: dict[str, dict[str, object]] = {
    "bridge": {"width_m": 4, "length_m": 72, "height_m": 6, "supports": 2, "style": "steel truss"},
    "flyover": {"width_m": 12, "length_m": 180, "height_m": 8, "supports": 6, "style": "concrete viaduct"},
    "building": {"width_m": 30, "length_m": 42, "height_m": 24, "supports": 0, "style": "mid-rise massing"},
    "road": {"width_m": 9, "length_m": 220, "height_m": 1, "supports": 0, "style": "two-lane corridor"},
    "pipeline": {"width_m": 2, "length_m": 180, "height_m": 2, "supports": 4, "style": "utility corridor"},
    "dam": {"width_m": 36, "length_m": 120, "height_m": 28, "supports": 0, "style": "concrete gravity dam"},
}


def _fallback_construction_plan(
    project_type: ConstructionType, request: str, site: SiteContext, current: ConstructionSpec | None = None
) -> ConstructionPlan:
    """Offline, constrained concept preview for every supported construction type."""
    import re

    spec = current.model_copy() if current else ConstructionSpec(
        project_type=project_type, **_CONSTRUCTION_DEFAULTS[project_type], stages=["site", "foundation", "structure", "finish"]
    )
    spec.project_type = project_type
    text = request.lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|metre|meter)\s*(?:wide|width)", text)
    if match:
        spec.width_m = min(80, max(2, float(match.group(1))))
    if "longer" in text or "long" in text:
        spec.length_m = min(2000, round(spec.length_m * 1.25))
    if "concrete" in text:
        spec.style = "concrete gravity dam" if project_type == "dam" else "concrete structure"
    if "truss" in text:
        spec.style = "steel truss"
    return ConstructionPlan(
        summary=f"Conceptual {project_type.replace('_', ' ')} for a {site.span_m:.0f}m map-derived context span.",
        spec=spec,
        assumptions=[
            "Map coordinates and span are visual context, not survey data.",
            "Qualified review is required for site conditions, safety, structure, cost, permits, and construction.",
        ],
        warnings=["Offline demo fallback used because Nebius Token Factory is not configured."],
        explanation="The constrained local preview generated an editable construction concept. Configure NEBIUS_API_KEY to use Nemotron planning.",
    )


def _fallback_plan(request: str, site: SiteContext, current: BridgeSpec | None = None) -> BridgePlan:
    """A clearly labeled offline demo plan; it is not presented as AI output."""
    text = request.lower()
    spec = current.model_copy() if current else BridgeSpec()
    if "truss" in text:
        spec.structure_type = "steel_truss"
    if "girder" in text or "beam" in text:
        spec.structure_type = "steel_girder"
    if "wider" in text or "width" in text or "wide" in text:
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|meter)", text)
        if match:
            spec.width_m = min(8, max(2, float(match.group(1))))
    if "two more" in text and "support" in text:
        spec.supports = min(8, spec.supports + 2)
    if "no support" in text:
        spec.supports = 0
    span = round(site.span_m, 1)
    return BridgePlan(
        summary=f"Conceptual {spec.structure_type.replace('_', ' ')} pedestrian bridge across a {span}m visual span.",
        spec=spec,
        assumptions=[
            "Endpoints and span are map-derived visual context, not survey data.",
            "Foundation, hydraulic, accessibility, and structural design require qualified review.",
        ],
        warnings=["Offline demo fallback used because Nebius Token Factory is not configured."],
        explanation="The deterministic fallback generated a constrained bridge concept. Configure NEBIUS_API_KEY to use Nemotron for site-aware planning and natural-language modifications.",
    )


def _parse_json(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("Model response was not a JSON object")
    return parsed


async def plan_bridge(request: str, site: SiteContext, current: BridgeSpec | None = None) -> tuple[BridgePlan, str]:
    if not settings.NEBIUS_API_KEY:
        return _fallback_plan(request, site, current), "offline-demo"

    prompt = {
        "request": request,
        "site_context": {**site.model_dump(), "visual_span_m": round(site.span_m, 1)},
        "current_spec": current.model_dump() if current else None,
        "rules": [
            "Create or modify only a conceptual pedestrian bridge.",
            "Do not claim structural safety, construction readiness, exact cost, permits, or engineering calculations.",
            "Use only these structure_type values: steel_truss, steel_girder.",
            "Keep width_m between 2 and 8, deck_elevation_m between 2.5 and 15, supports between 0 and 8.",
            "Return a JSON object only with summary, spec, assumptions, warnings, explanation.",
        ],
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{settings.NEBIUS_TOKEN_FACTORY_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.NEBIUS_API_KEY}"},
            json={
                "model": settings.NEBIUS_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are GeoAI's constrained infrastructure concept planner. Return valid JSON only."},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
    try:
        content = response.json()["choices"][0]["message"]["content"]
        return BridgePlan.model_validate(_parse_json(str(content))), "nebius-nemotron"
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("Nemotron returned an invalid bridge specification.") from exc


async def plan_construction(
    project_type: ConstructionType, request: str, site: SiteContext, current: ConstructionSpec | None = None
) -> tuple[ConstructionPlan, str]:
    if not settings.NEBIUS_API_KEY:
        return _fallback_construction_plan(project_type, request, site, current), "offline-demo"

    prompt = {
        "project_type": project_type,
        "request": request,
        "site_context": {**site.model_dump(), "visual_span_m": round(site.span_m, 1)},
        "current_spec": current.model_dump() if current else None,
        "rules": [
            "Create a visual construction concept only, never construction-ready engineering.",
            "Do not claim structural safety, survey precision, cost certainty, permits, or suitability.",
            f"Keep spec.project_type exactly '{project_type}'.",
            "Keep width_m 2..80, length_m 10..2000, height_m 1..150, supports 0..80.",
            "Use stages exactly from: site, foundation, structure, finish.",
            "Return JSON only with summary, spec, assumptions, warnings, explanation.",
        ],
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{settings.NEBIUS_TOKEN_FACTORY_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.NEBIUS_API_KEY}"},
            json={
                "model": settings.NEBIUS_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a constrained construction concept planner. Return valid JSON only."},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
    try:
        content = response.json()["choices"][0]["message"]["content"]
        plan = ConstructionPlan.model_validate(_parse_json(str(content)))
        if plan.spec.project_type != project_type:
            raise ValueError("Nemotron returned a mismatched construction type.")
        return plan, "nebius-nemotron"
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("Nemotron returned an invalid construction specification.") from exc

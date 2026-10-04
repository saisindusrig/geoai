"""LLM provider abstraction: Ollama / OpenAI / Anthropic / Mock.

Design generation uses structured JSON via generate_design_json().
Workspace copilot uses chat_completion() for free-form + JSON copilot replies.
"""

import asyncio
import json
import logging
from typing import Literal

import httpx

from app.core.config import settings
from app.services.ai.ollama_client import OllamaError, chat_completion as ollama_chat, parse_json_from_text

logger = logging.getLogger(__name__)

ProviderName = Literal["ollama", "openai", "anthropic", "mock", "mock-fallback", "fallback"]
PLANNER_TIMEOUT_SECONDS = 45
OPENAI_PLANNER_MODEL = "gpt-4o-mini"
ANTHROPIC_PLANNER_MODEL = "claude-sonnet-4-20250514"


def normalize_ai_provider() -> str:
    """Resolved primary provider from AI_PROVIDER env (defaults to mock when unset)."""
    raw = (settings.AI_PROVIDER or "mock").strip().lower()
    if raw in ("ollama", "openai", "anthropic", "mock", "auto"):
        return raw
    return "mock"


def _provider_chain() -> list[str]:
    """Primary AI_PROVIDER first, then other reachable providers (never mock in chain)."""
    primary = normalize_ai_provider()
    if primary == "mock":
        return []

    if primary == "auto":
        if settings.OPENAI_API_KEY:
            primary = "openai"
        elif settings.ANTHROPIC_API_KEY:
            primary = "anthropic"
        else:
            primary = "ollama"

    chain: list[str] = []

    def add(name: str) -> None:
        if name not in chain:
            chain.append(name)

    add(primary)
    for name in ("ollama", "openai", "anthropic"):
        if name == primary:
            continue
        if name == "openai" and not settings.OPENAI_API_KEY:
            continue
        if name == "anthropic" and not settings.ANTHROPIC_API_KEY:
            continue
        add(name)
    return chain


async def _openai_generate(system: str, user: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


async def _anthropic_generate(system: str, user: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": user + "\nReturn only JSON, no prose."}],
            },
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"]
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])


async def _ollama_generate_json(system: str, user: str) -> dict:
    text = await ollama_chat(system, user + "\nReturn only JSON, no prose.", json_mode=True)
    return parse_json_from_text(text)


async def chat_completion(system: str, user: str, *, json_mode: bool = False) -> tuple[str, str]:
    """Returns (text, provider_name). Tries providers in chain order."""
    last_error: Exception | None = None
    for name in _provider_chain():
        try:
            if name == "ollama":
                text = await ollama_chat(system, user, json_mode=json_mode)
                return text, "ollama"
            if name == "openai":
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": user},
                            ],
                            **({"response_format": {"type": "json_object"}} if json_mode else {}),
                            "temperature": 0.2,
                        },
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"]
                    return text, "openai"
            if name == "anthropic":
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": settings.ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                        },
                        json={
                            "model": "claude-sonnet-4-20250514",
                            "max_tokens": 4096,
                            "system": system,
                            "messages": [{"role": "user", "content": user}],
                        },
                    )
                    resp.raise_for_status()
                    text = resp.json()["content"][0]["text"]
                    return text, "anthropic"
        except OllamaError as exc:
            last_error = exc
            logger.warning("Ollama chat failed: %s", exc)
        except Exception as exc:
            last_error = exc
            logger.warning("%s chat failed: %s", name, exc)
    raise RuntimeError(str(last_error or "No AI provider available"))


def _mock_generate(project_type: str, params: dict) -> dict:
    """Deterministic schema-valid design used when no AI keys are configured."""
    base = {
        "project_type": project_type,
        "assumptions": [
            "No verified geotechnical borehole data provided",
            "Traffic/usage load is preliminary",
            "Utility data unavailable",
            "Generated by mock AI provider (no API key configured)",
        ],
        "risks": ["soil bearing capacity unknown", "existing utilities unknown"],
        "required_engineer_review": True,
        "required_permissions": [],
    }
    if project_type == "flyover":
        length = float(params.get("length_m", 500))
        spacing = float(params.get("pier_spacing_m", 30))
        return {
            **base,
            "summary": f"Preliminary {params.get('lanes', 4)}-lane flyover concept, {length:.0f}m long",
            "geometry": {
                "length_m": length,
                "deck_width_m": float(params.get("deck_width_m", 16)),
                "clearance_m": float(params.get("clearance_m", 5.5)),
                "pier_spacing_m": spacing,
                "pier_count": max(2, int(length / spacing) + 1),
                "foundation_depth_m_assumed": float(params.get("foundation_depth_m_assumed", 8)),
            },
            "materials": {
                "concrete_grade": params.get("concrete_grade", "M35") + " assumed",
                "steel_grade": params.get("steel_grade", "Fe500") + " assumed",
                "asphalt_thickness_mm": params.get("asphalt_thickness_mm", 80),
            },
            "layers": [
                {"name": "foundation", "description": "Assumed pile/open foundation placeholder"},
                {"name": "piers", "description": "Vertical supports"},
                {"name": "pier_caps", "description": "Cap beams"},
                {"name": "deck_slab", "description": "Main slab"},
                {"name": "road_surface", "description": "Wearing coat/asphalt"},
                {"name": "barriers", "description": "Crash barriers/parapet"},
            ],
            "construction_sequence": [
                "survey and utility detection", "traffic diversion planning",
                "foundation construction", "pier construction", "girder placement",
                "deck slab casting", "road surfacing",
                "safety barriers and drainage", "testing and handover",
            ],
        }
    if project_type == "building":
        floors = int(params.get("floors", 4))
        return {
            **base,
            "summary": f"Preliminary G+{floors - 1} building massing concept",
            "geometry": {
                "builtup_area_sqm": float(params.get("builtup_area_sqm", 400)),
                "floors": floors,
                "floor_height_m": float(params.get("floor_height_m", 3.2)),
            },
            "materials": {
                "concrete_grade": params.get("concrete_grade", "M25") + " assumed",
                "steel_grade": params.get("steel_grade", "Fe500") + " assumed",
            },
            "layers": [
                {"name": "foundation", "description": "Foundation placeholder"},
                {"name": "columns", "description": "Column grid placeholder"},
                {"name": "slabs", "description": "Floor slabs"},
                {"name": "core", "description": "Stair/lift core placeholder"},
                {"name": "facade", "description": "Facade placeholder"},
            ],
            "construction_sequence": [
                "site survey and soil test", "excavation and foundation",
                "structural frame floor by floor", "masonry and services",
                "finishes", "testing and handover",
            ],
        }
    if project_type == "pipeline":
        return {
            **base,
            "summary": f"Preliminary {params.get('pipe_diameter_mm', 600)}mm pipeline/drainage concept",
            "geometry": {
                "length_m": float(params.get("length_m", 300)),
                "pipe_diameter_mm": float(params.get("pipe_diameter_mm", 600)),
            },
            "materials": {"pipe_material": params.get("pipe_material", "RCC") + " assumed"},
            "layers": [
                {"name": "trench", "description": "Excavated trench"},
                {"name": "bedding", "description": "Sand bedding"},
                {"name": "pipe", "description": "Pipe along alignment"},
                {"name": "backfill", "description": "Compacted backfill"},
                {"name": "manholes", "description": "Inspection chambers"},
            ],
            "construction_sequence": [
                "alignment survey and utility detection", "trench excavation",
                "bedding placement", "pipe laying and jointing",
                "manhole construction", "backfilling and compaction",
                "testing and road restoration",
            ],
        }
    # road
    return {
        **base,
        "summary": f"Preliminary {params.get('lanes', 2)}-lane road segment concept",
        "geometry": {
            "length_m": float(params.get("length_m", 1000)),
            "road_width_m": float(params.get("road_width_m", 7.5)),
        },
        "materials": {"asphalt_thickness_mm": params.get("asphalt_thickness_mm", 80)},
        "layers": [
            {"name": "formation", "description": "Prepared subgrade"},
            {"name": "base_course", "description": "Granular base/WMM"},
            {"name": "pavement", "description": "Bituminous surfacing"},
            {"name": "shoulders", "description": "Side shoulders"},
            {"name": "drains", "description": "Side drainage"},
        ],
        "construction_sequence": [
            "survey and setting out", "formation preparation",
            "base course laying", "asphalt paving",
            "markings and signage", "drainage works and handover",
        ],
    }


async def generate_plan_json(
    system: str,
    user: str,
    *,
    timeout: float = PLANNER_TIMEOUT_SECONDS,
) -> tuple[dict, str, str | None]:
    """Structured design-parameter JSON from LLM. Retries once; raises on total failure."""
    last_error: Exception | None = None
    for attempt in range(2):
        for name in _provider_chain():
            try:
                if name == "ollama":
                    data = await asyncio.wait_for(
                        _ollama_generate_json(system, user),
                        timeout=timeout,
                    )
                    return data, "ollama", settings.OLLAMA_MODEL
                if name == "openai":
                    data = await asyncio.wait_for(
                        _openai_generate(system, user),
                        timeout=timeout,
                    )
                    return data, "openai", OPENAI_PLANNER_MODEL
                if name == "anthropic":
                    data = await asyncio.wait_for(
                        _anthropic_generate(system, user),
                        timeout=timeout,
                    )
                    return data, "anthropic", ANTHROPIC_PLANNER_MODEL
            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning("%s plan JSON timed out (attempt %d)", name, attempt + 1)
            except Exception as exc:
                last_error = exc
                logger.warning("%s plan JSON failed (attempt %d): %s", name, attempt + 1, exc)
        if attempt == 0:
            logger.info("Retrying LLM plan JSON once after failure")
    raise RuntimeError(str(last_error or "No AI provider available for planning"))


async def generate_design_json(system: str, user: str, project_type: str, params: dict) -> tuple[dict, str]:
    """Returns (design_json, provider_name). Falls back to mock on any failure."""
    for name in _provider_chain():
        try:
            if name == "ollama":
                return await _ollama_generate_json(system, user), "ollama"
            if name == "openai":
                return await _openai_generate(system, user), "openai"
            if name == "anthropic":
                return await _anthropic_generate(system, user), "anthropic"
        except Exception as exc:
            logger.warning("%s design generation failed: %s", name, exc)
    return _mock_generate(project_type, params), "mock"

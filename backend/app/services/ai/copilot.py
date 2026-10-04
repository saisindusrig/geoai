"""LLM-powered workspace copilot with structured actions and regex fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.api.routes.estimates import latest_estimate
from app.core.disclaimer import DISCLAIMER
from app.core.project_catalog import project_type_family
from app.db.models import DesignScenario, Project, SiteAnalysis
from app.services.ai import providers

logger = logging.getLogger(__name__)

COPILOT_SYSTEM_PROMPT = """You are sitegeoai Copilot, a preliminary civil/infrastructure planning assistant.

Rules:
- All outputs are CONCEPTUAL planning only — never claim final engineering approval.
- NEVER invent final BOQ quantities, costs, or schedules. Reference existing calculated values from context when available.
- Suggest parameter changes, workflows, and design concepts only.
- When suggesting numeric parameters, put them in actions — do not state them as verified engineering values.
- Always include at least one warning about preliminary planning and licensed engineer review.

Return ONLY valid JSON with this exact shape:
{
  "message": "helpful assistant reply in plain language",
  "actions": [
    {"type": "update_parameters", "payload": {"length_m": 600}},
    {"type": "run_site_analysis", "payload": {}},
    {"type": "generate_design", "payload": {}}
  ],
  "warnings": ["This is preliminary planning only and must be verified by engineers."]
}

Allowed action types:
- update_parameters: payload is a flat object of design parameter keys/values to merge
- run_site_analysis: payload {} — user should confirm before running site analysis
- generate_design: payload {} — user should confirm before regenerating design

Use empty actions [] when no action is needed. Keep actions minimal (0-2 per turn)."""


def _latest_scenario(db: Session, project_id: int) -> DesignScenario | None:
    return (
        db.query(DesignScenario)
        .filter(DesignScenario.project_id == project_id)
        .order_by(DesignScenario.created_at.desc())
        .first()
    )


def _latest_analysis(db: Session, project_id: int) -> SiteAnalysis | None:
    return (
        db.query(SiteAnalysis)
        .filter(SiteAnalysis.project_id == project_id)
        .order_by(SiteAnalysis.created_at.desc())
        .first()
    )


def build_copilot_context(db: Session, project: Project) -> dict[str, Any]:
    scenario = _latest_scenario(db, project.id)
    analysis = _latest_analysis(db, project.id)
    estimate = latest_estimate(db, project.id)

    ctx: dict[str, Any] = {
        "project": {
            "id": project.id,
            "name": project.name,
            "project_type": project.project_type,
            "project_type_family": project_type_family(project.project_type),
            "status": project.status,
            "units": project.units,
            "location_name": project.location_name,
            "center_lat": project.center_lat,
            "center_lng": project.center_lng,
            "has_boundary": project.boundary_geojson is not None,
            "has_alignment": project.alignment_geojson is not None,
            "accuracy_tier": project.accuracy_tier,
            "survey_mode_enabled": project.survey_mode_enabled,
        },
        "boundary_geojson": project.boundary_geojson,
        "alignment_geojson": project.alignment_geojson,
    }

    if analysis:
        ctx["site_analysis"] = {
            "area_sqm": analysis.area_sqm,
            "perimeter_m": analysis.perimeter_m,
            "elevation_min_m": analysis.elevation_min_m,
            "elevation_max_m": analysis.elevation_max_m,
            "slope_percent_estimate": analysis.slope_percent_estimate,
            "risks": analysis.risks_json,
        }

    if scenario:
        ctx["latest_scenario"] = {
            "id": scenario.id,
            "name": scenario.name,
            "status": scenario.status,
            "input_parameters": scenario.input_parameters_json or {},
            "design_summary": (scenario.design_output_json or {}).get("summary"),
            "assumptions": scenario.assumptions_json or (scenario.design_output_json or {}).get("assumptions"),
            "risks": (scenario.design_output_json or {}).get("risks"),
        }
        design = scenario.design_output_json or {}
        calculated = design.get("calculated")
        if calculated:
            ctx["calculated_summary"] = {
                "quantities": calculated.get("quantities"),
                "cost_summary": calculated.get("cost_summary"),
                "timeline": calculated.get("timeline"),
            }

    if estimate:
        ctx["latest_estimate"] = {
            "concrete_m3": estimate.concrete_m3,
            "steel_kg": estimate.steel_kg,
            "excavation_m3": estimate.excavation_m3,
            "total_cost_estimate": estimate.total_cost_estimate,
            "line_item_count": len(estimate.line_items_json or []),
        }

    return ctx


def _normalize_actions(raw_actions: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_actions, list):
        return []
    normalized: list[dict[str, Any]] = []
    allowed = {"update_parameters", "run_site_analysis", "generate_design", "show_layer", "download"}
    for item in raw_actions:
        if not isinstance(item, dict):
            continue
        action_type = item.get("type")
        if action_type not in allowed:
            continue
        payload = item.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        if action_type == "update_parameters" and not payload:
            continue
        normalized.append({"type": action_type, "payload": payload})
    return normalized[:3]


def _normalize_warnings(raw_warnings: Any) -> list[str]:
    if not isinstance(raw_warnings, list):
        return [DISCLAIMER]
    warnings = [str(w) for w in raw_warnings if w]
    if not warnings:
        warnings.append(DISCLAIMER)
    return warnings


def _parse_copilot_json(text: str) -> dict[str, Any]:
    from app.services.ai.ollama_client import parse_json_from_text

    data = parse_json_from_text(text)
    message = str(data.get("message") or "").strip()
    if not message:
        message = "I reviewed your project context. Let me know what you'd like to adjust."
    return {
        "message": message,
        "actions": _normalize_actions(data.get("actions")),
        "warnings": _normalize_warnings(data.get("warnings")),
    }


def _fallback_regex_response(msg: str, db: Session, project_id: int) -> dict[str, Any]:
    """Rule-based fallback when LLM is unavailable."""
    scenario = _latest_scenario(db, project_id)
    params = dict(scenario.input_parameters_json or {}) if scenario else {}
    actions: list[dict[str, Any]] = []
    warnings = [DISCLAIMER, "Copilot is running in offline fallback mode (no LLM provider available)."]

    lanes = re.search(r"(\d+)\s*lane", msg)
    length = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|meter|metre)s?\b", msg)
    spacing = re.search(r"pier\s+spacing\s*(?:to|of)?\s*(\d+(?:\.\d+)?)", msg)
    floors = re.search(r"(\d+)\s*floor", msg)

    if lanes:
        params["lanes"] = int(lanes.group(1))
        params["deck_width_m"] = int(lanes.group(1)) * 3.5 + 2
        message = (
            f"I suggest updating to {lanes.group(1)} lanes (deck width ~{params['deck_width_m']}m). "
            "Confirm the action below to apply parameters, then regenerate the design."
        )
        actions = [{"type": "update_parameters", "payload": params}]
    elif spacing:
        params["pier_spacing_m"] = float(spacing.group(1))
        message = f"Pier spacing of {spacing.group(1)}m looks reasonable for a preliminary concept. Confirm to apply."
        actions = [{"type": "update_parameters", "payload": params}]
    elif floors:
        params["floors"] = int(floors.group(1))
        message = f"Updating to {floors.group(1)} floors is a concept-level change. Confirm to apply parameters."
        actions = [{"type": "update_parameters", "payload": params}]
    elif length and ("long" in msg or "length" in msg):
        params["length_m"] = float(length.group(1))
        message = f"Length {length.group(1)}m noted. Confirm to update parameters before regenerating."
        actions = [{"type": "update_parameters", "payload": params}]
    elif "analyze" in msg or "site analysis" in msg:
        message = "I can run site analysis on your boundary/alignment. Confirm below to start."
        actions = [{"type": "run_site_analysis", "payload": {}}]
    elif "regenerate" in msg or "generate" in msg or "design" in msg:
        message = "Ready to regenerate the preliminary design with current parameters. Confirm to start."
        actions = [{"type": "generate_design", "payload": {}}]
    elif "reduce cost" in msg or "cheaper" in msg:
        message = (
            "Cost reduction ideas (conceptual): reduce length/width, increase pier spacing, "
            "lower concrete grade, or phase construction. Tell me a specific change to propose parameters."
        )
    elif "report" in msg or "pdf" in msg:
        message = "You can download the preliminary PDF report from the Reports page or export center."
        actions = [{"type": "download", "payload": {"export": "pdf"}}]
    else:
        message = (
            "I can help adjust parameters, run site analysis, or regenerate the preliminary design. "
            "Try: 'make this 4 lanes', 'run site analysis', or 'regenerate design'."
        )

    return {"message": message, "actions": actions, "warnings": warnings, "provider": "fallback"}


async def run_copilot(db: Session, project: Project, user_message: str) -> dict[str, Any]:
    """Run LLM copilot with structured JSON output; fall back to regex rules."""
    context = build_copilot_context(db, project)
    user_prompt = (
        f"Project context:\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"User message:\n{user_message.strip()}\n\n"
        "Respond with JSON only."
    )

    try:
        text, provider = await providers.chat_completion(COPILOT_SYSTEM_PROMPT, user_prompt, json_mode=True)
        parsed = _parse_copilot_json(text)
        parsed["provider"] = provider
        parsed["disclaimer"] = DISCLAIMER
        # Backward compat for stream client expecting single `action`
        parsed["reply"] = parsed["message"]
        parsed["action"] = parsed["actions"][0] if len(parsed["actions"]) == 1 else None
        return parsed
    except Exception as exc:
        logger.warning("Copilot LLM failed (%s), using regex fallback", exc)
        result = _fallback_regex_response(user_message.lower(), db, project.id)
        result["disclaimer"] = DISCLAIMER
        result["reply"] = result["message"]
        result["action"] = result["actions"][0] if len(result["actions"]) == 1 else None
        result["llm_error"] = str(exc)
        return result

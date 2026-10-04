"""Safe LLM design parameter planner — structured JSON only, no mesh generation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.core.project_catalog import project_type_family
from app.services.ai import providers
from app.services.ai.design_plan_schemas import (
    DEFAULTS_BY_FAMILY,
    FAMILY_ALIASES,
    DesignPlan,
    DesignParameters,
)

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = (
    "You are sitegeoai Design Parameter Planner for preliminary civil infrastructure concepts. "
    "Return ONLY a JSON object — no prose, no markdown, no 3D geometry, no mesh coordinates. "
    "Your job is to translate user design instructions into safe numeric planning parameters. "
    "Never claim final engineering approval. Include conservative assumptions and warnings when "
    "data is missing. Use realistic Indian/highway-style defaults when unspecified. "
    "Do not invent official regulations. If local code compliance is unknown, note it in warnings."
)

PLANNER_JSON_SCHEMA_HINT = """
Required JSON shape:
{
  "project_type": "flyover|road|building|pipeline",
  "parameters": {
    "lanes": number,
    "lane_width_m": number,
    "total_width_m": number,
    "length_m": number,
    "clearance_m": number,
    "pier_spacing_m": number,
    "deck_depth_m": number,
    "deck_width_m": number,
    "road_width_m": number,
    "shoulder_width_m": number,
    "asphalt_thickness_mm": number,
    "base_thickness_mm": number,
    "foundation_depth_m_assumed": number,
    "drainage_required": boolean,
    "service_roads_required": boolean,
    "builtup_area_sqm": number,
    "floors": number,
    "floor_height_m": number,
    "pipe_diameter_mm": number,
    "trench_width_m": number,
    "trench_depth_m": number,
    "concrete_grade": string,
    "utility_type": string
  },
  "assumptions": ["string"],
  "warnings": ["string"],
  "missing_inputs": [{"field": "string", "reason": "string"}]
}
Include only parameters relevant to the project type; omit unknown fields or set null.
"""


@dataclass
class PlannerResult:
    planning_mode: str  # llm | template | fallback
    parameters: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_inputs: list[dict[str, str]] = field(default_factory=list)
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_error: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "planning_mode": self.planning_mode,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "design_assumptions": self.assumptions,
            "design_warnings": self.warnings,
            "missing_inputs": self.missing_inputs,
            "final_parameters": self.parameters,
        }


def design_instructions(params: dict) -> str:
    raw = params.get("design_instructions") or params.get("custom_instructions") or ""
    return str(raw).strip()


def should_use_planner(params: dict) -> bool:
    """Only invoke LLM when user supplied meaningful design instructions."""
    return bool(design_instructions(params))


def _resolve_family(project_type: str) -> str:
    family = project_type_family(project_type)
    return FAMILY_ALIASES.get(family, family)


def build_planner_user_prompt(
    *,
    project_type: str,
    params: dict,
    site_ctx: dict | None,
    alignment_length_m: float | None,
    elevation_meta: dict | None,
    instructions: str,
) -> str:
    context = {
        "project_type": project_type,
        "form_parameters": {k: v for k, v in params.items() if not str(k).startswith("generation_")},
        "alignment_length_m": alignment_length_m,
        "site_context": site_ctx or {},
        "elevation_metadata": elevation_meta or {},
        "design_instructions": instructions,
    }
    return (
        f"Plan design parameters for this project.\n\n"
        f"Context:\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"{PLANNER_JSON_SCHEMA_HINT}\n"
        "Return ONLY the JSON object."
    )


def _lane_derived_width(lanes: int, lane_width_m: float, *, family: str) -> float:
    shoulder = 1.0 if family == "flyover" else 0.0
    return round(lanes * lane_width_m + shoulder * 2, 2)


def apply_plan_parameters(
    project_type: str,
    form_params: dict,
    plan: DesignPlan,
) -> tuple[dict[str, Any], list[str]]:
    """Merge validated plan into form params with deterministic clamps."""
    family = _resolve_family(project_type)
    merged: dict[str, Any] = dict(form_params)
    corrections: list[str] = []
    raw = plan.parameters.model_dump(exclude_none=True)
    defaults = DEFAULTS_BY_FAMILY.get(family, {})

    if plan.project_type and plan.project_type not in (project_type, family, *FAMILY_ALIASES.keys()):
        corrections.append(
            f"LLM project_type '{plan.project_type}' ignored; using '{project_type}'"
        )

    lanes = raw.get("lanes")
    lane_w = raw.get("lane_width_m", defaults.get("lane_width_m", 3.5))

    for key, value in raw.items():
        if key in ("total_width_m", "lane_width_m"):
            continue
        if value is None:
            continue
        merged[key] = value

    if lanes is not None:
        merged["lanes"] = int(lanes)
        derived = raw.get("total_width_m")
        if derived is None:
            derived = _lane_derived_width(int(lanes), float(lane_w), family=family)
        if family == "flyover":
            merged["deck_width_m"] = float(derived)
        elif family == "road":
            merged["road_width_m"] = float(derived)
        elif raw.get("total_width_m") is not None:
            if family == "flyover":
                merged["deck_width_m"] = float(raw["total_width_m"])
            elif family == "road":
                merged["road_width_m"] = float(raw["total_width_m"])

    if raw.get("total_width_m") is not None and lanes is None:
        if family == "flyover":
            merged["deck_width_m"] = float(raw["total_width_m"])
        elif family == "road":
            merged["road_width_m"] = float(raw["total_width_m"])

    if raw.get("deck_width_m") is not None and family == "flyover":
        merged["deck_width_m"] = float(raw["deck_width_m"])
    if raw.get("road_width_m") is not None and family == "road":
        merged["road_width_m"] = float(raw["road_width_m"])

    if raw.get("deck_depth_m") is not None:
        merged["deck_depth_m"] = float(raw["deck_depth_m"])

    # Deterministic clamps on critical values
    clamps: list[tuple[str, float, float, str]] = []
    if family == "flyover":
        clamps = [
            ("clearance_m", 4.0, 12.0, "m"),
            ("pier_spacing_m", 15.0, 60.0, "m"),
            ("deck_width_m", 6.0, 60.0, "m"),
            ("foundation_depth_m_assumed", 3.0, 40.0, "m"),
        ]
    elif family == "road":
        clamps = [
            ("road_width_m", 3.0, 40.0, "m"),
            ("shoulder_width_m", 0.0, 5.0, "m"),
            ("lanes", 1, 10, ""),
        ]
    elif family == "building":
        clamps = [
            ("floors", 1, 60, ""),
            ("builtup_area_sqm", 50.0, 100_000.0, "m²"),
        ]
    elif family == "pipeline":
        clamps = [
            ("pipe_diameter_mm", 100.0, 3000.0, "mm"),
            ("trench_depth_m", 0.8, 10.0, "m"),
        ]

    for key, lo, hi, unit in clamps:
        if key not in merged:
            continue
        try:
            val = float(merged[key])
        except (TypeError, ValueError):
            corrections.append(f"Removed invalid {key}: {merged[key]!r}")
            merged.pop(key, None)
            continue
        if val < lo:
            corrections.append(f"{key} raised from {val} to minimum {lo}{unit}")
            merged[key] = int(lo) if key == "lanes" or key == "floors" else lo
        elif val > hi:
            corrections.append(f"{key} lowered from {val} to maximum {hi}{unit}")
            merged[key] = int(hi) if key == "lanes" or key == "floors" else hi

    # Flyover pier count sanity vs length
    length_m = float(merged.get("length_m") or form_params.get("length_m") or 500)
    spacing = float(merged.get("pier_spacing_m") or defaults.get("pier_spacing_m", 30))
    if family == "flyover" and spacing > length_m:
        corrections.append(f"Pier spacing {spacing}m exceeds length; capped to {max(15, length_m / 2):.0f}m")
        merged["pier_spacing_m"] = max(15.0, length_m / 2)

    return merged, corrections


def _coerce_parameter_dict(raw: dict[str, Any], project_type: str) -> dict[str, Any]:
    """Clamp unsafe LLM numeric values before Pydantic validation."""
    family = _resolve_family(project_type)
    out = dict(raw)
    float_clamps = {
        "clearance_m": (4.0, 12.0),
        "pier_spacing_m": (15.0, 60.0),
        "deck_width_m": (6.0, 60.0),
        "road_width_m": (3.0, 40.0),
        "shoulder_width_m": (0.0, 5.0),
        "lane_width_m": (2.5, 5.0),
        "foundation_depth_m_assumed": (3.0, 40.0),
        "deck_depth_m": (0.3, 2.0),
        "floor_height_m": (2.5, 6.0),
        "trench_depth_m": (0.8, 10.0),
        "trench_width_m": (0.6, 5.0),
    }
    int_clamps = {"lanes": (1, 12), "floors": (1, 60)}
    for key, (lo, hi) in float_clamps.items():
        if key in out and out[key] is not None:
            try:
                out[key] = max(lo, min(hi, float(out[key])))
            except (TypeError, ValueError):
                out.pop(key, None)
    for key, (lo, hi) in int_clamps.items():
        if key in out and out[key] is not None:
            try:
                out[key] = int(max(lo, min(hi, int(out[key]))))
            except (TypeError, ValueError):
                out.pop(key, None)
    if family == "flyover" and out.get("pier_spacing_m") and out.get("length_m"):
        try:
            length = float(out["length_m"])
            spacing = float(out["pier_spacing_m"])
            if spacing > length:
                out["pier_spacing_m"] = max(15.0, length / 2)
        except (TypeError, ValueError):
            pass
    return out


def parse_and_validate_plan(raw: dict, project_type: str) -> DesignPlan:
    payload = dict(raw)
    if isinstance(payload.get("parameters"), dict):
        payload["parameters"] = _coerce_parameter_dict(payload["parameters"], project_type)
    plan = DesignPlan.model_validate(payload)
    if not plan.project_type:
        plan.project_type = project_type
    return plan


async def plan_design(
    *,
    project_type: str,
    params: dict,
    site_ctx: dict | None = None,
    alignment_length_m: float | None = None,
    elevation_meta: dict | None = None,
) -> PlannerResult:
    """Run optional LLM planner; always returns safe merged parameters."""
    instructions = design_instructions(params)
    family = _resolve_family(project_type)

    if not should_use_planner(params):
        logger.info("Design planner: template mode (no instructions / use_llm)")
        return PlannerResult(
            planning_mode="template",
            parameters=dict(params),
            assumptions=["Deterministic template parameters used (no design instructions)"],
        )

    if not providers._provider_chain():
        logger.info("Design planner: fallback — no LLM provider configured")
        return PlannerResult(
            planning_mode="fallback",
            parameters=dict(params),
            warnings=["No LLM provider configured; using form parameters"],
            llm_error="no_provider",
        )

    user_prompt = build_planner_user_prompt(
        project_type=project_type,
        params=params,
        site_ctx=site_ctx,
        alignment_length_m=alignment_length_m,
        elevation_meta=elevation_meta,
        instructions=instructions,
    )

    try:
        raw_json, provider_name, model_name = await providers.generate_plan_json(
            PLANNER_SYSTEM_PROMPT,
            user_prompt,
        )
    except Exception as exc:
        logger.warning("Design planner LLM failed: %s", exc)
        return PlannerResult(
            planning_mode="fallback",
            parameters=dict(params),
            warnings=[f"LLM planning failed: {exc}"],
            llm_error=str(exc),
        )

    try:
        if isinstance(raw_json, dict) and "parameters" not in raw_json and any(
            k in raw_json for k in ("lanes", "clearance_m", "road_width_m")
        ):
            raw_json = {
                "project_type": project_type,
                "parameters": {k: v for k, v in raw_json.items() if k not in (
                    "assumptions", "warnings", "missing_inputs", "project_type"
                )},
                "assumptions": raw_json.get("assumptions", []),
                "warnings": raw_json.get("warnings", []),
                "missing_inputs": raw_json.get("missing_inputs", []),
            }
        plan = parse_and_validate_plan(raw_json, project_type)
    except (ValidationError, TypeError, ValueError) as exc:
        logger.warning("Design planner schema validation failed: %s", exc)
        return PlannerResult(
            planning_mode="fallback",
            parameters=dict(params),
            warnings=[f"LLM output failed schema validation: {exc}"],
            llm_provider=provider_name,
            llm_model=model_name,
            llm_error=str(exc),
        )

    merged, corrections = apply_plan_parameters(project_type, params, plan)
    if alignment_length_m is not None:
        merged["length_m"] = round(float(alignment_length_m), 2)

    warnings = list(plan.warnings) + corrections
    assumptions = list(plan.assumptions)
    if not assumptions:
        assumptions.append(f"LLM-planned parameters for {family} concept")

    missing = [m.model_dump() for m in plan.missing_inputs]

    logger.info(
        "Design planner: LLM mode provider=%s model=%s family=%s",
        provider_name,
        model_name,
        family,
    )
    return PlannerResult(
        planning_mode="llm",
        parameters=merged,
        assumptions=assumptions,
        warnings=warnings,
        missing_inputs=missing,
        llm_provider=provider_name,
        llm_model=model_name,
    )

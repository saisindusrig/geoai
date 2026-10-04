"""Report-ready design review summary (PDF / JSON export)."""

from __future__ import annotations

from typing import Any

from app.services.design.design_validator import CONCEPTUAL_DISCLAIMER
from app.services.design.validation_schemas import DesignValidationResult


def build_design_review(
    *,
    project_type: str,
    params: dict[str, Any],
    geometry_spec: dict[str, Any] | None,
    planning_meta: dict[str, Any] | None,
    validation: DesignValidationResult,
    cost_summary: dict[str, Any] | None = None,
    quantities: dict[str, Any] | None = None,
    preview_mode: bool = False,
) -> dict[str, Any]:
    """Structured review object for UI and PDF export."""
    spec = geometry_spec or {}
    planning = planning_meta or {}

    return {
        "project_type": project_type,
        "final_parameters": dict(params),
        "geometry_mode": spec.get("geometry_mode", "unknown"),
        "elevation_mode": spec.get("elevation_mode", "unknown"),
        "elevation_assumed": spec.get("elevation_assumed"),
        "max_grade_percent": spec.get("max_grade_percent"),
        "alignment_based": spec.get("geometry_mode") == "alignment",
        "elevation_aware": spec.get("elevation_mode") == "profile",
        "planning_mode": planning.get("planning_mode", "template"),
        "llm_provider": planning.get("llm_provider"),
        "llm_model": planning.get("llm_model"),
        "boq_summary": {
            "approximate": preview_mode,
            "cost_summary": cost_summary,
            "quantities": quantities,
        },
        "validation": validation.to_dict(),
        "validation_status": validation.validation_status,
        "validation_score": validation.score,
        "warnings": [w.message for w in validation.warnings],
        "errors": [e.message for e in validation.errors],
        "recommendations": [r.message for r in validation.recommendations],
        "assumptions": validation.assumptions,
        "planning_assumptions": planning.get("design_assumptions") or [],
        "planning_warnings": planning.get("design_warnings") or [],
        "missing_inputs": planning.get("missing_inputs") or [],
        "conceptual_disclaimer": CONCEPTUAL_DISCLAIMER,
        "not_for_construction": True,
    }

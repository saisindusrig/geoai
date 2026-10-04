"""Scenario summary, detail, and comparison helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.project_catalog import project_type_family
from app.db.models import DesignScenario, GeneratedFile, Project, QuantityEstimate
from app.services.storage import normalize_file_url

COMPARISON_DISCLAIMER = (
    "Scenario comparison is for preliminary planning only — not final engineering approval."
)
MAX_COMPARE = 4
MIN_COMPARE = 2

MODE_LABELS = {
    "fast_preview": "Fast preview",
    "balanced": "Balanced",
    "high_detail": "High detail",
}


def format_scenario_name(
    project_type: str,
    params: dict[str, Any],
    generation_mode: str,
    created_at: datetime | None = None,
) -> str:
    """Auto-name: Flyover · 4 lanes · Balanced · 14 Jun 2026 18:30"""
    family = project_type_family(project_type)
    label = project_type.replace("_", " ").title()
    parts: list[str] = [label]

    lanes = params.get("lanes")
    if lanes is not None:
        parts.append(f"{int(lanes)} lanes")

    width = params.get("deck_width_m") or params.get("road_width_m") or params.get("total_width_m")
    if width is not None and lanes is None:
        parts.append(f"{float(width):.0f}m wide")

    clearance = params.get("clearance_m")
    if clearance is not None and family == "flyover":
        parts.append(f"{float(clearance):.1f}m clearance")

    mode_label = MODE_LABELS.get(generation_mode, generation_mode.replace("_", " ").title())
    parts.append(mode_label)

    ts = created_at or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    parts.append(ts.strftime("%d %b %Y %H:%M"))
    return " · ".join(parts)


def _estimate_for_scenario(db: Session, scenario_id: int) -> QuantityEstimate | None:
    return (
        db.query(QuantityEstimate)
        .filter(QuantityEstimate.design_scenario_id == scenario_id)
        .order_by(QuantityEstimate.created_at.desc())
        .first()
    )


def _files_for_scenario(db: Session, project_id: int, scenario_id: int) -> list[GeneratedFile]:
    return (
        db.query(GeneratedFile)
        .filter(
            GeneratedFile.project_id == project_id,
            GeneratedFile.design_scenario_id == scenario_id,
        )
        .order_by(GeneratedFile.created_at.desc())
        .all()
    )


def _extract_params(scenario: DesignScenario) -> dict[str, Any]:
    return dict(scenario.input_parameters_json or {})


def _design(scenario: DesignScenario) -> dict[str, Any]:
    return dict(scenario.design_output_json or {})


def build_scenario_summary(
    db: Session,
    scenario: DesignScenario,
    project: Project,
) -> dict[str, Any]:
    params = _extract_params(scenario)
    design = _design(scenario)
    review = design.get("design_review") or {}
    validation = design.get("validation") or review.get("validation") or {}
    spec = design.get("geometry_spec") or {}
    calc = design.get("calculated") or {}
    cost = calc.get("cost_summary") or {}
    quantities = calc.get("quantities") or {}
    estimate = _estimate_for_scenario(db, scenario.id)
    files = _files_for_scenario(db, project.id, scenario.id)

    generation_mode = str((scenario.input_parameters_json or {}).get("generation_mode", "balanced"))

    family = project_type_family(project.project_type)
    width = (
        params.get("deck_width_m")
        or params.get("road_width_m")
        or review.get("final_parameters", {}).get("deck_width_m")
        or review.get("final_parameters", {}).get("road_width_m")
    )

    model_url = normalize_file_url(next((f.file_url for f in files if f.file_type == "glb"), None))
    preview_url = normalize_file_url(next((f.file_url for f in files if f.file_type == "glb-preview"), None))

    pier_spacing = params.get("pier_spacing_m")
    length_m = (
        params.get("length_m")
        or spec.get("length_m")
        or (design.get("geometry") or {}).get("length_m")
    )

    return {
        "scenario_id": scenario.id,
        "name": scenario.name,
        "title": scenario.name,
        "status": scenario.status,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "generation_mode": generation_mode,
        "planning_mode": review.get("planning_mode") or (design.get("planning") or {}).get("planning_mode"),
        "project_type": project.project_type,
        "length_m": length_m,
        "lanes": params.get("lanes"),
        "width_m": width,
        "clearance_m": params.get("clearance_m") if family == "flyover" else None,
        "pier_spacing_m": pier_spacing if family == "flyover" else None,
        "cost_total": estimate.total_cost_estimate if estimate else cost.get("total_medium"),
        "cost_currency": cost.get("currency", "INR"),
        "materials_summary": {
            "concrete_m3": quantities.get("concrete_m3") or (estimate.concrete_m3 if estimate else None),
            "steel_kg": quantities.get("steel_kg") or (estimate.steel_kg if estimate else None),
            "asphalt_m3": quantities.get("asphalt_m3") or (estimate.asphalt_m3 if estimate else None),
            "excavation_m3": quantities.get("excavation_m3") or (estimate.excavation_m3 if estimate else None),
        },
        "validation_status": validation.get("validation_status") or review.get("validation_status"),
        "validation_score": validation.get("score") if validation.get("score") is not None else review.get("validation_score"),
        "warning_count": len(validation.get("warnings") or review.get("warnings") or []),
        "error_count": len(validation.get("errors") or review.get("errors") or []),
        "geometry_mode": spec.get("geometry_mode") or review.get("geometry_mode"),
        "elevation_mode": spec.get("elevation_mode") or review.get("elevation_mode"),
        "max_grade_percent": spec.get("max_grade_percent") or review.get("max_grade_percent"),
        "model_url": model_url or preview_url,
        "preview_url": preview_url,
        "report_url": f"/api/projects/{project.id}/exports/pdf",
        "key_assumptions": (scenario.assumptions_json or design.get("assumptions") or [])[:5],
        "duration_months": (calc.get("timeline") or {}).get("estimated_months_medium"),
    }


def build_scenario_detail(
    db: Session,
    scenario: DesignScenario,
    project: Project,
) -> dict[str, Any]:
    summary = build_scenario_summary(db, scenario, project)
    design = _design(scenario)
    estimate = _estimate_for_scenario(db, scenario.id)
    files = _files_for_scenario(db, project.id, scenario.id)

    return {
        **summary,
        "input_parameters": scenario.input_parameters_json,
        "design_output": design,
        "assumptions": scenario.assumptions_json or design.get("assumptions"),
        "validation": design.get("validation"),
        "design_review": design.get("design_review"),
        "planning": design.get("planning"),
        "estimate": {
            "total_cost_estimate": estimate.total_cost_estimate if estimate else None,
            "concrete_m3": estimate.concrete_m3 if estimate else None,
            "steel_kg": estimate.steel_kg if estimate else None,
            "asphalt_m3": estimate.asphalt_m3 if estimate else None,
            "line_items": estimate.line_items_json if estimate else None,
        }
        if estimate
        else None,
        "generated_files": [
            {
                "id": f.id,
                "file_type": f.file_type,
                "file_url": normalize_file_url(f.file_url),
                "metadata": f.metadata_json,
            }
            for f in files
        ],
    }


def _comparison_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": summary["scenario_id"],
        "name": summary["name"],
        "cost_total": summary.get("cost_total"),
        "validation_score": summary.get("validation_score"),
        "validation_status": summary.get("validation_status"),
        "length_m": summary.get("length_m"),
        "width_m": summary.get("width_m"),
        "lanes": summary.get("lanes"),
        "pier_spacing_m": summary.get("pier_spacing_m"),
        "max_grade_percent": summary.get("max_grade_percent"),
        "geometry_mode": summary.get("geometry_mode"),
        "elevation_mode": summary.get("elevation_mode"),
        "warning_count": summary.get("warning_count", 0),
        "error_count": summary.get("error_count", 0),
        "recommendations": [],
        "duration_months": summary.get("duration_months"),
    }


def compare_scenarios(
    db: Session,
    project: Project,
    scenario_ids: list[int],
) -> dict[str, Any]:
    if len(scenario_ids) < MIN_COMPARE:
        raise HTTPException(422, f"Select at least {MIN_COMPARE} scenarios to compare")
    if len(scenario_ids) > MAX_COMPARE:
        raise HTTPException(422, f"Compare at most {MAX_COMPARE} scenarios at once")

    unique_ids = list(dict.fromkeys(scenario_ids))
    if len(unique_ids) != len(scenario_ids):
        raise HTTPException(422, "Duplicate scenario IDs in compare request")

    rows: list[dict[str, Any]] = []
    for sid in unique_ids:
        scenario = db.get(DesignScenario, sid)
        if scenario is None or scenario.project_id != project.id:
            raise HTTPException(404, f"Scenario {sid} not found for this project")
        if scenario.status in ("cancelled", "failed", "running"):
            raise HTTPException(
                422,
                f"Scenario {sid} is not ready for comparison (status: {scenario.status})",
            )
        summary = build_scenario_summary(db, scenario, project)
        row = _comparison_row(summary)
        design = _design(scenario)
        review = design.get("design_review") or {}
        row["recommendations"] = (review.get("recommendations") or [])[:3]
        rows.append(row)

    def _valid_cost(r: dict) -> bool:
        return r.get("cost_total") is not None

    def _valid_score(r: dict) -> bool:
        return r.get("validation_score") is not None

    best_cost = min((r for r in rows if _valid_cost(r)), key=lambda r: r["cost_total"], default=None)
    best_score = max((r for r in rows if _valid_score(r)), key=lambda r: r["validation_score"], default=None)
    fewest_warnings = min(rows, key=lambda r: (r.get("warning_count") or 0, r.get("error_count") or 0))

    return {
        "project_id": project.id,
        "scenario_ids": unique_ids,
        "rows": rows,
        "best_option_by": {
            "lowest_cost": best_cost["scenario_id"] if best_cost else None,
            "highest_validation_score": best_score["scenario_id"] if best_score else None,
            "fewest_warnings": fewest_warnings["scenario_id"] if fewest_warnings else None,
        },
        "notes": [
            COMPARISON_DISCLAIMER,
            "Costs and scores are planning-level estimates only.",
        ],
    }

"""Deterministic engineering validation for generated design scenarios."""

from __future__ import annotations

from typing import Any

from app.core.disclaimer import DISCLAIMER
from app.core.project_catalog import project_type_family
from app.services.design.validation_schemas import (
    DesignRecommendation,
    DesignValidationResult,
    ValidationError,
    ValidationWarning,
)

CONCEPTUAL_DISCLAIMER = (
    "This is a conceptual preliminary design for planning purposes only — "
    "not for construction, tender, or statutory approval."
)

# Typical planning thresholds (deterministic, not code-compliant claims)
LANE_WIDTH_MIN_M = 2.5
LANE_WIDTH_TYPICAL_M = 3.5
MAX_GRADE_WARN_PERCENT = 8.0
MAX_GRADE_FAIL_PERCENT = 12.0
CLEARANCE_MIN_M = 4.0
CLEARANCE_RECOMMENDED_M = 5.5
PIER_SPACING_MIN_M = 15.0
PIER_SPACING_MAX_WARN_M = 45.0
LONG_CORRIDOR_M = 500.0


def _deduct_score(score: int, amount: int) -> int:
    return max(0, score - amount)


def _finalize(
    score: int,
    warnings: list[ValidationWarning],
    errors: list[ValidationError],
    recommendations: list[DesignRecommendation],
    assumptions: list[str],
) -> DesignValidationResult:
    if errors:
        status = "fail"
    elif warnings:
        status = "warning"
    else:
        status = "pass"
    if score < 50 and status != "fail":
        status = "fail"
    elif score < 75 and status == "pass":
        status = "warning"

    return DesignValidationResult(
        validation_status=status,
        score=score,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations,
        assumptions=assumptions,
        conceptual_disclaimer=CONCEPTUAL_DISCLAIMER,
    )


def _check_corridor_params(
    *,
    family: str,
    params: dict[str, Any],
    geometry_spec: dict[str, Any],
    score: int,
    warnings: list[ValidationWarning],
    errors: list[ValidationError],
    recommendations: list[DesignRecommendation],
    assumptions: list[str],
) -> int:
    lanes = params.get("lanes")
    length_m = float(params.get("length_m") or geometry_spec.get("length_m") or 0)
    geometry_mode = geometry_spec.get("geometry_mode", "straight")
    elevation_mode = geometry_spec.get("elevation_mode", "flat")
    elevation_assumed = geometry_spec.get("elevation_assumed", True)
    max_grade = geometry_spec.get("max_grade_percent")

    if family in ("flyover", "road") and geometry_mode != "alignment":
        warnings.append(
            ValidationWarning(
                code="no_alignment_geometry",
                message="Geometry uses straight fallback — draw an alignment for route-following design.",
                field="alignment",
            )
        )
        score = _deduct_score(score, 12)
        recommendations.append(
            DesignRecommendation(
                code="draw_alignment",
                message="Draw a centerline alignment on the map before regenerating.",
            )
        )

    if elevation_mode == "flat" or elevation_assumed:
        warnings.append(
            ValidationWarning(
                code="flat_elevation",
                message="Terrain elevation is flat or assumed — vertical geometry may not match site.",
                field="elevation_mode",
            )
        )
        score = _deduct_score(score, 10)
        recommendations.append(
            DesignRecommendation(
                code="run_site_analysis",
                message="Run site analysis and ensure terrain sampling is available along the alignment.",
            )
        )

    if max_grade is not None:
        grade = float(max_grade)
        if grade >= MAX_GRADE_FAIL_PERCENT:
            errors.append(
                ValidationError(
                    code="excessive_grade",
                    message=f"Max grade {grade:.1f}% exceeds safe preliminary limit ({MAX_GRADE_FAIL_PERCENT}%).",
                    field="max_grade_percent",
                )
            )
            score = _deduct_score(score, 25)
        elif grade >= MAX_GRADE_WARN_PERCENT:
            warnings.append(
                ValidationWarning(
                    code="steep_grade",
                    message=f"Max grade {grade:.1f}% is steep — verify vertical alignment and drainage.",
                    field="max_grade_percent",
                )
            )
            score = _deduct_score(score, 10)

    if lanes is not None:
        try:
            lane_count = int(lanes)
        except (TypeError, ValueError):
            lane_count = 0
        if lane_count < 1:
            errors.append(
                ValidationError(
                    code="invalid_lanes",
                    message="Lane count must be at least 1.",
                    field="lanes",
                )
            )
            score = _deduct_score(score, 20)
        elif lane_count > 10:
            warnings.append(
                ValidationWarning(
                    code="high_lane_count",
                    message=f"{lane_count} lanes is unusually high for a single preliminary segment.",
                    field="lanes",
                )
            )
            score = _deduct_score(score, 8)

        width_key = "deck_width_m" if family == "flyover" else "road_width_m"
        total_w = params.get(width_key) or params.get("total_width_m")
        if total_w is not None and lane_count >= 1:
            try:
                width = float(total_w)
                min_required = lane_count * LANE_WIDTH_MIN_M
                typical = lane_count * LANE_WIDTH_TYPICAL_M
                if width < min_required:
                    errors.append(
                        ValidationError(
                            code="lane_width_too_narrow",
                            message=(
                                f"Total width {width:.1f} m is below minimum "
                                f"({min_required:.1f} m) for {lane_count} lanes."
                            ),
                            field=width_key,
                        )
                    )
                    score = _deduct_score(score, 25)
                elif width < typical * 0.92:
                    warnings.append(
                        ValidationWarning(
                            code="narrow_carriageway",
                            message=(
                                f"Width {width:.1f} m is tight for {lane_count} lanes "
                                f"(typical ≥ {typical:.1f} m)."
                            ),
                            field=width_key,
                        )
                    )
                    score = _deduct_score(score, 10)
            except (TypeError, ValueError):
                pass

    if family == "flyover":
        clearance = params.get("clearance_m")
        if clearance is not None:
            try:
                c = float(clearance)
                if c < CLEARANCE_MIN_M:
                    errors.append(
                        ValidationError(
                            code="clearance_too_low",
                            message=f"Vertical clearance {c:.1f} m is below minimum {CLEARANCE_MIN_M} m.",
                            field="clearance_m",
                        )
                    )
                    score = _deduct_score(score, 25)
                elif c < CLEARANCE_RECOMMENDED_M:
                    warnings.append(
                        ValidationWarning(
                            code="clearance_marginal",
                            message=f"Clearance {c:.1f} m is below typical urban flyover ({CLEARANCE_RECOMMENDED_M} m).",
                            field="clearance_m",
                        )
                    )
                    score = _deduct_score(score, 8)
            except (TypeError, ValueError):
                pass

        spacing = params.get("pier_spacing_m")
        if spacing is not None and length_m > 0:
            try:
                sp = float(spacing)
                if sp < PIER_SPACING_MIN_M:
                    warnings.append(
                        ValidationWarning(
                            code="pier_spacing_tight",
                            message=f"Pier spacing {sp:.0f} m is tight — may increase cost.",
                            field="pier_spacing_m",
                        )
                    )
                    score = _deduct_score(score, 6)
                elif sp > PIER_SPACING_MAX_WARN_M:
                    warnings.append(
                        ValidationWarning(
                            code="pier_spacing_wide",
                            message=f"Pier spacing {sp:.0f} m is long — verify structural span assumptions.",
                            field="pier_spacing_m",
                        )
                    )
                    score = _deduct_score(score, 8)
                if sp > length_m:
                    errors.append(
                        ValidationError(
                            code="pier_spacing_exceeds_length",
                            message="Pier spacing exceeds corridor length.",
                            field="pier_spacing_m",
                        )
                    )
                    score = _deduct_score(score, 20)
            except (TypeError, ValueError):
                pass

    if family == "road":
        shoulder = params.get("shoulder_width_m")
        if shoulder is not None:
            try:
                sw = float(shoulder)
                if sw <= 0 and length_m >= LONG_CORRIDOR_M:
                    warnings.append(
                        ValidationWarning(
                            code="no_shoulder",
                            message="Zero shoulder width on a long road segment — add shoulders for safety.",
                            field="shoulder_width_m",
                        )
                    )
                    score = _deduct_score(score, 8)
            except (TypeError, ValueError):
                pass

    if length_m <= 0:
        warnings.append(
            ValidationWarning(
                code="missing_length",
                message="Corridor length is missing or zero.",
                field="length_m",
            )
        )
        score = _deduct_score(score, 15)

    assumptions.append(
        "Deterministic validation checks preliminary parameters only — not statutory code compliance."
    )
    return score


def _check_building(params: dict[str, Any], score: int, warnings: list, errors: list) -> int:
    floors = params.get("floors")
    area = params.get("builtup_area_sqm")
    if floors is not None:
        try:
            f = int(floors)
            if f > 40:
                warnings.append(
                    ValidationWarning(
                        code="high_rise",
                        message=f"{f} floors requires detailed structural and fire engineering.",
                        field="floors",
                    )
                )
                score = _deduct_score(score, 10)
        except (TypeError, ValueError):
            pass
    if area is not None:
        try:
            a = float(area)
            if a > 50_000:
                warnings.append(
                    ValidationWarning(
                        code="large_footprint",
                        message="Very large built-up area — verify column grid and services.",
                        field="builtup_area_sqm",
                    )
                )
                score = _deduct_score(score, 8)
        except (TypeError, ValueError):
            pass
    return score


def _check_pipeline(params: dict[str, Any], score: int, warnings: list) -> int:
    depth = params.get("trench_depth_m")
    diameter = params.get("pipe_diameter_mm")
    if depth is not None and diameter is not None:
        try:
            if float(depth) * 1000 < float(diameter) * 1.5:
                warnings.append(
                    ValidationWarning(
                        code="shallow_trench",
                        message="Trench depth may be insufficient for pipe diameter and bedding.",
                        field="trench_depth_m",
                    )
                )
                score = _deduct_score(score, 10)
        except (TypeError, ValueError):
            pass
    return score


def validate_design(
    *,
    project_type: str,
    params: dict[str, Any],
    geometry_spec: dict[str, Any] | None,
    planning_meta: dict[str, Any] | None = None,
    preview_mode: bool = False,
    boq_approximate: bool = False,
    design_assumptions: list[str] | None = None,
) -> DesignValidationResult:
    """Run deterministic validation on generated design parameters and metadata."""
    family = project_type_family(project_type)
    spec = geometry_spec or {}
    planning = planning_meta or {}

    score = 100
    warnings: list[ValidationWarning] = []
    errors: list[ValidationError] = []
    recommendations: list[DesignRecommendation] = []
    assumptions: list[str] = list(design_assumptions or [])[:8]

    assumptions.append(CONCEPTUAL_DISCLAIMER)
    assumptions.append(DISCLAIMER[:120] + "…")

    if preview_mode or boq_approximate:
        warnings.append(
            ValidationWarning(
                code="approximate_boq",
                message="BOQ quantities are approximate (fast preview mode).",
            )
        )
        score = _deduct_score(score, 8)

    if planning.get("planning_mode") == "fallback":
        warnings.append(
            ValidationWarning(
                code="llm_planning_fallback",
                message="AI parameter planner fell back to form values — review parameters manually.",
            )
        )
        score = _deduct_score(score, 6)

    if family in ("flyover", "road", "bridge", "layout"):
        score = _check_corridor_params(
            family="flyover" if family in ("flyover", "bridge") else "road",
            params=params,
            geometry_spec=spec,
            score=score,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
            assumptions=assumptions,
        )
    elif family == "building":
        score = _check_building(params, score, warnings, errors)
    elif family == "pipeline":
        score = _check_pipeline(params, score, warnings)

    if not recommendations:
        recommendations.append(
            DesignRecommendation(
                code="engineer_review",
                message="Have a licensed engineer review geometry, quantities, and site conditions.",
            )
        )

    return _finalize(score, warnings, errors, recommendations, assumptions)

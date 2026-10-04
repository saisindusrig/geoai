"""Tests for deterministic design engineering validation (Phase 4)."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.services.ai.orchestrator import _attach_validation_and_review
from app.services.ai import design_planner
from app.services.design.design_validator import validate_design


def _road_params(**overrides):
    base = {
        "length_m": 1000,
        "road_width_m": 14.0,
        "lanes": 4,
        "shoulder_width_m": 1.5,
        "asphalt_thickness_mm": 80,
    }
    base.update(overrides)
    return base


def _road_spec(**overrides):
    base = {
        "geometry_mode": "alignment",
        "elevation_mode": "profile",
        "elevation_assumed": False,
        "max_grade_percent": 5.0,
        "length_m": 1000,
    }
    base.update(overrides)
    return base


def test_valid_design_gets_pass_or_warning():
    result = validate_design(
        project_type="road",
        params=_road_params(),
        geometry_spec=_road_spec(),
        preview_mode=False,
        boq_approximate=False,
    )
    assert result.validation_status in ("pass", "warning")
    assert result.score >= 60
    assert result.conceptual_disclaimer


def test_invalid_lane_width_is_fail():
    result = validate_design(
        project_type="road",
        params=_road_params(road_width_m=6.0, lanes=4),
        geometry_spec=_road_spec(),
    )
    assert result.validation_status == "fail"
    assert any(e.code == "lane_width_too_narrow" for e in result.errors)


def test_excessive_grade_creates_warning_or_fail():
    result = validate_design(
        project_type="road",
        params=_road_params(),
        geometry_spec=_road_spec(max_grade_percent=10.0),
    )
    assert result.validation_status in ("warning", "fail")
    assert any(
        w.code == "steep_grade" for w in result.warnings
    ) or any(e.code == "excessive_grade" for e in result.errors)


def test_missing_alignment_creates_warning():
    result = validate_design(
        project_type="flyover",
        params={"length_m": 400, "deck_width_m": 16, "lanes": 4, "clearance_m": 5.5, "pier_spacing_m": 30},
        geometry_spec={"geometry_mode": "straight", "elevation_mode": "profile", "elevation_assumed": False},
    )
    assert any(w.code == "no_alignment_geometry" for w in result.warnings)


def test_flat_elevation_fallback_creates_warning():
    result = validate_design(
        project_type="road",
        params=_road_params(),
        geometry_spec=_road_spec(elevation_mode="flat", elevation_assumed=True),
    )
    assert any(w.code == "flat_elevation" for w in result.warnings)


def test_validation_attached_to_orchestrator_helper():
    design = {"assumptions": ["Test assumption"], "summary": "Test"}
    review = _attach_validation_and_review(
        design,
        project_type="road",
        params=_road_params(),
        geometry_spec=_road_spec(),
        planning_meta={"planning_mode": "template"},
        quantities={"concrete_m3": 10},
        cost_summary={"total_medium": 1000, "currency": "INR"},
        preview_mode=False,
        boq_approximate=False,
    )
    assert "validation" in design
    assert "design_review" in design
    assert review["validation_status"] in ("pass", "warning", "fail")
    assert review["planning_mode"] == "template"


def test_use_llm_without_instructions_uses_template_mode():
    mock_plan = AsyncMock()

    async def _run():
        with patch.object(settings, "AI_PROVIDER", "openai"):
            with patch.object(settings, "OPENAI_API_KEY", "sk-test"):
                with patch(
                    "app.services.ai.providers.generate_plan_json",
                    mock_plan,
                ):
                    return await design_planner.plan_design(
                        project_type="flyover",
                        params={"length_m": 500, "use_llm": True},
                    )

    result = asyncio.run(_run())
    mock_plan.assert_not_called()
    assert result.planning_mode == "template"


def test_should_use_planner_requires_instructions():
    assert design_planner.should_use_planner({"use_llm": True}) is False
    assert design_planner.should_use_planner({"design_instructions": "4 lanes"}) is True

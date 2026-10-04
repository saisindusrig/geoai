"""Tests for safe LLM design parameter planner (Phase 3)."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.services.ai import design_planner, providers
from app.services.ai.design_plan_schemas import DesignPlan, DesignParameters
from app.services.ai.design_planner import apply_plan_parameters, should_use_planner


VALID_LLM_PLAN = {
    "project_type": "flyover",
    "parameters": {
        "lanes": 4,
        "lane_width_m": 3.65,
        "clearance_m": 5.5,
        "pier_spacing_m": 35,
        "drainage_required": True,
    },
    "assumptions": ["4-lane urban flyover concept"],
    "warnings": ["Geotechnical data not verified"],
    "missing_inputs": [{"field": "soil_bearing", "reason": "No borehole data"}],
}


def test_should_use_planner_with_design_instructions():
    assert should_use_planner({"design_instructions": "4 lane flyover"}) is True
    assert should_use_planner({"custom_instructions": "add drainage"}) is True
    assert should_use_planner({"use_llm": True}) is False
    assert should_use_planner({"length_m": 500}) is False


def test_valid_llm_json_accepted():
    plan = DesignPlan.model_validate(VALID_LLM_PLAN)
    merged, corrections = apply_plan_parameters(
        "flyover",
        {"length_m": 500, "deck_width_m": 16, "clearance_m": 5.5, "pier_spacing_m": 30},
        plan,
    )
    assert merged["lanes"] == 4
    assert merged["clearance_m"] == 5.5
    assert merged["pier_spacing_m"] == 35
    assert merged["deck_width_m"] > 14


def test_missing_fields_filled_with_lane_derived_width():
    plan = DesignPlan(
        project_type="road",
        parameters=DesignParameters(lanes=4, lane_width_m=3.5),
        assumptions=["Four lanes"],
    )
    merged, _ = apply_plan_parameters("road", {"length_m": 1000, "road_width_m": 7.5}, plan)
    assert merged["lanes"] == 4
    assert merged["road_width_m"] == pytest.approx(14.0)


def test_impossible_values_corrected():
    raw = {
        "project_type": "flyover",
        "parameters": {"clearance_m": 2.0, "pier_spacing_m": 5.0},
        "assumptions": [],
        "warnings": [],
        "missing_inputs": [],
    }
    plan = design_planner.parse_and_validate_plan(raw, "flyover")
    merged, corrections = apply_plan_parameters(
        "flyover",
        {"length_m": 200, "clearance_m": 5.5, "pier_spacing_m": 30, "deck_width_m": 16},
        plan,
    )
    assert merged["clearance_m"] >= 4.0
    assert merged["pier_spacing_m"] >= 15.0


def test_invalid_llm_json_falls_back_to_template():
    async def _run():
        with patch.object(settings, "AI_PROVIDER", "openai"):
            with patch.object(settings, "OPENAI_API_KEY", "sk-test"):
                with patch(
                    "app.services.ai.providers.generate_plan_json",
                    new=AsyncMock(return_value=({"not_a_plan": True}, "openai", "gpt-4o-mini")),
                ):
                    return await design_planner.plan_design(
                        project_type="flyover",
                        params={
                            "length_m": 500,
                            "design_instructions": "4 lane flyover",
                            "clearance_m": 5.5,
                        },
                    )

    result = asyncio.run(_run())
    assert result.planning_mode == "fallback"
    assert result.parameters["length_m"] == 500
    assert any("validation" in w.lower() for w in result.warnings)


def test_no_provider_uses_template_mode():
    async def _run():
        with patch.object(settings, "AI_PROVIDER", "mock"):
            with patch.object(settings, "OPENAI_API_KEY", ""):
                with patch.object(settings, "ANTHROPIC_API_KEY", ""):
                    return await design_planner.plan_design(
                        project_type="flyover",
                        params={
                            "length_m": 500,
                            "design_instructions": "4 lane flyover",
                        },
                    )

    result = asyncio.run(_run())
    assert result.planning_mode == "fallback"
    assert result.llm_error == "no_provider"


def test_design_instructions_reach_planner_prompt():
    prompt = design_planner.build_planner_user_prompt(
        project_type="flyover",
        params={"length_m": 500, "design_instructions": "economical pier spacing"},
        site_ctx={"elevation_min_m": 100},
        alignment_length_m=480.0,
        elevation_meta={"elevation_mode": "profile"},
        instructions="economical pier spacing",
    )
    assert "economical pier spacing" in prompt
    assert "480" in prompt


def test_planner_metadata_includes_mode_and_warnings():
    async def _run():
        with patch.object(settings, "AI_PROVIDER", "openai"):
            with patch.object(settings, "OPENAI_API_KEY", "sk-test"):
                with patch(
                    "app.services.ai.providers.generate_plan_json",
                    new=AsyncMock(return_value=(VALID_LLM_PLAN, "openai", "gpt-4o-mini")),
                ):
                    return await design_planner.plan_design(
                        project_type="flyover",
                        params={
                            "length_m": 500,
                            "design_instructions": "4 lane flyover with drainage",
                            "deck_width_m": 16,
                            "clearance_m": 5.5,
                            "pier_spacing_m": 30,
                        },
                        alignment_length_m=500.0,
                    )

    result = asyncio.run(_run())
    meta = result.to_metadata()
    assert meta["planning_mode"] == "llm"
    assert meta["llm_provider"] == "openai"
    assert meta["llm_model"] == "gpt-4o-mini"
    assert len(meta["design_assumptions"]) >= 1
    assert meta["final_parameters"]["lanes"] == 4


def test_generate_plan_json_retries_once():
    calls = {"n": 0}

    async def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return {"project_type": "road", "parameters": {"lanes": 2}, "assumptions": [], "warnings": []}

    async def _run():
        with patch.object(settings, "AI_PROVIDER", "openai"):
            with patch.object(settings, "OPENAI_API_KEY", "sk-test"):
                with patch("app.services.ai.providers._provider_chain", return_value=["openai"]):
                    with patch("app.services.ai.providers._openai_generate", new=AsyncMock(side_effect=flaky)):
                        return await providers.generate_plan_json("sys", "user")

    data, name, model = asyncio.run(_run())
    assert name == "openai"
    assert data["project_type"] == "road"
    assert calls["n"] == 2


def test_design_parameters_rejects_out_of_range():
    with pytest.raises(ValidationError):
        DesignParameters(clearance_m=1.0)

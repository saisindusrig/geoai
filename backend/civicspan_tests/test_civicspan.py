from app.services.ai.civicspan import SiteContext, _fallback_construction_plan, _fallback_plan


def _site() -> SiteContext:
    return SiteContext(
        start={"lat": 18.5196, "lng": 73.8553},
        end={"lat": 18.5196, "lng": 73.8563},
        crossing="waterway",
    )


def test_fallback_plan_creates_a_safe_conceptual_bridge_plan():
    plan = _fallback_plan(
        request="Create a short steel truss pedestrian bridge with two more supports",
        site=_site(),
    )

    assert plan.spec.bridge_type == "pedestrian_bridge"
    assert plan.spec.structure_type == "steel_truss"
    assert 2 <= plan.spec.width_m <= 8
    assert plan.spec.supports == 4
    assert len(plan.spec.stages) == 5
    assert plan.warnings


def test_fallback_plan_uses_girder_when_requested():
    plan = _fallback_plan(
        request="A 6 metre wide girder walkway bridge",
        site=_site(),
    )

    assert plan.spec.structure_type == "steel_girder"
    assert plan.spec.width_m == 6


def test_construction_fallback_supports_a_dam_concept():
    plan = _fallback_construction_plan(
        "dam",
        "Create a 40 metre wide concrete gravity dam",
        _site(),
    )

    assert plan.spec.project_type == "dam"
    assert plan.spec.style == "concrete gravity dam"
    assert plan.spec.width_m == 40
    assert plan.spec.stages == ["site", "foundation", "structure", "finish"]

from app.services.ai.civicspan import BridgeSpec, GeoPoint, SiteContext, _fallback_plan


def _site():
    return SiteContext(
        start=GeoPoint(lat=18.525, lng=73.852),
        end=GeoPoint(lat=18.525, lng=73.8525),
        crossing="waterway",
    )


def test_fallback_is_constrained_and_conceptual():
    plan = _fallback_plan("Build a steel truss bridge", _site())
    assert plan.spec.structure_type == "steel_truss"
    assert 2 <= plan.spec.width_m <= 8
    assert "not survey data" in plan.assumptions[0]


def test_fallback_modifies_existing_spec():
    plan = _fallback_plan("Make it wider to 5 meters and add two more supports", _site(), BridgeSpec(supports=2))
    assert plan.spec.width_m == 5
    assert plan.spec.supports == 4

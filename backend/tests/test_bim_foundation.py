from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.domain.bim import BIMProject
from app.services.assistant.bim_foundation import validate_foundation, propagate_parameters


def fixture(asset_type="BRIDGE"):
    def component(id, dependencies):
        return dict(id=id, asset_id="asset", assembly_id="assembly", component_type="BEAM",
                    parameters=[dict(id="offset", value=2, unit="m")], placement={}, material_id="steel",
                    dependency_ids=dependencies, geometry=dict(primitive=dict(primitive_type="BOX", center=[0, 0, 0], size=[5, .3, .5])),
                    provenance=dict(design_id="concept", design_version=1, source_kind="PREVIEW_ASSUMPTION"))
    return dict(assets=[dict(id="asset", asset_type=asset_type, assembly_ids=["assembly"])],
                assemblies=[dict(id="assembly", asset_id="asset", role="SUPPORT_FRAME", component_ids=["a", "b", "unrelated"])],
                components=[component("a", ["copy"]), component("b", ["copy"]), component("unrelated", [])],
                materials=[dict(id="steel", name="Concept steel", category="STEEL")],
                dependencies=[dict(id="copy", source_component_id="a", source_parameter_id="offset", target_component_id="b", target_parameter_id="offset", operation="COPY")])


@pytest.mark.parametrize("asset_type", ["BRIDGE", "INDUSTRIAL_PLATFORM"])
def test_round_trip_and_deterministic_cross_asset_propagation(asset_type):
    raw = fixture(asset_type)
    before = deepcopy(raw)
    spec, order = validate_foundation(raw)
    assert BIMProject.model_validate(spec.model_dump(by_alias=True)) == spec
    first, dirty = propagate_parameters(spec, {("a", "offset"): 3}, expected_design_version=1)
    assert (first, dirty) == propagate_parameters(spec, {("a", "offset"): 3}, expected_design_version=1)
    assert dirty == ["a", "b"]
    assert [c.id for c in first.components] == [c.id for c in spec.components]
    assert first.components[1].parameters[0].value == 3
    assert first.components[2] == spec.components[2]
    assert first.components[0].geometry == spec.components[0].geometry
    assert raw == before
    assert order.index("a") < order.index("b")
    assert "soil" in first.unknowns and first.engineering_status == "UNVERIFIED"


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d.update(schema_version="bim-project/2"), "bim-project/1"),
    (lambda d: d["components"][0].update(material_id="missing"), "UNRESOLVED_MATERIAL"),
    (lambda d: d["components"][0].update(id="b"), "DUPLICATE_SEMANTIC_ID"),
    (lambda d: d["assemblies"][0].update(component_ids=["a"]), "ASSEMBLY_MEMBERSHIP_MISMATCH"),
    (lambda d: d["dependencies"][0].update(source_parameter_id="missing"), "UNRESOLVED_PARAMETER"),
    (lambda d: d["components"][0]["parameters"][0].update(value=float("nan")), "finite"),
    (lambda d: d["components"][0]["geometry"]["primitive"].update(size=[0, 1, 1]), "greater than 0"),
    (lambda d: d["components"][0].update(validation_status="ENGINEERING_APPROVED"), "UNVALIDATED"),
    (lambda d: d["components"][0]["geometry"].update(script="execute()"), "Extra inputs"),
    (lambda d: d["components"][0]["parameters"][0].update(unit="deg"), "DEPENDENCY_UNIT_MISMATCH"),
])
def test_invalid_contracts_and_references(mutate, code):
    raw = fixture()
    mutate(raw)
    with pytest.raises((ValueError, ValidationError), match=code):
        validate_foundation(raw)


def test_cycles():
    raw = fixture()
    raw["dependencies"].append(dict(id="back", source_component_id="b", source_parameter_id="offset", target_component_id="a", target_parameter_id="offset", operation="COPY"))
    for c in raw["components"][:2]:
        c["dependency_ids"].append("back")
    with pytest.raises(ValueError, match="CIRCULAR_DEPENDENCY"):
        validate_foundation(raw)


@pytest.mark.parametrize("case,code", [("stale", "STALE_DESIGN_VERSION"), ("unresolved", "DEPENDENCY_REQUIRES_REVIEW"), ("constraint", "PARAMETER_CONSTRAINT_VIOLATION"), ("driven", "DEPENDENT_PARAMETER_EDIT")])
def test_atomic_failures(case, code):
    raw = fixture()
    if case == "unresolved":
        raw["dependencies"][0]["operation"] = "UNRESOLVED"
    if case == "constraint":
        raw["constraints"] = [dict(id="bound", component_id="b", parameter_id="offset", minimum=1, maximum=2)]
    before = deepcopy(raw)
    with pytest.raises(ValueError, match=code):
        propagate_parameters(raw, {("b" if case == "driven" else "a", "offset"): 3}, expected_design_version=2 if case == "stale" else 1)
    assert before == raw


def test_noop_preserves_components():
    spec, _ = validate_foundation(fixture())
    result, dirty = propagate_parameters(spec, {("a", "offset"): 2}, expected_design_version=1)
    assert result == spec and dirty == []


def test_checked_in_schema():
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "docs/contracts/bim-project.schema.json"
    assert json.loads(path.read_text(encoding="utf-8")) == BIMProject.model_json_schema(by_alias=True)


def test_relationships_and_multiple_writers():
    raw = fixture()
    raw["connections"] = [dict(id="support", from_component_id="a", to_component_id="b", kind="SUPPORTED_BY")]
    for c in raw["components"][:2]:
        c["relationship_ids"] = ["support"]
    validate_foundation(raw)
    raw["dependencies"].append({**raw["dependencies"][0], "id": "second"})
    for c in raw["components"][:2]:
        c["dependency_ids"].append("second")
    with pytest.raises(ValueError, match="MULTIPLE_DEPENDENCY_WRITERS"):
        validate_foundation(raw)

import pytest
from pydantic import TypeAdapter, ValidationError
from app.domain.stage1 import (Fact, HorizontalCRS, VerticalReference, SiteSelection, Evidence,
                              CivilIntent, AssetCapability, ProposalCommand, ValidationResult)
from app.services.assistant.foundation import capability, require_execution, submit_proposal_command, guard_assistant_response

HASH = "a" * 64


def test_unknown_roundtrip_and_zero():
    raw = {"id": "elevation", "sourceKind": "UNKNOWN", "value": None, "reason": "NOT_COLLECTED"}
    fact = Fact[float].model_validate(raw)
    assert Fact[float].model_validate_json(fact.model_dump_json()) == fact
    with pytest.raises(ValidationError):
        Fact[float].model_validate(raw | {"value": 0})
    known = Fact[float].model_validate({"id": "zero", "sourceKind": "SURVEY", "value": 0,
        "evidenceIds": ["e1"], "use": "CONCEPT", "verification": "UNVERIFIED"})
    assert known.root.value == 0
    assert known.root.verification == "UNVERIFIED"


@pytest.mark.parametrize("definition,unit", [("bogus", "METRE"), ("EPSG:4326", "METRE"), ("EPSG:4978", "METRE")])
def test_invalid_crs(definition, unit):
    with pytest.raises((ValidationError, ValueError)):
        TypeAdapter(HorizontalCRS).validate_python({"status":"RESOLVED", "definition":definition, "axisOrder":"XY", "unit":unit})


def test_unknown_crs_and_vertical_cannot_have_values():
    with pytest.raises(ValidationError):
        TypeAdapter(HorizontalCRS).validate_python({"status":"UNKNOWN", "definition":"EPSG:4326"})
    with pytest.raises(ValidationError):
        TypeAdapter(VerticalReference).validate_python({"status":"UNKNOWN", "identifier":"sea level"})


P1 = {"type":"Point", "coordinates":[77,12]}
P2 = {"type":"Point", "coordinates":[77.01,12.01]}
LINE = {"type":"LineString", "coordinates":[P1["coordinates"],P2["coordinates"]]}
AREA = {"type":"Polygon", "coordinates":[[[77,12],[77.01,12],[77.01,12.01],[77,12]]]}


@pytest.mark.parametrize("selection", [
    {"kind":"POINT","geometry":P1}, {"kind":"AREA","geometry":AREA},
    {"kind":"ROUTE","geometry":LINE}, {"kind":"ENDPOINTS","endpointA":P1,"endpointB":P2},
    {"kind":"CROSSING","geometry":LINE,"endpointA":P1,"endpointB":P2},
])
def test_selection_variants_roundtrip(selection):
    adapter = TypeAdapter(SiteSelection)
    result = adapter.validate_python(selection)
    assert adapter.validate_json(result.model_dump_json(by_alias=True)) == result


@pytest.mark.parametrize("selection", [{"kind":"AREA","geometry":LINE},
    {"kind":"ENDPOINTS","endpointA":P1,"endpointB":P1},
    {"kind":"CROSSING","geometry":LINE,"endpointA":P2,"endpointB":P1}])
def test_invalid_selections(selection):
    with pytest.raises(ValidationError):
        TypeAdapter(SiteSelection).validate_python(selection)


def evidence(source):
    return dict(id="e1", projectId="1", sourceType=source["kind"], source=source,
        retrievedAt="2026-10-08T00:00:00Z", horizontalCrs={"status":"UNKNOWN"},
        verticalReference={"status":"UNKNOWN"}, accuracy={}, status="UNVERIFIED", contentHash=HASH)


def test_evidence_required_fields_and_survey_not_verified():
    with pytest.raises(ValidationError):
        Evidence.model_validate(evidence({"kind":"SURVEY"}))
    survey = evidence({"kind":"SURVEY","surveyDatasetId":"s1","sourceFileId":"f1"})
    assert Evidence.model_validate(survey).status == "UNVERIFIED"
    with pytest.raises(ValidationError):
        Evidence.model_validate(survey | {"status":"VERIFIED"})
    with pytest.raises(ValidationError):
        Evidence.model_validate(survey | {"accuracy":{"horizontalRmseM":0.01}})


def test_public_map_does_not_become_validated_input():
    with pytest.raises(ValidationError):
        Fact[bool].model_validate(dict(id="road", sourceKind="PUBLIC_MAP", value=False,
            evidenceIds=["map"],use="VALIDATED_INPUT",verification="VERIFIED"))


def test_generic_multi_asset_intent_and_unknown_asset():
    names = ["Apartment A", "Apartment B", "Access road", "Drainage", "Bridge", "Cofferdam"]
    intent = CivilIntent(kind="DESIGN_REQUEST", domain="CIVIL_INFRASTRUCTURE", needs_clarification=False,
        assets=[dict(id=str(i), asset_type="UNKNOWN_CIVIL_ASSET" if name == "Cofferdam" else name,
                     requested_asset_name=name) for i,name in enumerate(names)])
    assert len(intent.assets) == 6
    assert CivilIntent.model_validate_json(intent.model_dump_json()) == intent
    assert capability("Cofferdam").asset_type == "Cofferdam"
    assert require_execution("Cofferdam", "DISCUSS").discussion_support == "FULL"
    for name in names:
        with pytest.raises(ValueError, match="UNSUPPORTED_OPERATION"):
            require_execution(name, "GENERATE")


def test_capability_cannot_advertise_unsupported_execution():
    raw = capability("TUNNEL").model_dump() | {"supported_operations":["GENERATE"]}
    with pytest.raises(ValidationError):
        AssetCapability.model_validate(raw)


@pytest.mark.parametrize("action", [None, {"type":"update_parameters","payload":{"floors":3}},
    {"type":"generate_design"}, {"type":"delete_objects"}])
def test_assistant_reply_boundary(action):
    result = guard_assistant_response({"reply":"Explanation", "action":action})
    assert result["actions"] == []
    assert result["action"] is None
    if action:
        assert "PROPOSAL_REQUIRED" in result["warnings"][0]


def test_proposal_skeleton_cannot_execute():
    with pytest.raises(NotImplementedError, match="PROPOSAL_SERVICE_UNAVAILABLE"):
        submit_proposal_command(ProposalCommand(effect="PROPOSAL_ONLY",kind="CHANGE_REQUEST",request="Raise selected object",objects=[]))


def test_validation_cannot_pass_blocker():
    with pytest.raises(ValidationError):
        ValidationResult(id="v",level="CONCEPT_VALIDATION",validator_id="v",validator_version="1",
            input_hash=HASH,status="PASSED",issues=[dict(code="MISSING",severity="BLOCKER",component_ids=[],
                field_paths=[],evidence_ids=[],message="Missing",remediation="Supply input")])

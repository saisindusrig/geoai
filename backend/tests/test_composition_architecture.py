"""Cross-domain contracts and routing: fixture adapters never execute geometry."""
import pytest
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException
from app.core.asset_families import FAMILIES, COMPONENT_KINDS, ASSET_DEFINITIONS, asset_definition, catalogue_coverage
from app.services.assistant.specialists import AdapterMetadata, AdapterRegistry, ADAPTERS, route_assets, ExecutionRouter
from app.services.assistant.foundation import capability
from app.domain.composition import PatchProposal, RelationshipInput, ObjectLineage
from app.services.assistant.composition import save_relationship, project_composition, check_patch
from app.services.assistant.storage import insert, digest
from test_site_workspace import site_db, api_client


class Spec(BaseModel):
    name: str


class FixtureAdapter:
    specification_schema = Spec
    metadata = AdapterMetadata("fixture", "1", "BUILDING", frozenset({"building"}),
        frozenset({"DISCUSS", "PLAN", "PROPOSE", "GENERATE", "VALIDATE_GEOMETRY", "ANALYZE"}), "fixture/1", frozenset({"TRANSLATE_COMPONENT"}))

    def can_handle(self, asset_type): return asset_type.lower() == "building"
    def requirements_to_specification(self, *args): raise AssertionError("No execution")
    validate_specification = generate_preview = generate = validate_geometry = apply_patch = requirements_to_specification


def registry():
    result = AdapterRegistry(); result.register(FixtureAdapter()); return result


def test_catalogue_overlay_preserves_ids_and_fallbacks():
    assert asset_definition("dam")["family"] == "DAM"
    category = next(k for k in ASSET_DEFINITIONS if asset_definition(k)["mappingSource"] == "CATEGORY")
    assert asset_definition(category)["catalogueId"] == category
    assert asset_definition("cofferdam")["family"] == "CUSTOM"
    assert asset_definition("new_unknown_object")["catalogueId"] is None
    assert asset_definition("new_unknown_object")["family"] == "CUSTOM"
    assert {a["catalogueId"] for a in catalogue_coverage()["assets"]} == set(ASSET_DEFINITIONS)
    assert all(set(f.component_kinds) <= COMPONENT_KINDS.keys() for f in FAMILIES.values())
    assert "FOUNDATION" in FAMILIES["BUILDING"].component_kinds
    assert asset_definition("building")["generationStatus"] == "UNSUPPORTED"


def test_capability_registry_all_operations():
    actual = capability("building", registry())
    assert set(actual.supported_operations) == {"DISCUSS", "PLAN", "PROPOSE", "GENERATE", "VALIDATE_GEOMETRY", "ANALYZE"}
    assert actual.generation_support == actual.geometry_validation_support == actual.engineering_analysis_support == "FULL"
    for asset in ("building", "bridge", "unknown"):
        actual = capability(asset, AdapterRegistry())
        assert actual.discussion_support == "FULL"
        assert actual.planning_support == actual.proposal_support == "CONCEPT_ONLY"
        assert actual.generation_support == "UNSUPPORTED"
    assert ADAPTERS.resolve("building") is None


def test_adapter_lookup_rejects_wrong_family_and_type():
    reg = registry()
    assert reg.resolve("BUILDING").metadata.id == "fixture"
    assert reg.resolve("bridge") is None
    assert reg.resolve("warehouse") is None
    assert reg.resolve("unknown") is None
    with pytest.raises(ValueError): reg.register(FixtureAdapter())


@pytest.mark.parametrize("types,status", [(["building"], "SUPPORTED"), (["building", "bridge"], "PARTIAL"), (["bridge", "unknown"], "UNSUPPORTED")])
def test_execution_router_chooses_server_adapter(types, status):
    result = route_assets([{"assetRequestId": str(i), "assetType": t, "adapterId": "malicious"} for i,t in enumerate(types)], registry())
    assert result["status"] == status
    assert result["atomicApproval"]
    assert result["canBuildAll"] == (status == "SUPPORTED")
    assert all(a["adapterId"] in {None, "fixture"} for a in result["assets"])


def assets(db):
    for aid, project, kind in [("a",1,"building"),("b",1,"road"),("c",1,"unknown"),("foreign",2,"bridge")]:
        insert(db,"asset_instances",id=aid,project_id=project,asset_type=kind,name=aid)
    db.commit()


def test_relational_composition_ownership_and_idempotency(site_db):
    assets(site_db)
    request = RelationshipInput(client_request_id="edge",from_asset_id="a",to_asset_id="b",kind="SERVES")
    first = save_relationship(site_db,1,request)
    assert save_relationship(site_db,1,request)["id"] == first["id"]
    composition = project_composition(site_db,1)
    assert {a["family"] for a in composition["assets"]} == {"BUILDING","ROAD","CUSTOM"}
    assert len(composition["relationships"]) == 1
    with pytest.raises(HTTPException): save_relationship(site_db,1,request.model_copy(update={"client_request_id":"foreign","to_asset_id":"foreign"}))
    assert project_composition(site_db,2)["relationships"] == []


def patch(**changes):
    args = dict(base_model_revision_id="1",target_component_id="pier-a",expected_component_hash=digest({"id":"pier-a","name":"Pier A","geometry":{"kind":"box"}}),asset_type="building",parameters={"operation":"TRANSLATE_COMPONENT","deltaM":[0,0,1]})
    return PatchProposal(**(args | changes))


def test_patch_preflight_supported_never_applies(site_db):
    assert check_patch(site_db,1,patch(),registry()) == {"status":"SUPPORTED","code":"REVIEW_AND_APPROVAL_REQUIRED","applicable":False}
    assert check_patch(site_db,1,patch())["status"] == "UNSUPPORTED"
    assert check_patch(site_db,1,patch(expected_component_hash="0"*64),registry())["status"] == "STALE"
    for project, data in [(1,patch(base_model_revision_id="999")),(2,patch()),(1,patch(target_component_id="foreign"))]:
        with pytest.raises(HTTPException): check_patch(site_db,project,data,registry())


def test_patch_and_lineage_fail_closed():
    with pytest.raises(ValidationError): patch(parameters={"operation":"EXECUTE_CODE","code":"evil"})
    with pytest.raises(ValidationError): patch(parameters={"operation":"SET_DIMENSION","dimension":"WIDTH","valueM":-1})
    with pytest.raises(ValidationError): ObjectLineage(object_id="x",origin="GENERATED",created_in_revision_id="1",last_modified_in_revision_id="1")
    with pytest.raises(ValidationError): ObjectLineage(object_id="x",origin="MANUAL",proposal_id="fake",created_in_revision_id="1",last_modified_in_revision_id="1")


def test_multi_asset_proposal_relationship_staleness(site_db):
    from test_assistant_runtime import message, approval
    from app.domain.assistant_runtime import ProposalRequest, ProposalContent
    from app.services.assistant.proposals import ProposalService
    msg,_ = message(site_db,"Design a building, road and cofferdam concept")
    svc = ProposalService()
    request = ProposalRequest(client_request_id="multi",message_id=msg["id"],title="Site concept",rationale="Review separately",
        assets=[{"assetRequestId":f"A{i}","assetType":t,"name":t,"requirements":["Concept only"]} for i,t in enumerate(["building","road","cofferdam"])])
    view = svc.create(site_db,1,1,request)
    entries = view["content"]["assetProposals"]
    assert [a["assetFamily"] for a in entries] == ["BUILDING","ROAD","CUSTOM"]
    assert all(not a["generationEligible"] and a["blockers"] for a in entries)
    legacy = dict(view["content"]); legacy.pop("assetProposals")
    assert ProposalContent.model_validate(legacy).asset_proposals == []
    svc.approve(site_db,1,1,approval(view))
    assert ExecutionRouter(registry()).route_approved(site_db,1,view["id"])["status"] == "PARTIAL"
    save_relationship(site_db,1,RelationshipInput(client_request_id="new-edge",from_asset_id=entries[0]["assetId"],to_asset_id=entries[1]["assetId"],kind="SERVES"))
    assert svc.read(site_db,1,view["id"])["status"] == "STALE"
    with pytest.raises(HTTPException): ExecutionRouter(registry()).route_approved(site_db,1,view["id"])


def test_composition_api_ownership(api_client):
    assert api_client.get("/api/projects/1/composition").status_code == 200
    assert api_client.get("/api/projects/2/composition").status_code == 404

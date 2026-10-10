"""Offline staged authoring and real native proofs. No provider invocation."""
from copy import deepcopy
import json
import pytest
from pydantic import ValidationError
from app.domain.bim_authoring import AuthoringBundle, AssemblyPlan
from app.experimental.bim_authoring import (FrozenAuthoringContext, AuthoringError, capabilities,
    prepare_candidate, stage_packet, proposal_summary, compile_offline_proof, proposal_request, create_offline_proposal)
from app.experimental.bim_authoring_fixtures import authoring_case
from app.experimental.cad_contract import Source, digest, encode


@pytest.fixture
def context():
    return FrozenAuthoringContext(Source(project_id=1,revision_id=1,revision_document_hash="a"*64,
        design_id="server-owned-design",design_version=7,source_model_revision_id="1"),"selection-1","AREA",
        ("selected-existing-object",),("server-evidence",),True)


def raw(name="platform"):
    return authoring_case(name).model_dump(mode="json")


def rebind(data):
    from app.domain.bim_authoring import AuthoringIntent
    data["plan"]["intent_hash"]=digest(AuthoringIntent.model_validate(data["intent"]))
    plan=AssemblyPlan.model_validate(data["plan"])
    for expansion in data["expansions"]:expansion["plan_hash"]=digest(plan)
    data["relationships"]["plan_hash"]=digest(plan)
    return data


@pytest.mark.parametrize("name,count",[("bridge",13),("platform",12),("mixed",25),("unregistered",12)])
def test_deterministic_hierarchy_and_native_geometry(context,name,count):
    original=authoring_case(name)
    candidate=prepare_candidate(original,context)
    assert len(candidate.model.components) == count
    assert original == authoring_case(name)
    assert candidate.candidate_hash == prepare_candidate(original.model_dump(mode="json",by_alias=True),context).candidate_hash
    for stage in ("UNDERSTAND","PLAN","EXPAND","RELATE"):
        packet=stage_packet(stage,intent=original.intent,plan=original.plan,assembly_id=original.plan.assemblies[0].id,expansions=original.expansions)
        assert len(encode(packet)) <= 24000
        assert packet["capabilities"]["productionCadBuild"] is False
    results,blobs=compile_offline_proof(candidate)
    assert len(results) == count
    assert all(r.geometry_valid and r.solid_count == 1 and r.volume_m3 > 0 for r in results)
    assert all(c.provenance.design_id == context.source.design_id and c.provenance.design_version == 7 for c in candidate.model.components)
    review=proposal_summary(candidate,results)
    assert review["geometryStatus"] == "NATIVE_GEOMETRY_VERIFIED"
    assert review["finalizationBlocked"] and review["engineeringStatus"] == "UNVERIFIED"
    assert review["unresolvedConnections"] and review["unresolvedClearances"]
    if name == "mixed":
        assert len(candidate.model.assets) == 2
        assert len({d.asset_id for d in candidate.geometry.definitions}) == 2
        second=[r for r in results if r.component_id.startswith("platform-")]
        assert min(r.bounds_m[0] for r in second) > 19
    assert len(blobs) >= count


def test_cross_asset_reuse_and_parameter_propagation(context):
    from app.services.assistant.bim_foundation import propagate_parameters
    from app.experimental.cad_contract import from_bim
    platform=prepare_candidate(authoring_case("platform"),context)
    custom=prepare_candidate(authoring_case("unregistered"),context)
    assert [(d.recipe,d.material) for d in platform.geometry.definitions] == [(d.recipe,d.material) for d in custom.geometry.definitions]
    updated,dirty=propagate_parameters(platform.model,{("platform-primary-0","length"):6},expected_design_version=7)
    assert dirty == ["platform-primary-0","platform-primary-1"]
    derived=from_bim(updated,platform.mapping,source=context.source)
    assert next(d for d in derived.definitions if d.component_id == "platform-primary-1").recipe.parameters["length"] == 6
    old={d.component_id:d for d in platform.geometry.definitions}
    assert all(d == old[d.component_id] for d in derived.definitions if d.component_id not in dirty)


def test_nested_placements_and_bounded_expansion(context):
    data=raw()
    root=data["plan"]["assemblies"][0]
    root["placement"]={"origin":[10,20,0],"heading_deg":90}
    data["plan"]["assemblies"][1]["placement"]["origin"]=[2,0,0]
    candidate=prepare_candidate(rebind(data),context)
    beam=next(d for d in candidate.geometry.definitions if d.component_id == "platform-primary-0")
    assert beam.assembly_placement.origin == pytest.approx([10,22,0])
    assert beam.assembly_placement.heading_deg == 90
    expansion=stage_packet("EXPAND",intent=candidate.bundle.intent,plan=candidate.bundle.plan,assembly_id=candidate.bundle.plan.assemblies[1].id)
    assert "assembly" in expansion["input"] and "expansions" not in expansion["input"]


@pytest.mark.parametrize("field",["project_id","source_revision","approval_id","provenance","geometry_validation","python","javascript","cad_script"])
def test_no_model_owned_authority_or_executable_fields(context,field):
    data=raw();data[field]="untrusted"
    with pytest.raises(ValidationError):prepare_candidate(data,context)


def test_feature_gate_source_scope_and_unknowns(context):
    from dataclasses import replace
    with pytest.raises(AuthoringError,match="CAPABILITY_DISABLED"):
        prepare_candidate(raw(),replace(context,enabled=False))
    data=raw();data["intent"]["requested_object_refs"]=["other-project-object"]
    with pytest.raises(AuthoringError,match="UNAUTHORIZED_OBJECT"):
        prepare_candidate(rebind(data),context)
    data=raw();data["intent"]["requested_selection_ref"]="other-selection"
    with pytest.raises(AuthoringError,match="UNAUTHORIZED_SELECTION"):
        prepare_candidate(rebind(data),context)
    with pytest.raises(AuthoringError,match="SELECTION_INCOMPATIBLE"):
        prepare_candidate(raw(),replace(context,selection_kind="ROUTE"))
    data=raw();data["intent"]["systems"][0]["compatible_selection_kinds"]=["ROUTE"]
    with pytest.raises(AuthoringError,match="SELECTION_CAPABILITY"):
        prepare_candidate(rebind(data),replace(context,selection_kind="ROUTE"))
    candidate=prepare_candidate(raw(),context)
    assert {"terrain","soil","loads","foundations","engineeringApproval"}.issubset(candidate.model.unknowns)
    assert not hasattr(candidate.bundle,"project_id")
    bridge=prepare_candidate(authoring_case("bridge"),context)
    assert "crossingConditions" in bridge.model.unknowns


def test_unsupported_feature_is_explicit_and_never_compiles(context,monkeypatch):
    from app.experimental import cad_worker
    monkeypatch.setattr(cad_worker,"compile_batch",lambda *_:pytest.fail("Rejected feature must not invoke native work"))
    with pytest.raises(AuthoringError,match="UNSUPPORTED_FEATURE") as failure:
        prepare_candidate(authoring_case("unsupported"),context)
    assert failure.value.references == ("REINFORCEMENT_CAGE",)
    from app.experimental.bim_authoring import review_offline
    review=review_offline(authoring_case("unsupported"),context)
    assert review["geometryStatus"] == "REJECTED" and review["unsupportedPortions"]
    assert review["engineeringStatus"] == "UNVERIFIED" and review["finalizationBlocked"]


@pytest.mark.parametrize("case",["negative","units","duplicate","material","section","recipe","recipe-id","membership","support","clearance","cycle","support-cycle","constraint","constraint-applicability","dangling-connection","self-connection","dependency-values","unknown-component","parent-cycle","cross-asset-parent","stale-plan","stale-intent","unresolved-dependency"])
def test_invalid_authoring_rejected(context,case):
    data=raw("mixed" if case == "cross-asset-parent" else "platform")
    first=data["expansions"][0]["components"][0]
    if case == "negative":first["parameters"][0]["value"]=-1
    if case == "units":first["parameters"][0]["unit"]="mm"
    if case == "duplicate":data["expansions"][0]["components"][1]["id"]=first["id"]
    if case == "material":first["material_id"]="not-a-material"
    if case == "section":first["cross_section_id"]="missing-section"
    if case == "recipe":first["recipe"]["operation"]="ARBITRARY_SCRIPT"
    if case == "recipe-id":first["recipe"]["component_id"]="different-component"
    if case == "membership":data["expansions"].pop()
    if case == "support":data["relationships"]["connections"]=[]
    if case == "clearance":data["relationships"]["clearances"]=[]
    if case == "cycle":
        dependency=data["relationships"]["dependencies"][0]
        data["relationships"]["dependencies"].append(dict(**{**dependency,"id":"reverse-copy","source_component_id":dependency["target_component_id"],"target_component_id":dependency["source_component_id"]}))
    if case == "support-cycle":
        edge=data["relationships"]["connections"][0];edge["external_support"]=None;edge["to_component_id"]="platform-primary-0"
    if case in {"constraint","constraint-applicability"}:
        data["relationships"]["constraints"]=[dict(id="required-limit",component_id=first["id"],parameter_id="length" if case == "constraint" else "not-a-parameter",minimum=1,maximum=2)]
    if case == "dangling-connection":data["relationships"]["connections"][4]["to_component_id"]="missing-member"
    if case == "self-connection":data["relationships"]["connections"][4]["to_component_id"]=data["relationships"]["connections"][4]["from_component_id"]
    if case == "dependency-values":next(c for e in data["expansions"] for c in e["components"] if c["id"] == "platform-primary-1")["parameters"][0]["value"]=6
    if case == "unknown-component":data["plan"]["assemblies"][0]["groups"][0]["component_type"]="REINFORCEMENT";rebind(data)
    if case == "parent-cycle":data["plan"]["assemblies"][0]["parent_id"]=data["plan"]["assemblies"][1]["id"];rebind(data)
    if case == "cross-asset-parent":data["plan"]["assemblies"][0]["parent_id"]="platform-column-assemblies";rebind(data)
    if case == "stale-plan":data["expansions"][0]["plan_hash"]="f"*64
    if case == "stale-intent":data["intent"]["requested_structure"]="Changed request"
    if case == "unresolved-dependency":data["relationships"]["dependencies"][0]["operation"]="UNRESOLVED"
    with pytest.raises((ValueError,AuthoringError)):prepare_candidate(data,context)


def test_budget_and_stage_boundaries(context):
    data=raw();data["plan"]["assemblies"][0]["groups"][0]["count"]=8
    with pytest.raises(AuthoringError,match="ASSEMBLY_BUDGET"):prepare_candidate(rebind(data),context)
    b=authoring_case("platform")
    with pytest.raises(AuthoringError,match="EXPANSIONS_REQUIRED"):stage_packet("RELATE",intent=b.intent,plan=b.plan)
    with pytest.raises(AuthoringError,match="UNKNOWN_AUTHORING_STAGE"):stage_packet("BUILD")
    assert capabilities()["dependencies"] == ["COPY"]
    with pytest.raises(AuthoringError,match="HUMAN_REQUEST_REQUIRED"):stage_packet("UNDERSTAND")


def test_total_component_budget(context):
    data=raw()
    for i in range(7):
        data["plan"]["assemblies"].append(dict(id=f"extra-{i}",asset_id=data["plan"]["assets"][0]["id"],role="EXTRA",groups=[dict(id=f"extra-group-{i}",role="BEAM",component_type="BEAM",count=8)]))
    with pytest.raises(AuthoringError,match="COMPONENT_BUDGET"):prepare_candidate(rebind(data),context)


def test_mutated_candidate_cannot_run_native(context,monkeypatch):
    from app.experimental import cad_worker
    candidate=prepare_candidate(raw(),context)
    candidate.model.components.pop()
    monkeypatch.setattr(cad_worker,"compile_batch",lambda *_:pytest.fail("Modified candidate must not compile"))
    with pytest.raises(AuthoringError,match="CANDIDATE_MUTATED"):compile_offline_proof(candidate)


def test_review_data_uses_existing_proposal_contract(context):
    candidate=prepare_candidate(authoring_case("mixed"),context)
    summary=proposal_summary(candidate)
    assert len(summary["assets"]) == 2 and len(summary["components"]) == 25
    assert summary["geometryStatus"] == "CONTRACT_VALID_NATIVE_NOT_RUN"
    request=proposal_request(candidate,request_id="offline",message_id="owned-human-message")
    assert len(request.assets) == 2
    assert all(candidate.candidate_hash in a.requirements[0] for a in request.assets)
    assert all(a.ai3d_design is None and a.building_spec is None for a in request.assets)
    assert "UNRESOLVED" in json.dumps(summary)


def test_owned_proposal_no_approval_no_native_no_revision(cad_db,monkeypatch):
    from test_assistant_runtime import message
    from app.experimental import cad_worker
    from app.db.models import ModelRevision,GeneratedFile
    from app.services.assistant.storage import rows
    from app.experimental.cad_artifacts import local_orphans
    monkeypatch.setattr(cad_worker,"compile_batch",lambda *_:pytest.fail("Proposal authoring must not compile"))
    msg,_=message(cad_db,"Create a conceptual industrial elevated platform for explicit review.")
    view=create_offline_proposal(cad_db,project_id=1,user_id=1,message_id=msg["id"],request_id="authoring-proposal",data=authoring_case("platform"))
    assert view["review"]["sourceRevision"] == 1
    assert cad_db.query(ModelRevision).count() == 1
    assert not rows(cad_db,"proposal_approvals",1)
    assert cad_db.query(GeneratedFile).filter_by(file_type="bim_authoring_review_v1").count() == 1
    assert local_orphans(cad_db,user_id=1,project_id=1)["orphanHashes"] == []
    assert create_offline_proposal(cad_db,project_id=1,user_id=1,message_id=msg["id"],request_id="authoring-proposal",data=authoring_case("platform"))["proposal"]["id"] == view["proposal"]["id"]
    from fastapi import HTTPException
    with pytest.raises(HTTPException):create_offline_proposal(cad_db,project_id=1,user_id=2,message_id=msg["id"],request_id="unauthorized",data=authoring_case("platform"))


# Existing isolated ownership/profile/revision fixture; no shared production DB.
from test_cad_workspace import cad_db
from test_site_workspace import site_db

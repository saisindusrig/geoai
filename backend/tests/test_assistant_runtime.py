"""Deterministic Step 6–9 tests; no live provider or geometry mutation."""
import asyncio
import copy
import pytest
from fastapi import HTTPException
from app.domain.assistant_runtime import ProposalRequest, ApplicationApproval
from app.domain.site_workspace import ConversationInput, MessageInput
from app.services.assistant.conversations import ConversationService
from app.services.assistant.storage import rows, owned_row, digest, update
from app.services.assistant.proposals import ProposalService
from app.services.assistant.policy import evaluate
from app.services.assistant.context import build_context
from app.services.assistant.tools import execute, ToolContext
from app.services.assistant.runtime import process, queue_run, retry_run
from app.services.ai.nebius import AssistantProviderError
from app.db.models import Project, ModelRevision
from test_site_workspace import site_db, profile, api_client


def message(db,text="Design a bridge concept",selected=False):
    data=profile(db)[3]["version"]
    svc=ConversationService()
    convo=svc.create(db,1,1,ConversationInput(client_request_id="runtime"))
    result=svc.submit(db,1,1,convo["id"],MessageInput(client_request_id=str(len(rows(db,"conversation_messages",1))),
        parts=[{"kind":"TEXT","text":text}],context={"siteProfileVersionId":data["id"],"siteSelectionVersionId":data["selectionVersion"]["id"],
            "modelRevisionId":"1","selectedObjectIds":["pier-a"] if selected else []}))
    return owned_row(db,"conversation_messages",1,result["messageId"]),result["runId"]


def proposal(db,text="Design a bridge concept",selected=False,**kwargs):
    msg,_=message(db,text,selected)
    req=ProposalRequest(client_request_id="proposal",message_id=msg["id"],title="Bridge concept",rationale="Recorded concept rationale",
        assets=[{"assetType":"BRIDGE","name":"Bridge A"}],**kwargs)
    return ProposalService().create(db,1,1,req),req


def approval(view):
    return ApplicationApproval(client_request_id="approve",proposal_version_id=view["id"],proposal_hash=view["contentHash"],
        dependency_hash=view["dependencyHash"],validation_hash=view["validationHash"],alternative_id=None,
        acknowledged_assumption_version_ids=view["content"]["contract"]["assumptionVersionIds"],expected_model_revision_id="1")


def test_proposal_immutable_revision_and_approval(site_db):
    view,req=proposal(site_db,assumptions=["Concept height requires confirmation"])
    assert view["status"]=="READY_FOR_REVIEW"
    svc=ProposalService();assert svc.create(site_db,1,1,req)["id"]==view["id"]
    first=svc.approve(site_db,1,1,approval(view));assert svc.approve(site_db,1,1,approval(view))==first
    assert len(rows(site_db,"proposal_approvals",1))==1
    second=svc.create(site_db,1,1,req.model_copy(update={"client_request_id":"revision","parent_version_id":view["id"],"title":"Revised"}))
    assert second["version"]==2 and view["contentHash"]==owned_row(site_db,"design_proposal_versions",1,view["id"])["content_hash"]
    assert len(rows(site_db,"model_revisions",1))==1
    assert svc.read(site_db,1,view["id"])["status"]=="STALE"
    specs=rows(site_db,"asset_specification_versions",1)
    assert specs[0]["asset_id"]==specs[1]["asset_id"] and specs[1]["version"]==2


@pytest.mark.parametrize("field",["proposal_hash","dependency_hash","validation_hash"])
def test_approval_exact_hash(site_db,field):
    view,_=proposal(site_db)
    with pytest.raises(HTTPException):ProposalService().approve(site_db,1,1,approval(view).model_copy(update={field:"0"*64}))
    assert not rows(site_db,"proposal_approvals",1)


def test_stale_boundary_and_no_build(site_db):
    view,_=proposal(site_db);svc=ProposalService();svc.approve(site_db,1,1,approval(view))
    for _ in range(2):
        with pytest.raises(HTTPException) as e:svc.build(site_db,1,view["id"])
        assert e.value.detail["code"]=="GENERATION_UNAVAILABLE"
    assert not rows(site_db,"generation_requests",1)
    site_db.get(Project,1).boundary_geojson=None;site_db.commit()
    assert svc.read(site_db,1,view["id"])["status"]=="STALE"
    with pytest.raises(HTTPException):svc.approve(site_db,1,1,approval(view))


def test_attached_manual_edit_race_and_unrelated_edit(site_db):
    view,_=proposal(site_db,"Raise this pier by 0.5 m",True,translation={"objectIds":["pier-a"],"deltaM":[0,0,.5]})
    svc=ProposalService();svc.approve(site_db,1,1,approval(view))
    doc=copy.deepcopy(site_db.get(ModelRevision,1).document_json);doc["components"].append({"id":"other","geometry":{}})
    site_db.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json=doc));site_db.commit()
    # Placement absence on the new revision is a real dependency change; mirror unchanged placement.
    from app.db.models import ModelPlacement
    site_db.add(ModelPlacement(project_id=1,model_revision_id=2,anchor_longitude=77,anchor_latitude=12,anchor_elevation=None,local_transform_json={"preserve":True}));site_db.commit()
    assert svc.read(site_db,1,view["id"])["current"]
    doc=copy.deepcopy(doc);doc["components"][0]["name"]="Changed pier"
    site_db.add(ModelRevision(id=3,project_id=1,design_scenario_id=1,revision_number=3,document_json=doc));site_db.commit()
    assert svc.read(site_db,1,view["id"])["status"]=="STALE"


@pytest.mark.parametrize("text,kind,effect",[("Why is this entrance here?","EXPLANATION_REQUEST","READ_ONLY"),
    ("Move this entrance east.","CHANGE_REQUEST","PROPOSAL_ONLY"),("What's the slope here?","SITE_QUERY","READ_ONLY"),
    ("Is this bridge structurally safe?","ANALYSIS_REQUEST","READ_ONLY"),("Approve it.","PROPOSAL_APPROVAL","APPROVAL_UI_REQUIRED"),
    ("I want two buildings, an access road, drainage and a bridge.","DESIGN_REQUEST","PROPOSAL_ONLY"),
    ("Can we discuss a cofferdam?","QUESTION","READ_ONLY")])
def test_intent_policy(site_db,text,kind,effect):
    msg,_=message(site_db,text,True);policy=evaluate(msg)
    assert policy["intent"]["kind"]==kind and policy["allowedEffect"]==effect
    if "two buildings" in text:assert len(policy["intent"]["assets"])==5


def test_context_budget_unknown_and_no_whole_model(site_db):
    msg,_=message(site_db,"What is the slope?",True)
    context=build_context(site_db,1,msg,evaluate(msg))
    assert context["site"]["relief"]["minElevation"]["sourceKind"]=="UNKNOWN"
    assert context["capturedSelection"][0]["objectId"]=="pier-a"
    with pytest.raises(HTTPException):build_context(site_db,1,msg,evaluate(msg),budget=100)


@pytest.mark.parametrize("name,args",[("delete_model",{}),("get_site_profile",{"projectId":2}),("sample_terrain",{"sampleCount":26}),
    ("query_nearby_context",{"radiusM":501}),("get_site_profile",{"url":"https://evil.test"})])
def test_denied_tools(site_db,name,args):
    msg,rid=message(site_db);tc=ToolContext(1,1,rid,msg["id"],"READ_ONLY")
    assert execute(site_db,tc,name,args)["status"]=="DENIED"


def test_tools_unknown_and_readonly(site_db):
    msg,rid=message(site_db);tc=ToolContext(1,1,rid,msg["id"],"READ_ONLY")
    result=execute(site_db,tc,"sample_terrain",{})
    assert result["status"]=="PARTIAL" and result["data"][0]["elevation"]["value"] is None
    assert execute(site_db,tc,"create_proposal",{"title":"X","rationale":"X","assets":[{"assetType":"DAM","name":"Dam"}]})["status"]=="DENIED"


class FixtureProvider:
    def __init__(self,replies):self.replies=iter(replies)
    async def __call__(self,system,payload):
        reply=next(self.replies)
        if isinstance(reply,Exception):raise reply
        return reply


def test_provider_reply_and_frozen_retry(site_db):
    msg,rid=message(site_db,"What is the slope?",True)
    queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([AssistantProviderError("TIMEOUT")])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="TIMEOUT"
    retry,created=retry_run(site_db,1,1,rid,"again");assert created
    assert retry_run(site_db,1,1,rid,"again")== (retry,False)
    assert owned_row(site_db,"assistant_runs",1,retry)["context_snapshot"]["context"]==msg["context"]
    intent=evaluate(msg)["intent"]
    asyncio.run(process(site_db,1,retry,FixtureProvider([intent,{"text":"Elevation is unknown; upload a survey."}])))
    assert owned_row(site_db,"assistant_runs",1,retry)["status"]=="COMPLETE"
    assert len(rows(site_db,"conversation_messages",1))==2


def test_schema_repair_and_tool_loop_limit(site_db):
    msg,rid=message(site_db,"What objects are selected?",True);queue_run(site_db,1,1,rid)
    intent=evaluate(msg)["intent"]
    tool={"toolCalls":[{"name":"get_selected_objects","arguments":"{}"}]}
    asyncio.run(process(site_db,1,rid,FixtureProvider([{"invalid":True},intent,*([tool]*9)])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="TOOL_LIMIT"
    assert len(rows(site_db,"assistant_tool_executions",1))==1


@pytest.mark.parametrize("code",["MISSING_KEY","MISSING_MODEL","UNREACHABLE","TIMEOUT","RATE_LIMITED","PROVIDER_ERROR"])
def test_provider_failure_preserves_user(site_db,code):
    msg,rid=message(site_db);queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([AssistantProviderError(code)])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]==code
    assert [m["role"] for m in rows(site_db,"conversation_messages",1)]==["USER"]


@pytest.mark.parametrize("reply",[{"invalid":True},{"text":"x","toolCalls":[{"name":"delete_model","arguments":"{}"}]}])
def test_invalid_provider_output_fails_closed(site_db,reply):
    msg,rid=message(site_db);queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],reply,reply])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="INVALID_RESPONSE"
    assert len(rows(site_db,"model_revisions",1))==1


def test_proposal_via_controlled_tool_and_response(site_db):
    import json
    msg,rid=message(site_db);queue_run(site_db,1,1,rid)
    call={"name":"create_proposal","arguments":json.dumps({"title":"Bridge concept","rationale":"Concept discussion only","assets":[{"assetType":"BRIDGE","name":"Bridge A"}]})}
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"toolCalls":[call]},{"text":"Review this concept proposal."}])))
    assert owned_row(site_db,"assistant_runs",1,rid)["status"]=="COMPLETE"
    reply=rows(site_db,"conversation_messages",1)[-1]
    assert any(p["kind"]=="PROPOSAL" for p in reply["parts"])
    assert not rows(site_db,"proposal_approvals",1) and len(rows(site_db,"model_revisions",1))==1


def test_illegal_transition_and_blocker(site_db):
    msg,_=message(site_db)
    c={**msg["context"],"editorDirty":True}
    # Make a separately submitted dirty message rather than modifying immutable context.
    service=ConversationService()
    result=service.submit(site_db,1,1,msg["conversation_id"],MessageInput(client_request_id="dirty",parts=msg["parts"],context={
        "siteProfileVersionId":c["siteProfileVersionId"],"siteSelectionVersionId":c["siteSelectionVersionId"],"modelRevisionId":"1","editorDirty":True}))
    req=ProposalRequest(client_request_id="dirty-proposal",message_id=result["messageId"],title="Concept",rationale="Review",assets=[{"assetType":"BUILDING","name":"A"}])
    svc=ProposalService();view=svc.create(site_db,1,1,req)
    assert view["status"]=="HAS_ISSUES"
    with pytest.raises(HTTPException):svc.approve(site_db,1,1,approval(view))
    with pytest.raises(HTTPException):svc.transition(site_db,1,view["id"],"BUILT")


def test_cross_project_proposal_and_tool_references(site_db):
    view,_=proposal(site_db)
    with pytest.raises(HTTPException):ProposalService().read(site_db,2,view["id"])
    msg,rid=message(site_db,"What is here?")
    tc=ToolContext(2,2,rid,msg["id"],"PROPOSAL_ONLY")
    with pytest.raises(HTTPException):execute(site_db,tc,"get_site_profile",{})
    with pytest.raises(HTTPException):ProposalService().create(site_db,1,1,ProposalRequest(client_request_id="read-only",message_id=msg["id"],title="Bad",rationale="Bad",assets=[{"assetType":"ROAD","name":"R"}]))


def test_missing_selection_clarifies(site_db):
    msg,_=message(site_db,"Raise these three piers by 0.5 m")
    policy=evaluate(msg)
    assert policy["intent"]["needsClarification"] and policy["allowedEffect"]=="READ_ONLY"


@pytest.mark.parametrize("status,body,expected",[(429,{},"RATE_LIMITED"),(500,{},"UNAVAILABLE"),(200,{"choices":[]},"INVALID_RESPONSE"),
    (200,{"choices":[{"message":{"content":"not json"}}]},"INVALID_RESPONSE")])
def test_transport_errors(monkeypatch,status,body,expected):
    import httpx
    from app.core.config import settings
    from app.services.ai.nebius import assistant_json
    monkeypatch.setattr(settings,"NEBIUS_API_KEY","fixture-credential")
    monkeypatch.setattr(settings,"NEBIUS_CHAT_MODEL","fixture-model")
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:original(transport=httpx.MockTransport(lambda request:httpx.Response(status,json=body)),**kwargs))
    with pytest.raises(AssistantProviderError) as e:asyncio.run(assistant_json("fixture",{}))
    assert e.value.code==expected


@pytest.mark.parametrize("field,expected",[("NEBIUS_API_KEY","MISSING_CONFIGURATION"),("NEBIUS_CHAT_MODEL","MISSING_CONFIGURATION")])
def test_missing_configuration(monkeypatch,field,expected):
    from app.core.config import settings
    from app.services.ai.nebius import assistant_json
    monkeypatch.setattr(settings,"NEBIUS_API_KEY","fixture-credential")
    monkeypatch.setattr(settings,"NEBIUS_CHAT_MODEL","fixture-model")
    monkeypatch.setattr(settings,field,"")
    with pytest.raises(AssistantProviderError) as e:asyncio.run(assistant_json("fixture",{}))
    assert e.value.code==expected


def test_application_api_approval_and_foreign_access(site_db,api_client):
    msg,_=message(site_db)
    request={"clientRequestId":"http-proposal","messageId":msg["id"],"title":"Concept","rationale":"Review","assets":[{"assetType":"TUNNEL","name":"Tunnel"}]}
    response=api_client.post("/api/projects/1/proposals",json=request)
    assert response.status_code==200,response.text
    view=response.json()
    assert api_client.get(f"/api/projects/2/proposals/versions/{view['id']}").status_code==404
    body=approval(view).model_dump(mode="json",by_alias=True)
    assert api_client.post("/api/projects/1/proposals/approve",json=body).status_code==200
    assert api_client.post("/api/projects/1/proposals/approve",json=body).status_code==200
    assert api_client.post(f"/api/projects/1/proposals/versions/{view['id']}/build").status_code==409


def test_atomic_queue_blocks_second_active_run(site_db):
    convo=ConversationService().create(site_db,1,1,ConversationInput(client_request_id="atomic"))
    req=MessageInput(client_request_id="one",parts=[{"kind":"TEXT","text":"Hello"}],context={})
    first=ConversationService().submit(site_db,1,1,convo["id"],req,orchestrate=True)
    assert first["status"]=="QUEUED"
    assert ConversationService().submit(site_db,1,1,convo["id"],req,orchestrate=True)==first
    with pytest.raises(HTTPException) as exc:
        ConversationService().submit(site_db,1,1,convo["id"],req.model_copy(update={"client_request_id":"two"}),orchestrate=True)
    assert exc.value.detail["code"]=="RUN_ACTIVE"


def test_generation_commit_gate_does_not_overwrite_manual_work(site_db):
    view,_=proposal(site_db);svc=ProposalService();svc.approve(site_db,1,1,approval(view))
    assert svc.assert_build_current(site_db,1,view["id"],"1")
    site_db.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json={"components":[{"id":"manual-work"}]}));site_db.commit()
    with pytest.raises(HTTPException):svc.assert_build_current(site_db,1,view["id"],"1")
    assert site_db.get(ModelRevision,2).document_json["components"][0]["id"]=="manual-work"


def test_accepted_memory_priority_and_staleness(site_db):
    from app.services.assistant.memory import MemoryService
    from app.domain.site_workspace import MemoryInput
    memory=MemoryService()
    item=memory.create(site_db,1,1,MemoryInput(client_request_id="hard",content={"kind":"REQUIREMENT","key":"width","constraint":{"operator":"EQ","value":7,"unit":"m"},"hardness":"HARD"}))
    memory.transition(site_db,1,1,item["id"],1,"accept","PROPOSED")
    msg,_=message(site_db)
    data=build_context(site_db,1,msg,evaluate(msg))
    assert data["acceptedMemory"][0]["content"]["content"]["constraint"]["value"]==7
    view=ProposalService().create(site_db,1,1,ProposalRequest(client_request_id="memory-proposal",message_id=msg["id"],title="Concept",rationale="Seven metres",assets=[{"assetType":"ROAD","name":"Road"}]))
    new=memory.create(site_db,1,1,MemoryInput(client_request_id="hard-2",content={"kind":"PREFERENCE","key":"material","value":"Concrete","priority":"NORMAL"}))
    memory.transition(site_db,1,1,new["id"],1,"accept","PROPOSED")
    assert ProposalService().read(site_db,1,view["id"])["status"]=="STALE"

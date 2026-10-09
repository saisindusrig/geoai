"""Core product behavior through the real policy, context and persisted runtime, without network."""
import asyncio
import json
import pytest
from fastapi import HTTPException
from app.services.assistant.policy import evaluate
from app.services.assistant.runtime import process, queue_run
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import owned_row, rows
from app.domain.assistant_runtime import ProposalRequest
from test_assistant_runtime import message, FixtureProvider
from test_site_workspace import site_db

SCENARIOS=[
    ("A","I want a flyover here.","DESIGN_REQUEST",["BRIDGE"],False),
    ("B","Create two warehouses with parking, road, drainage and water tank.","DESIGN_REQUEST",["BUILDING","BUILDING","SITE","ROAD","DRAINAGE","WATER"],False),
    ("C","Move these piers 500 mm east.","CHANGE_REQUEST",None,True),
    ("D","Why is my site not engineering ready?","EXPLANATION_REQUEST",None,False),
    ("E","Put a road through here and avoid steep terrain.","DESIGN_REQUEST",["ROAD"],False),
    ("F","Can this bridge safely handle this span?","ANALYSIS_REQUEST",["BRIDGE"],False),
    ("G","Create an elevated bicycle warehouse connected to a pedestrian bridge.","DESIGN_REQUEST",["BUILDING","BRIDGE"],False),
    ("H","Move the retaining wall.","CHANGE_REQUEST",["RETAINING"],False),
    ("I","Add drainage.","DESIGN_REQUEST",["DRAINAGE"],False),
    ("J","What objects are selected?","QUESTION",None,True),
]


@pytest.mark.parametrize("label,text,kind,families,selected",SCENARIOS,ids=[s[0] for s in SCENARIOS])
def test_product_scenarios(site_db,label,text,kind,families,selected):
    if label=="C":
        from app.db.models import ModelRevision
        model=site_db.get(ModelRevision,1)
        model.document_json={**model.document_json,"components":[{"id":oid,"name":"Pier","geometry":{}} for oid in ("P03","P04","P05")]}
        site_db.commit()
        # Submit exact persisted selections, never forge references.
        from app.domain.site_workspace import ConversationInput,MessageInput
        from app.services.assistant.conversations import ConversationService
        from test_site_workspace import profile
        version=profile(site_db)[3]["version"];svc=ConversationService()
        convo=svc.create(site_db,1,1,ConversationInput(client_request_id="core"))
        result=svc.submit(site_db,1,1,convo["id"],MessageInput(client_request_id="edit",parts=[{"kind":"TEXT","text":text}],
            context={"modelRevisionId":"1","selectedObjectIds":["P03","P04","P05"],"siteProfileVersionId":version["id"],"siteSelectionVersionId":version["selectionVersion"]["id"]}))
        msg=owned_row(site_db,"conversation_messages",1,result["messageId"]);rid=result["runId"]
    else:msg,rid=message(site_db,text,selected)
    policy=evaluate(msg);u=policy["understanding"]
    assert policy["intent"]["kind"]==kind
    if families:assert [a["assetFamily"] for a in u["assets"]]==families
    assert all(value=="UNKNOWN" for value in u["unknowns"].values()) and not u["assumptions"]
    assert all(c["engineeringAnalysisSupport"]=="UNSUPPORTED" for c in policy["capabilities"])
    assert all(c["generationSupport"]==("FULL" if c["assetType"].upper() in {"BUILDING","WAREHOUSE","OFFICE_BUILDING"} else "UNSUPPORTED") for c in policy["capabilities"])
    if label in {"B","G"}:assert u["relationships"]
    if label=="C":
        assert u["proposedTranslation"]["objectIds"]==["P03","P04","P05"]
        assert u["proposedTranslation"]["deltaM"]==[.5,0,0]
        assert u["sourceModelRevisionId"]=="1"
        assert u["requiredTools"][:2]==["get_selected_objects","get_model_revision"]
    if label=="D":assert "get_site_readiness" in u["requiredTools"]
    if label=="E":assert "get_active_terrain" in u["requiredTools"]
    if label=="H":assert policy["intent"]["needsClarification"] and policy["allowedEffect"]=="READ_ONLY"
    if label=="J":assert u["requiredTools"]==["get_selected_objects"]
    queue_run(site_db,1,1,rid)
    replies=[policy["intent"],{"text":"A preliminary concept can be reviewed; engineering data remain unknown."}]
    asyncio.run(process(site_db,1,rid,FixtureProvider(replies)))
    assert owned_row(site_db,"assistant_runs",1,rid)["status"]=="COMPLETE"
    assert len(rows(site_db,"model_revisions",1))==1 and not rows(site_db,"proposal_approvals",1)
    reply=rows(site_db,"conversation_messages",1)[-1]
    if kind=="DESIGN_REQUEST" or label=="C":
        vid=next(p["proposalVersionId"] for p in reply["parts"] if p["kind"]=="PROPOSAL")
        plan=ProposalService().read(site_db,1,vid)["content"]["planning"]
        assert plan["relationships"]==u["relationships"] and plan["approvalRequired"]
        assert plan["siteProfileVersionId"]==msg["context"]["siteProfileVersionId"]
    if label=="F":assert "cannot determine safe or unsafe" in reply["parts"][0]["text"]
    if label=="H":assert reply["parts"][0]["kind"]=="QUESTION"


def test_generic_readiness_needs_no_tools(site_db):
    msg,_=message(site_db,"What is site readiness?")
    assert evaluate(msg)["understanding"]["requiredTools"]==[]


def test_nonblocking_model_clarification_does_not_block_plan(site_db):
    msg,_=message(site_db,"I want a pedestrian bridge here.")
    from app.domain.stage1 import CivilIntent
    intent=CivilIntent.model_validate(evaluate(msg)["intent"]).model_copy(update={"needs_clarification":True,"clarification_question":"What material?"})
    assert not evaluate(msg,intent)["intent"]["needsClarification"]


@pytest.mark.parametrize("translation",[
    {"objectIds":["pier-a"],"deltaM":[500,0,0]},
    {"objectIds":["pier-a"],"deltaM":[0,.5,0]},None])
def test_edit_translation_must_match_request(site_db,translation):
    msg,_=message(site_db,"Move these piers 500 mm east.",True)
    request=ProposalRequest(client_request_id="bad",message_id=msg["id"],title="Move piers",rationale="Requested edit",
        assets=[{"assetType":"BRIDGE","name":"Piers"}],translation=translation)
    with pytest.raises(HTTPException) as exc:ProposalService().create(site_db,1,1,request)
    assert exc.value.detail["code"]=="TRANSLATION_MISMATCH"


def test_operation_cache_and_relevant_tool_advertising(site_db):
    msg,rid=message(site_db,"What objects are selected?",True);queue_run(site_db,1,1,rid)
    from app.services.ai.provider import FixtureProvider as Adapter
    payloads=[]
    replies=iter([evaluate(msg)["intent"],{"toolCalls":[{"name":"get_selected_objects","arguments":"{}"}]},
                  {"toolCalls":[{"name":"get_selected_objects","arguments":"{}"}]},{"text":"One pier is selected."}])
    async def callback(system,payload):payloads.append(payload);return next(replies)
    asyncio.run(process(site_db,1,rid,Adapter(callback)))
    assert owned_row(site_db,"assistant_runs",1,rid)["status"]=="COMPLETE"
    assert len(rows(site_db,"assistant_tool_executions",1))==1
    assert [t["name"] for t in payloads[-1]["tools"]]==["get_selected_objects"]


def test_no_site_still_explains_concept_without_invention(site_db):
    from app.domain.site_workspace import ConversationInput,MessageInput
    from app.services.assistant.conversations import ConversationService
    svc=ConversationService();convo=svc.create(site_db,1,1,ConversationInput(client_request_id="no-site"))
    result=svc.submit(site_db,1,1,convo["id"],MessageInput(client_request_id="drain",parts=[{"kind":"TEXT","text":"Add drainage."}],context={}))
    msg=owned_row(site_db,"conversation_messages",1,result["messageId"]);queue_run(site_db,1,1,result["runId"])
    asyncio.run(process(site_db,1,result["runId"],FixtureProvider([evaluate(msg)["intent"],{"text":"Concept"}])))
    reply=rows(site_db,"conversation_messages",1)[-1]
    assert "remain unknown" in reply["parts"][0]["text"] and not rows(site_db,"design_proposal_versions",1)


def test_unrelated_tool_denied(site_db):
    msg,rid=message(site_db,"What objects are selected?",True);queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"toolCalls":[{"name":"sample_terrain","arguments":"{}"}]}])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="TOOL_POLICY_DENIED"
    assert not rows(site_db,"assistant_tool_executions",1)


def test_model_cannot_claim_direct_mutation(site_db):
    msg,rid=message(site_db,"What objects are selected?",True);queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"text":"I have moved the piers."}])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="UNAUTHORIZED_MUTATION_CLAIM"
    assert len(rows(site_db,"model_revisions",1))==1


def test_model_cannot_drop_requested_assets(site_db):
    msg,rid=message(site_db,SCENARIOS[1][1]);queue_run(site_db,1,1,rid)
    args={"title":"Warehouse", "rationale":"Site", "assets":[{"assetType":"WAREHOUSE","name":"One warehouse"}]}
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"toolCalls":[{"name":"create_proposal","arguments":json.dumps(args)}]}])))
    assert owned_row(site_db,"assistant_runs",1,rid)["error_code"]=="ASSET_DECOMPOSITION_MISMATCH"
    assert not rows(site_db,"design_proposal_versions",1)


def test_normal_reply_uses_geoai_brand(site_db):
    msg,rid=message(site_db,"Hello");queue_run(site_db,1,1,rid)
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"text":"Qwen/Qwen3.5-397B-A17B on Nebius is ready."}])))
    text=rows(site_db,"conversation_messages",1)[-1]["parts"][0]["text"]
    assert "Qwen" not in text and "Nebius" not in text and "GeoAI" in text

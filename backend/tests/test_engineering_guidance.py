import asyncio
import copy
import pytest
from fastapi import HTTPException
from app.db.models import ModelRevision,EngineeringAnalysis
from app.domain.site_workspace import MessageInput,ConversationInput
from app.services.assistant.conversations import ConversationService
from app.services.assistant.engineering_guidance import saved_context,answer,MODELS
from app.services.assistant.runtime import process
from app.services.assistant.storage import rows,digest
from app.services.design.opensees_benchmark import digest as model_digest
from test_site_workspace import site_db


def prepare(db):
    rev=db.get(ModelRevision,1)
    rev.document_json={"components":[{"id":"beam","name":"Beam A","category":"beam","geometry":{"kind":"box","size":[6,.2,.3]},"transform":{"position":[0,0,3],"rotation_deg":[0,0,0],"scale":[1,1,1]},"material":{"name":"Appearance only"}}]}
    db.add(EngineeringAnalysis(id=1,project_id=1,model_revision_id=1,analysis_type="OPENSEES_PHYSICAL_FRAME",algorithm_version="test",status="VERIFIED",actor_user_id=1,result_json={"model_document_sha256":model_digest(rev.document_json),"solver_version":"3.8.0","engineering_approval":"DISABLED","elements":[{"component_id":"beam","samples":[{"moment_nm":-28000,"axial_n":-1000,"shear_n":30000},{"moment_nm":22000,"axial_n":-1000,"shear_n":-30000}]}],"applied_loads":{"source":"Explicit synthetic load","nodal_loads_si":{"2":[0,-1000,0]}}}))
    db.commit()


def test_real_saved_units_and_no_mutation(site_db):
    prepare(site_db);before=copy.deepcopy(site_db.get(ModelRevision,1).document_json)
    context=saved_context(site_db,1,1,["beam"])
    text,actions=answer("Show beam bending moment",context)
    assert "-28.000000" in text and "22.000000 kN·m" in text and "3.8.0" in text
    assert "moment" in actions and context["selected"][0]["geometry"]["size"]==[6,.2,.3]
    assert site_db.get(ModelRevision,1).document_json==before
    text,_=answer("What loads have been applied?",context)
    assert "[kN, kN, kN·m]" in text and "Explicit synthetic load" in text


def test_stale_results_never_explained_as_current(site_db):
    prepare(site_db)
    context=saved_context(site_db,1,1,["beam"],True)
    text,_=answer("bending moment",context)
    assert "STALE" in text and "-28.000000" not in text
    site_db.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json=copy.deepcopy(site_db.get(ModelRevision,1).document_json)));site_db.commit()
    assert saved_context(site_db,1,1,["beam"])["stale"]


def test_scope_and_unsaved_selection_are_rejected(site_db):
    prepare(site_db)
    with pytest.raises(HTTPException):saved_context(site_db,2,1,["beam"])
    with pytest.raises(HTTPException):saved_context(site_db,1,1,["invented"])


def test_reconnection_does_not_route_a_cad_question_to_connection_inputs(site_db):
    prepare(site_db)
    text,actions=answer("Explain the CAD source after reconnection.",saved_context(site_db,1,1,[]))
    assert "CAD-generated components" in text
    assert "drawing" in actions


def test_missing_assessment_and_unsupported_request(site_db):
    prepare(site_db)
    site_db.add(EngineeringAnalysis(id=2,project_id=1,model_revision_id=1,analysis_type="REAL_CONNECTION_INPUT",algorithm_version="test",status="BLOCKED_MISSING_ENGINEERING_INPUTS",actor_user_id=1,result_json={"assessment":{"missing":[{"path":"anchors.A.material","reason":"Declare provenance"}]}}));site_db.commit()
    context=saved_context(site_db,1,1,["beam"])
    assert context["missing"][0]["group"]=="Material properties"
    assert "Declare provenance" in answer("why blocked",context)[0]
    assert "cannot execute scripts" in answer("execute Python script and approve safe design",context)[0]


@pytest.mark.parametrize("count",[233,1001])
def test_large_missing_assessment_is_complete_or_explicitly_bounded(site_db,count):
    prepare(site_db)
    missing=[{"path":f"anchors.{i}.material","reason":"Declare provenance"} for i in range(count)]
    site_db.add(EngineeringAnalysis(id=2,project_id=1,model_revision_id=1,analysis_type="REAL_CONNECTION_INPUT",algorithm_version="test",status="BLOCKED_MISSING_ENGINEERING_INPUTS",actor_user_id=1,result_json={"assessment":{"missing":missing}}));site_db.commit()
    context=saved_context(site_db,1,1,["beam"])
    assert context["missingTotal"]==count
    assert len(context["missing"])==min(count,1000)
    text,_=answer("why blocked",context)
    assert ("complete saved list" in text)==(count<=1000)
    if count>1000:assert "1000 of 1001" in text


def test_offline_history_idempotency_and_no_provider(site_db):
    prepare(site_db);svc=ConversationService()
    conversation=svc.create(site_db,1,1,ConversationInput(client_request_id="offline"))
    request=MessageInput(client_request_id="question",parts=[{"kind":"TEXT","text":"Explain this beam"}],context={"modelRevisionId":"1","selectedObjectIds":["beam"]},assistant_mode="ENGINEERING_OFFLINE",requested_model=MODELS[0])
    run=svc.submit(site_db,1,1,conversation["id"],request,orchestrate=True)
    class ForbiddenProvider:
        async def complete(self,*args):raise AssertionError("Paid provider must not be called")
    asyncio.run(process(site_db,1,run["runId"],ForbiddenProvider()))
    reply=svc.messages(site_db,1,conversation["id"])["messages"][-1]
    assert reply["engineering"]["actualModel"] is None and reply["engineering"]["requestedModel"]==MODELS[0]
    assert "Beam A" in reply["parts"][0]["text"]
    assert svc.submit(site_db,1,1,conversation["id"],request,orchestrate=True)["status"]=="COMPLETE"
    assert len(rows(site_db,"conversation_messages",1))==2
    assert len(rows(site_db,"engineering_analyses",1))==1
    with pytest.raises(Exception):MessageInput(client_request_id="bad",parts=[{"kind":"TEXT","text":"Hello"}],context={},requested_model="invented")

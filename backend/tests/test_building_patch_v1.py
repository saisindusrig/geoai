from copy import deepcopy
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.domain.building_patch import BuildingPatch
from app.domain.assistant_runtime import ProposalRequest, ApplicationApproval
from app.domain.site_workspace import ConversationInput, MessageInput
from app.services.assistant.building_patch import BuildingPatchValidator
from app.services.assistant.conversations import ConversationService
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import rows, digest
from app.db.models import ModelRevision
from test_building_specialist_v1 import create
from test_assistant_runtime import approval
from test_site_workspace import site_db, profile

def generated(db):
    service=ProposalService();view=create(db)
    service.approve(db,1,1,approval(view))
    revision=db.get(ModelRevision,int(service.build(db,1,view["id"])["modelRevisionId"]))
    return revision

def patch_for(db, revision, target, parameters):
    component=next(c for c in revision.document_json["components"] if c["id"]==target)
    lineage=next(r for r in rows(db,"model_object_lineage",1) if r["model_revision_id"]==revision.id and r["object_id"]==target)
    spec=next(r for r in rows(db,"asset_specification_versions",1) if r["id"]==lineage["specification_version_id"])
    return BuildingPatch(building_id="office-01",asset_id=lineage["asset_id"],source_model_revision_id=str(revision.id),
        source_specification_version_id=spec["id"],source_specification_hash=spec["content_hash"],operations=[{
            "operationId":"edit-1","targetComponentId":target,"expectedComponentHash":digest(component),"parameters":parameters}])

def propose(db, revision, patch, text="Change this building component as specified."):
    data=profile(db)[3]["version"]
    conversations=ConversationService()
    conversation=conversations.create(db,1,1,ConversationInput(client_request_id="patch"))
    msg=conversations.submit(db,1,1,conversation["id"],MessageInput(client_request_id="patch",parts=[{"kind":"TEXT","text":text}],
        context={"siteProfileVersionId":data["id"],"siteSelectionVersionId":data["selectionVersion"]["id"],"scenarioId":"1",
                 "modelRevisionId":str(revision.id),"selectedObjectIds":[patch.operations[0].target_component_id]}))
    return ProposalService().create(db,1,1,ProposalRequest(client_request_id="patch",message_id=msg["messageId"],title="Building edit",
        rationale="Selected-component conceptual change",assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingPatch":patch}]))

@pytest.mark.parametrize("target,parameters",[
    ("office-01:c0-0",{"operationType":"MOVE_COMPONENT","delta":[500,0,0],"unit":"mm"}),
    ("office-01:c0-0",{"operationType":"ROTATE_COMPONENT","angleDeg":30}),
    ("office-01:window",{"operationType":"RESIZE_OPENING","width":1.5}),
    ("office-01:entry",{"operationType":"MOVE_OPENING","offsetM":3}),
    ("office-01:w0-1-end",{"operationType":"ADD_OPENING","openingId":"new-window","kind":"window","offsetM":2,"width":1.5,"height":1,"sillM":1}),
    ("office-01:window",{"operationType":"REMOVE_OPENING"}),
])
def test_approved_atomic_patch_revision(site_db,monkeypatch,target,parameters):
    revision=generated(site_db);original=deepcopy(revision.document_json)
    patch=patch_for(site_db,revision,target,parameters)
    validator=BuildingPatchValidator()
    assert validator.preview(site_db,1,patch)["document"]==validator.preview(site_db,1,patch)["document"]
    view=propose(site_db,revision,patch,"Move this column 500 mm east." if parameters["operationType"]=="MOVE_COMPONENT" else "Change this building component as specified.")
    service=ProposalService()
    with pytest.raises(HTTPException):service.build(site_db,1,view["id"])
    command=approval(view).model_copy(update={"expected_model_revision_id":str(revision.id)})
    service.approve(site_db,1,1,command)
    monkeypatch.setattr("app.api.routes.model_revisions.save_file",lambda *args:"/test/patch.glb")
    result=service.build(site_db,1,view["id"])
    assert service.build(site_db,1,view["id"])==result
    saved=site_db.get(ModelRevision,int(result["modelRevisionId"]))
    assert saved.id!=revision.id and site_db.get(ModelRevision,revision.id).document_json==original
    if parameters["operationType"]=="MOVE_COMPONENT":
        component=next(c for c in saved.document_json["components"] if c["id"]==target)
        assert component["transform"]["position"][0]==5.5
    lineage=[r for r in rows(site_db,"model_object_lineage",1) if r["model_revision_id"]==saved.id]
    assert all(r["payload"].get("generationModelRevisionId")==revision.id for r in lineage)
    affected=[r for r in lineage if r["payload"].get("patchProvenance")]
    assert affected and all(r["payload"]["patchProvenance"]["resultingModelRevisionId"]==saved.id for r in affected)

@pytest.mark.parametrize("fault",["stale_hash","missing","oversize","wrong_asset","locked","unsupported_dependency"])
def test_invalid_patch_rejected(site_db,fault):
    revision=generated(site_db)
    patch=patch_for(site_db,revision,"office-01:window",{"operationType":"RESIZE_OPENING","width":1.5})
    raw=patch.model_dump(mode="json",by_alias=True)
    if fault=="stale_hash":raw["operations"][0]["expectedComponentHash"]="0"*64
    if fault=="missing":raw["operations"][0]["targetComponentId"]="missing"
    if fault=="oversize":raw["operations"][0]["parameters"]["width"]=100
    if fault=="wrong_asset":raw["assetId"]="wrong"
    patch=BuildingPatch.model_validate(raw)
    if fault=="locked":
        doc=deepcopy(revision.document_json);next(c for c in doc["components"] if c["id"]=="office-01:window")["locked"]=True
        revision.document_json=doc;site_db.commit()
    if fault=="unsupported_dependency":patch=patch_for(site_db,revision,"office-01:w0-1-end",{"operationType":"MOVE_COMPONENT","delta":[.5,0,0]})
    with pytest.raises(HTTPException):BuildingPatchValidator().preview(site_db,1,patch)

def test_unsupported_sizing_schema():
    with pytest.raises(ValidationError):BuildingPatch.model_validate({"operations":[{"parameters":{"operationType":"STRUCTURAL_SIZING"}}]})

def test_stale_revision_rejected(site_db):
    revision=generated(site_db)
    patch=patch_for(site_db,revision,"office-01:c0-0",{"operationType":"MOVE_COMPONENT","delta":[.5,0,0]})
    site_db.add(ModelRevision(project_id=1,design_scenario_id=1,revision_number=revision.revision_number+1,document_json=deepcopy(revision.document_json)))
    site_db.commit()
    with pytest.raises(HTTPException) as exc:BuildingPatchValidator().preview(site_db,1,patch)
    assert exc.value.detail["code"]=="STALE_PATCH"

def test_execution_failure_rolls_back_revision(site_db,monkeypatch):
    revision=generated(site_db);original=deepcopy(revision.document_json)
    patch=patch_for(site_db,revision,"office-01:c0-0",{"operationType":"MOVE_COMPONENT","delta":[.5,0,0]})
    view=propose(site_db,revision,patch)
    service=ProposalService();service.approve(site_db,1,1,approval(view).model_copy(update={"expected_model_revision_id":str(revision.id)}))
    def fail(*args):raise RuntimeError("Storage unavailable")
    monkeypatch.setattr("app.api.routes.model_revisions.save_file",fail)
    with pytest.raises(RuntimeError):service.build(site_db,1,view["id"])
    assert site_db.query(ModelRevision).count()==2
    assert site_db.get(ModelRevision,revision.id).document_json==original
    assert service.read(site_db,1,view["id"])["status"]=="APPROVED"

@pytest.mark.parametrize("text,count,question",[
    ("Move this wall.",2,"Select the one component"),
    ("Make this window wider.",1,"What width"),
])
def test_blocking_patch_clarification(text,count,question):
    from app.services.assistant.policy import evaluate
    message={"parts":[{"kind":"TEXT","text":text}],"context":{"selection":[{"objectId":f"wall-{i}","assetId":"building"} for i in range(count)]}}
    result=evaluate(message)
    assert result["allowedEffect"]=="READ_ONLY"
    assert question in result["intent"]["clarificationQuestion"]

def test_explicit_patch_capabilities():
    from app.services.assistant.foundation import capability
    actual=capability("OFFICE_BUILDING")
    assert "BUILDING_PATCH_OPENING" in actual.patch_capabilities
    assert "BUILDING_PATCH_INTERNAL_WALL" not in actual.patch_capabilities
    assert capability("ROAD").patch_capabilities==[]

def test_assistant_patch_tool_boundary(site_db):
    import asyncio,json
    from app.services.assistant.runtime import process,queue_run
    from app.services.assistant.policy import evaluate
    from app.services.assistant.storage import owned_row
    from test_assistant_runtime import FixtureProvider
    revision=generated(site_db)
    patch=patch_for(site_db,revision,"office-01:c0-0",{"operationType":"MOVE_COMPONENT","delta":[500,0,0],"unit":"mm"})
    # Create a message/proposal first to retain deterministic frozen context, then
    # evaluate another tool request under that same approved proposal-only policy.
    view=propose(site_db,revision,patch,"Move this column 500 mm east.")
    message=next(r for r in rows(site_db,"conversation_messages",1) if r["parts"]==[{"kind":"TEXT","text":"Move this column 500 mm east."}])
    run=next(r for r in rows(site_db,"assistant_runs",1) if r["message_id"]==message["id"])
    queue_run(site_db,1,1,run["id"])
    args={"title":"Move selected column","rationale":"Exactly 500 mm east","assets":[{"assetType":"OFFICE_BUILDING","name":"Office","buildingPatch":patch.model_dump(mode="json",by_alias=True)}]}
    asyncio.run(process(site_db,1,run["id"],FixtureProvider([evaluate(message)["intent"],
        {"toolCalls":[{"name":"get_selected_objects","arguments":"{}"},{"name":"get_model_revision","arguments":"{}"}]},
        {"toolCalls":[{"name":"create_proposal","arguments":json.dumps(args)}]}, {"text":"Review the proposed column move."}])))
    assert owned_row(site_db,"assistant_runs",1,run["id"])["status"]=="COMPLETE"
    assert site_db.query(ModelRevision).count()==2

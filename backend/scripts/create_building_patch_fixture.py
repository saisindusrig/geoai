"""Fresh generated project plus a deterministic Assistant patch proposal; no live AI."""
import asyncio, json
import create_building_workspace_fixture as fixture
from app.db.session import SessionLocal
from app.db.models import ModelRevision, Project
from app.services.assistant.storage import owned_row, rows, digest
from app.services.assistant.runtime import queue_run, process
from app.services.assistant.policy import evaluate
from app.services.assistant.conversations import ConversationService
from app.services.site_profiles.service import SiteProfileService
from app.domain.site_workspace import ConversationInput, MessageInput
from app.domain.building_patch import BuildingPatch
from test_assistant_runtime import FixtureProvider

with SessionLocal() as db:
    project=db.query(Project).filter_by(name="Building V1 workspace acceptance").order_by(Project.id.desc()).first()
    revision=db.query(ModelRevision).filter_by(project_id=project.id).order_by(ModelRevision.id.desc()).first()
    pid=project.id;uid=project.user_id
    lineage=next(r for r in rows(db,"model_object_lineage",pid) if r["model_revision_id"]==revision.id and r["object_id"]=="office-01:c0-0")
    spec=owned_row(db,"asset_specification_versions",pid,lineage["specification_version_id"])
    target=next(c for c in revision.document_json["components"] if c["id"]==lineage["object_id"])
    selection=owned_row(db,"site_selection_versions",pid,revision.document_json["metadata"]["placementProvenance"]["elevation_provenance_json"]["selectionVersionId"])
    profiles=SiteProfileService();prepared,_=profiles.prepare(db,pid,uid,selection["id"])
    profiles.build(db,pid,prepared["id"],prepared["jobId"])
    data=profiles.read(db,pid,prepared["id"])["version"]
    conversations=ConversationService();conversation=conversations.list(db,pid)[0]
    result=conversations.submit(db,pid,uid,conversation["id"],MessageInput(client_request_id="move-column",parts=[{"kind":"TEXT","text":"Move this column 500 mm east."}],
        context={"siteProfileVersionId":data["id"],"siteSelectionVersionId":data["selectionVersion"]["id"],"scenarioId":str(revision.design_scenario_id),
            "modelRevisionId":str(revision.id),"selectedObjectIds":[target["id"]]}))
    patch=BuildingPatch(building_id="office-01",asset_id=lineage["asset_id"],source_model_revision_id=str(revision.id),
        source_specification_version_id=spec["id"],source_specification_hash=spec["content_hash"],operations=[{"operationId":"move-column", "targetComponentId":target["id"],
            "expectedComponentHash":digest(target),"parameters":{"operationType":"MOVE_COMPONENT","delta":[500,0,0],"unit":"mm"}}])
    args={"title":"Move selected column 500 mm east","rationale":"Exact selected-column conceptual patch","assets":[{"assetType":"OFFICE_BUILDING","name":"Office","buildingPatch":patch.model_dump(mode="json",by_alias=True)}]}
    queue_run(db,pid,uid,result["runId"])
    message=owned_row(db,"conversation_messages",pid,result["messageId"])
    asyncio.run(process(db,pid,result["runId"],FixtureProvider([evaluate(message)["intent"],
        {"toolCalls":[{"name":"get_selected_objects","arguments":"{}"},{"name":"get_model_revision","arguments":"{}"}]},
        {"toolCalls":[{"name":"create_proposal","arguments":json.dumps(args)}]}, {"text":"Review the proposed 500 mm column movement."}])))
    proposal=next(p["proposalVersionId"] for m in rows(db,"conversation_messages",pid) for p in m["parts"] if p["kind"]=="PROPOSAL")
    print(json.dumps({"projectId":pid,"scenarioId":revision.design_scenario_id,"sourceRevisionId":revision.id,"proposalVersionId":proposal}))

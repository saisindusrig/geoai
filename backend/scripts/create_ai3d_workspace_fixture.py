"""Dedicated Building + generic composition acceptance fixture. No provider calls."""
import asyncio
import json
import create_building_workspace_fixture
from app.db.session import SessionLocal
from app.db.models import Project, ModelRevision
from app.domain.site_workspace import MessageInput
from app.services.assistant.storage import owned_row, rows
from app.services.assistant.conversations import ConversationService
from app.services.assistant.runtime import queue_run, process
from app.services.assistant.policy import evaluate
from app.services.assistant.ai3d_validation import site_summary
from app.services.site_profiles.service import SiteProfileService
from test_assistant_runtime import FixtureProvider
from test_ai3d_v1 import fixture

with SessionLocal() as db:
    project=db.query(Project).filter_by(name="Building V1 workspace acceptance").order_by(Project.id.desc()).first()
    project.name="Generic 3D V1 workspace acceptance";db.commit()
    base=db.query(ModelRevision).filter_by(project_id=project.id).order_by(ModelRevision.id.desc()).first()
    selected=rows(db,"site_selection_versions",project.id)[-1]
    profiles=SiteProfileService();prepared,_=profiles.prepare(db,project.id,project.user_id,selected["id"])
    profiles.build(db,project.id,prepared["id"],prepared["jobId"]);profile=profiles.read(db,project.id,prepared["id"])["version"]
    conversations=ConversationService();convo=conversations.list(db,project.id)[0]
    posted=conversations.submit(db,project.id,project.user_id,convo["id"],MessageInput(client_request_id="generic-mixed",
        parts=[{"kind":"TEXT","text":"Create two warehouses with parking, road, drainage and water tank."}],
        context={"modelRevisionId":str(base.id),"scenarioId":str(base.design_scenario_id),"siteSelectionVersionId":selected["id"],"siteProfileVersionId":profile["id"]}))
    message=owned_row(db,"conversation_messages",project.id,posted["messageId"])
    summary=site_summary(db,project.id,message["context"])
    design=fixture("mixed",summary["selectionReference"],str(base.id))
    arguments={"title":"Mixed generic infrastructure layout","rationale":"Two warehouses, parking, access road, drainage and tank composed by one generic executor.",
        "assets":[{"assetType":"AI3D_DESIGN","name":"Mixed infrastructure","ai3dDesign":design}]}
    queue_run(db,project.id,project.user_id,posted["runId"])
    asyncio.run(process(db,project.id,posted["runId"],FixtureProvider([evaluate(message)["intent"],
        {"toolCalls":[{"name":"get_site_profile","arguments":"{}"}]},
        {"toolCalls":[{"name":"create_proposal","arguments":json.dumps(arguments)}]},
        {"text":"Review the preliminary mixed layout and explicit preview dimensions. Terrain and engineering adequacy remain unvalidated."}])))
    run=owned_row(db,"assistant_runs",project.id,posted["runId"])
    if run["status"]!="COMPLETE":raise RuntimeError(run["error_code"])
    proposal=next(part["proposalVersionId"] for message in rows(db,"conversation_messages",project.id) for part in message["parts"] if part["kind"]=="PROPOSAL")
    print(json.dumps({"projectId":project.id,"sourceRevisionId":base.id,"proposalVersionId":proposal,"scenarioId":base.design_scenario_id}))

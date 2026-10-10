"""Prepare exactly one isolated Phase 4C scenario. Never sends model requests."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/".cad-proof-output"/"4c-controlled-live"
OUT.mkdir(parents=True,exist_ok=True)
DATABASE=OUT/"acceptance.db"
os.environ["DATABASE_URL"]="sqlite:///"+DATABASE.as_posix()
ACTOR=490001
PROJECT=490001
for key in ("GEOAI_EXPERIMENTAL_CAD","GEOAI_EXPERIMENTAL_BIM_AUTHORING"):
    os.environ[key]="true"
for key in ("GEOAI_CAD_TEST_USER_IDS","GEOAI_BIM_AUTHORING_USER_IDS"):
    os.environ[key]=str(ACTOR)
for key in ("GEOAI_CAD_TEST_PROJECT_IDS","GEOAI_BIM_AUTHORING_PROJECT_IDS"):
    os.environ[key]=str(PROJECT)

REQUEST="Design an elevated industrial maintenance platform with columns, primary and secondary steel beams, and a platform slab. Organize the structure into three BIM assemblies. Use explicit metre dimensions, supported sections and materials. Include component identities, placement, dependency relationships, support intent and clearance unknowns. This is a preliminary concept, not a structural engineering design."


def prepare():
    from app.core.config import settings
    settings.LOCAL_STORAGE_DIR=str(OUT/"public")
    from app.services import storage
    storage._s3_configured=lambda:False
    storage._get_s3=lambda:None
    from app.db.session import engine,SessionLocal,get_db
    from app.db.models import Base,User,Project,DesignScenario,ModelRevision,ModelPlacement
    from app.services.design.editable_model import geometry_spec_to_document
    from app.services.site_profiles.selection import save_selection
    from app.services.site_profiles.evidence import WGS84
    from app.services.site_profiles.service import SiteProfileService
    from app.domain.site_workspace import SelectionInput,ConversationInput,MessageInput
    from app.services.assistant.conversations import ConversationService
    from app.services.ai.provider import ModelRouter,RoutingMetadata
    from app.services.ai.nebius_config import resolve
    from app.experimental.cad_contract import digest
    from app.core.security import get_current_user_id
    from app.main import app
    from fastapi.testclient import TestClient
    manifest_path=OUT/"prepared.json"
    if manifest_path.exists():
        print(manifest_path.read_text())
        return
    if DATABASE.exists() and DATABASE.stat().st_size:
        raise RuntimeError("Existing unrecorded acceptance database: inspect before reuse")
    Base.metadata.create_all(engine)
    db=SessionLocal()
    actor=User(id=ACTOR,name="Phase 4C isolated test actor",email="phase4c@isolated.invalid")
    area={"type":"Polygon","coordinates":[[[77,12],[77.001,12],[77.001,12.001],[77,12.001],[77,12]]]}
    project=Project(id=PROJECT,user_id=ACTOR,name="Phase 4C synthetic maintenance platform acceptance",project_type="custom",boundary_geojson=area)
    db.add(actor);db.flush();db.add(project);db.flush()
    scenario=DesignScenario(project_id=PROJECT,name="One conceptual platform scenario")
    db.add(scenario);db.flush()
    document=geometry_spec_to_document(project,scenario,{"objects":[]})
    document["origin"]["elevation_m"]=None
    revision=ModelRevision(project_id=PROJECT,design_scenario_id=scenario.id,revision_number=1,document_json=document)
    db.add(revision);db.flush()
    db.add(ModelPlacement(project_id=PROJECT,model_revision_id=revision.id,anchor_longitude=77,anchor_latitude=12,anchor_elevation=None,local_transform_json={}))
    db.commit()
    selection=save_selection(db,PROJECT,ACTOR,SelectionInput(selection={"kind":"AREA","geometry":area},original_crs=WGS84))
    svc=SiteProfileService()
    profile,_=svc.prepare(db,PROJECT,ACTOR,selection["id"])
    svc.build(db,PROJECT,profile["id"],profile["jobId"])
    saved=svc.read(db,PROJECT,profile["id"])
    convo=ConversationService().create(db,PROJECT,ACTOR,ConversationInput(client_request_id="phase-4c-one-scenario"))
    message=ConversationService().submit(db,PROJECT,ACTOR,convo["id"],MessageInput(client_request_id="phase-4c-request",parts=[{"kind":"TEXT","text":REQUEST}],
        context={"siteProfileVersionId":saved["version"]["id"],"siteSelectionVersionId":selection["id"],"modelRevisionId":str(revision.id),
            "scenarioId":str(scenario.id),"selectedObjectIds":[],"editorDirty":False}),orchestrate=False)
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user_id]=lambda:ACTOR
    try:
        with TestClient(app) as client:
            response=client.post(f"/api/projects/{PROJECT}/experimental-cad/bim-authoring/runs",json={"request_id":"phase-4c-one-live-run","message_id":message["messageId"]})
            if response.status_code != 200:raise RuntimeError(f"Preparation rejected: HTTP {response.status_code}")
            run=response.json()
            assert run["calls"]==0 and run["completedStages"]==[]
    finally:
        app.dependency_overrides.clear()
    route=ModelRouter().route(RoutingMetadata(intent="DESIGN_REQUEST",requested_effect="PROPOSAL_ONLY",complexity="COMPLEX",engineering_sensitive=True))
    config=resolve(model=route.model,timeout=route.timeout)
    manifest=dict(status="PREPARED_AWAITING_EXPLICIT_PAID_AUTHORIZATION",database=str(DATABASE),testActorId=ACTOR,testProjectId=PROJECT,
        scenarioId=scenario.id,revisionId=revision.id,originalDocumentHash=digest(document),siteProfileVersionId=saved["version"]["id"],selectionVersionId=selection["id"],
        conversationId=convo["id"],messageId=message["messageId"],runId=run["runId"],request=REQUEST,model=route.model,tier=route.tier,
        timeoutSeconds=route.timeout,maxOutputTokensPerCall=route.max_output_tokens,normalCalls=6,maxCalls=12,maxGeneratedOutputTokens=42000,
        credentialsConfigured=bool(config.api_key),syntheticSite=True,terrainSoilLoadsSurveyElevation="UNKNOWN",endpointTransport="In-process FastAPI TestClient",
        authenticationScope="Isolated owned test principal injected through standard dependency; no production login/session is used",
        productionCadBuild=False,approvalAllowed=False,nativeBuildAllowed=False,paidRequestsSent=0)
    manifest_path.write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    db.close()


if __name__=="__main__":prepare()

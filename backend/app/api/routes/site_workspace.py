"""Project-authorized Stage 1 site, conversation and memory application commands."""
import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session
from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user_id
from app.db.models import EngineeringAnalysis
from app.db.session import get_db
from app.domain.site_workspace import (SelectionInput, ProfileInput, ConversationInput, MessageInput,
                                      MemoryInput, MemoryRevisionInput, MemoryAction, ProfileView, ReadinessView, ConversationView, MemoryView, MessageView, RunSummary)
from app.services.assistant.storage import owned_row, table, error
from app.services.assistant.conversations import ConversationService
from app.services.assistant.memory import MemoryService
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService, run_profile_job
from app.services.site_profiles.evidence import WGS84
from app.domain.assistant_runtime import ProposalRequest, ApplicationApproval, RetryCommand, ProposalView
from app.services.assistant.proposals import ProposalService
from app.services.assistant.runtime import queue_run, background_run, retry_run, recover

router=APIRouter(prefix="/api/projects/{project_id}",tags=["site-workspace"])
profiles=SiteProfileService()
conversations=ConversationService()
memory=MemoryService()


def scope(project_id:int,db:Session=Depends(get_db),actor:int=Depends(get_current_user_id)):
    get_owned_project(project_id,db,actor)
    return db,actor


from app.domain.composition import RelationshipInput, PatchProposal
from app.services.assistant.composition import project_composition, save_relationship, check_patch


@router.get("/composition")
def get_composition(project_id:int,access=Depends(scope)):
    return project_composition(access[0],project_id)


@router.post("/composition/relationships")
def create_relationship(project_id:int,body:RelationshipInput,access=Depends(scope)):
    return save_relationship(access[0],project_id,body)


@router.post("/composition/patch-preflight")
def patch_preflight(project_id:int,body:PatchProposal,access=Depends(scope)):
    return check_patch(access[0],project_id,body)


@router.post("/site-selections")
def create_selection(project_id:int,body:SelectionInput,access=Depends(scope)):
    db,actor=access
    return save_selection(db,project_id,actor,body)


@router.post("/site-selections/from-project")
def selection_from_project(project_id:int,access=Depends(scope)):
    db,actor=access
    project=get_owned_project(project_id,db,actor)
    if project.boundary_geojson:
        selection={"kind":"AREA","geometry":project.boundary_geojson}
    elif project.alignment_geojson:
        selection={"kind":"ROUTE","geometry":project.alignment_geojson}
    elif project.center_lng is not None and project.center_lat is not None:
        selection={"kind":"POINT","geometry":{"type":"Point","coordinates":[project.center_lng,project.center_lat]}}
    else:
        error(422,"SAVED_SELECTION_REQUIRED","Save a boundary, alignment or project location first.")
    return save_selection(db,project_id,actor,SelectionInput(selection=selection,original_crs=WGS84))


@router.post("/site-selections/{selection_id}/versions")
def revise_selection(project_id:int,selection_id:str,body:SelectionInput,access=Depends(scope)):
    return save_selection(access[0],project_id,access[1],body,selection_id)


@router.get("/site-selections/{selection_id}/versions/{version}")
def get_selection(project_id:int,selection_id:str,version:int,access=Depends(scope)):
    db,_=access
    owned_row(db,"site_selections",project_id,selection_id)
    t=table("site_selection_versions")
    result=db.execute(sa.select(t.c.selection_payload).where(t.c.project_id==project_id,t.c.selection_id==selection_id,t.c.version==version)).scalar()
    if result is None: error(404,"NOT_FOUND","Selection version not found")
    return result


def queue(db,project_id,actor,selection_id,background,profile_id=None):
    result,start=profiles.prepare(db,project_id,actor,selection_id,profile_id)
    if start:
        background.add_task(run_profile_job,db.get_bind(),project_id,result["id"],result["jobId"])
    return result


@router.post("/site-profiles",status_code=202)
def create_profile(project_id:int,body:ProfileInput,background:BackgroundTasks,access=Depends(scope)):
    return queue(access[0],project_id,access[1],body.selection_version_id,background)


@router.get("/site-profiles")
def list_profiles(project_id:int,access=Depends(scope)):
    db,_=access;t=table("site_profiles")
    ids=db.execute(sa.select(t.c.id).where(t.c.project_id==project_id).order_by(t.c.created_at.desc()).limit(50)).scalars()
    return {"profiles":[profiles.read(db,project_id,pid) for pid in ids]}


@router.get("/site-profiles/{profile_id}",response_model=ProfileView)
def get_profile(project_id:int,profile_id:str,version:int|None=Query(None,ge=1),access=Depends(scope)):
    return profiles.read(access[0],project_id,profile_id,version)


@router.post("/site-profiles/{profile_id}/refresh",status_code=202)
def refresh_profile(project_id:int,profile_id:str,background:BackgroundTasks,access=Depends(scope)):
    db,actor=access
    profile=owned_row(db,"site_profiles",project_id,profile_id)
    t=table("site_selection_versions")
    selection_id=db.execute(sa.select(t.c.id).where(t.c.project_id==project_id,t.c.selection_id==profile["selection_id"]).order_by(t.c.version.desc()).limit(1)).scalar_one_or_none()
    return queue(db,project_id,actor,selection_id,background,profile_id)


@router.get("/site-profiles/{profile_id}/readiness",response_model=ReadinessView)
def get_readiness(project_id:int,profile_id:str,operation:str|None=None,access=Depends(scope)):
    db,_=access
    result=profiles.read(db,project_id,profile_id)
    if not result["version"]:
        return {"status":"PENDING","current":False,"siteDataState":"UNCONFIGURED","operations":[]}
    assessment=owned_row(db,"engineering_analyses",project_id,result["version"]["readinessAssessmentId"])["result_json"]
    operations=[{**o,"eligible":o["eligible"] and result["current"],"reasons":o["reasons"]+([] if result["current"] else ["STALE_PROFILE"])} for o in assessment["operations"]]
    if operation:
        if operation not in {o["operation"] for o in operations}:error(422,"INVALID_OPERATION","Unknown readiness operation")
        operations=[o for o in operations if o["operation"]==operation]
    return {**assessment,"current":result["current"],"operations":operations}


@router.get("/site-profiles/{profile_id}/samples")
def get_samples(project_id:int,profile_id:str,version:int|None=None,cursor:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),access=Depends(scope)):
    result=profiles.read(access[0],project_id,profile_id,version)
    if not result["version"]:error(404,"NOT_FOUND","Profile has no sample set yet")
    artifact=owned_row(access[0],"site_sample_sets",project_id,result["version"]["terrain"]["sampleSetId"])
    samples=artifact["payload"]["samples"]
    return {"id":artifact["id"],"samples":samples[cursor:cursor+limit],"nextCursor":cursor+limit if cursor+limit<len(samples) else None,
            "method":artifact["payload"]["method"],"nodataPolicy":artifact["payload"]["nodataPolicy"]}


@router.get("/site-profiles/{profile_id}/missing-information")
def get_missing(project_id:int,profile_id:str,access=Depends(scope)):
    db,_=access;result=profiles.read(db,project_id,profile_id)
    t=table("site_missing_information")
    return {"items":list(db.execute(sa.select(t.c.payload).where(t.c.project_id==project_id,t.c.profile_version_id==result["version"]["id"])).scalars()) if result["version"] else []}


@router.get("/site-evidence/{evidence_id}")
def get_evidence(project_id:int,evidence_id:str,access=Depends(scope)):
    return owned_row(access[0],"site_evidence",project_id,evidence_id)["payload"]


@router.post("/conversations",response_model=ConversationView)
def create_conversation(project_id:int,body:ConversationInput,access=Depends(scope)):
    return conversations.create(access[0],project_id,access[1],body)


@router.get("/conversations")
def list_conversations(project_id:int,access=Depends(scope)):
    return {"conversations":conversations.list(access[0],project_id)}


@router.get("/conversations/{conversation_id}/messages")
def list_messages(project_id:int,conversation_id:str,before:int|None=Query(None,ge=1),limit:int=Query(50,ge=1,le=100),access=Depends(scope)):
    return conversations.messages(access[0],project_id,conversation_id,before,limit)


@router.post("/conversations/{conversation_id}/messages",status_code=202)
def send_message(project_id:int,conversation_id:str,body:MessageInput,background:BackgroundTasks,access=Depends(scope)):
    db,actor=access
    from app.services.assistant.storage import rows
    for run in rows(db,"assistant_runs",project_id):
        if run["conversation_id"]==conversation_id:recover(db,project_id,run)
    result=conversations.submit(db,project_id,actor,conversation_id,body,orchestrate=True)
    if result["status"]=="QUEUED":
        background.add_task(background_run,db.get_bind(),project_id,result["runId"])
    return result


@router.get("/assistant/runs/{run_id}",response_model=RunSummary)
def read_run(project_id:int,run_id:str,access=Depends(scope)):
    recover(access[0],project_id,owned_row(access[0],"assistant_runs",project_id,run_id))
    return conversations.run_output(owned_row(access[0],"assistant_runs",project_id,run_id))


@router.get("/assistant/runs/{run_id}/events")
def run_events(project_id:int,run_id:str,access=Depends(scope)):
    owned_row(access[0],"assistant_runs",project_id,run_id)
    t=table("assistant_run_events")
    return {"events":list(access[0].execute(sa.select(t.c.payload).where(t.c.project_id==project_id,t.c.run_id==run_id).order_by(t.c.sequence)).scalars())}


@router.post("/assistant/runs/{run_id}/retry",status_code=202)
def retry_assistant(project_id:int,run_id:str,body:RetryCommand,background:BackgroundTasks,access=Depends(scope)):
    db,actor=access
    rid,created=retry_run(db,project_id,actor,run_id,body.client_request_id)
    if created:background.add_task(background_run,db.get_bind(),project_id,rid)
    return conversations.run_output(owned_row(db,"assistant_runs",project_id,rid))


@router.post("/proposals",response_model=ProposalView)
def create_proposal(project_id:int,body:ProposalRequest,access=Depends(scope)):
    from app.services.assistant.policy import evaluate
    message=owned_row(access[0],"conversation_messages",project_id,body.message_id)
    if evaluate(message)["allowedEffect"]!="PROPOSAL_ONLY":error(403,"READ_ONLY_POLICY","This message is read-only.")
    return ProposalService().create(access[0],project_id,access[1],body)


@router.get("/proposals/versions/{version_id}",response_model=ProposalView)
def read_proposal(project_id:int,version_id:str,access=Depends(scope)):
    return ProposalService().read(access[0],project_id,version_id)


@router.post("/proposals/approve")
def approve_proposal(project_id:int,body:ApplicationApproval,access=Depends(scope)):
    return ProposalService().approve(access[0],project_id,access[1],body)


@router.post("/proposals/versions/{version_id}/reject")
def reject_proposal(project_id:int,version_id:str,access=Depends(scope)):
    return ProposalService().reject(access[0],project_id,version_id)


@router.post("/proposals/versions/{version_id}/build")
def build_proposal(project_id:int,version_id:str,access=Depends(scope)):
    return ProposalService().build(access[0],project_id,version_id)


@router.get("/memory")
def list_memory(project_id:int,kind:str|None=None,status:str|None=None,asset_id:str|None=Query(None,alias="assetId"),access=Depends(scope)):
    if asset_id:owned_row(access[0],"asset_instances",project_id,asset_id)
    return {"items":memory.list(access[0],project_id,kind,status,asset_id)}


@router.post("/memory",response_model=MemoryView)
def create_memory(project_id:int,body:MemoryInput,access=Depends(scope)):
    return memory.create(access[0],project_id,access[1],body)


@router.post("/memory/{item_id}/versions",response_model=MemoryView)
def revise_memory(project_id:int,item_id:str,body:MemoryRevisionInput,access=Depends(scope)):
    return memory.create(access[0],project_id,access[1],body,item_id)


@router.post("/memory/{item_id}/versions/{version}/accept",response_model=MemoryView)
def accept_memory(project_id:int,item_id:str,version:int,body:MemoryAction,access=Depends(scope)):
    return memory.transition(access[0],project_id,access[1],item_id,version,"accept",body.expected_status)


@router.post("/memory/{item_id}/versions/{version}/reject",response_model=MemoryView)
def reject_memory(project_id:int,item_id:str,version:int,body:MemoryAction,access=Depends(scope)):
    return memory.transition(access[0],project_id,access[1],item_id,version,"reject",body.expected_status)

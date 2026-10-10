"""Human application commands only; not registered as AI/chat tools."""
import asyncio
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.experimental.cad_capability import require_cad
from app.experimental.cad_artifacts import retrieve
from app.domain.assistant_runtime import ApplicationApproval
from app.services.assistant.proposals import ProposalService

router = APIRouter(prefix="/api/projects/{project_id}/experimental-cad", tags=["experimental-cad"])


class AuthoringStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1,max_length=128,pattern=r"^[a-zA-Z0-9_-]+$")
    message_id: str = Field(min_length=1,max_length=128)


class AuthoringAdvance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recover_interrupted: bool = False


@router.post("/bim-authoring/runs")
def authoring_start(project_id: int,body: AuthoringStart,db=Depends(get_db),user_id=Depends(get_current_user_id)):
    from app.experimental.bim_orchestration import start
    from app.experimental.bim_authoring import AuthoringError
    from fastapi import HTTPException
    try:
        return start(db,project_id=project_id,user_id=user_id,**body.model_dump())
    except AuthoringError as exc:
        db.rollback()
        raise HTTPException(409,{"code":exc.code}) from exc


@router.get("/bim-authoring/runs/{run_id}")
def authoring_read(project_id: int,run_id: int,db=Depends(get_db),user_id=Depends(get_current_user_id)):
    from app.experimental.bim_orchestration import read
    from app.experimental.bim_authoring import AuthoringError
    from fastapi import HTTPException
    try:
        return read(db,project_id=project_id,user_id=user_id,run_id=run_id)
    except AuthoringError as exc:
        db.rollback()
        raise HTTPException(409,{"code":exc.code}) from exc


@router.post("/bim-authoring/runs/{run_id}/advance")
async def authoring_advance(project_id: int,run_id: int,body: AuthoringAdvance,db=Depends(get_db),user_id=Depends(get_current_user_id)):
    from app.experimental.bim_orchestration import advance
    from app.experimental.bim_authoring import AuthoringError
    from fastapi import HTTPException
    try:
        return await advance(db,project_id=project_id,user_id=user_id,run_id=run_id,**body.model_dump())
    except AuthoringError as exc:
        db.rollback()
        raise HTTPException(409,{"code":exc.code}) from exc


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    message_id: str = Field(min_length=1, max_length=128)
    bim: dict
    mapping: dict


class FixtureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    scenario_id: int = Field(gt=0)
    expected_revision_id: int = Field(gt=0)
    beam_length: float = Field(default=5, ge=5, le=6, allow_inf_nan=False)


@router.post("/support-frame/review")
def fixture_review(project_id: int, body: FixtureInput, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    require_cad(db, project_id, user_id)
    from app.db.models import ModelRevision, GeneratedFile
    from app.services.assistant.storage import rows, owned_row
    from app.services.assistant.conversations import ConversationService
    from app.domain.site_workspace import ConversationInput, MessageInput
    from app.experimental.cad_fixtures import support_frame
    from app.experimental.cad_artifacts import PrivateStore
    from app.experimental.cad_workspace import _fail
    base = db.query(ModelRevision).filter_by(project_id=project_id, design_scenario_id=body.scenario_id).order_by(ModelRevision.revision_number.desc()).first()
    if not base or base.id != body.expected_revision_id:
        _fail("STALE_SOURCE_REVISION")
    profiles = rows(db, "site_profiles", project_id)
    head = next((p for p in reversed(profiles) if p.get("latest_version_id")), None)
    if not head:
        _fail("SITE_PROFILE_REQUIRED", 422)
    profile = owned_row(db, "site_profile_versions", project_id, head["latest_version_id"])
    from app.services.site_profiles.service import SiteProfileService
    if not SiteProfileService().read(db, project_id, head["id"])["current"]:
        _fail("STALE_SITE_PROFILE")
    bim, mapping = support_frame()
    snapshot_id = base.document_json.get("metadata", {}).get("cadSnapshotId")
    if snapshot_id:
        import json
        row = db.query(GeneratedFile).filter_by(id=snapshot_id, project_id=project_id, file_type="cad_review_v1").one_or_none()
        if not row:
            _fail("CAD_REVIEW_NOT_FOUND")
        snapshot = json.loads(PrivateStore().get(project_id, row.metadata_json["snapshotHash"]))
        bim, mapping = snapshot["bim"], snapshot["mapping"]
    from app.services.assistant.bim_foundation import propagate_parameters
    from app.domain.bim import BIMProject
    model = BIMProject.model_validate(bim)
    if body.beam_length != next(p.value for c in model.components if c.id == "primary-0" for p in c.parameters if p.id == "length"):
        model, _ = propagate_parameters(model, {("primary-0", "length"): body.beam_length}, expected_design_version=model.components[0].provenance.design_version)
    conversation = ConversationService().create(db, project_id, user_id, ConversationInput(client_request_id="cad-review-" + body.request_id))
    message = ConversationService().submit(db, project_id, user_id, conversation["id"], MessageInput(
        client_request_id=body.request_id, parts=[{"kind":"TEXT", "text":"Create an experimental CAD support frame concept for explicit review."}],
        context={"siteProfileVersionId":profile["id"], "siteSelectionVersionId":profile["selection_version_id"],
            "modelRevisionId":str(base.id), "scenarioId":str(body.scenario_id), "selectedObjectIds":[]}), orchestrate=False)
    from app.experimental.cad_workspace import create_review
    return create_review(db, project_id=project_id, user_id=user_id, request_id=body.request_id, message_id=message["messageId"], bim=model, mapping=mapping)


@router.get("/capability")
def capability(project_id: int, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    require_cad(db, project_id, user_id)
    return {"experimentalCad": True, "productionCadBuild": False}


@router.post("/reviews")
def review(project_id: int, body: ReviewInput, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    from app.experimental.cad_workspace import create_review
    return create_review(db, project_id=project_id, user_id=user_id, **body.model_dump())


@router.post("/approve")
def approve(project_id: int, body: ApplicationApproval, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    require_cad(db, project_id, user_id)
    from app.experimental.cad_workspace import _snapshot
    from app.experimental.cad_artifacts import PrivateStore
    _snapshot(db, project_id, body.proposal_version_id, PrivateStore())
    return ProposalService().approve(db, project_id, user_id, body)


@router.post("/reviews/{version_id}/execute")
async def execute(project_id: int, version_id: str, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    # The bounded supervisor runs in a thread; native code runs only in its child.
    from app.experimental.cad_workspace import execute_review
    return await asyncio.to_thread(execute_review, db, project_id=project_id, user_id=user_id, version_id=version_id)


@router.get("/catalogs/{catalog_id}/meshes/{sha}")
def mesh(project_id: int, catalog_id: int, sha: str, db=Depends(get_db), user_id=Depends(get_current_user_id)):
    require_cad(db, project_id, user_id)
    from app.experimental.cad_contract import Manifest
    from fastapi import HTTPException
    manifest = Manifest.model_validate_json(retrieve(db, user_id=user_id, project_id=project_id, catalog_id=catalog_id))
    if sha not in {r.mesh.sha256 for r in manifest.results}:
        raise HTTPException(404, "Mesh not found")
    data = retrieve(db, user_id=user_id, project_id=project_id, catalog_id=catalog_id, artifact_hash=sha)
    return Response(data, media_type="application/json", headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})

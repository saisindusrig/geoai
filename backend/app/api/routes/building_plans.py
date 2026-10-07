"""Owned, immutable proposals and explicit, idempotent approval/build."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.config import settings
from app.core.security import get_current_user
from app.db.models import BuildingPlan, DesignScenario, ModelRevision, User, UsageEvent, AuditLog, utcnow
from app.db.session import get_db
from app.services import jobs
from app.services.ai import building_plan as planner
from app.services.ai.nebius import NebiusError
from app.services.rate_limit import enforce_rate_limit
from app.services.usage import enforce_usage_limit

router = APIRouter(prefix="/api/projects/{project_id}/ai/building-plans", tags=["building-plans"])


class PlanRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=6000)
    base_revision_id: int | None = None


class BuildRequest(BaseModel):
    approve: bool = False


def owned(project_id, db, user):
    project = get_owned_project(project_id, db, user.id)
    if project.project_type != "building":
        raise HTTPException(422, "The AI building assistant is available for building projects.")
    return project


def get_plan(db, project_id, plan_id):
    plan = db.query(BuildingPlan).filter_by(id=plan_id, project_id=project_id).first()
    if not plan:
        raise HTTPException(404, "Building plan not found")
    return plan


def snapshot(db, project):
    try:
        return planner.context(db, project)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def output(plan, db, project):
    try:
        stale = planner.fingerprint(planner.context(db, project)) != plan.context_hash
    except ValueError:
        stale = True
    return {"id": plan.id, "parent_id": plan.parent_id, "prompt": plan.prompt, "spec": plan.spec_json,
            "base_revision_id": plan.context_json.get("base_revision_id"), "stale": stale,
            "approved_at": plan.approved_at, "job_id": plan.job_id, "scenario_id": plan.scenario_id,
            "provider": "nebius", "model": plan.provider_model, "created_at": plan.created_at,
            "elevation_known": plan.context_json["origin"].get("elevation_m") is not None}


@router.get("")
def list_plans(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = owned(project_id, db, user)
    plans = db.query(BuildingPlan).filter_by(project_id=project_id).order_by(BuildingPlan.id.desc()).limit(30).all()
    return {"plans": [output(p, db, project) for p in plans]}


@router.get("/{plan_id}")
def read_plan(project_id: int, plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = owned(project_id, db, user)
    return output(get_plan(db, project_id, plan_id), db, project)


async def create(project_id, payload, request, db, user, parent_id=None):
    project = owned(project_id, db, user)
    parent = get_plan(db, project_id, parent_id) if parent_id else None
    ctx = snapshot(db, project)
    if payload.base_revision_id != ctx["base_revision_id"]:
        raise HTTPException(409, "Open the latest saved model revision before planning; the selected model is no longer current.")
    enforce_rate_limit("building.plan", user_id=user.id, request=request)
    enforce_usage_limit(db, user, "llm.plan", project_id=project_id, request=request)
    revision = db.get(ModelRevision, ctx["base_revision_id"]) if ctx["base_revision_id"] else None
    try:
        spec = await planner.propose(payload.prompt, ctx, parent.spec_json if parent else None,
                                     revision.document_json if revision else None)
    except NebiusError as exc:
        raise HTTPException(503, str(exc)) from exc
    except planner.PlanValidationError as exc:
        raise HTTPException(422, {"message": str(exc), "errors": exc.errors}) from exc
    except (ValidationError, ValueError) as exc:
        raise HTTPException(422, "The AI returned an invalid building specification. Refine your request and retry.") from exc
    errors = planner.validate_spec(spec, ctx)
    if errors:
        raise HTTPException(422, {"message": "The proposed layout needs revision: " + " ".join(errors[:8]), "errors": errors})
    db.expire_all()
    if planner.fingerprint(snapshot(db, project)) != planner.fingerprint(ctx):
        raise HTTPException(409, "The plot or model changed while planning. Please create a new plan.")
    plan = BuildingPlan(project_id=project_id, user_id=user.id, parent_id=parent_id,
                        prompt=payload.prompt, spec_json=spec.model_dump(), context_json=ctx,
                        context_hash=planner.fingerprint(ctx), provider_model=settings.NEBIUS_CHAT_MODEL)
    db.add(plan)
    db.add(UsageEvent(user_id=user.id, project_id=project_id, event_type="llm.plan", units=1,
                      metadata_json={"provider": "nebius", "feature": "building_assistant"}))
    db.commit()
    db.refresh(plan)
    return output(plan, db, project)


@router.post("")
async def create_plan(project_id: int, payload: PlanRequest, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await create(project_id, payload, request, db, user)


@router.post("/{plan_id}/revisions")
async def revise_plan(project_id: int, plan_id: int, payload: PlanRequest, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return await create(project_id, payload, request, db, user, plan_id)


@router.post("/{plan_id}/build")
async def build_plan(project_id: int, plan_id: int, payload: BuildRequest, request: Request,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = owned(project_id, db, user)
    plan = get_plan(db, project_id, plan_id)
    if not payload.approve:
        raise HTTPException(422, "Review the plan and explicitly approve it before building.")
    if plan.job_id:
        return {"job_id": plan.job_id, "scenario_id": plan.scenario_id, "status": (jobs.get_status(plan.job_id) or {}).get("status", "unknown")}
    if planner.fingerprint(snapshot(db, project)) != plan.context_hash:
        raise HTTPException(409, "The plot, placement, or model changed. Request a revised plan before approval.")
    errors = planner.validate_spec(planner.BuildingSpec.model_validate(plan.spec_json), plan.context_json)
    if errors:
        raise HTTPException(422, " ".join(errors))
    enforce_rate_limit("generation.start", user_id=user.id, request=request)
    for event in ("scenario.created", "generation.started"):
        enforce_usage_limit(db, user, event, project_id=project_id, request=request)
    job_id = uuid.uuid4().hex
    # Atomic claim also works on SQLite, where SELECT FOR UPDATE is ignored.
    claimed = db.query(BuildingPlan).filter_by(id=plan.id, job_id=None).update(
        {"job_id": job_id, "approved_at": utcnow(), "approved_by": user.id}, synchronize_session=False)
    if not claimed:
        db.rollback()
        db.refresh(plan)
        return {"job_id": plan.job_id, "scenario_id": plan.scenario_id, "status": "queued"}
    scenario = DesignScenario(project_id=project_id, name=f"AI building plan {plan.id}", status="running",
                              input_parameters_json={"approved_building_plan_id": plan.id, "generation_mode": "high_detail"})
    db.add(scenario)
    db.flush()
    db.query(BuildingPlan).filter_by(id=plan.id).update({"scenario_id": scenario.id}, synchronize_session=False)
    db.add(AuditLog(user_id=user.id, project_id=project_id, action="building_plan.approved",
                    entity_type="building_plan", entity_id=str(plan.id), metadata_json={"job_id": job_id}))
    for event in ("scenario.created", "generation.started"):
        db.add(UsageEvent(user_id=user.id, project_id=project_id, event_type=event, units=1,
                          metadata_json={"scenario_id": scenario.id, "job_id": job_id}))
    db.commit()
    try:
        jobs.submit_design_generation(project_id=project_id, scenario_id=scenario.id, mode="high_detail", user_id=user.id, job_id=job_id)
    except Exception as exc:
        jobs.fail_job(job_id, exc)
        scenario.status = "failed"
        db.commit()
        raise HTTPException(503, "Generation could not start. Request a revised plan to retry.") from exc
    return {"job_id": job_id, "scenario_id": scenario.id, "status": "queued"}

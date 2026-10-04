from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.project_catalog import asset_supports_generation
from app.core.security import get_current_user, get_current_user_id
from app.db.models import DesignScenario, User
from app.db.session import get_db
from app.services import jobs
from app.services.design.scenario_summary import (
    build_scenario_detail,
    build_scenario_summary,
    compare_scenarios,
)
from app.services.audit import log_audit_event
from app.services.rate_limit import enforce_rate_limit
from app.services.usage import enforce_usage_limit, record_usage_event

router = APIRouter(prefix="/api/projects/{project_id}", tags=["design"])


class GenerateRequest(BaseModel):
    scenario_name: str = "Scenario 1"
    parameters: dict[str, Any] = {}
    generation_mode: str = "balanced"  # fast_preview | balanced | high_detail


class CompareScenariosRequest(BaseModel):
    scenario_ids: list[int] = Field(min_length=2, max_length=4)


@router.post("/design/generate")
async def generate_design(
    project_id: int,
    payload: GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user.id)
    if not asset_supports_generation(project.project_type):
        raise HTTPException(422, "This asset is a site reference; engineering generation is not supported.")
    mode = payload.generation_mode if payload.generation_mode in (
        "fast_preview",
        "balanced",
        "high_detail",
    ) else "balanced"

    enforce_rate_limit("generation.start", user_id=user.id, request=request)
    enforce_usage_limit(db, user, "scenario.created", project_id=project.id, request=request)
    enforce_usage_limit(db, user, "generation.started", project_id=project.id, request=request)

    scenario = DesignScenario(
        project_id=project.id,
        name=payload.scenario_name,
        input_parameters_json={**payload.parameters, "generation_mode": mode},
        status="running",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    scenario_id = scenario.id
    record_usage_event(
        db,
        user_id=user.id,
        event_type="scenario.created",
        project_id=project.id,
        metadata={"scenario_id": scenario_id},
    )

    job_id = jobs.submit_design_generation(
        project_id=project_id,
        scenario_id=scenario_id,
        mode=mode,
        user_id=user.id,
    )
    record_usage_event(
        db,
        user_id=user.id,
        event_type="generation.started",
        project_id=project_id,
        metadata={"scenario_id": scenario_id, "job_id": job_id, "generation_mode": mode},
    )
    log_audit_event(
        db,
        user_id=user.id,
        action="generation.started",
        entity_type="job",
        entity_id=job_id,
        project_id=project_id,
        metadata={"scenario_id": scenario_id, "generation_mode": mode},
        request=request,
    )
    return {"job_id": job_id, "scenario_id": scenario_id, "status": "queued", "generation_mode": mode}


@router.get("/scenarios")
def list_scenarios(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    scenarios = (
        db.query(DesignScenario)
        .filter(DesignScenario.project_id == project_id)
        .order_by(DesignScenario.created_at.desc())
        .all()
    )
    summaries = [build_scenario_summary(db, s, project) for s in scenarios]
    return {"summaries": summaries, "scenarios": summaries}


@router.get("/scenarios/{scenario_id}")
def get_scenario_detail(
    project_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    scenario = db.get(DesignScenario, scenario_id)
    if scenario is None or scenario.project_id != project_id:
        raise HTTPException(404, "Scenario not found")
    return build_scenario_detail(db, scenario, project)


@router.post("/scenarios/compare")
def compare_project_scenarios(
    project_id: int,
    payload: CompareScenariosRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    return compare_scenarios(db, project, payload.scenario_ids)


@router.put("/scenarios/{scenario_id}/assumptions")
def update_assumptions(
    project_id: int,
    scenario_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    scenario = db.get(DesignScenario, scenario_id)
    if scenario is None or scenario.project_id != project_id:
        raise HTTPException(404, "Scenario not found")
    assumptions = payload.get("assumptions")
    if not isinstance(assumptions, list):
        raise HTTPException(422, "Body must contain 'assumptions' list")
    scenario.assumptions_json = assumptions
    if scenario.design_output_json:
        design = dict(scenario.design_output_json)
        design["assumptions"] = assumptions
        scenario.design_output_json = design
    db.commit()
    return {"ok": True, "assumptions": assumptions}

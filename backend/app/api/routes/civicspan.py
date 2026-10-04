"""Public, hackathon-focused API for the GeoAI concept studio."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai.civicspan import (
    BridgePlan,
    BridgeSpec,
    ConstructionPlan,
    ConstructionSpec,
    ConstructionType,
    SiteContext,
    plan_bridge,
    plan_construction,
)

router = APIRouter(prefix="/api/geoai", tags=["geoai"])


class BridgePlanRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    site: SiteContext
    current_spec: BridgeSpec | None = None


class ConstructionPlanRequest(BaseModel):
    project_type: ConstructionType
    request: str = Field(min_length=8, max_length=1200)
    site: SiteContext
    current_spec: ConstructionSpec | None = None


@router.post("/plan", response_model=BridgePlan)
async def create_or_modify_bridge(payload: BridgePlanRequest):
    try:
        plan, provider = await plan_bridge(payload.prompt, payload.site, payload.current_spec)
        plan.warnings.append(f"Planner: {provider}. Conceptual visualization only; not engineering advice.")
        return plan
    except Exception as exc:
        raise HTTPException(502, "The AI planner could not create a safe bridge specification.") from exc


@router.post("/concept", response_model=ConstructionPlan)
async def create_or_modify_construction_concept(payload: ConstructionPlanRequest):
    try:
        plan, provider = await plan_construction(
            payload.project_type, payload.request, payload.site, payload.current_spec
        )
        plan.warnings.append(f"Planner: {provider}. Conceptual visualization only; not engineering advice.")
        return plan
    except Exception as exc:
        raise HTTPException(502, "The AI planner could not create a safe construction concept.") from exc

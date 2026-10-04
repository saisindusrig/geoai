from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.disclaimer import DISCLAIMER
from app.core.security import get_current_user_id
from app.db.models import DesignScenario, QuantityEstimate
from app.db.session import get_db

router = APIRouter(prefix="/api/projects/{project_id}/estimates", tags=["estimates"])


def latest_estimate(db: Session, project_id: int) -> QuantityEstimate | None:
    return (
        db.query(QuantityEstimate)
        .join(DesignScenario, QuantityEstimate.design_scenario_id == DesignScenario.id)
        .filter(DesignScenario.project_id == project_id)
        .order_by(QuantityEstimate.created_at.desc())
        .first()
    )


def estimate_out(e: QuantityEstimate) -> dict:
    return {
        "id": e.id,
        "design_scenario_id": e.design_scenario_id,
        "concrete_m3": e.concrete_m3,
        "cement_bags": e.cement_bags,
        "steel_kg": e.steel_kg,
        "rebar_kg": e.rebar_kg,
        "excavation_m3": e.excavation_m3,
        "backfill_m3": e.backfill_m3,
        "formwork_sqm": e.formwork_sqm,
        "asphalt_m3": e.asphalt_m3,
        "pipe_length_m": e.pipe_length_m,
        "pipe_diameter_mm": e.pipe_diameter_mm,
        "total_cost_estimate": e.total_cost_estimate,
        "line_items": e.line_items_json or [],
        "created_at": e.created_at,
        "disclaimer": DISCLAIMER,
    }


@router.get("")
def get_estimate(
    project_id: int,
    scenario_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    if scenario_id is not None:
        estimate = (
            db.query(QuantityEstimate)
            .join(DesignScenario, QuantityEstimate.design_scenario_id == DesignScenario.id)
            .filter(DesignScenario.project_id == project_id, DesignScenario.id == scenario_id)
            .order_by(QuantityEstimate.created_at.desc())
            .first()
        )
    else:
        estimate = latest_estimate(db, project_id)
    if estimate is None:
        return None
    return estimate_out(estimate)


@router.put("/{estimate_id}/line-items")
def update_line_items(
    project_id: int,
    estimate_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Inline BOQ editing: replace line items and recompute amounts/total."""
    get_owned_project(project_id, db, user_id)
    estimate = db.get(QuantityEstimate, estimate_id)
    if estimate is None:
        raise HTTPException(404, "Estimate not found")
    line_items = payload.get("line_items")
    if not isinstance(line_items, list):
        raise HTTPException(422, "Body must contain 'line_items' list")
    for li in line_items:
        li["amount"] = round(float(li.get("quantity", 0)) * float(li.get("rate", 0)), 2)
    estimate.line_items_json = line_items
    direct = sum(li["amount"] for li in line_items)
    estimate.total_cost_estimate = round(direct * 1.16, 2)  # contingency + soft costs
    db.commit()
    return estimate_out(estimate)

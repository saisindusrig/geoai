from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user, get_current_user_id
from app.db.models import RateItem, User
from app.db.session import get_db
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/admin/rates", tags=["admin"])


class RateIn(BaseModel):
    region: str = "default"
    item_code: str
    item_name: str
    unit: str
    rate: float
    currency: str = "INR"


def _out(r: RateItem) -> dict:
    return {
        "id": r.id,
        "region": r.region,
        "item_code": r.item_code,
        "item_name": r.item_name,
        "unit": r.unit,
        "rate": r.rate,
        "currency": r.currency,
        "updated_at": r.updated_at,
    }


@router.get("")
def list_rates(
    region: str = "default",
    db: Session = Depends(get_db),
    _user_id: int = Depends(get_current_user_id),
):
    """Read-only rate library — available to all authenticated users for BOQ display."""
    return [_out(r) for r in db.query(RateItem).filter(RateItem.region == region).order_by(RateItem.item_code)]


@router.post("", status_code=201)
def create_rate(
    payload: RateIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    rate = RateItem(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    log_audit_event(
        db,
        user_id=admin.id,
        action="rate.create",
        entity_type="rate",
        entity_id=rate.id,
        metadata={"item_code": rate.item_code, "region": rate.region, "rate": rate.rate},
        request=request,
    )
    return _out(rate)


@router.put("/{rate_id}")
def update_rate(
    rate_id: int,
    payload: RateIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    rate = db.get(RateItem, rate_id)
    if rate is None:
        raise HTTPException(404, "Rate not found")
    for key, value in payload.model_dump().items():
        setattr(rate, key, value)
    db.commit()
    db.refresh(rate)
    log_audit_event(
        db,
        user_id=admin.id,
        action="rate.update",
        entity_type="rate",
        entity_id=rate.id,
        metadata={"item_code": rate.item_code, "region": rate.region, "rate": rate.rate},
        request=request,
    )
    return _out(rate)


@router.delete("/{rate_id}", status_code=204)
def delete_rate(
    rate_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    rate = db.get(RateItem, rate_id)
    if rate is None:
        raise HTTPException(404, "Rate not found")
    meta = {"item_code": rate.item_code, "region": rate.region}
    db.delete(rate)
    db.commit()
    log_audit_event(
        db,
        user_id=admin.id,
        action="rate.delete",
        entity_type="rate",
        entity_id=rate_id,
        metadata=meta,
        request=request,
    )

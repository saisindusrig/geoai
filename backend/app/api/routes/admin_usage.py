"""Admin usage visibility API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.db.models import UsageEvent, User
from app.db.session import get_db
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/admin/usage", tags=["admin"])


def _out(entry: UsageEvent) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "project_id": entry.project_id,
        "event_type": entry.event_type,
        "units": entry.units,
        "metadata": entry.metadata_json,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("")
def list_usage_events(
    user_id: int | None = None,
    event_type: str | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(UsageEvent)
    if user_id is not None:
        query = query.filter(UsageEvent.user_id == user_id)
    if event_type:
        query = query.filter(UsageEvent.event_type == event_type)
    if from_date is not None:
        query = query.filter(UsageEvent.created_at >= from_date)
    if to_date is not None:
        query = query.filter(UsageEvent.created_at <= to_date)

    total = query.count()
    rows = query.order_by(UsageEvent.created_at.desc()).offset(offset).limit(limit).all()

    log_audit_event(
        db,
        user_id=admin.id,
        action="admin.usage_query",
        entity_type="usage",
        metadata={
            "filters": {
                "user_id": user_id,
                "event_type": event_type,
                "from": from_date.isoformat() if from_date else None,
                "to": to_date.isoformat() if to_date else None,
            },
            "limit": limit,
            "offset": offset,
            "result_count": len(rows),
        },
    )

    return {"total": total, "limit": limit, "offset": offset, "entries": [_out(e) for e in rows]}

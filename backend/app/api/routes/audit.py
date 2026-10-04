"""Admin audit log API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.db.models import AuditLog, User
from app.db.session import get_db

router = APIRouter(prefix="/api/admin/audit", tags=["admin"])


def _out(entry: AuditLog) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "action": entry.action,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "project_id": entry.project_id,
        "metadata": entry.metadata_json,
        "ip_address": entry.ip_address,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("")
def list_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    project_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if project_id is not None:
        query = query.filter(AuditLog.project_id == project_id)

    total = query.count()
    rows = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "entries": [_out(e) for e in rows]}

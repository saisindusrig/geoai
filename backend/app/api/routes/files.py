"""Authenticated file serving with path traversal protection."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.config import settings
from app.core.security import get_current_user, get_current_user_id
from app.db.models import User
from app.db.session import SessionLocal, get_db
from app.services.audit import log_audit_event
from app.services.rate_limit import enforce_rate_limit
from app.services.usage import enforce_usage_limit, record_usage_event

router = APIRouter(tags=["files"])

_PROJECT_PREFIX = re.compile(r"^projects/(\d+)/")


def _safe_local_path(file_path: str) -> Path:
    if not file_path or file_path.startswith("/") or ".." in file_path.replace("\\", "/"):
        raise HTTPException(400, "Invalid file path")
    root = Path(settings.LOCAL_STORAGE_DIR).resolve()
    target = (root / file_path).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(400, "Invalid file path")
    if not target.is_file():
        raise HTTPException(404, "File not found")
    return target


def _enforce_file_access(file_path: str, user_id: int, db: Session) -> None:
    if not settings.AUTH_REQUIRE_JWT:
        return
    match = _PROJECT_PREFIX.match(file_path.replace("\\", "/"))
    if not match:
        raise HTTPException(403, "File access denied")
    get_owned_project(int(match.group(1)), db, user_id)


@router.get("/files/{file_path:path}")
def serve_local_file(
    file_path: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Serve local storage files. Public in dev; JWT + project ownership in production."""
    _enforce_file_access(file_path, user.id, db)
    if settings.AUTH_REQUIRE_JWT or settings.USAGE_LIMITS_ENABLED:
        enforce_rate_limit("file.download", user_id=user.id, request=request)
        enforce_usage_limit(db, user, "file.download", request=request)
    target = _safe_local_path(file_path)
    match = _PROJECT_PREFIX.match(file_path.replace("\\", "/"))
    project_id = int(match.group(1)) if match else None
    if settings.AUTH_REQUIRE_JWT:
        audit_db = SessionLocal()
        try:
            log_audit_event(
                audit_db,
                user_id=user.id,
                action="file.download",
                entity_type="file",
                entity_id=file_path,
                project_id=project_id,
                metadata={"file_name": target.name},
                request=request,
            )
        finally:
            audit_db.close()
    if settings.USAGE_LIMITS_ENABLED:
        record_usage_event(
            db,
            user_id=user.id,
            event_type="file.download",
            project_id=project_id,
            metadata={"file_name": target.name},
        )
    return FileResponse(target)

"""Audit trail for sensitive actions."""

from __future__ import annotations

import re
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import AuditLog

SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|authorization|prompt|credential)",
    re.IGNORECASE,
)

MAX_METADATA_STRING = 500


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip secrets and truncate long strings before persistence."""
    if not metadata:
        return None

    def _clean(value: Any, key: str = "") -> Any:
        if isinstance(value, dict):
            return {k: _clean(v, k) for k, v in value.items() if not SENSITIVE_KEY_PATTERN.search(k)}
        if isinstance(value, list):
            return [_clean(v) for v in value[:20]]
        if isinstance(value, str):
            if SENSITIVE_KEY_PATTERN.search(key):
                return "[redacted]"
            if len(value) > MAX_METADATA_STRING:
                return value[:MAX_METADATA_STRING] + "…"
            return value
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return str(value)[:MAX_METADATA_STRING]

    cleaned = _clean(metadata)
    return cleaned if isinstance(cleaned, dict) else {"value": cleaned}


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    return ua[:512] if ua else None


def log_audit_event(
    db: Session,
    *,
    action: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    project_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        project_id=project_id,
        metadata_json=sanitize_metadata(metadata),
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

"""Usage tracking and plan limit enforcement."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.plans import (
    DAILY_EVENT_TYPES,
    EVENT_TO_LIMIT,
    PLAN_ADMIN,
    PLAN_FREE,
    PLAN_LIMITS,
    PLAN_PRO,
)
from app.core.security import ROLE_ADMIN, is_admin
from app.db.models import DesignScenario, Project, UsageEvent, User
from app.services.audit import log_audit_event, sanitize_metadata

logger = logging.getLogger(__name__)


def effective_plan(user: User) -> str:
    if is_admin(user) or (user.plan or PLAN_FREE) == PLAN_ADMIN:
        return PLAN_ADMIN
    plan = (user.plan or PLAN_FREE).lower()
    if plan not in PLAN_LIMITS:
        return PLAN_FREE
    return plan


def is_unlimited(user: User) -> bool:
    return effective_plan(user) == PLAN_ADMIN or is_admin(user)


def plan_limits(user: User) -> dict[str, int | None]:
    return PLAN_LIMITS[effective_plan(user)]


def _day_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _next_day_reset_utc() -> str:
    start = _day_start_utc()
    return (start + timedelta(days=1)).isoformat()


def record_usage_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    units: int = 1,
    project_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> UsageEvent:
    entry = UsageEvent(
        user_id=user_id,
        project_id=project_id,
        event_type=event_type,
        units=units,
        metadata_json=sanitize_metadata(metadata),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _count_projects(db: Session, user_id: int) -> int:
    return db.query(Project).filter(Project.user_id == user_id).count()


def _count_scenarios(db: Session, project_id: int) -> int:
    return db.query(DesignScenario).filter(DesignScenario.project_id == project_id).count()


def _count_daily_events(db: Session, user_id: int, event_types: set[str]) -> int:
    since = _day_start_utc()
    q = db.query(func.coalesce(func.sum(UsageEvent.units), 0)).filter(
        UsageEvent.user_id == user_id,
        UsageEvent.created_at >= since,
        UsageEvent.event_type.in_(event_types),
    )
    return int(q.scalar() or 0)


def _current_usage(db: Session, user: User, limit_key: str, project_id: int | None) -> int:
    if limit_key == "max_projects":
        return _count_projects(db, user.id)
    if limit_key == "max_scenarios_per_project" and project_id is not None:
        return _count_scenarios(db, project_id)
    daily_types = {et for et, lk in EVENT_TO_LIMIT.items() if lk == limit_key and et in DAILY_EVENT_TYPES}
    if daily_types:
        return _count_daily_events(db, user.id, daily_types)
    return 0


def check_usage_limit(
    db: Session,
    user: User,
    event_type: str,
    *,
    project_id: int | None = None,
) -> dict[str, Any]:
    """Return allowed flag and usage details."""
    if not settings.USAGE_LIMITS_ENABLED or is_unlimited(user):
        return {"allowed": True, "unlimited": True}

    limit_key = EVENT_TO_LIMIT.get(event_type)
    if not limit_key:
        return {"allowed": True}

    limits = plan_limits(user)
    maximum = limits.get(limit_key)
    if maximum is None:
        return {"allowed": True, "unlimited": True}

    current = _current_usage(db, user, limit_key, project_id)
    # For create actions, check if adding one more would exceed
    would_exceed = current >= maximum
    if event_type in {
        "project.create",
        "scenario.created",
        "generation.started",
        "llm.plan",
        "site_analysis.run",
        "file.download",
    } or event_type.startswith("export."):
        would_exceed = (current + 1) > maximum

    return {
        "allowed": not would_exceed,
        "limit": limit_key,
        "current": current,
        "max": maximum,
        "reset_at": _next_day_reset_utc() if limit_key != "max_projects" and limit_key != "max_scenarios_per_project" else None,
        "plan": effective_plan(user),
    }


def _raise_usage_limit(detail: dict[str, Any]) -> None:
    raise HTTPException(
        status_code=429,
        detail={
            "code": "usage_limit_exceeded",
            "limit": detail.get("limit"),
            "current": detail.get("current"),
            "max": detail.get("max"),
            "reset_at": detail.get("reset_at"),
            "plan": detail.get("plan"),
            "message": _limit_message(detail),
        },
    )


def _limit_message(detail: dict[str, Any]) -> str:
    limit = detail.get("limit", "usage")
    labels = {
        "max_projects": "project limit",
        "max_scenarios_per_project": "scenario limit for this project",
        "max_generations_per_day": "daily generation limit",
        "max_llm_plans_per_day": "daily AI planning limit",
        "max_exports_per_day": "daily export limit",
        "max_file_downloads_per_day": "daily file download limit",
    }
    label = labels.get(limit, "usage limit")
    reset = detail.get("reset_at")
    suffix = f" Resets at {reset}." if reset else ""
    return f"You have reached your {label} on the {detail.get('plan', 'free')} plan.{suffix}"


def enforce_usage_limit(
    db: Session,
    user: User,
    event_type: str,
    *,
    project_id: int | None = None,
    request: Request | None = None,
) -> None:
    result = check_usage_limit(db, user, event_type, project_id=project_id)
    if result.get("allowed", True):
        return
    try:
        log_audit_event(
            db,
            user_id=user.id,
            action="usage.limit_exceeded",
            entity_type="usage",
            project_id=project_id,
            metadata={
                "event_type": event_type,
                "limit": result.get("limit"),
                "current": result.get("current"),
                "max": result.get("max"),
            },
            request=request,
        )
    except Exception:
        logger.exception("Failed to audit usage limit exceeded")
    _raise_usage_limit(result)


def get_usage_summary(db: Session, user: User) -> dict[str, Any]:
    limits = plan_limits(user)
    unlimited = is_unlimited(user)
    plan = effective_plan(user)

    def _metric(limit_key: str, event_types: set[str] | None = None) -> dict[str, Any]:
        maximum = limits.get(limit_key)
        if unlimited or maximum is None:
            return {"current": _current_usage(db, user, limit_key, None) if limit_key == "max_projects" else None, "max": None, "unlimited": True}
        if limit_key == "max_projects":
            current = _count_projects(db, user.id)
        elif event_types:
            current = _count_daily_events(db, user.id, event_types)
        else:
            current = 0
        return {
            "current": current,
            "max": maximum,
            "unlimited": False,
            "reset_at": _next_day_reset_utc() if event_types else None,
        }

    gen_types = {et for et, lk in EVENT_TO_LIMIT.items() if lk == "max_generations_per_day"}
    llm_types = {et for et, lk in EVENT_TO_LIMIT.items() if lk == "max_llm_plans_per_day"}
    export_types = {et for et, lk in EVENT_TO_LIMIT.items() if lk == "max_exports_per_day"}

    return {
        "plan": plan,
        "unlimited": unlimited,
        "projects": _metric("max_projects"),
        "generations_today": _metric("max_generations_per_day", gen_types),
        "llm_plans_today": _metric("max_llm_plans_per_day", llm_types),
        "exports_today": _metric("max_exports_per_day", export_types),
        "limits": limits,
    }

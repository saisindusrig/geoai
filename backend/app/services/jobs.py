"""Job status store + background execution."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.job_errors import JobCancelledError, JobTimeoutError, classify_exception
from app.services.storage import normalize_file_url

logger = logging.getLogger(__name__)

_memory_store: dict[str, dict] = {}
_redis = None
_redis_checked = False

JOB_STAGES = (
    "queued",
    "analyzing_site",
    "generating_layout",
    "generating_3d_preview",
    "calculating_boq",
    "exporting_model",
    "saving_result",
    "completed",
    "failed",
    "cancelled",
)

TERMINAL_STAGES = frozenset({"completed", "failed", "cancelled"})
TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})

STAGE_LABELS = {
    "queued": "Queued",
    "analyzing_site": "Analyzing site",
    "generating_layout": "Generating layout",
    "generating_3d_preview": "Generating 3D preview",
    "calculating_boq": "Calculating BOQ",
    "exporting_model": "Exporting model",
    "saving_result": "Saving result",
    "completed": "Completed",
    "failed": "Failed",
    "cancelled": "Cancelled",
}

STAGE_PROGRESS = {
    "queued": 5,
    "analyzing_site": 15,
    "generating_layout": 30,
    "generating_3d_preview": 50,
    "calculating_boq": 70,
    "exporting_model": 85,
    "saving_result": 95,
    "completed": 100,
    "failed": 0,
    "cancelled": 0,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_redis():
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    _redis_checked = True
    try:
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        client.ping()
        _redis = client
        logger.info("Job store: Redis")
    except Exception:
        logger.warning("Redis unavailable; job store is in-memory")
        _redis = None
    return _redis


def _legacy_status(stage: str) -> str:
    if stage in ("completed",):
        return "completed"
    if stage in ("failed",):
        return "failed"
    if stage in ("cancelled",):
        return "cancelled"
    if stage in ("queued",):
        return "queued"
    return "running"


def _default_job(job_id: str) -> dict:
    now = _utc_now_iso()
    return {
        "job_id": job_id,
        "status": "queued",
        "stage": "queued",
        "progress": 5,
        "preview_ready": False,
        "preview_glb_url": None,
        "message": None,
        "result": None,
        "error": None,
        "error_type": None,
        "safe_error_message": None,
        "failed_stage": None,
        "retryable": False,
        "timings": None,
        "diagnostics": None,
        "created_at": now,
        "updated_at": now,
        "duration_ms": None,
        "cancel_requested": False,
        "user_id": None,
        "project_id": None,
    }


def _write(job_id: str, payload: dict) -> None:
    payload["updated_at"] = _utc_now_iso()
    if payload.get("created_at") is None:
        payload["created_at"] = payload["updated_at"]
    r = _get_redis()
    if r is not None:
        r.setex(f"job:{job_id}", 24 * 3600, json.dumps(payload, default=str))
    else:
        _memory_store[job_id] = payload


def _duration_ms(payload: dict) -> int | None:
    created = payload.get("created_at")
    updated = payload.get("updated_at")
    if not created or not updated:
        return None
    try:
        start = datetime.fromisoformat(created.replace("Z", "+00:00"))
        end = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        return max(0, int((end - start).total_seconds() * 1000))
    except (ValueError, TypeError):
        return None


def set_status(job_id: str, status: str, result: Any = None, error: str | None = None) -> None:
    update_job(job_id, status=status, stage=status if status in JOB_STAGES else None, result=result, error=error)


def update_job(
    job_id: str,
    *,
    status: str | None = None,
    stage: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    preview_ready: bool | None = None,
    preview_glb_url: str | None = None,
    result: Any = None,
    error: str | None = None,
    timings: dict | None = None,
    diagnostics: dict | None = None,
    error_type: str | None = None,
    safe_error_message: str | None = None,
    failed_stage: str | None = None,
    retryable: bool | None = None,
    cancel_requested: bool | None = None,
    user_id: int | None = None,
    project_id: int | None = None,
) -> None:
    current = get_status(job_id) or _default_job(job_id)

    if is_terminal(current) and stage not in TERMINAL_STAGES and status not in TERMINAL_STATUSES:
        return

    if stage is not None:
        current["stage"] = stage
        current["status"] = status if status is not None else _legacy_status(stage)
        if progress is None:
            current["progress"] = STAGE_PROGRESS.get(stage, current.get("progress", 0))
        current["stage_label"] = STAGE_LABELS.get(stage, stage.replace("_", " ").title())
    elif status is not None:
        current["status"] = status
    if progress is not None:
        current["progress"] = max(0, min(100, progress))
    if message is not None:
        current["message"] = message
    if preview_ready is not None:
        current["preview_ready"] = preview_ready
    if preview_glb_url is not None:
        current["preview_glb_url"] = preview_glb_url
    if result is not None:
        current["result"] = result
    if error is not None:
        current["error"] = error
    if timings is not None:
        current["timings"] = timings
    if diagnostics is not None:
        current["diagnostics"] = diagnostics
    if error_type is not None:
        current["error_type"] = error_type
    if safe_error_message is not None:
        current["safe_error_message"] = safe_error_message
    if failed_stage is not None:
        current["failed_stage"] = failed_stage
    if retryable is not None:
        current["retryable"] = retryable
    if cancel_requested is not None:
        current["cancel_requested"] = cancel_requested
    if user_id is not None:
        current["user_id"] = user_id
    if project_id is not None:
        current["project_id"] = project_id

    if current.get("stage") in TERMINAL_STAGES or current.get("status") in TERMINAL_STATUSES:
        current["duration_ms"] = _duration_ms(current)

    _write(job_id, current)


def get_status(job_id: str) -> dict | None:
    r = _get_redis()
    if r is not None:
        raw = r.get(f"job:{job_id}")
        return json.loads(raw) if raw else None
    return _memory_store.get(job_id)


def public_status(job_id: str) -> dict | None:
    """API-safe job payload — no raw stack traces."""
    status = get_status(job_id)
    if status is None:
        return None
    out = dict(status)
    if out.get("safe_error_message"):
        out["error"] = out["safe_error_message"]
    elif out.get("error"):
        out["error"] = "Design generation failed."
    if out.get("preview_glb_url"):
        out["preview_glb_url"] = normalize_file_url(out["preview_glb_url"])
    result = out.get("result")
    if isinstance(result, dict):
        normalized = dict(result)
        for key in ("preview_glb_url", "glb_url", "final_glb_url", "excavation_glb_url"):
            if key in normalized and isinstance(normalized[key], str):
                normalized[key] = normalize_file_url(normalized[key])
        out["result"] = normalized
    return out


def is_terminal(status: dict | None) -> bool:
    if not status:
        return False
    return status.get("status") in TERMINAL_STATUSES or status.get("stage") in TERMINAL_STAGES


def is_cancelled(job_id: str) -> bool:
    status = get_status(job_id)
    if not status:
        return False
    return (
        status.get("status") == "cancelled"
        or status.get("stage") == "cancelled"
        or bool(status.get("cancel_requested"))
    )


def ensure_not_cancelled(job_id: str | None) -> None:
    if job_id and is_cancelled(job_id):
        raise JobCancelledError("Job cancelled")


def cancel_job(job_id: str) -> dict | None:
    status = get_status(job_id)
    if status is None:
        return None
    if is_terminal(status):
        return public_status(job_id)
    update_job(
        job_id,
        stage="cancelled",
        status="cancelled",
        progress=0,
        message="Generation cancelled",
        cancel_requested=True,
        error_type="cancelled",
        safe_error_message="Generation was cancelled.",
        failed_stage=status.get("stage"),
        retryable=False,
        error="Generation was cancelled.",
    )
    return public_status(job_id)


def fail_job(job_id: str, exc: Exception, *, failed_stage: str | None = None) -> None:
    current = get_status(job_id) or _default_job(job_id)
    stage = failed_stage or current.get("stage") or "failed"
    info = classify_exception(exc, failed_stage=stage)
    diagnostics = dict(current.get("diagnostics") or {})
    diagnostics["failure_reason"] = info["error_type"]
    diagnostics["failed_stage"] = info["failed_stage"]
    update_job(
        job_id,
        stage="failed",
        status="failed",
        progress=0,
        message=info["safe_error_message"],
        error=info["safe_error_message"],
        error_type=info["error_type"],
        safe_error_message=info["safe_error_message"],
        failed_stage=info["failed_stage"],
        retryable=info["retryable"],
        diagnostics=diagnostics,
    )


def _schedule_task(coro) -> None:
    """Schedule coroutine on the running loop, or the main/default loop in sync callers."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
        return
    except RuntimeError:
        pass
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.create_task(coro)


def bind_job(job_id: str, *, user_id: int, project_id: int) -> None:
    update_job(job_id, user_id=user_id, project_id=project_id)


def user_can_access_job(job_id: str, user_id: int) -> bool:
    status = get_status(job_id)
    if status is None:
        return False
    owner = status.get("user_id")
    if owner is None:
        return not settings.AUTH_REQUIRE_JWT
    return owner == user_id


def use_arq_worker() -> bool:
    return bool(settings.USE_ARQ_WORKER and _get_redis() is not None)


async def _enqueue_arq_design(job_id: str, project_id: int, scenario_id: int, mode: str) -> None:
    from arq import create_pool
    from arq.connections import RedisSettings

    pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        await pool.enqueue_job("generate_design_task", job_id, project_id, scenario_id, mode)
    finally:
        await pool.close()


async def run_design_job(
    job_id: str,
    project_id: int,
    scenario_id: int,
    mode: str,
) -> dict:
    """Shared design generation runner for inline API jobs and Arq workers."""
    from app.db.models import DesignScenario, Project
    from app.db.session import SessionLocal
    from app.services.ai.orchestrator import run_design_generation

    db = SessionLocal()
    try:
        project = db.get(Project, project_id)
        scenario = db.get(DesignScenario, scenario_id)
        return await run_design_generation(
            db,
            project,
            scenario,
            job_id=job_id,
            mode=mode,
        )
    except JobCancelledError:
        db.rollback()
        scenario = db.get(DesignScenario, scenario_id)
        if scenario is not None and scenario.status not in ("completed", "preview"):
            scenario.status = "cancelled"
            db.commit()
        raise
    except (JobTimeoutError, TimeoutError):
        db.rollback()
        scenario = db.get(DesignScenario, scenario_id)
        if scenario is not None and scenario.status not in ("completed", "preview"):
            scenario.status = "failed"
            db.commit()
        raise
    except Exception:
        db.rollback()
        scenario = db.get(DesignScenario, scenario_id)
        if scenario is not None and scenario.status not in ("completed", "preview"):
            scenario.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


async def _complete_design_job(job_id: str, project_id: int, scenario_id: int, mode: str) -> None:
    try:
        result = await asyncio.wait_for(
            run_design_job(job_id, project_id, scenario_id, mode),
            timeout=settings.GENERATION_JOB_TIMEOUT_SECONDS,
        )
        if is_cancelled(job_id):
            return
        update_job(
            job_id,
            stage="completed",
            progress=100,
            message="Design generation completed",
            result=result,
        )
    except JobCancelledError:
        cancel_job(job_id)
    except asyncio.TimeoutError:
        logger.warning("Job %s timed out after %ss", job_id, settings.GENERATION_JOB_TIMEOUT_SECONDS)
        fail_job(
            job_id,
            JobTimeoutError("Generation timed out"),
            failed_stage=(get_status(job_id) or {}).get("stage"),
        )
    except Exception as exc:
        if is_cancelled(job_id):
            cancel_job(job_id)
            return
        logger.exception("Job %s failed", job_id)
        fail_job(job_id, exc, failed_stage=(get_status(job_id) or {}).get("stage"))


def submit_design_generation(
    *,
    project_id: int,
    scenario_id: int,
    mode: str,
    user_id: int | None = None,
) -> str:
    """Queue a design generation job (Arq worker when enabled, else in-process)."""
    job_id = uuid.uuid4().hex
    update_job(
        job_id,
        stage="queued",
        message="Waiting to start",
        user_id=user_id,
        project_id=project_id,
    )

    if use_arq_worker():

        async def _enqueue_runner() -> None:
            try:
                await _enqueue_arq_design(job_id, project_id, scenario_id, mode)
            except Exception:
                logger.exception("Arq enqueue failed for job %s; running inline", job_id)
                await _complete_design_job(job_id, project_id, scenario_id, mode)

        _schedule_task(_enqueue_runner())
        return job_id

    async def _inline_runner() -> None:
        await _complete_design_job(job_id, project_id, scenario_id, mode)

    _schedule_task(_inline_runner())
    return job_id


def submit(coro_factory, *, user_id: int | None = None, project_id: int | None = None) -> str:
    """Run an async job in the background; coro_factory(job_id) -> coroutine."""
    job_id = uuid.uuid4().hex
    update_job(job_id, stage="queued", message="Waiting to start", user_id=user_id, project_id=project_id)

    async def _runner():
        try:
            result = await asyncio.wait_for(
                coro_factory(job_id),
                timeout=settings.GENERATION_JOB_TIMEOUT_SECONDS,
            )
            if is_cancelled(job_id):
                return
            update_job(
                job_id,
                stage="completed",
                progress=100,
                message="Design generation completed",
                result=result,
            )
        except JobCancelledError:
            cancel_job(job_id)
        except asyncio.TimeoutError:
            logger.warning("Job %s timed out after %ss", job_id, settings.GENERATION_JOB_TIMEOUT_SECONDS)
            fail_job(
                job_id,
                JobTimeoutError("Generation timed out"),
                failed_stage=(get_status(job_id) or {}).get("stage"),
            )
        except Exception as exc:
            if is_cancelled(job_id):
                cancel_job(job_id)
                return
            logger.exception("Job %s failed", job_id)
            fail_job(job_id, exc, failed_stage=(get_status(job_id) or {}).get("stage"))

    _schedule_task(_runner())
    return job_id

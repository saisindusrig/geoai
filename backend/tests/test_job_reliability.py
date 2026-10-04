"""Job cancellation, failure metadata, timeout, and production readiness tests."""

import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.production import collect_production_warnings, production_readiness
from app.main import app
from app.services import jobs
from app.services.job_errors import JobCancelledError, JobTimeoutError, classify_exception

client = TestClient(app)


def test_cancel_queued_job():
    job_id = "manual-queued-job"
    jobs.update_job(job_id, stage="queued", status="queued")

    r = client.post(f"/api/jobs/{job_id}/cancel")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "cancelled"
    assert body["stage"] == "cancelled"
    assert body["error_type"] == "cancelled"
    assert body["safe_error_message"] == "Generation was cancelled."
    assert body["retryable"] is False
    assert body.get("created_at")
    assert body.get("updated_at")


def test_cancel_running_job_marks_terminal():
    job_id = "manual-running-job"
    jobs.update_job(job_id, stage="analyzing_site", status="running", progress=15)

    r = client.post(f"/api/jobs/{job_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert r.json()["failed_stage"] == "analyzing_site"


def test_cancelled_job_does_not_mark_completed():
    async def work(job_id: str):
        jobs.update_job(job_id, stage="generating_layout", status="running")
        jobs.cancel_job(job_id)
        jobs.ensure_not_cancelled(job_id)
        return {"scenario_id": 99, "glb_url": "http://example.com/model.glb"}

    async def run_case():
        job_id = jobs.submit(work)
        await asyncio.sleep(0.2)
        return job_id

    job_id = asyncio.run(run_case())
    status = jobs.public_status(job_id)
    assert status is not None
    assert status["status"] == "cancelled"
    assert status.get("result") is None


def test_failed_job_returns_safe_error_payload():
    async def boom(job_id: str):
        jobs.update_job(job_id, stage="exporting_model", status="running")
        raise RuntimeError("secret-api-key=abc123 connection reset")

    async def run_case():
        job_id = jobs.submit(boom)
        await asyncio.sleep(0.2)
        return job_id

    job_id = asyncio.run(run_case())
    status = jobs.public_status(job_id)
    assert status is not None
    assert status["status"] == "failed"
    assert status["error_type"] == "connection"
    assert "secret" not in (status.get("error") or "").lower()
    assert "abc123" not in (status.get("error") or "")
    assert status.get("failed_stage") == "exporting_model"
    assert status.get("duration_ms") is not None
    assert status.get("created_at")
    assert status.get("updated_at")

    r = client.get(f"/api/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["error_type"] == "connection"


def test_timeout_marks_job_failed():
    async def slow(_job_id: str):
        await asyncio.sleep(5)
        return {"ok": True}

    async def run_case():
        with patch.object(settings, "GENERATION_JOB_TIMEOUT_SECONDS", 0.05):
            job_id = jobs.submit(slow)
            await asyncio.sleep(0.3)
            return job_id

    job_id = asyncio.run(run_case())
    status = jobs.public_status(job_id)
    assert status is not None
    assert status["status"] == "failed"
    assert status["error_type"] == "timeout"
    assert status["retryable"] is True
    assert "timed out" in (status.get("safe_error_message") or "").lower()


def test_classify_timeout_exception():
    info = classify_exception(JobTimeoutError("x"), failed_stage="exporting_model")
    assert info["error_type"] == "timeout"
    assert info["retryable"] is True


def test_production_config_warnings():
    warnings = collect_production_warnings()
    codes = {w["code"] for w in warnings}
    assert "insecure_app_secret" in codes or settings.APP_SECRET not in (
        "dev-secret-change-me",
        "change-me-in-production",
    )


def test_system_status_includes_production_readiness():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    body = r.json()
    assert "production" in body
    prod = body["production"]
    assert "production_ready" in prod
    assert "deployment_ready" in prod
    assert "warnings" in prod
    assert "generation_timeout_seconds" in prod
    assert "database_backend" in prod
    assert prod["generation_timeout_seconds"] == settings.GENERATION_JOB_TIMEOUT_SECONDS


def test_cancel_unknown_job_404():
    r = client.post("/api/jobs/does-not-exist/cancel")
    assert r.status_code == 404


def test_production_readiness_flags_dev_secret():
    readiness = production_readiness()
    assert "using_dev_secret" in readiness
    assert "auth_jwt_required" in readiness
    assert isinstance(readiness["warning_count"], int)


def test_ensure_not_cancelled_raises():
    job_id = "cancel-check"
    jobs.update_job(job_id, stage="analyzing_site", status="running")
    jobs.cancel_job(job_id)
    try:
        jobs.ensure_not_cancelled(job_id)
        raised = False
    except JobCancelledError:
        raised = True
    assert raised

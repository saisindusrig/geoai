"""Observability: request IDs, structured logging, job diagnostics."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_includes_request_id_header():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID")
    assert len(r.headers["X-Request-ID"]) >= 8


def test_system_status_includes_observability_block():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    body = r.json()
    assert "observability" in body
    obs = body["observability"]
    assert obs["structured_request_logging"] is True
    assert obs["request_id_header"] == "X-Request-ID"
    assert "sentry_enabled" in obs


def test_error_response_includes_request_id():
    r = client.get("/api/jobs/not-a-real-job")
    assert r.status_code in (401, 404)
    assert r.headers.get("X-Request-ID")
    body = r.json()
    assert body.get("request_id") or (isinstance(body.get("detail"), dict) and body["detail"].get("request_id"))


def test_job_default_has_diagnostics_field():
    from app.services import jobs

    job_id = "diag-test-job"
    jobs.update_job(job_id, stage="queued")
    status = jobs.get_status(job_id)
    assert status is not None
    assert "diagnostics" in status


def test_build_generation_diagnostics():
    from app.services.generation_telemetry import build_generation_diagnostics

    diag = build_generation_diagnostics(
        {"llm_planning": 12.5, "glb_preview": 40.0},
        mode="fast_preview",
        provider="mock",
    )
    assert diag["generation_mode"] == "fast_preview"
    assert diag["provider"] == "mock"
    assert diag["llm_planning_ms"] == 12.5
    assert diag["glb_preview_ms"] == 40.0

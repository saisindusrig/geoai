"""Auth, project ownership, and job access control tests."""

import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.db.models import Project, User
from app.db.session import SessionLocal
from app.main import app
from app.services import jobs

client = TestClient(app)


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _ensure_user(db, user_id: int, email: str, name: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, name=name, email=email)
        db.add(user)
        db.commit()
    return user


def _create_project(owner_id: int, name: str = "Owned Project") -> int:
    r = client.post(
        "/api/projects",
        json={"name": name, "project_type": "flyover", "location_name": "Test"},
        headers=_auth(owner_id),
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_unauthenticated_rejected_when_jwt_required():
    with patch.object(settings, "AUTH_REQUIRE_JWT", True):
        r = client.get("/api/projects")
        assert r.status_code == 401


def test_dev_mock_user_when_jwt_not_required():
    with patch.object(settings, "AUTH_REQUIRE_JWT", False):
        r = client.get("/api/projects")
        assert r.status_code == 200


def test_user_cannot_access_other_users_project():
    db = SessionLocal()
    try:
        _ensure_user(db, 1, "one@test.com", "User One")
        _ensure_user(db, 2, "two@test.com", "User Two")
    finally:
        db.close()

    pid = _create_project(1, "Private Flyover")
    r = client.get(f"/api/projects/{pid}", headers=_auth(2))
    assert r.status_code == 404

    client.delete(f"/api/projects/{pid}", headers=_auth(1))


def test_user_cannot_generate_for_other_users_project():
    db = SessionLocal()
    try:
        _ensure_user(db, 1, "one@test.com", "User One")
        _ensure_user(db, 2, "two@test.com", "User Two")
    finally:
        db.close()

    pid = _create_project(1, "Gen Private")
    r = client.post(
        f"/api/projects/{pid}/design/generate",
        json={"scenario_name": "Hack", "parameters": {}, "generation_mode": "fast_preview"},
        headers=_auth(2),
    )
    assert r.status_code == 404

    client.delete(f"/api/projects/{pid}", headers=_auth(1))


def test_user_cannot_view_other_users_scenario_detail():
    db = SessionLocal()
    try:
        _ensure_user(db, 1, "one@test.com", "User One")
        _ensure_user(db, 2, "two@test.com", "User Two")
    finally:
        db.close()

    pid = _create_project(1, "Scenario Private")
    listed = client.get(f"/api/projects/{pid}/scenarios", headers=_auth(1)).json()
    summaries = listed.get("summaries") or listed.get("scenarios") or []
    if not summaries:
        gen = client.post(
            f"/api/projects/{pid}/design/generate",
            json={"scenario_name": "S1", "parameters": {}, "generation_mode": "fast_preview"},
            headers=_auth(1),
        )
        assert gen.status_code == 200
        listed = client.get(f"/api/projects/{pid}/scenarios", headers=_auth(1)).json()
        summaries = listed.get("summaries") or listed.get("scenarios") or []
    if summaries:
        sid = summaries[0]["scenario_id"]
        r = client.get(f"/api/projects/{pid}/scenarios/{sid}", headers=_auth(2))
        assert r.status_code == 404

    client.delete(f"/api/projects/{pid}", headers=_auth(1))


def test_user_cannot_compare_other_users_scenarios():
    db = SessionLocal()
    try:
        _ensure_user(db, 1, "one@test.com", "User One")
        _ensure_user(db, 2, "two@test.com", "User Two")
    finally:
        db.close()

    pid = _create_project(1, "Compare Private")
    listed = client.get(f"/api/projects/{pid}/scenarios", headers=_auth(1)).json()
    summaries = listed.get("summaries") or listed.get("scenarios") or []
    ids = [s["scenario_id"] for s in summaries[:2]]
    if len(ids) < 2:
        pytest.skip("Need at least two scenarios for compare ownership test")
    r = client.post(
        f"/api/projects/{pid}/scenarios/compare",
        json={"scenario_ids": ids},
        headers=_auth(2),
    )
    assert r.status_code == 404

    client.delete(f"/api/projects/{pid}", headers=_auth(1))


def test_user_cannot_cancel_other_users_job():
    db = SessionLocal()
    try:
        _ensure_user(db, 1, "one@test.com", "User One")
        _ensure_user(db, 2, "two@test.com", "User Two")
    finally:
        db.close()

    job_id = "owned-job-test"
    jobs.update_job(job_id, stage="running", status="running", user_id=1, project_id=999)

    r = client.post(f"/api/jobs/{job_id}/cancel", headers=_auth(2))
    assert r.status_code == 404

    r2 = client.post(f"/api/jobs/{job_id}/cancel", headers=_auth(1))
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"


def test_job_submit_stores_owner_context():
    async def noop(_job_id: str):
        await asyncio.sleep(0)
        return {"ok": True}

    async def run_case():
        return jobs.submit(noop, user_id=7, project_id=42)

    job_id = asyncio.run(run_case())
    status = jobs.get_status(job_id)
    assert status is not None
    assert status["user_id"] == 7
    assert status["project_id"] == 42


def test_register_login_and_me():
    import uuid

    email = f"phase7_user_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"name": "Phase 7", "email": email, "password": "securepass1"},
    )
    assert reg.status_code == 201
    assert reg.json()["user"]["role"] == "user"
    token = reg.json()["access_token"]

    login = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert login.status_code == 200

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_system_status_reflects_auth_state():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    prod = r.json()["production"]
    assert "auth_required" in prod
    assert "auth_ready" in prod
    assert "ownership_enforced" in prod
    assert "file_access_mode" in prod
    assert "deployment_ready" in prod

    with patch.object(settings, "AUTH_REQUIRE_JWT", True):
        with patch.object(settings, "ENVIRONMENT", "production"):
            from app.core.production import production_readiness

            readiness = production_readiness()
            assert readiness["auth_required"] is True
            assert readiness["ownership_enforced"] is True

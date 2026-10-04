"""Admin roles, rate/template protection, and audit logging tests."""

import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import ROLE_ADMIN, ROLE_USER, create_access_token
from app.db.models import AuditLog, User
from app.db.session import SessionLocal
from app.main import app
from app.services import jobs

client = TestClient(app)


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _ensure_user(user_id: int, email: str, name: str, role: str = ROLE_USER) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None:
            db.add(User(id=user_id, name=name, email=email, role=role))
        else:
            user.role = role
        db.commit()
    finally:
        db.close()


def test_new_users_default_to_role_user():
    email = "role_default@example.com"
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()
    r = client.post(
        "/api/auth/register",
        json={"name": "Role Test", "email": email, "password": "securepass1"},
    )
    assert r.status_code == 201
    assert r.json()["user"]["role"] == ROLE_USER


def test_normal_user_cannot_create_rate():
    _ensure_user(10, "user10@test.com", "User Ten", ROLE_USER)
    r = client.post(
        "/api/admin/rates",
        json={
            "region": "default",
            "item_code": "TEST-X",
            "item_name": "Test item",
            "unit": "m3",
            "rate": 100,
            "currency": "INR",
        },
        headers=_auth(10),
    )
    assert r.status_code == 403


def test_admin_can_create_update_delete_rate():
    _ensure_user(11, "admin11@test.com", "Admin Eleven", ROLE_ADMIN)
    headers = _auth(11)
    r = client.post(
        "/api/admin/rates",
        json={
            "region": "default",
            "item_code": "ADM-TEST",
            "item_name": "Admin test",
            "unit": "m3",
            "rate": 123,
            "currency": "INR",
        },
        headers=headers,
    )
    assert r.status_code == 201
    rate_id = r.json()["id"]

    r2 = client.put(
        f"/api/admin/rates/{rate_id}",
        json={
            "region": "default",
            "item_code": "ADM-TEST",
            "item_name": "Admin test",
            "unit": "m3",
            "rate": 456,
            "currency": "INR",
        },
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["rate"] == 456

    r3 = client.delete(f"/api/admin/rates/{rate_id}", headers=headers)
    assert r3.status_code == 204


def test_normal_user_can_read_rates():
    _ensure_user(12, "reader12@test.com", "Reader", ROLE_USER)
    r = client.get("/api/admin/rates", headers=_auth(12))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_normal_user_cannot_update_template():
    _ensure_user(13, "user13@test.com", "User 13", ROLE_USER)
    templates = client.get("/api/admin/templates", headers=_auth(13)).json()
    assert templates
    tid = templates[0]["id"]
    r = client.put(
        f"/api/admin/templates/{tid}",
        json={
            "project_type": templates[0]["project_type"],
            "name": templates[0]["name"],
            "default_parameters_json": templates[0]["default_parameters_json"],
        },
        headers=_auth(13),
    )
    assert r.status_code == 403


def test_dev_mock_user_is_admin_when_jwt_off():
    with patch.object(settings, "AUTH_REQUIRE_JWT", False):
        with patch.object(settings, "DEV_MOCK_USER_ROLE", "admin"):
            r = client.get("/api/auth/me")
            assert r.status_code == 200
            assert r.json()["role"] == ROLE_ADMIN


def test_audit_logged_on_login_and_register():
    import uuid

    db = SessionLocal()
    try:
        db.query(AuditLog).filter(AuditLog.action.in_(["auth.login", "auth.register"])).delete()
        db.commit()
    finally:
        db.close()

    email = f"audit_user_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"name": "Audit", "email": email, "password": "securepass1"},
    )
    assert reg.status_code == 201

    login = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert login.status_code == 200

    db = SessionLocal()
    try:
        actions = {row.action for row in db.query(AuditLog).all()}
        assert "auth.register" in actions
        assert "auth.login" in actions
    finally:
        db.close()


def test_audit_logged_on_rate_update():
    _ensure_user(14, "admin14@test.com", "Admin 14", ROLE_ADMIN)
    headers = _auth(14)
    created = client.post(
        "/api/admin/rates",
        json={
            "region": "default",
            "item_code": "AUDIT-R",
            "item_name": "Audit rate",
            "unit": "m3",
            "rate": 1,
            "currency": "INR",
        },
        headers=headers,
    ).json()
    client.put(
        f"/api/admin/rates/{created['id']}",
        json={**created, "rate": 2},
        headers=headers,
    )
    db = SessionLocal()
    try:
        assert db.query(AuditLog).filter(AuditLog.action == "rate.update").count() >= 1
    finally:
        db.close()
    client.delete(f"/api/admin/rates/{created['id']}", headers=headers)


def test_generation_started_and_cancel_audit():
    _ensure_user(15, "gen15@test.com", "Gen User", ROLE_USER)
    headers = _auth(15)
    project = client.post(
        "/api/projects",
        json={"name": "Audit Gen", "project_type": "flyover"},
        headers=headers,
    ).json()
    pid = project["id"]

    gen = client.post(
        f"/api/projects/{pid}/design/generate",
        json={"scenario_name": "Audit scenario", "parameters": {}, "generation_mode": "fast_preview"},
        headers=headers,
    )
    assert gen.status_code == 200
    job_id = gen.json()["job_id"]

    client.post(f"/api/jobs/{job_id}/cancel", headers=headers)

    db = SessionLocal()
    try:
        actions = {row.action for row in db.query(AuditLog).filter(AuditLog.project_id == pid).all()}
        assert "generation.started" in actions
        assert "generation.cancelled" in actions
    finally:
        db.close()

    client.delete(f"/api/projects/{pid}", headers=headers)


def test_normal_user_cannot_view_audit_logs():
    _ensure_user(16, "user16@test.com", "User 16", ROLE_USER)
    r = client.get("/api/admin/audit", headers=_auth(16))
    assert r.status_code == 403


def test_admin_can_view_audit_logs():
    _ensure_user(17, "admin17@test.com", "Admin 17", ROLE_ADMIN)
    r = client.get("/api/admin/audit", headers=_auth(17))
    assert r.status_code == 200
    body = r.json()
    assert "entries" in body
    assert isinstance(body["entries"], list)


def test_system_status_includes_roles_and_audit_flags():
    r = client.get("/api/system/status")
    prod = r.json()["production"]
    assert prod["roles_enabled"] is True
    assert prod["audit_enabled"] is True
    assert prod["admin_routes_protected"] is True


def test_job_owner_context_still_stored():
    async def noop(_job_id: str):
        await asyncio.sleep(0)
        return {"ok": True}

    async def run_case():
        return jobs.submit(noop, user_id=99, project_id=88)

    job_id = asyncio.run(run_case())
    status = jobs.get_status(job_id)
    assert status["user_id"] == 99
    assert status["project_id"] == 88

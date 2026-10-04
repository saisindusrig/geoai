"""Usage limits, rate limiting, and plan enforcement tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.plans import PLAN_FREE
from app.core.security import ROLE_ADMIN, ROLE_USER, create_access_token
from app.db.models import DesignScenario, Project, UsageEvent, User
from app.db.session import SessionLocal
from app.main import app

client = TestClient(app)


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _ensure_user(user_id: int, email: str, name: str, *, role: str = ROLE_USER, plan: str = PLAN_FREE) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None:
            db.add(User(id=user_id, name=name, email=email, role=role, plan=plan))
        else:
            user.role = role
            user.plan = plan
        db.commit()
    finally:
        db.close()


def _create_project(user_id: int, name: str = "Limit test project") -> int:
    db = SessionLocal()
    try:
        project = Project(user_id=user_id, name=name, project_type="building", status="draft")
        db.add(project)
        db.commit()
        db.refresh(project)
        return project.id
    finally:
        db.close()


def _count_usage(user_id: int, event_type: str) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(UsageEvent)
            .filter(UsageEvent.user_id == user_id, UsageEvent.event_type == event_type)
            .count()
        )
    finally:
        db.close()


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_free_user_project_limit():
    uid = 501
    _ensure_user(uid, "free501@test.com", "Free User", plan=PLAN_FREE)
    db = SessionLocal()
    try:
        db.query(Project).filter(Project.user_id == uid).delete()
        db.commit()
    finally:
        db.close()

    for i in range(3):
        r = client.post(
            "/api/projects",
            json={"name": f"P{i}", "project_type": "building"},
            headers=_auth(uid),
        )
        assert r.status_code == 201, r.text

    r = client.post(
        "/api/projects",
        json={"name": "P over limit", "project_type": "building"},
        headers=_auth(uid),
    )
    assert r.status_code == 429
    detail = r.json()["detail"]
    assert detail["code"] == "usage_limit_exceeded"
    assert detail["limit"] == "max_projects"
    assert detail["current"] == 3
    assert detail["max"] == 3
    assert "message" in detail


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_free_user_generation_daily_limit():
    uid = 502
    _ensure_user(uid, "free502@test.com", "Free Gen", plan=PLAN_FREE)
    project_id = _create_project(uid)

    db = SessionLocal()
    try:
        db.query(UsageEvent).filter(UsageEvent.user_id == uid).delete()
        db.commit()
        for _ in range(10):
            db.add(
                UsageEvent(
                    user_id=uid,
                    project_id=project_id,
                    event_type="generation.started",
                    units=1,
                )
            )
        db.commit()
    finally:
        db.close()

    r = client.post(
        f"/api/projects/{project_id}/design/generate",
        json={"scenario_name": "Over limit", "parameters": {}, "generation_mode": "fast_preview"},
        headers=_auth(uid),
    )
    assert r.status_code == 429
    detail = r.json()["detail"]
    assert detail["code"] == "usage_limit_exceeded"
    assert detail["limit"] == "max_generations_per_day"
    assert detail["reset_at"]


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_scenario_per_project_limit():
    uid = 503
    _ensure_user(uid, "free503@test.com", "Free Scenarios", plan=PLAN_FREE)
    project_id = _create_project(uid)

    db = SessionLocal()
    try:
        db.query(DesignScenario).filter(DesignScenario.project_id == project_id).delete()
        for i in range(10):
            db.add(DesignScenario(project_id=project_id, name=f"S{i}", status="pending"))
        db.commit()
    finally:
        db.close()

    r = client.post(
        f"/api/projects/{project_id}/design/generate",
        json={"scenario_name": "Eleventh", "parameters": {}, "generation_mode": "fast_preview"},
        headers=_auth(uid),
    )
    assert r.status_code == 429
    assert r.json()["detail"]["limit"] == "max_scenarios_per_project"


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_admin_bypasses_limits():
    uid = 504
    _ensure_user(uid, "admin504@test.com", "Admin User", role=ROLE_ADMIN, plan=PLAN_FREE)
    db = SessionLocal()
    try:
        db.query(Project).filter(Project.user_id == uid).delete()
        for i in range(5):
            db.add(Project(user_id=uid, name=f"Admin P{i}", project_type="building", status="draft"))
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/projects",
        json={"name": "Admin extra", "project_type": "building"},
        headers=_auth(uid),
    )
    assert r.status_code == 201


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_usage_event_recorded_on_project_create():
    uid = 505
    _ensure_user(uid, "free505@test.com", "Recorder", plan=PLAN_FREE)
    db = SessionLocal()
    try:
        db.query(Project).filter(Project.user_id == uid).delete()
        db.query(UsageEvent).filter(UsageEvent.user_id == uid).delete()
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/projects",
        json={"name": "Recorded", "project_type": "building"},
        headers=_auth(uid),
    )
    assert r.status_code == 201
    assert _count_usage(uid, "project.create") >= 1


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_usage_summary_endpoint():
    uid = 506
    _ensure_user(uid, "free506@test.com", "Summary User", plan=PLAN_FREE)
    r = client.get("/api/usage/summary", headers=_auth(uid))
    assert r.status_code == 200
    body = r.json()
    assert body["plan"] == PLAN_FREE
    assert "projects" in body
    assert "generations_today" in body
    assert "llm_plans_today" in body
    assert "exports_today" in body


@patch.object(settings, "RATE_LIMITING_ENABLED", True)
def test_login_rate_limit_returns_safe_message():
    with patch("app.services.rate_limit.check_rate_limit", return_value=(False, 21, 20)):
        r = client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "wrongpassword"},
        )
    assert r.status_code == 429
    detail = r.json()["detail"]
    assert detail["code"] == "rate_limit_exceeded"
    assert "Too many login attempts" in detail["message"]


def test_system_status_includes_usage_flags():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    prod = r.json()["production"]
    assert "usage_limits_enabled" in prod
    assert "rate_limiting_enabled" in prod
    assert "redis_rate_limit_backend" in prod


@patch.object(settings, "USAGE_LIMITS_ENABLED", True)
def test_admin_usage_query():
    admin_id = 507
    _ensure_user(admin_id, "admin507@test.com", "Admin Seven", role=ROLE_ADMIN, plan="admin")
    r = client.get("/api/admin/usage?limit=5", headers=_auth(admin_id))
    assert r.status_code == 200
    assert "entries" in r.json()

"""Backend smoke tests for GeoAI API."""

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_health():
    for path in ("/health", "/api/health"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_system_status():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    body = r.json()
    assert "database_type" in body
    assert "postgis_available" in body
    assert "survey_mode_available" in body
    assert "production" in body
    assert "production_ready" in body["production"]
    assert body["ai"]["active_provider"] in ("mock", "openai", "anthropic", "gemini", "ollama")
    assert "ollama" in body["ai"]


def test_demo_project():
    r = client.get("/api/projects/demo")
    assert r.status_code == 200
    body = r.json()
    assert "Demo" in body["name"] or body["project_type"] == "flyover"
    assert body.get("boundary_geojson") is not None


def test_project_validation_endpoint():
    demo = client.get("/api/projects/demo").json()
    pid = demo["id"]
    r = client.get(f"/api/projects/{pid}/validation")
    assert r.status_code == 200
    body = r.json()
    assert body["project_id"] == pid
    assert isinstance(body["checks"], list)
    assert len(body["checks"]) >= 5
    assert "disclaimer" in body


def test_report_pdf_does_not_crash():
    demo = client.get("/api/projects/demo").json()
    pid = demo["id"]
    r = client.get(f"/api/projects/{pid}/exports/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 500


def test_auth_token():
    r = client.post("/api/auth/token", json={"user_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body


def test_projects_crud():
    r = client.post(
        "/api/projects",
        json={"name": "Test Flyover", "project_type": "flyover", "location_name": "Test"},
    )
    assert r.status_code == 201
    project = r.json()
    pid = project["id"]

    r2 = client.get(f"/api/projects/{pid}")
    assert r2.status_code == 200

    r3 = client.get("/api/projects/summaries")
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)

    client.delete(f"/api/projects/{pid}")


def test_site_suggestions():
    r = client.post(
        "/api/projects",
        json={
            "name": "Suggest Test",
            "project_type": "building",
            "center_lat": 12.97,
            "center_lng": 77.59,
        },
    )
    pid = r.json()["id"]
    sr = client.post(f"/api/projects/{pid}/site-suggestions", json={"lng": 77.59, "lat": 12.97})
    assert sr.status_code == 200
    assert len(sr.json()["suggestions"]) > 0
    client.delete(f"/api/projects/{pid}")


def test_ai_chat_stream():
    r = client.post(
        "/api/projects",
        json={"name": "AI Test", "project_type": "flyover"},
    )
    pid = r.json()["id"]
    sr = client.post(f"/api/projects/{pid}/ai/chat/stream", json={"message": "4 lanes"})
    assert sr.status_code == 200
    assert "data:" in sr.text
    assert '"actions"' in sr.text
    client.delete(f"/api/projects/{pid}")


def test_jwt_auth_header():
    token = create_access_token(1)
    r = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

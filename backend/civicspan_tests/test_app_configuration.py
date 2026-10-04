"""Regression checks for the lean API entry point."""
from fastapi.testclient import TestClient
from civicspan_app import app
from app.core.config import settings


def test_lean_api_includes_auth_routes():
    paths = app.openapi()["paths"]
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths


def test_lean_api_allows_configured_frontend_origin(monkeypatch):
    monkeypatch.setattr(settings, "NEXT_PUBLIC_APP_URL", "https://app.example.com")
    # Reload to rebuild the middleware from the current settings.
    import importlib
    import civicspan_app
    configured_app = importlib.reload(civicspan_app).app
    response = TestClient(configured_app).options(
        "/api/projects",
        headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"

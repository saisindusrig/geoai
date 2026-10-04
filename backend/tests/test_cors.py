"""CORS origin helpers."""

from app.core.cors import build_cors_origin_regex, build_cors_origins


def test_build_cors_origins_includes_app_url(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "NEXT_PUBLIC_APP_URL", "https://app.example.com")
    monkeypatch.setattr(config.settings, "CORS_ALLOWED_ORIGINS", "https://staging.example.com")

    origins = build_cors_origins()
    assert "https://app.example.com" in origins
    assert "https://staging.example.com" in origins
    assert "http://localhost:3000" in origins


def test_netlify_origin_regex_matches_deploy_urls():
    import re

    pattern = build_cors_origin_regex()
    assert pattern is not None
    compiled = re.compile(pattern)
    assert compiled.fullmatch("https://flourishing-mochi-432285.netlify.app")
    assert compiled.fullmatch("https://deploy-preview-42--flourishing-mochi-432285.netlify.app")


def test_cors_preflight_for_netlify_origin():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "https://flourishing-mochi-432285.netlify.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == (
        "https://flourishing-mochi-432285.netlify.app"
    )

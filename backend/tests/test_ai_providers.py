"""Tests for Ollama provider, copilot response shape, and AI_PROVIDER selection."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.ai import providers
from app.services.ai.ollama_client import OllamaError, chat_completion, check_ollama_available

client = TestClient(app)


def test_ollama_unavailable_handling():
    with patch("app.services.ai.ollama_client.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        status = asyncio.run(check_ollama_available())
        assert status["available"] is False
        assert status["configured_model_ready"] is False


def test_ollama_chat_connect_error():
    with patch("app.services.ai.ollama_client.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(OllamaError, match="Cannot connect"):
            asyncio.run(chat_completion("system", "user"))


def test_ai_chat_response_shape():
    r = client.post(
        "/api/projects",
        json={"name": "Copilot Shape Test", "project_type": "flyover"},
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    with patch(
        "app.services.ai.providers.chat_completion",
        new=AsyncMock(
            return_value=(
                json.dumps(
                    {
                        "message": "Try 4 lanes with wider deck.",
                        "actions": [{"type": "update_parameters", "payload": {"lanes": 4}}],
                        "warnings": ["Preliminary only."],
                    }
                ),
                "ollama",
            )
        ),
    ):
        sr = client.post(f"/api/projects/{pid}/ai/chat", json={"message": "make 4 lanes"})
        assert sr.status_code == 200
        body = sr.json()
        assert "message" in body
        assert isinstance(body["actions"], list)
        assert body["actions"][0]["type"] == "update_parameters"
        assert isinstance(body["warnings"], list)
        assert "disclaimer" in body
        assert body["provider"] == "ollama"
        assert body["reply"] == body["message"]

    client.delete(f"/api/projects/{pid}")


def test_ai_chat_stream_response_shape():
    r = client.post(
        "/api/projects",
        json={"name": "Copilot Stream Test", "project_type": "flyover"},
    )
    pid = r.json()["id"]

    with patch(
        "app.services.ai.providers.chat_completion",
        new=AsyncMock(
            return_value=(
                json.dumps({"message": "Hello", "actions": [], "warnings": []}),
                "mock",
            )
        ),
    ):
        sr = client.post(f"/api/projects/{pid}/ai/chat/stream", json={"message": "hi"})
        assert sr.status_code == 200
        assert "data:" in sr.text
        assert '"done": true' in sr.text or '"done":true' in sr.text
        assert '"actions"' in sr.text

    client.delete(f"/api/projects/{pid}")


def test_copilot_fallback_when_llm_fails():
    r = client.post(
        "/api/projects",
        json={"name": "Fallback Test", "project_type": "flyover"},
    )
    pid = r.json()["id"]

    with patch(
        "app.services.ai.providers.chat_completion",
        new=AsyncMock(side_effect=RuntimeError("no provider")),
    ):
        sr = client.post(f"/api/projects/{pid}/ai/chat", json={"message": "4 lanes please"})
        assert sr.status_code == 200
        body = sr.json()
        assert body["provider"] == "fallback"
        assert "message" in body
        assert isinstance(body["actions"], list)

    client.delete(f"/api/projects/{pid}")


def test_system_status_includes_ollama():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    body = r.json()
    assert "ollama" in body["ai"]
    ollama = body["ai"]["ollama"]
    assert "available" in ollama
    assert "model" in ollama
    assert "base_url" in ollama
    assert body["ai"]["active_provider"] in ("mock", "openai", "anthropic", "ollama", "gemini")


def test_ai_provider_chain_respects_mock():
    with patch.object(settings, "AI_PROVIDER", "mock"):
        with patch.object(settings, "OPENAI_API_KEY", "sk-test"):
            chain = providers._provider_chain()
            assert chain == []


def test_ai_provider_chain_ollama_primary():
    with patch.object(settings, "AI_PROVIDER", "ollama"):
        with patch.object(settings, "OPENAI_API_KEY", ""):
            chain = providers._provider_chain()
            assert chain[0] == "ollama"


def test_generate_design_json_falls_back_to_mock():
    async def _run():
        with patch.object(settings, "AI_PROVIDER", "ollama"):
            with patch(
                "app.services.ai.providers._ollama_generate_json",
                new=AsyncMock(side_effect=OllamaError("down")),
            ):
                with patch.object(settings, "OPENAI_API_KEY", ""):
                    with patch.object(settings, "ANTHROPIC_API_KEY", ""):
                        return await providers.generate_design_json(
                            "system", "user", "flyover", {"length_m": 400}
                        )

    design, name = asyncio.run(_run())
    assert name == "mock"
    assert design["project_type"] == "flyover"

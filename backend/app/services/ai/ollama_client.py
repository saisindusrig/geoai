"""Ollama local LLM client (httpx async, non-streaming)."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


def ollama_base_url() -> str:
    return settings.OLLAMA_BASE_URL.rstrip("/")


async def check_ollama_available() -> dict[str, Any]:
    """Probe Ollama /api/tags. Returns availability + installed model names."""
    url = f"{ollama_base_url()}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        configured = settings.OLLAMA_MODEL
        model_ready = any(
            m == configured or m.startswith(f"{configured}:")
            for m in models
        )
        return {
            "available": True,
            "models": models,
            "configured_model": configured,
            "configured_model_ready": model_ready,
        }
    except Exception as exc:
        logger.debug("Ollama unavailable at %s: %s", url, exc)
        return {
            "available": False,
            "models": [],
            "configured_model": settings.OLLAMA_MODEL,
            "configured_model_ready": False,
            "error": str(exc),
        }


async def chat_completion(
    system: str,
    user: str,
    *,
    json_mode: bool = False,
) -> str:
    """Call Ollama /api/chat (stream=false). Returns assistant message content."""
    url = f"{ollama_base_url()}/api/chat"
    payload: dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    if json_mode:
        payload["format"] = "json"

    timeout = httpx.Timeout(settings.OLLAMA_TIMEOUT_SECONDS)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            body = resp.json()
    except httpx.ConnectError as exc:
        raise OllamaError(
            f"Cannot connect to Ollama at {ollama_base_url()}. "
            "Start Ollama and run: ollama pull " + settings.OLLAMA_MODEL
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaError(f"Ollama HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
    except Exception as exc:
        raise OllamaError(str(exc)) from exc

    message = body.get("message") or {}
    content = message.get("content")
    if not content or not isinstance(content, str):
        raise OllamaError("Ollama returned empty assistant content")
    return content


def parse_json_from_text(text: str) -> dict:
    """Extract JSON object from model output (handles markdown fences)."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        stripped = "\n".join(lines[start:end]).strip()
    start, end = stripped.find("{"), stripped.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(stripped[start:end])

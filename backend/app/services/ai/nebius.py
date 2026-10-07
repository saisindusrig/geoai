"""Server-only Token Factory client; never silently substitutes a mock response."""
import json

import httpx

from app.core.config import settings


class NebiusError(ValueError):
    pass


async def completion(system: str, user: str, *, json_mode: bool = True) -> str:
    if not settings.NEBIUS_API_KEY or not settings.NEBIUS_CHAT_MODEL:
        raise NebiusError("Configure NEBIUS_API_KEY and NEBIUS_CHAT_MODEL on the backend to use the building assistant.")
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                settings.NEBIUS_TOKEN_FACTORY_BASE_URL.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.NEBIUS_API_KEY}"},
                json={
                    "model": settings.NEBIUS_CHAT_MODEL,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.2,
                    "max_tokens": 12000,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                },
            )
            response.raise_for_status()
            choice = response.json()["choices"][0]
            if choice.get("finish_reason") == "length":
                raise NebiusError("The AI plan exceeded the response limit. Request a smaller building or fewer rooms.")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise NebiusError("Nebius returned an empty response. Please retry.")
            return content
    except httpx.TimeoutException as exc:
        raise NebiusError("Nebius timed out. Your model is unchanged; please retry.") from exc
    except httpx.HTTPStatusError as exc:
        raise NebiusError(f"Nebius returned HTTP {exc.response.status_code}. Check the backend model, endpoint, and API credentials.") from exc
    except (httpx.RequestError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise NebiusError("Nebius is unavailable or returned an invalid response. Please retry.") from exc


async def generate_json(system: str, user: str) -> dict:
    try:
        value = json.loads(await completion(system, user))
        if not isinstance(value, dict):
            raise NebiusError("Nebius returned invalid JSON. A building object is required.")
        return value
    except (json.JSONDecodeError, TypeError) as exc:
        raise NebiusError("Nebius returned invalid JSON. Please revise the request and retry.") from exc

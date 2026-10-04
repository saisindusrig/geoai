"""CORS origin configuration for API ↔ frontend (local, Netlify, custom domains)."""

from __future__ import annotations

from app.core.config import settings

_LOCAL_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

# Netlify production + preview deploys (e.g. flourishing-mochi-432285.netlify.app).
_NETLIFY_ORIGIN_REGEX = r"https://[\w-]+(?:--[\w-]+)?\.netlify\.app"


def build_cors_origins() -> list[str]:
    origins: set[str] = set(_LOCAL_ORIGINS)
    if settings.NEXT_PUBLIC_APP_URL:
        origins.add(settings.NEXT_PUBLIC_APP_URL.rstrip("/"))
    for raw in settings.CORS_ALLOWED_ORIGINS.split(","):
        value = raw.strip().rstrip("/")
        if value:
            origins.add(value)
    return sorted(origins)


def build_cors_origin_regex() -> str | None:
    if settings.CORS_ALLOW_NETLIFY:
        return _NETLIFY_ORIGIN_REGEX
    return None

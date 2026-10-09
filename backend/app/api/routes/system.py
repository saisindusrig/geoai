"""System / infrastructure status for admin and settings UI."""

from fastapi import APIRouter

from app.core.config import settings
from app.core.disclaimer import DISCLAIMER
from app.core.request_context import REQUEST_ID_HEADER
from app.core.sentry import sentry_enabled
from app.db.session import IS_POSTGRES
from app.services import jobs, storage
from app.services.ai.ollama_client import check_ollama_available
from app.services.ai.providers import normalize_ai_provider
from app.core.production import production_readiness

router = APIRouter(prefix="/api/system", tags=["system"])


def _redis_available() -> bool:
    return jobs._get_redis() is not None


def _storage_mode() -> str:
    return "s3" if storage._get_s3() is not None else "local"


async def _ai_provider_status() -> dict:
    configured = normalize_ai_provider()
    ollama = await check_ollama_available()

    # Active = configured primary when reachable, else first fallback
    if configured == "nebius":
        active = "nebius" if settings.NEBIUS_API_KEY else "unavailable"
    elif configured == "auto" and settings.NEBIUS_API_KEY:
        active = "nebius"
    elif configured == "ollama" and ollama["available"]:
        active = "ollama"
    elif configured == "openai" and settings.OPENAI_API_KEY:
        active = "openai"
    elif configured == "anthropic" and settings.ANTHROPIC_API_KEY:
        active = "anthropic"
    elif settings.OPENAI_API_KEY:
        active = "openai"
    elif settings.ANTHROPIC_API_KEY:
        active = "anthropic"
    elif ollama["available"]:
        active = "ollama"
    else:
        active = "mock"

    return {
        "configured_provider": configured,
        "active_provider": active,
        "mock_mode": active == "mock",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "nebius_configured": bool(settings.NEBIUS_API_KEY),
        "nebius_model": settings.NEBIUS_CHAT_MODEL,
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "gemini_implemented": False,
        "ollama": {
            "primary": configured == "ollama",
            "base_url": settings.OLLAMA_BASE_URL,
            "model": settings.OLLAMA_MODEL,
            "available": ollama["available"],
            "model_ready": ollama.get("configured_model_ready", False),
            "installed_models": ollama.get("models", []),
        },
    }


def _map_provider_status() -> dict:
    return {
        "google_maps_configured": bool(settings.GOOGLE_MAPS_API_KEY),
        "mapbox_configured": bool(settings.MAPBOX_TOKEN),
        "cesium_ion_configured": bool(settings.CESIUM_ION_READ_TOKEN),
        "osm_fallback": True,
    }


@router.get("/status")
async def system_status():
    from app.core.infrastructure import dependency_status
    dependencies = dependency_status()
    postgis = dependencies["database"]["postgis"]
    ai = await _ai_provider_status()
    ai["assistant"] = dependencies["ai"]
    return {
        "database_type": dependencies["database"]["backend"],
        "dependencies": dependencies,
        "postgis_available": postgis,
        "database_mode_label": "Full survey mode (PostGIS)" if postgis else "Limited GIS mode (SQLite)" if dependencies["database"]["backend"]=="sqlite" else "PostGIS unavailable",
        "redis_available": dependencies["redis"]["status"]=="AVAILABLE",
        "job_store": "redis" if dependencies["redis"]["status"]=="AVAILABLE" else "in_memory",
        "storage_mode": dependencies["storage"]["mode"],
        "survey_mode_available": postgis,
        "ai": ai,
        "maps": _map_provider_status(),
        "observability": {
            "structured_request_logging": True,
            "request_id_header": REQUEST_ID_HEADER,
            "sentry_enabled": sentry_enabled(),
            "sentry_configured": bool(settings.SENTRY_DSN),
        },
        "production": production_readiness(dependencies),
        "disclaimer": DISCLAIMER,
    }

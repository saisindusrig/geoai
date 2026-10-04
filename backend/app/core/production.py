"""Production readiness checks and safe status flags."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.sentry import sentry_enabled
from app.db.session import IS_POSTGRES
from app.services import jobs, storage
from app.services.rate_limit import rate_limit_backend_available

logger = logging.getLogger(__name__)

DEV_SECRETS = frozenset({"dev-secret-change-me", "change-me-in-production"})


def _warning(code: str, message: str, *, severity: str = "warning") -> dict:
    return {"code": code, "message": message, "severity": severity}


def _is_production() -> bool:
    return settings.ENVIRONMENT.lower() in ("production", "prod")


def file_access_mode() -> str:
    if storage._get_s3() is not None:
        return "s3_presigned"
    if settings.AUTH_REQUIRE_JWT:
        return "local_authenticated"
    return "local_public"


def collect_production_warnings() -> list[dict]:
    """Non-fatal warnings for dev/prod misconfiguration."""
    warnings: list[dict] = []
    is_prod = _is_production()

    if settings.APP_SECRET in DEV_SECRETS:
        warnings.append(
            _warning(
                "insecure_app_secret",
                "APP_SECRET is still a development default — set a strong secret in production.",
                severity="critical" if is_prod else "warning",
            )
        )

    if is_prod and not settings.AUTH_REQUIRE_JWT:
        warnings.append(
            _warning(
                "auth_jwt_not_required",
                "AUTH_REQUIRE_JWT must be true in production.",
                severity="critical",
            )
        )

    if is_prod and not IS_POSTGRES:
        warnings.append(
            _warning(
                "sqlite_in_production",
                "SQLite fallback is active — use PostgreSQL/PostGIS in production.",
                severity="critical",
            )
        )

    if not jobs._get_redis():
        warnings.append(
            _warning(
                "redis_unavailable",
                "Redis is unavailable — jobs run in-memory and will not survive restarts.",
                severity="warning" if not is_prod else "critical",
            )
        )

    if storage._get_s3() is None:
        warnings.append(
            _warning(
                "local_storage",
                "Object storage uses local filesystem — configure S3/MinIO for production.",
                severity="warning" if not is_prod else "critical",
            )
        )

    if not settings.GOOGLE_MAPS_API_KEY and not settings.MAPBOX_TOKEN:
        warnings.append(
            _warning(
                "map_tokens_missing",
                "No Google Maps or Mapbox token configured — map tiles may use OSM fallback only.",
            )
        )

    if not settings.CESIUM_ION_TOKEN:
        warnings.append(
            _warning(
                "cesium_ion_missing",
                "CESIUM_ION_TOKEN is not set — Cesium world terrain/imagery may be limited.",
            )
        )

    return warnings


def production_readiness() -> dict:
    warnings = collect_production_warnings()
    critical = [w for w in warnings if w.get("severity") == "critical"]
    auth_required = settings.AUTH_REQUIRE_JWT
    ownership_enforced = auth_required
    auth_ready = auth_required or not _is_production()
    deployment_ready = len(critical) == 0 and auth_ready
    return {
        "environment": settings.ENVIRONMENT,
        "auth_required": auth_required,
        "auth_jwt_required": auth_required,
        "auth_ready": auth_ready,
        "ownership_enforced": ownership_enforced,
        "roles_enabled": True,
        "audit_enabled": True,
        "admin_routes_protected": True,
        "usage_limits_enabled": settings.USAGE_LIMITS_ENABLED,
        "rate_limiting_enabled": settings.RATE_LIMITING_ENABLED,
        "redis_rate_limit_backend": rate_limit_backend_available(),
        "use_arq_worker": settings.USE_ARQ_WORKER,
        "database_backend": "postgresql" if IS_POSTGRES else "sqlite",
        "migrations": "alembic",
        "sentry_enabled": sentry_enabled(),
        "sentry_configured": bool(settings.SENTRY_DSN),
        "file_access_mode": file_access_mode(),
        "using_dev_secret": settings.APP_SECRET in DEV_SECRETS,
        "generation_timeout_seconds": settings.GENERATION_JOB_TIMEOUT_SECONDS,
        "warnings": warnings,
        "warning_count": len(warnings),
        "critical_count": len(critical),
        "production_ready": len(critical) == 0,
        "deployment_ready": deployment_ready,
    }


def log_startup_warnings() -> None:
    for w in collect_production_warnings():
        msg = f"[production] {w['code']}: {w['message']}"
        if w.get("severity") == "critical":
            logger.warning(msg)
        else:
            logger.info(msg)

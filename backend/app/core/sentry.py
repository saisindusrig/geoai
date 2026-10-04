"""Optional Sentry initialization — no-op when SENTRY_DSN is unset."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
_initialized = False


def init_sentry() -> bool:
    global _initialized
    if _initialized or not settings.SENTRY_DSN:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning("sentry-sdk not installed — skipping Sentry initialization")
        return False

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
    )
    _initialized = True
    logger.info("Sentry initialized for environment=%s", settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT)
    return True


def sentry_enabled() -> bool:
    return bool(settings.SENTRY_DSN) and _initialized

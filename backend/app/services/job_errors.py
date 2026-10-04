"""Safe job error classification for API responses."""

from __future__ import annotations

import asyncio

RETRYABLE_TYPES = frozenset({"timeout", "connection", "rate_limit", "provider", "unknown"})


class JobCancelledError(Exception):
    """Raised when a job is cancelled between pipeline stages."""


class JobTimeoutError(Exception):
    """Raised when generation exceeds GENERATION_JOB_TIMEOUT_SECONDS."""


def classify_exception(exc: Exception, *, failed_stage: str | None = None) -> dict:
    """Return error_type, safe_error_message, retryable — never expose secrets or stack traces."""
    if isinstance(exc, JobCancelledError):
        return {
            "error_type": "cancelled",
            "safe_error_message": "Generation was cancelled.",
            "retryable": False,
            "failed_stage": failed_stage or "cancelled",
        }
    if isinstance(exc, (JobTimeoutError, asyncio.TimeoutError)):
        return {
            "error_type": "timeout",
            "safe_error_message": "Generation timed out. Try again with Fast Preview or fewer parameters.",
            "retryable": True,
            "failed_stage": failed_stage or "timeout",
        }

    msg = str(exc).lower()
    error_type = "unknown"
    retryable = True
    safe = "Design generation failed. Please try again or adjust parameters."

    if "connection" in msg or "connect" in msg or "unreachable" in msg:
        error_type = "connection"
        safe = "A network or service connection failed. Check AI/storage services and retry."
    elif "rate" in msg and "limit" in msg:
        error_type = "rate_limit"
        safe = "The AI provider rate limit was reached. Wait a moment and retry."
    elif "validation" in msg or "invalid" in msg:
        error_type = "validation"
        retryable = False
        safe = "Generation parameters or site data were invalid. Review inputs and retry."
    elif "unsupported" in msg:
        error_type = "configuration"
        retryable = False
        safe = "This generation mode or project type is not supported."
    elif "not found" in msg:
        error_type = "not_found"
        retryable = False
        safe = "Required project or scenario data was not found."
    elif "permission" in msg or "unauthorized" in msg:
        error_type = "auth"
        retryable = False
        safe = "Generation was blocked by an authorization check."

    if error_type not in RETRYABLE_TYPES:
        retryable = error_type in RETRYABLE_TYPES

    return {
        "error_type": error_type,
        "safe_error_message": safe,
        "retryable": retryable,
        "failed_stage": failed_stage or "failed",
    }

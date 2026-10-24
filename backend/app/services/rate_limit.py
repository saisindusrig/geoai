"""Lightweight per-key rate limiting with Redis or in-memory fallback."""

from __future__ import annotations

import logging
import time
import hashlib
import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.core.config import settings
from app.db.session import SessionLocal
from app.services import jobs
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)

_memory_buckets: dict[str, tuple[int, float]] = {}


@dataclass(frozen=True)
class RateLimitRule:
    key_prefix: str
    max_calls: int
    window_seconds: int
    message: str


RATE_RULES = {
    "building.plan": RateLimitRule("rl:building-plan", 6, 60, "Too many building planning requests. Please wait a moment."),
    "auth.login": RateLimitRule("rl:login", 20, 60, "Too many login attempts. Please wait and try again."),
    "auth.login_account": RateLimitRule("rl:login-account", 10, 60, "Too many sign-in attempts. Please wait and try again."),
    "auth.register": RateLimitRule("rl:register", 10, 3600, "Too many registration attempts. Please try again later."),
    "generation.start": RateLimitRule("rl:gen", 10, 60, "Too many generation requests. Please wait a moment."),
    "file.download": RateLimitRule("rl:file", 60, 60, "Too many file download requests. Please slow down."),
}


def _redis_incr(key: str, window_seconds: int) -> int:
    r = jobs._get_redis()
    if r is None:
        return -1
    pipe = r.pipeline()
    pipe.incr(key)
    # Fixed window: rejected requests must not perpetually extend cooldown.
    pipe.expire(key, window_seconds, nx=True)
    results = pipe.execute()
    return int(results[0])


def _memory_incr(key: str, window_seconds: int) -> int:
    now = time.time()
    count, expires = _memory_buckets.get(key, (0, 0.0))
    if now >= expires:
        count = 0
        expires = now + window_seconds
    count += 1
    _memory_buckets[key] = (count, expires)
    return count


def rate_limit_backend_available() -> bool:
    return jobs._get_redis() is not None


def check_rate_limit(scope: str, *, user_id: int | None = None, ip: str | None = None, subject: str | None = None) -> tuple[bool, int, int]:
    """Return (allowed, current_count, max_calls)."""
    if not settings.RATE_LIMITING_ENABLED:
        return True, 0, 0
    rule = RATE_RULES.get(scope)
    if rule is None:
        return True, 0, 0

    parts = [rule.key_prefix]
    if user_id is not None:
        parts.append(f"u:{user_id}")
    if ip:
        parts.append(f"ip:{ip}")
    if subject:
        parts.append(f"subject:{subject}")
    key = ":".join(parts)

    count = _redis_incr(key, rule.window_seconds)
    if count < 0:
        if settings.ENVIRONMENT.lower() in ('production', 'prod'):
            raise HTTPException(503, 'Shared rate-limit service unavailable; request refused')
        count = _memory_incr(key, rule.window_seconds)

    return count <= rule.max_calls, count, rule.max_calls


def enforce_login_account_limit(email: str) -> None:
    # Independent of source IP and identical for known/unknown accounts.
    # Neither raw email nor an unsalted email digest enters Redis keys.
    subject = hmac.new(settings.APP_SECRET.encode(), email.strip().lower().encode(), hashlib.sha256).hexdigest()
    allowed, _, _ = check_rate_limit("auth.login_account", subject=subject)
    if not allowed:
        raise HTTPException(429, "Too many sign-in attempts. Please wait and try again.", headers={"Retry-After": "60"})


def enforce_rate_limit(
    scope: str,
    *,
    user_id: int | None = None,
    request: Request | None = None,
) -> None:
    ip = None
    if request and request.client:
        # Proxy normalization belongs to the ASGI server trusted-proxy policy.
        # Raw client-supplied forwarding headers must not create new buckets.
        ip = request.client.host

    allowed, current, maximum = check_rate_limit(scope, user_id=user_id, ip=ip)
    if allowed:
        return

    rule = RATE_RULES[scope]
    try:
        audit_db = SessionLocal()
        try:
            log_audit_event(
                audit_db,
                user_id=user_id,
                action="rate.limit_exceeded",
                entity_type="rate_limit",
                metadata={"scope": scope, "current": current, "max": maximum},
                request=request,
            )
        finally:
            audit_db.close()
    except Exception:
        logger.exception("Failed to audit rate limit exceeded")

    raise HTTPException(
        status_code=429,
        detail={
            "code": "rate_limit_exceeded",
            "scope": scope,
            "current": current,
            "max": maximum,
            "message": rule.message,
        },
    )

"""Structured HTTP request logging middleware."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import REQUEST_ID_HEADER, generate_request_id, path_context, request_id_var
from app.core.security import decode_token

logger = logging.getLogger("geoai.request")


def _optional_user_id(request: Request) -> int | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


def _safe_error_type(response: Response) -> str | None:
    if response.status_code < 400:
        return None
    if response.status_code == 401:
        return "unauthorized"
    if response.status_code == 403:
        return "forbidden"
    if response.status_code == 404:
        return "not_found"
    if response.status_code == 422:
        return "validation_error"
    if response.status_code == 429:
        return "rate_or_usage_limit"
    if response.status_code >= 500:
        return "server_error"
    return "client_error"


def _log_event(level: int, payload: dict[str, Any]) -> None:
    logger.log(level, json.dumps(payload, default=str))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or generate_request_id()
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        user_id = _optional_user_id(request)
        ctx = path_context(request.url.path)
        status_code = 500
        error_type: str | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_type = _safe_error_type(response)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except Exception:
            error_type = "unhandled_exception"
            logger.exception("Unhandled exception request_id=%s path=%s", request_id, request.url.path)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            payload: dict[str, Any] = {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": status_code,
                "duration_ms": duration_ms,
            }
            if user_id is not None:
                payload["user_id"] = user_id
            payload.update(ctx)
            if error_type:
                payload["error_type"] = error_type
            level = logging.WARNING if status_code >= 400 else logging.INFO
            _log_event(level, payload)
            request_id_var.reset(token)

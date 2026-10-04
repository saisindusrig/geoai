"""Global exception handlers with safe client payloads."""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.request_context import REQUEST_ID_HEADER, get_request_id

logger = logging.getLogger(__name__)


def _with_request_id(content: dict) -> dict:
    rid = get_request_id()
    if rid:
        content["request_id"] = rid
    return content


def _response(status_code: int, content: dict) -> JSONResponse:
    rid = get_request_id()
    headers = {REQUEST_ID_HEADER: rid} if rid else None
    return JSONResponse(status_code=status_code, content=_with_request_id(content), headers=headers)


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        content = {"detail": detail}
    else:
        content = {"detail": {"message": str(detail)}}
    return _response(exc.status_code, content)


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return _response(
        422,
        {
            "detail": {
                "code": "validation_error",
                "message": "Request validation failed",
                # Custom validators can attach exception objects to ctx.
                # Return actionable fields without echoing raw inputs.
                "errors": [{"type": error["type"], "loc": error["loc"], "msg": error["msg"]} for error in exc.errors()],
            }
        },
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error request_id=%s", get_request_id())
    return _response(
        500,
        {
            "detail": {
                "code": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            }
        },
    )

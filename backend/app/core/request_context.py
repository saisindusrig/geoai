"""Request correlation ID and path context helpers."""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_PROJECT_RE = re.compile(r"/api/projects/(\d+)")
_JOB_RE = re.compile(r"/api/jobs/([^/]+)")


def generate_request_id() -> str:
    return uuid.uuid4().hex


def get_request_id() -> str:
    return request_id_var.get() or ""


def set_request_id(value: str) -> None:
    request_id_var.set(value)


def path_context(path: str) -> dict[str, str | int]:
    ctx: dict[str, str | int] = {}
    project = _PROJECT_RE.search(path)
    if project:
        ctx["project_id"] = int(project.group(1))
    job = _JOB_RE.search(path)
    if job:
        ctx["job_id"] = job.group(1)
    return ctx

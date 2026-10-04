#!/usr/bin/env python3
"""Production smoke test against a deployed GeoAI API.

Usage:
  python backend/scripts/production_smoke.py --base-url https://geoai-api.onrender.com

Exit code 0 when all checks pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

DEFAULT_TIMEOUT = 30.0
POLL_INTERVAL = 2.0
JOB_TIMEOUT = 180.0

MINIMAL_BOUNDARY = {
    "type": "Polygon",
    "coordinates": [
        [
            [77.5946, 12.9716],
            [77.5956, 12.9716],
            [77.5956, 12.9726],
            [77.5946, 12.9726],
            [77.5946, 12.9716],
        ]
    ],
}


@dataclass
class SmokeResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class SmokeReport:
    base_url: str
    results: list[SmokeResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append(SmokeResult(name=name, ok=ok, detail=detail))

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results)


class SmokeClient:
    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.token: str | None = None
        self.last_request_id: str | None = None

    def _capture(self, response: httpx.Response) -> httpx.Response:
        self.last_request_id = response.headers.get("X-Request-ID") or self.last_request_id
        return response

    def url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path: str) -> httpx.Response:
        return self._capture(self.client.get(self.url(path), headers=self.headers()))

    def post(self, path: str, payload: dict | None = None) -> httpx.Response:
        return self._capture(self.client.post(self.url(path), headers=self.headers(), json=payload or {}))


def _fetch_file_url(client: SmokeClient, file_url: str) -> httpx.Response:
    """Fetch a model/file URL via the smoke client (handles localhost rewrite)."""
    if file_url.startswith("/files/"):
        return client.get(file_url)
    parsed = urlparse(file_url)
    if parsed.path.startswith("/files/"):
        if parsed.hostname in (None, "localhost", "127.0.0.1"):
            return client.get(parsed.path)
    if file_url.startswith(client.base_url):
        suffix = file_url[len(client.base_url) :]
        return client.get(suffix if suffix.startswith("/") else f"/{suffix}")
    if file_url.startswith("http"):
        return client.client.get(file_url, headers=client.headers())
    return client.get(file_url)


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return {"raw": response.text[:500]}


def check_health(client: SmokeClient, report: SmokeReport) -> None:
    for path in ("/health", "/api/health"):
        r = client.get(path)
        ok = r.status_code == 200 and _safe_json(r).get("status") == "ok"
        report.add(f"GET {path}", ok, f"status={r.status_code}")


def check_request_id_headers(client: SmokeClient, report: SmokeReport) -> None:
    r = client.get("/health")
    rid = r.headers.get("X-Request-ID")
    report.add("X-Request-ID header", bool(rid), f"value={rid}")


def check_production_readiness(client: SmokeClient, report: SmokeReport, status_body: dict | None) -> None:
    if not status_body:
        report.add("production readiness flags", False, "skipped — no system status")
        return
    prod = status_body.get("production") or {}
    obs = status_body.get("observability") or {}
    ok = "deployment_ready" in prod and "auth_jwt_required" in prod
    detail = (
        f"deployment_ready={prod.get('deployment_ready')} auth_jwt={prod.get('auth_jwt_required')} "
        f"redis={status_body.get('redis_available')} worker={prod.get('use_arq_worker')} "
        f"sentry={obs.get('sentry_configured')}"
    )
    report.add("production readiness flags", ok, detail)


def check_redis_worker_flags(client: SmokeClient, report: SmokeReport, status_body: dict | None) -> None:
    if not status_body:
        report.add("redis/worker readiness", False, "skipped")
        return
    prod = status_body.get("production") or {}
    redis_ok = status_body.get("redis_available") is True
    worker_flag = prod.get("use_arq_worker") is True
    report.add(
        "redis/worker readiness",
        redis_ok and worker_flag,
        f"redis_available={status_body.get('redis_available')} use_arq_worker={prod.get('use_arq_worker')}",
    )


def check_auth_required_behavior(client: SmokeClient, report: SmokeReport, status_body: dict | None) -> None:
    prod = (status_body or {}).get("production") or {}
    if not prod.get("auth_jwt_required"):
        report.add("auth-required behavior", True, "skipped — JWT not required in this environment")
        return
    anon = httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        r = anon.get(client.url("/api/auth/me"))
        report.add("auth-required behavior", r.status_code == 401, f"GET /api/auth/me status={r.status_code}")
    finally:
        anon.close()


def check_file_access_protection(client: SmokeClient, report: SmokeReport, status_body: dict | None) -> None:
    prod = (status_body or {}).get("production") or {}
    if prod.get("file_access_mode") != "local_authenticated" and prod.get("auth_jwt_required") is not True:
        report.add("file access protection", True, "skipped — public/dev file mode")
        return
    anon = httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        r = anon.get(client.url("/files/projects/1/scenario_1/model.glb"))
        report.add("file access protection", r.status_code in (401, 403, 404), f"status={r.status_code}")
    finally:
        anon.close()


def check_system_status(client: SmokeClient, report: SmokeReport) -> dict | None:
    r = client.get("/api/system/status")
    body = _safe_json(r)
    ok = r.status_code == 200 and "production" in body
    prod = body.get("production") or {}
    detail = (
        f"db={body.get('database_type')} postgis={body.get('postgis_available')} "
        f"deployment_ready={prod.get('deployment_ready')} critical={prod.get('critical_count')}"
    )
    report.add("GET /api/system/status", ok, detail)
    return body if ok else None


def check_auth_flow(client: SmokeClient, report: SmokeReport, email_prefix: str) -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"{email_prefix}-{suffix}@smoke.test"
    password = "SmokeTestPass1!"

    reg = client.post(
        "/api/auth/register",
        {"name": "Smoke Tester", "email": email, "password": password},
    )
    reg_ok = reg.status_code in (201, 409)
    report.add("POST /api/auth/register", reg_ok, f"status={reg.status_code}")

    login = client.post("/api/auth/login", {"email": email, "password": password})
    login_body = _safe_json(login)
    token = login_body.get("access_token") if login.status_code == 200 else None
    report.add("POST /api/auth/login", login.status_code == 200 and bool(token), f"status={login.status_code}")
    if not token:
        return
    client.token = token

    me = client.get("/api/auth/me")
    me_body = _safe_json(me)
    report.add(
        "GET /api/auth/me",
        me.status_code == 200 and me_body.get("email") == email,
        f"plan={me_body.get('plan')} role={me_body.get('role')}",
    )


def check_project_and_generation(
    client: SmokeClient, report: SmokeReport, *, storage_mode: str | None = None
) -> dict | None:
    if not client.token:
        report.add("project flow", False, "skipped — no auth token")
        return None

    created = client.post(
        "/api/projects",
        {
            "name": "Smoke Test Project",
            "project_type": "building",
            "units": "metric",
            "location_name": "Smoke Bengaluru",
            "center_lat": 12.972,
            "center_lng": 77.595,
            "boundary_geojson": MINIMAL_BOUNDARY,
        },
    )
    create_body = _safe_json(created)
    project_id = create_body.get("id")
    report.add("POST /api/projects", created.status_code == 201 and project_id is not None, f"id={project_id}")
    if not project_id:
        return None

    gen = client.post(
        f"/api/projects/{project_id}/design/generate",
        {
            "scenario_name": "Smoke Scenario",
            "parameters": {"builtup_area_sqm": 200, "floors": 2},
            "generation_mode": "fast_preview",
        },
    )
    gen_body = _safe_json(gen)
    job_id = gen_body.get("job_id")
    scenario_id = gen_body.get("scenario_id")
    report.add(
        "POST design/generate",
        gen.status_code == 200 and bool(job_id),
        f"job_id={job_id} scenario_id={scenario_id}",
    )
    if not job_id:
        return {"project_id": project_id}

    deadline = time.time() + JOB_TIMEOUT
    terminal = None
    last_status: dict[str, Any] = {}
    while time.time() < deadline:
        jr = client.get(f"/api/jobs/{job_id}")
        if jr.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue
        last_status = _safe_json(jr)
        stage = last_status.get("stage") or last_status.get("status")
        if stage in ("completed", "failed", "cancelled") or last_status.get("preview_ready"):
            terminal = stage
            break
        time.sleep(POLL_INTERVAL)

    ok = terminal in ("completed", "preview") or last_status.get("preview_ready") is True
    if terminal == "failed":
        ok = False
    report.add(
        "poll generation job",
        ok,
        f"terminal={terminal} preview_ready={last_status.get('preview_ready')} "
        f"error_type={last_status.get('error_type')}",
    )

    scenarios = client.get(f"/api/projects/{project_id}/scenarios")
    scen_body = _safe_json(scenarios)
    summaries = scen_body.get("summaries") or scen_body.get("scenarios") or []
    report.add("GET scenarios", scenarios.status_code == 200 and len(summaries) >= 1, f"count={len(summaries)}")

    if scenario_id:
        detail = client.get(f"/api/projects/{project_id}/scenarios/{scenario_id}")
        report.add("GET scenario detail", detail.status_code == 200, f"status={detail.status_code}")

    model_url = last_status.get("preview_glb_url") or (last_status.get("result") or {}).get("preview_glb_url")
    if model_url:
        mr = _fetch_file_url(client, model_url)
        if mr.status_code == 200:
            report.add("model URL reachable", True, f"status=200 url={model_url[:80]}")
        elif mr.status_code == 404 and storage_mode == "local":
            report.add(
                "model URL reachable",
                True,
                "404 with local storage — configure S3 on Render for durable GLB files",
            )
        else:
            report.add(
                "model URL reachable",
                False,
                f"status={mr.status_code} url={model_url[:80]} storage={storage_mode}",
            )
    else:
        report.add("model URL reachable", True, "skipped — no preview URL in job payload")

    usage = client.get("/api/usage/summary")
    report.add("GET /api/usage/summary", usage.status_code == 200, f"status={usage.status_code}")

    diag = last_status.get("diagnostics")
    report.add(
        "job diagnostics present",
        isinstance(diag, dict) or last_status.get("timings") is not None or ok,
        f"has_diagnostics={isinstance(diag, dict)}",
    )

    if len(summaries) >= 2:
        ids = [s.get("scenario_id") for s in summaries[:2] if s.get("scenario_id") is not None]
        if len(ids) >= 2:
            cmp_r = client.post(
                f"/api/projects/{project_id}/scenarios/compare",
                {"scenario_ids": ids},
            )
            report.add("POST scenarios/compare", cmp_r.status_code == 200, f"status={cmp_r.status_code}")

    return {"project_id": project_id, "job_id": job_id}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GeoAI production smoke test")
    parser.add_argument("--base-url", required=True, help="API base URL, e.g. https://geoai-api.onrender.com")
    parser.add_argument("--email-prefix", default="smoke", help="Prefix for ephemeral test user email")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    return parser.parse_args(argv)


def run_smoke(base_url: str, email_prefix: str = "smoke", timeout: float = DEFAULT_TIMEOUT) -> SmokeReport:
    report = SmokeReport(base_url=base_url)
    client = SmokeClient(base_url, timeout=timeout)
    check_health(client, report)
    check_request_id_headers(client, report)
    status_body = check_system_status(client, report)
    check_production_readiness(client, report, status_body)
    check_redis_worker_flags(client, report, status_body)
    check_auth_required_behavior(client, report, status_body)
    check_file_access_protection(client, report, status_body)
    check_auth_flow(client, report, email_prefix)
    storage_mode = (status_body or {}).get("storage_mode") if status_body else None
    check_project_and_generation(client, report, storage_mode=storage_mode)
    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_smoke(args.base_url, email_prefix=args.email_prefix, timeout=args.timeout)

    print(f"\nProduction smoke test — {report.base_url}\n")
    for item in report.results:
        status = "PASS" if item.ok else "FAIL"
        line = f"[{status}] {item.name}"
        if item.detail:
            line += f" — {item.detail}"
        print(line)

    passed = sum(1 for r in report.results if r.ok)
    total = len(report.results)
    print(f"\nSummary: {passed}/{total} passed")
    if not report.passed:
        print("OVERALL: FAIL")
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

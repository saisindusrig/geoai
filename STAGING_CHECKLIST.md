# Staging Launch Checklist — GeoAI 3D Construction Planner

Use this checklist before promoting a staging or production release.

## Backend deploy

- [ ] API, worker, PostgreSQL/PostGIS, Redis and object storage services provisioned
- [ ] `geoai-api` web service healthy at `/health`
- [ ] `geoai-worker` running (`arq app.workers.tasks.WorkerSettings`)
- [ ] Build completed `alembic upgrade head` without errors
- [ ] Startup logs show `deployment_ready` (check API logs)
- [ ] `GET /api/system/status` returns expected database/redis/storage flags

## Frontend deploy

- [ ] Frontend build succeeded (`npm ci && npm run build`)
- [ ] `NEXT_PUBLIC_API_URL` points to staging/production API
- [ ] `NEXT_PUBLIC_AUTH_REQUIRE_JWT=true` in production context
- [ ] App loads dashboard without console errors

## Environment variables

### Backend (API + worker)

- [ ] `DATABASE_URL` (Postgres)
- [ ] `REDIS_URL`
- [ ] `APP_SECRET` (not dev default)
- [ ] `ENVIRONMENT=production`
- [ ] `AUTH_REQUIRE_JWT=true`
- [ ] `USE_ARQ_WORKER=true`
- [ ] `NEXT_PUBLIC_APP_URL` = frontend URL (CORS)
- [ ] `S3_*` configured for durable files
- [ ] Optional: `SENTRY_DSN`, AI keys, map tokens

### Frontend

- [ ] `NEXT_PUBLIC_API_URL`
- [ ] `NEXT_PUBLIC_AUTH_REQUIRE_JWT=true`
- [ ] Optional: `NEXT_PUBLIC_SENTRY_DSN`, map tokens

## Infrastructure checks

### PostGIS

Alembic migrations `001` and `002` run `CREATE EXTENSION IF NOT EXISTS postgis` on PostgreSQL. **Manual SQL is optional** — only needed if the provider blocks extension creation from the app user.

To verify after deploy:

- [ ] `/api/system/status` → `postgis_available: true`

If migrations fail and PostGIS is missing, run once in database provider SQL console:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Then redeploy API + worker.

### Redis + worker

- [ ] `/api/system/status` → `redis_available: true`, `job_store: redis`
- [ ] `production.use_arq_worker: true`
- [ ] Worker logs show Arq startup without Redis errors

### S3 / object storage

- [ ] Follow [STORAGE_SETUP.md](./STORAGE_SETUP.md) (R2 or AWS)
- [ ] `/api/system/status` → `storage_mode: s3` (not `local`)
- [ ] No critical `local_storage` warning
- [ ] Production smoke: `model URL reachable` passes (200, not 404 advisory)

## Auth

- [ ] Register new user works
- [ ] Login returns JWT
- [ ] `/api/auth/me` returns user + plan
- [ ] Unauthenticated project access returns 401 when JWT required
- [ ] First admin promoted: `python backend/scripts/create_admin.py you@company.com`

## Maps

- [ ] Map loads (OSM fallback minimum)
- [ ] Optional: satellite/3D tiles with Mapbox/Cesium/Google keys
- [ ] Browser keys restricted by domain in provider dashboard

## Core workflow tests

### Generation

- [ ] Create project with boundary
- [ ] Run `fast_preview` generation
- [ ] Job reaches preview/completed
- [ ] Job response includes `diagnostics` timings

### GLB visibility

- [ ] Preview/final GLB URL returns 200 when authenticated
- [ ] 3D model visible in workspace/model page

### PDF report

- [ ] Open report page
- [ ] Download PDF export

### Usage limits

- [ ] Settings usage card loads `/api/usage/summary`
- [ ] Free plan limits enforced (429 with `usage_limit_exceeded`) when exceeded

### Admin audit

- [ ] Admin can open audit logs (`GET /api/admin/audit`)
- [ ] Admin usage query works (`GET /api/admin/usage`)

## Observability

- [ ] API responses include `X-Request-ID` header
- [ ] Error JSON includes `request_id` for support/debugging
- [ ] Optional: `SENTRY_DSN` set and errors appear in Sentry

## Automated smoke test

```bash
cd backend
python scripts/production_smoke.py --base-url https://api.example.com
```

Expected: `OVERALL: PASS`

Smoke test verifies:

- Health + system status + production readiness flags
- Request ID headers
- Auth register/login/me
- Project create + generation poll
- Scenarios + usage summary
- Redis/worker readiness flags (via system status)
- File access behavior (unauthenticated file probe when JWT required)

## CI

- [ ] GitHub Actions `CI` workflow green on target branch
- [ ] Backend pytest + frontend lint/test/build passed
- [ ] ESLint runs with `--max-warnings 0`
- [ ] Playwright critical-path E2E passed (register → workspace)
- [ ] Optional: run **Staging smoke** workflow (`staging-smoke.yml`) against staging API

## Polish checklist

- [ ] `npm run lint` — zero warnings
- [ ] `npm test` — Vitest unit/component tests green
- [ ] `npm run test:e2e` — Playwright critical path (local or CI)
- [ ] `ANALYZE=true npm run build` — review largest bundles (Cesium, map libs)
- [ ] Accessibility: skip link, mobile More menu, login errors, nav drawer focus
- [ ] Manual smoke: `python backend/scripts/production_smoke.py --base-url <staging-api>`

## Rollback plan

- [ ] Previous API/worker release IDs noted
- [ ] Previous frontend release noted
- [ ] Database migration is forward-only (no destructive downgrade planned)

---

After all items pass, run **[MANUAL_QA.md](./MANUAL_QA.md)** for full browser QA, then promote to production.

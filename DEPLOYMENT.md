# Deployment — GeoAI / CivicSpan

Repository: [saisindusrig/geoai](https://github.com/saisindusrig/geoai).

This repository provides a Next.js frontend and FastAPI backend. Choose hosting services that support Node.js and Python; configuration is independent of the previous hosting accounts.

## Services and environments

- Frontend: Node.js 20.9+ (Node.js 22 LTS recommended), installed with `npm ci` in `frontend`.
- API: Python 3.12+ with `backend/requirements.txt` for all platform routes.
- Optional lean CivicSpan demo: `backend/requirements-civicspan.txt` and `civicspan_app:app`.
- Production data: PostgreSQL/PostGIS, Redis and durable S3-compatible object storage.
- Background worker: `arq app.workers.tasks.WorkerSettings` using the same database/storage settings as the API.

Use `.env.example` as the variable template. Keep real credentials in the hosting provider's secret settings, never in Git. Set `ENVIRONMENT=production`, `AUTH_REQUIRE_JWT=true`, a strong `APP_SECRET`, `DATABASE_URL`, `REDIS_URL`, and `USE_ARQ_WORKER=true` for the full production platform. Set `NEXT_PUBLIC_APP_URL` and `CORS_ALLOWED_ORIGINS` to the new frontend origins. Enable `CORS_ALLOW_NETLIFY` only if you deliberately need that provider's preview domains.

Configure object storage using [STORAGE_SETUP.md](./STORAGE_SETUP.md), and set `PUBLIC_API_URL` to the new API origin.

## Backend release

From `backend`:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Set the port to the hosting platform's assigned port where required. Use `/health` as the health check. Run the Arq worker as a separate process when `USE_ARQ_WORKER=true`.

## Frontend release

Set `NEXT_PUBLIC_API_URL` to the new API origin and `NEXT_PUBLIC_AUTH_REQUIRE_JWT=true` before building. Public map credentials must have domain/referrer restrictions.

From `frontend`:

```bash
npm ci
npm run build
npm run start -- --port 3000
```

Use a Next.js-compatible host and its assigned port. Files under `frontend/public/models`, `textures`, `videos`, and the generated Cesium runtime are required at runtime. The `prebuild` script copies Cesium and synchronizes the asset catalogue automatically.

## Production smoke test

After both services are live:

```bash
cd backend
pip install -r requirements.txt
python scripts/production_smoke.py --base-url https://api.example.com
```

The script checks:

- `/health`, `/api/system/status`
- `X-Request-ID` on responses
- Production readiness flags (`deployment_ready`, auth, Redis/worker)
- Auth-required behavior (401 when JWT required)
- File access protection (401/403 for anonymous GLB fetch in prod mode)
- Register + login + `/api/auth/me`
- Create project with minimal boundary
- Start `fast_preview` generation
- Poll job until preview/completed/failed (includes job diagnostics when present)
- List scenarios, scenario detail, scenario compare (when 2+ scenarios exist)
- Usage summary
- Model URL when available

Exit code **0** = all checks passed. Safe diagnostics only (no secrets printed).

See also **[STAGING_CHECKLIST.md](./STAGING_CHECKLIST.md)** for manual pre-launch verification.

---

## Error tracking (optional Sentry)

Sentry is **optional** — the app runs normally without it.

### Backend

Set in the API and worker environments:

| Variable | Notes |
|----------|-------|
| `SENTRY_DSN` | From Sentry project settings |
| `SENTRY_ENVIRONMENT` | e.g. `staging`, `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | e.g. `0.1` |

When `SENTRY_DSN` is set, the API initializes `sentry-sdk` at startup. Verify via `GET /api/system/status` → `observability.sentry_enabled`.

### Frontend

Set `NEXT_PUBLIC_SENTRY_DSN` in the frontend build environment. The repo includes a lightweight hook in `frontend/lib/observability.ts`; install `@sentry/nextjs` and wire `Sentry.init` there when you want client-side error forwarding.

---

## Local production-like mode

Simulate production constraints locally:

```bash
# Terminal 1 — infrastructure
docker compose up -d

# Terminal 2 — API
cd backend
cp ../.env.example ../.env
# Edit .env:
#   ENVIRONMENT=production
#   AUTH_REQUIRE_JWT=true
#   DATABASE_URL=postgresql+psycopg2://geoai:geoai@localhost:5432/geoai
#   REDIS_URL=redis://localhost:6379/0
#   USE_ARQ_WORKER=true
#   APP_SECRET=local-prod-test-secret-not-for-deploy
#   NEXT_PUBLIC_APP_URL=http://localhost:3000
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3 — worker
cd backend
arq app.workers.tasks.WorkerSettings

# Terminal 4 — frontend
cd frontend
# frontend/.env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_AUTH_REQUIRE_JWT=true
npm run dev
```

Smoke against local API:

```bash
python backend/scripts/production_smoke.py --base-url http://localhost:8000
```

---

## Create first admin user

1. Register via the app or API:
   ```bash
   curl -X POST https://YOUR-API/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"name":"Admin","email":"you@company.com","password":"YourSecurePass1"}'
   ```
2. Promote to admin (from repo, with `DATABASE_URL` set):
   ```bash
   cd backend
   python scripts/create_admin.py you@company.com
   ```
3. Log in again — `/api/auth/me` should show `"role": "admin"`, `"plan": "admin"`.

Alternatively, SQL on Postgres:
```sql
UPDATE users SET role = 'admin', plan = 'admin' WHERE email = 'you@company.com';
```

---

## Rotate API keys

1. Generate new key in provider dashboard (OpenAI, Mapbox, S3, etc.).
2. Update the API and worker environment variables.
3. Redeploy the API and worker.
4. For browser map keys, update frontend `NEXT_PUBLIC_*` variables and redeploy frontend.
5. Revoke old keys after verifying `/api/system/status` and maps.

Rotate `APP_SECRET` only with a plan to invalidate all JWTs (all users must log in again).

---

## Object storage (S3 / MinIO)

Many hosting providers use **ephemeral** filesystems. Without durable storage:

- GLB/PDF files are lost on restart
- `/api/system/status` reports `local_storage` as **critical** in production

**MinIO locally** (docker-compose):

```env
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=geoai-files
S3_ACCESS_KEY=geoai
S3_SECRET_KEY=your-minio-secret
```

**Production:** use AWS S3, Cloudflare R2, or similar. **Step-by-step:** [STORAGE_SETUP.md](./STORAGE_SETUP.md) (R2 recommended).

| Provider | Required vars | Notes |
|----------|---------------|-------|
| **MinIO** (local/docker) | `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Bucket auto-created |
| **AWS S3** | `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION` | Create bucket first; omit `S3_ENDPOINT` |
| **Cloudflare R2** | All four `S3_*` + `S3_ENDPOINT` (R2 URL) | Use R2 access keys |

Also set **`PUBLIC_API_URL`** to your deployed API URL (e.g. `https://api.example.com`) so local `/files/` links work until S3 is configured. The backend also recognizes `RENDER_EXTERNAL_URL` for compatibility when `PUBLIC_API_URL` is unset.

Run smoke after deploy:

```bash
python backend/scripts/production_smoke.py --base-url https://api.example.com
```

---

## Migrations & startup

| Step | When |
|------|------|
| `alembic upgrade head` | Release step before API/worker startup |
| `init_db()` | API **startup** — seeds rates/templates/demo, creates missing tables |
| Startup warnings | Logged via `production_readiness()` — check API logs |
| `/api/system/status` | `production.deployment_ready`, `critical_count`, warnings |

**PostGIS:** Migrations `001` and `002` both run `CREATE EXTENSION IF NOT EXISTS postgis` on PostgreSQL before any `geometry` columns are used. You do **not** need a separate manual SQL step if the build completes `alembic upgrade head` successfully. After deploy, confirm `postgis_available: true` in `/api/system/status`. If extension creation is blocked by your Postgres provider, run `CREATE EXTENSION IF NOT EXISTS postgis;` once in the database shell, then redeploy.

**Note:** Migration `002` adds `engineering_layers.geom` as PostGIS `geometry(Geometry, 0)`. It is idempotent (skips tables/columns that already exist from `001`).

SQLite is allowed for local dev only. Production with SQLite triggers a **critical** warning.

---

## CI/CD

GitHub Actions: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)

On push/PR to `main`:

- Backend: `pytest`
- Frontend: `npm run lint`, `npm test`, `npm run build`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| **401 on all API calls** | JWT required but no token | Set `NEXT_PUBLIC_AUTH_REQUIRE_JWT=true` on Netlify; log in; check `Authorization` header |
| **401 after deploy** | Wrong `APP_SECRET` or expired token | Log in again; verify same secret on API/worker |
| **CORS errors** | Frontend URL not allowed | Set `NEXT_PUBLIC_APP_URL` on backend to exact frontend URL; redeploy API. Also verify `NEXT_PUBLIC_API_URL` in the frontend build environment matches your deployed API URL (404 on `/health` means wrong host, not CORS) |
| **Model not showing** | Job failed or GLB missing | Check job status `/api/jobs/{id}`; verify worker running; check S3 config |
| **GLB 404** | Ephemeral disk or auth | Use S3; ensure logged in; files served via `/files/...` with JWT |
| **Job stuck queued** | Worker not running or no Redis | Enable `geoai-worker`; verify `REDIS_URL`; `USE_ARQ_WORKER=true` |
| **Redis unavailable** | Wrong URL or service down | Check the Redis service; `GET /api/system/status` → `redis_available` |
| **Map tiles missing** | No Mapbox/Google token | Add keys or use OSM fallback; restrict public keys by domain |
| **429 usage limit** | Free plan caps | Settings → usage card; wait for daily reset or promote to `pro`/`admin` |
| **PostGIS / survey disabled** | SQLite or extension missing | Use PostgreSQL with PostGIS; migrations enable PostGIS automatically — verify `postgis_available` in system status |
| **deployment_ready: false** | Critical config warnings | Fix items in `/api/system/status` → `production.warnings` |

---

## Security checklist

- [ ] `APP_SECRET` unique per environment (not `dev-secret-change-me`)
- [ ] `AUTH_REQUIRE_JWT=true` in production
- [ ] S3 configured for file persistence
- [ ] Redis configured for jobs + rate limits
- [ ] Worker service running alongside API
- [ ] No secrets in frontend env or git
- [ ] Map keys referrer-restricted
- [ ] First admin created intentionally (not default dev user)

---

## Local dev quickstart

See **[LOCAL_SETUP.md](./LOCAL_SETUP.md)** for SQLite/mock mode without Docker.

---

## Manual QA

See **[MANUAL_QA.md](./MANUAL_QA.md)** for browser checklists.

---

## Disclaimer

All outputs remain **preliminary planning only** — not construction-ready drawings or approvals.

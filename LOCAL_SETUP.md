# Local Setup — GeoAI 3D Construction Planner

This guide covers running the platform locally for development and demo.

## Prerequisites

- **Node.js 20+** and npm
- **Python 3.11+** (3.13 tested)
- **Docker Desktop** (optional but recommended for PostGIS, Redis, MinIO)

## Quick start (recommended — with Docker)

```bash
# From repo root
cp .env.example .env

docker compose up -d   # PostGIS + Redis + MinIO

cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# New terminal — optional background worker (uses Redis when available)
cd backend
arq app.workers.tasks.WorkerSettings

# New terminal — frontend
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001 (user `geoai`, password `geoai-secret`)

## Quick start (no Docker)

If Docker is unavailable, the backend **automatically falls back**:

| Service   | Full mode              | Dev fallback                    |
|-----------|------------------------|---------------------------------|
| Database  | PostGIS (PostgreSQL)   | SQLite at `backend/dev.db`      |
| Jobs      | Redis + Arq            | In-process execution            |
| Storage   | MinIO / S3             | `backend/storage/` filesystem   |
| AI / maps | Real API keys          | Mock providers (offline demo)   |

```bash
cp .env.example .env
# Leave DATABASE_URL unset or unreachable — SQLite is used automatically

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

**Note:** Survey-grade imports, spatial indexes, and advanced CRS workflows require **PostGIS**. On SQLite you will see **Limited GIS mode** in Settings.

## Demo project

On first API startup, the backend seeds **Demo Flyover (Bengaluru)** (typically project id `5`).

Demo flow:

1. Dashboard → open demo project
2. Workspace / Map → boundary + alignment visible
3. Enable survey mode (full features need PostGIS)
4. 3D model, Estimate, Cost, Timeline, Report
5. Export PDF / CSV / GeoJSON

Works without API keys using mock AI and OSM/terrain fallbacks.

## Environment variables

Copy `.env.example` to `.env` at the repo root. Key variables:

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | No (dev) | PostGIS connection; omit for SQLite |
| `REDIS_URL` | No | Job queue; omit for in-process jobs |
| `S3_*` | No | MinIO/S3; omit for local filesystem |
| `APP_SECRET` | Yes (prod) | JWT signing |
| `NEXT_PUBLIC_API_URL` | Yes | Frontend → backend URL (e.g. `http://localhost:8000`) |
| `OPENAI_API_KEY` etc. | No | Cloud AI; all blank + `AI_PROVIDER=mock` → mock provider |
| `AI_PROVIDER` | No | `ollama` (local), `openai`, `anthropic`, `mock`, or `auto` |
| `OLLAMA_*` | No | Local Ollama when `AI_PROVIDER=ollama` — see [Ollama setup](#ollama-local-ai) below |

**Never put provider API keys in frontend env vars.** Only `NEXT_PUBLIC_*` URLs belong in the Next.js app.

## Production-like local mode

To mirror production constraints locally (JWT required, Redis, worker, Postgres):

```bash
docker compose up -d
# .env:
#   ENVIRONMENT=production
#   AUTH_REQUIRE_JWT=true
#   USE_ARQ_WORKER=true
#   DATABASE_URL=postgresql+psycopg2://geoai:geoai@localhost:5432/geoai
#   REDIS_URL=redis://localhost:6379/0

cd backend && alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
# separate terminal:
arq app.workers.tasks.WorkerSettings

# frontend/.env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_AUTH_REQUIRE_JWT=true
cd frontend && npm run dev
```

Smoke test: `python backend/scripts/production_smoke.py --base-url http://localhost:8000`

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for full production checklist.

## Ollama (local AI)

Use [Ollama](https://ollama.com) for **local LLM testing** — workspace copilot and optional design generation without cloud API keys.

### Install Ollama

1. Download from https://ollama.com and install for your OS.
2. Pull the model (match `OLLAMA_MODEL` in `.env`):

```bash
ollama pull llama3.2
```

3. Verify Ollama is running (default API: `http://localhost:11434`):

```bash
ollama run llama3.2
# or: curl http://localhost:11434/api/tags
```

### Configure `.env`

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT_SECONDS=120
```

Restart the backend after changing env vars. Check **Settings → System status** for Ollama availability and installed models.

### What Ollama can do in this app

| Feature | Ollama role |
|---------|-------------|
| **Workspace copilot** | Real LLM chat with structured actions (parameter suggestions, run analysis, generate design) |
| **Design generation** | Optional structured concept JSON when `AI_PROVIDER=ollama` |
| **BOQ / cost / timeline** | **Not from LLM** — always computed by backend calculators |

### What Ollama cannot do

- Replace licensed engineering sign-off or produce construction-ready drawings.
- Invent final BOQ quantities or costs (the copilot is instructed not to; calculators own numbers).
- Run without a local GPU/CPU — large models may be slow on low-end machines.
- Guarantee valid JSON on every turn — the app falls back to rule-based copilot if Ollama is offline or returns invalid output.

For production, set `AI_PROVIDER=openai` or `anthropic` and add the corresponding API key.

## Migrations

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"   # when changing models
```

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Validation & system status

- `GET /api/projects/{id}/validation` — readiness checks before design/BOQ/export
- `GET /api/system/status` — database mode, PostGIS, Redis, storage, AI/map providers

These are shown in the workspace/map sidebar and Settings page.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Frontend can't reach API | Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` |
| Survey import fails | Start Docker PostGIS and set `DATABASE_URL` |
| Port 3000 in use | Stop other Next.js dev servers |
| Empty demo project | Restart backend (seeds on startup) |

## Disclaimer

All outputs are **preliminary planning only** — not final engineering drawings or legal approvals.

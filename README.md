# GeoAI — AI-Assisted Civil Infrastructure Planning

[![CI](https://github.com/saisindusrig/geoai/actions/workflows/ci.yml/badge.svg)](https://github.com/saisindusrig/geoai/actions/workflows/ci.yml)
[![CAD worker](https://github.com/saisindusrig/geoai/actions/workflows/cad-worker-linux.yml/badge.svg)](https://github.com/saisindusrig/geoai/actions/workflows/cad-worker-linux.yml)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![CesiumJS](https://img.shields.io/badge/3D-CesiumJS-6CADDF)](https://cesium.com/platform/cesiumjs/)

GeoAI is an end-to-end workspace for exploring civil and infrastructure concepts on real terrain. It combines geospatial context, editable 3D models, approval-gated AI assistance, deterministic engineering calculators, and preliminary project reporting in one browser-based workflow.

![GeoAI terrain planning workspace](frontend/public/images/hero-planning-still.png)

> [!IMPORTANT]
> GeoAI produces **preliminary planning outputs**, not final structural drawings, legal construction approvals, or a substitute for licensed engineers, surveyors, and authority sign-off.

## Why GeoAI

Infrastructure planning data is usually fragmented across maps, spreadsheets, CAD tools, reports, and disconnected AI experiments. GeoAI brings the early-stage workflow together while keeping important decisions reviewable:

- Ground project context in maps, terrain, survey inputs, and visible evidence.
- Generate bounded building and infrastructure concepts through an assistant.
- Review proposals before they modify the active project revision.
- Edit typed model components instead of accepting opaque generated geometry.
- Calculate BOQ, cost, and schedule outputs in deterministic backend services.
- Export planning evidence as PDF, CSV, GeoJSON, DXF, and CAD artifacts.

## Product capabilities

### Geospatial workspace

- MapLibre and Cesium 3D views with terrain and imagery provenance.
- Boundary drawing, measurement, search, feature inspection, and sun study tools.
- Survey imports, CRS handling, GCP validation, accuracy tiers, and mesh export.
- Seeded **Demo Flyover (Bengaluru)** project for a complete offline-friendly tour.

### AI-assisted design

- Core Assistant, Building Specialist, and Building Patch workflows.
- Context preflight, clarification, selection awareness, and typed tool boundaries.
- Approval-gated proposals with revision history and editable parameters.
- Ollama, OpenAI, Anthropic, Nebius, and mock-provider paths.
- AI proposes concepts; backend calculators remain the source of quantities and costs.

### BIM and CAD experimentation

- Structured BIM project and authoring contracts.
- Assembly authoring, orchestration, model evaluation, and canary tooling.
- Experimental CAD geometry, revision, artifact, and workspace APIs.
- Dedicated Linux CAD worker image and automated runtime verification.
- Browser-side mesh conversion and review inside the model editor.

### Planning and reporting

- Site analysis, scenarios, BOQ and estimate generation, cost analysis, and timeline.
- Project-readiness validation and system capability reporting.
- PostGIS/Redis/S3 production services with lightweight local fallbacks.
- PDF, CSV, GeoJSON, DXF, and model-oriented export flows.

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ Next.js workspace                                            │
│ Dashboard · MapLibre · Cesium · Model editor · Assistant UI │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST / JSON
┌──────────────────────────────▼───────────────────────────────┐
│ FastAPI application                                          │
│ Projects · Assistant · Design · BIM/CAD · BOQ · Exports     │
└──────────────┬───────────────────────┬───────────────────────┘
               │                       │
      ┌────────▼────────┐     ┌────────▼──────────────────────┐
      │ PostGIS/SQLite  │     │ Redis/Arq · S3/MinIO · AI   │
      └─────────────────┘     └───────────────────────────────┘
```

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Zustand |
| Maps and 3D | MapLibre GL, CesiumJS, deck.gl, Three.js |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Data | PostGIS in full mode; SQLite local fallback |
| Jobs | Redis + Arq; in-process development fallback |
| Storage | S3/MinIO; local filesystem fallback |
| AI | Ollama, OpenAI, Anthropic, Nebius, or deterministic mock |

## Quick start

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (optional, for PostGIS, Redis, and MinIO)

### Run locally

```bash
git clone https://github.com/saisindusrig/geoai.git
cd geoai
cp .env.example .env

# Optional full-service infrastructure
docker compose up -d

# Terminal 1 — API
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2 — web app
cd frontend
npm install
npm run dev
```

Open the app at [http://localhost:3000](http://localhost:3000) and the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

Docker is optional for the primary demo. When external services are unavailable, GeoAI falls back to SQLite, in-process jobs, local storage, and mock AI. See [LOCAL_SETUP.md](./LOCAL_SETUP.md) for environment variables and detailed setup.

## Validation and tests

```bash
# Frontend
cd frontend
npm run lint
npm test
npm run build

# Backend
cd backend
python -c "from app.db.init_db import init_db; init_db()"
pytest -q tests
pytest -q civicspan_tests
```

The suites cover API health, project validation, calculators, auth, exports, assistant safety, proposal approval, revision handling, BIM/CAD contracts, terrain provenance, and workspace flows. The two backend test directories run separately because both contain a `test_civicspan.py` module.

## API highlights

- `GET /health`
- `GET /api/system/status`
- `GET /api/projects/demo`
- `GET /api/projects/{id}/validation`
- `GET /api/projects/{id}/exports/pdf`
- Experimental CAD routes are capability-gated and intended for evaluation.

## Accuracy tiers

| Tier | Intended use |
| --- | --- |
| `visual` | Concept and client preview |
| `gis_grade` | Planning GIS workflows |
| `survey_grade` | Survey-adjusted geometry |
| `engineering_ready` | Highest input confidence; outputs remain preliminary |

Full survey workflows require PostGIS. SQLite environments report **Limited GIS mode** in Settings.

## Repository guide

```text
frontend/        Next.js application, map/3D workspace, and browser tests
backend/         FastAPI services, engineering logic, BIM/CAD experiments, tests
docs/            Technical decisions, contracts, acceptance evidence, deployment
.github/         CI and CAD-worker verification workflows
docker-compose.yml
.env.example
```

Start with these documents:

- [Local setup](./LOCAL_SETUP.md)
- [Deployment guide](./DEPLOYMENT.md)
- [Manual QA](./MANUAL_QA.md)
- [Staging checklist](./STAGING_CHECKLIST.md)
- [BIM foundation](./docs/BIM_FOUNDATION_V1.md)
- [CAD integration foundation](./docs/CAD_INTEGRATION_FOUNDATION_3B1.md)

## Contributing

Useful contributions include focused bug fixes, tests, accessibility improvements, documentation corrections, geospatial interoperability, and bounded BIM/CAD experiments. Please use a feature branch, keep changes reviewable, and open a pull request describing the user-facing outcome and validation performed.

## License

This repository is currently marked for private/internal use. Add an explicit open-source license before redistributing or accepting external code contributions.

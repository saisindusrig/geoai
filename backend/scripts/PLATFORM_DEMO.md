# Offline maintenance platform acceptance

This fixture creates one **unapproved** AI3D proposal for a 5 m × 3 m industrial maintenance platform: four columns, four beams and one slab. Deck top local Z is approximately 3 m; surveyed ground elevation remains unknown. Member sections are visual placeholders. Loads, foundations, clearances, structural adequacy and code compliance are unverified. The ordinary proposal review, assumption acknowledgment, approval, generic executor and Cesium editor remain mandatory.

Use a dedicated, disposable local SQLite database, never a working project database. Every invocation creates a fresh project so browser approval/editing can be reproduced without altering prior projects. No model provider is called: the script uses the existing scripted `FixtureProvider`. Native CAD and BIM authoring stay disabled.

From `backend`, with the installed Python environment (PowerShell example):

```powershell
$env:PYTHONPATH='.'
$env:DATABASE_URL='sqlite:///./.cad-proof-output/platform-demo.sqlite'
$env:AI_PROVIDER='mock'
$env:ENVIRONMENT='development'
$env:GEOAI_EXPERIMENTAL_CAD='false'
$env:GEOAI_EXPERIMENTAL_BIM_AUTHORING='false'
$env:LOCAL_STORAGE_DIR=(Join-Path (Get-Location) '.cad-proof-output/platform-storage')
New-Item -ItemType Directory -Force .cad-proof-output | Out-Null
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/create_platform_workspace_fixture.py
# Keep the same environment; disable inherited cloud-storage settings in-process.
./.venv/Scripts/python.exe -c "from app.core.config import settings; settings.S3_ACCESS_KEY=''; settings.S3_SECRET_KEY=''; import uvicorn; uvicorn.run('app.main:app',host='127.0.0.1',port=8000)"
```

Preserve existing services: use port 8000 only if free, or configure the frontend API URL for another local port. In another terminal run `npm run dev` from `frontend`, with `NEXT_PUBLIC_API_URL=http://localhost:8000` and `NEXT_PUBLIC_AUTH_REQUIRE_JWT=false`, or reuse a matching existing development server.

Set `PLATFORM_ACCEPTANCE_PROJECT_ID` to the printed project ID, then from `frontend`:

```powershell
$env:PLATFORM_ACCEPTANCE_PROJECT_ID='<printed projectId>'
$env:PLAYWRIGHT_SKIP_WEBSERVER='true'
$env:PLAYWRIGHT_CHANNEL='msedge' # Optional installed browser; default uses Playwright Chromium.
node node_modules/@playwright/test/cli.js test e2e/platform-workspace-acceptance.spec.ts --reporter=list
```

The test checks the visible dimensions and assumptions, disabled approval before acknowledgment, explicit approval and generation, then selects the slab, moves its east position from 0 to 0.25 m, saves, reloads and compares revisions (0 added, 0 removed, 1 modified). This deliberately conceptual edit is not an engineering correction. Three screenshots are saved under `frontend/test-results/platform-*.png`. Basemap tokens are replaced with null for bundled Natural Earth imagery; no paid inference is involved.

Backend regression command: `python -m pytest tests/test_industrial_platform.py tests/test_ai3d_v1.py -q`. Frontend checks: `npm test -- components/workspace/ProposalReview.test.tsx`, `npx tsc --noEmit`, `npm run lint`, `npm run build`.

CI seeds its own proposal and runs this smoke test rather than skipping it; screenshots and failure context are uploaded as `platform-acceptance-evidence`. Keep fixture databases, generated files and local logs out of Git. This workflow performs no merge or deployment.

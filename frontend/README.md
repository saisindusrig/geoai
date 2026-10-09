# GeoAI frontend

This Next.js App Router application provides the GeoAI dashboard, project creation dialog, project workspaces, map/3D views, and assistant/review panels.

## Setup

Follow the repository [local setup guide](../LOCAL_SETUP.md). From this directory:

```bash
npm install
npm run dev
```

The dashboard's **New Project** flow asks for a project name, creates an unclassified project, and opens its workspace. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` when the backend is not at its default local URL.

## Checks

```bash
npm run test
npx tsc --noEmit
npm run lint
npm run test:e2e -- --grep "name-only project"
```

The full Playwright suite is `npm run test:e2e`. The Building workspace and patch acceptance specs require a dedicated seeded backend project; see `backend/scripts/create_building_workspace_fixture.py` and `backend/scripts/create_building_patch_fixture.py`.

Build scripts sync the asset catalogue and copy Cesium assets before running `next build`.

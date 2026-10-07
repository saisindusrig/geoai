# AI building assistant

In a saved **building** project, draw and save a plot boundary, then open **AI Building Assistant** in the workspace toolbar. Describe the building, select **Create plan**, review the floor preview, dimensions and assumptions, then choose **Approve and build**. **Request changes** saves a new proposal without overwriting earlier plans or models. Save manual model edits before planning. Architecture and Structural frame controls are available in Scene layers after generation.

## Backend configuration

Set `NEBIUS_API_KEY`, `NEBIUS_CHAT_MODEL`, and `NEBIUS_TOKEN_FACTORY_BASE_URL` in the backend environment. Existing endpoint/model settings are preserved; the standard endpoint is `https://api.tokenfactory.nebius.com/v1/`. Keys never go to the frontend. The building assistant always uses Nebius; optionally set `AI_PROVIDER=nebius` to use it for the main provider too. Provider failures are visible and do not generate mock building plans.

Restart the backend after configuring it. Apply `alembic upgrade head` from `backend` for production; migration 007 adds `building_plans`. The existing development initializer also creates the table. No prior scenarios or revisions are rewritten.

## API and persistence

- `GET/POST /api/projects/{project_id}/ai/building-plans`: list or propose, with `{prompt, base_revision_id}` on POST.
- `GET /.../building-plans/{id}`: retrieve the proposal, specification, stale status and submitted job.
- `POST /.../building-plans/{id}/revisions`: propose changes with `{prompt, base_revision_id}`.
- `POST /.../building-plans/{id}/build`: explicitly approve with `{approve: true}`; returns `job_id` and `scenario_id`.

Ownership applies to all operations. Plans capture the saved boundary, origin, placement and latest model revision. Changes invalidate unbuilt plans. Repeated approval returns the same job. The worker validates approval again and produces geometry directly from the saved specification; it never runs a second planner. Each build creates a scenario and editable revision, retaining prior scenarios. Existing placement anchors are inherited, with ground support review required for the new geometry.

## Limits

Version 1 supports up to ten floors, rectangular footprints and rooms, straight walls with actual opening cutouts, and repeated conceptual column/beam layouts. It checks plot containment, room overlaps, dimensions, IDs and opening placement. It does not validate structural adequacy, circulation, accessibility, fire safety or building regulations. Missing survey elevation stays unknown; zero used by the renderer is a visual reference only. Quantities cover conceptual structural volumes; architectural finishes and excavation are not a complete estimate.

The existing in-memory job mode cannot resume after a server restart. Use the application's Redis/Arq deployment for durable jobs; if a submitted job is unavailable, request a new plan revision rather than repeatedly approving it. Plans are retained records and prevent project deletion under the existing evidence-retention policy.

## Verification

Run `python -m pytest tests/test_building_assistant.py` in `backend`, and `npm test -- components/workspace/BuildingAssistant.test.tsx`, `npx tsc --noEmit`, and `npm run lint` in `frontend`.

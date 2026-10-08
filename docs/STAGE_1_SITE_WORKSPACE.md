# GeoAI Stage 1: Steps 4 and 5

Implemented 8 October 2026. Scope ends at deterministic site profiles, persistent conversations and explicitly reviewed project memory. No Nebius orchestration, tools, proposal generation, approval/build or generator changes were added in this batch.

Subsequent batch: `STAGE_1_ASSISTANT_RUNTIME.md` records the later Steps 6–9 implementation and its provider/execution limitations. The scope and verification below describe the original Steps 4–5 delivery.

## Implementation and files

- `backend/app/domain/site_workspace.py`: bounded, typed profile, message, context, memory and API contracts. `domain/stage1.py` adds compatible evidence source references.
- `backend/app/services/site_profiles/selection.py`: immutable selections and CRS resolution for AREA, ROUTE, CROSSING, POINT and ENDPOINTS.
- `backend/app/services/site_profiles/retrieval.py`: captures project/model/placement/terrain/source dependencies and retrieves existing terrain observations and retained project context.
- `backend/app/services/site_profiles/derivation.py`: deterministic geodesic/projected dimensions, sampling and valid profile slopes.
- `backend/app/services/site_profiles/evidence.py`: evidence identities, provenance and explicit unknown facts.
- `backend/app/services/site_profiles/service.py`: profile refresh, dependency verification, version deduplication, sample artifacts, missing information and existing readiness integration.
- `backend/app/services/assistant/storage.py`: ownership, stable identities and transaction serialization helpers.
- `backend/app/services/assistant/conversations.py`: conversations, immutable typed messages, frozen context, idempotent submission and persisted placeholder runs.
- `backend/app/services/assistant/memory.py`: four typed memory kinds, explicit review, scope, conflicts and audited supersession.
- `backend/app/api/routes/site_workspace.py` and `app/main.py`: project-owned routes and refresh background tasks.
- `backend/app/db/stage1_workspace_schema.py`, `app/db/models.py`, `alembic/versions/010_site_workspace.py`: additive profile refresh metadata and immutable sample artifacts; existing foundation tables remain in use.
- `backend/scripts/export_stage1_contracts.py`, `docs/contracts/stage1.schema.json`, `frontend/lib/generated/stage1.ts`: generated shared contracts.
- `frontend/components/workspace/PersistentAssistant.tsx`, `components/model-editor/ProfessionalModelEditor.tsx`, `app/projects/[id]/workspace/page.tsx`: persistence UI in the existing Assistant tab. Local/demo workspaces retain their existing flow.
- `backend/tests/test_site_workspace.py`, `test_site_workspace_migration.py`, updated `test_migrations.py` and `test_stage1_storage.py`, and `frontend/components/workspace/PersistentAssistant.test.tsx`: focused coverage.

## APIs

All paths below are relative to `/api/projects/{project_id}` and enforce existing project ownership. Referenced records must also belong to that project. Retry-safe commands use `clientRequestId`; revision/review operations enforce expected versions or states.

- Selections: `POST /site-selections`, `POST /site-selections/from-project`, `POST /site-selections/{id}/versions`, `GET /site-selections/{id}/versions/{version}`.
- Profiles: `POST /site-profiles`, `GET /site-profiles`, `GET /site-profiles/{id}`, `POST /site-profiles/{id}/refresh`.
- Profile details: `GET /site-profiles/{id}/readiness`, `/samples`, `/missing-information`; `GET /site-evidence/{id}`. Profile retrieval supports a specific version; samples are paginated and readiness accepts an operation.
- Conversations: `POST /conversations`, `GET /conversations`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`; `GET /assistant/runs/{id}`.
- Memory: `GET /memory`, `POST /memory`, `POST /memory/{id}/versions`, `POST /memory/{id}/versions/{version}/accept`, `POST /memory/{id}/versions/{version}/reject`.

## Site facts, evidence and unknowns

The pipeline snapshots saved selection, boundary, model revision, placement, active terrain and available source dependencies before work. It verifies dependencies again under a project lock before marking the immutable result current. A changed dependency leaves the completed historical result stale. Equivalent refreshes reuse a version. No geometry placement or terrain activation is performed.

AREA uses geodesic area/perimeter and a projected bounding rectangle; near-square orientation stays unknown. ROUTE and CROSSING support bounded terrain profiles and slopes only between adjacent valid samples with compatible vertical references. POINT samples one position. ENDPOINTS reports distance/bearing and endpoint samples without inventing a route. Unsupported extent and unresolved CRS fail explicitly. Large extents beyond the bounded local derivation limits are unsupported.

Only explicitly active terrain supplies elevation. Missing, outside-coverage, incompatible-reference and failed samples remain unknown; measured zero remains zero. Derived evidence names its inputs and algorithm/version. Public-map observations stay contextual; unvalidated survey and public-map facts do not become validated engineering inputs.

Nearby context reuses retained project SiteAnalysis data, spatially filtered around the selection. It does not make a new external map request. Retained responses have a digest and capture time; unknown original coverage is declared, results are PARTIAL, mock results are rejected, and empty results never assert absence. Context features and scan sizes are bounded. Source snapshots currently retain up to 100 records per source category. Project model references are identified separately from any assertion of spatial intersection.

Missing information includes elevation, soil, groundwater, utilities, flood level, survey accuracy, ownership and local code. Blocking depends on the requested operation: soil absence can permit conceptual work while blocking foundation analysis. Existing readiness rules remain authoritative.

Refresh uses the existing job tracking store plus a FastAPI background task. Persisted refresh state and a 120-second lease make interrupted work visible and retryable; this is not automatic durable queue replay. An old worker cannot overwrite a newer refresh.

## Frozen messages and explicit memory

The UI copies selected object IDs, saved geometry, model revision and dirty state at send time. A retry retains that exact submission. The backend resolves object references against the pinned saved revision and atomically persists ordered message parts, context, run and event. Site/profile, scenario, proposal and accepted memory version references are stored with the message. Later selection/model/memory changes do not rewrite old messages. Unsaved objects without saved revision identity must be saved or cleared first.

TEXT, ATTACHMENT, PROPOSAL, QUESTION, EVIDENCE and ASSUMPTION parts are supported. Attachment metadata and nested references are validated. Secret patterns are rejected and internal reasoning fields are not accepted. No provider is called: the persisted placeholder run reports `ORCHESTRATION_NOT_ENABLED`, with no fabricated assistant answer.

Chat does not create accepted memory. REQUIREMENT, PREFERENCE, DECISION and ASSUMPTION records begin as proposed and require explicit acceptance. Rejection is explicit. Accepting a proposed replacement version atomically supersedes the prior version and records an audit event; scope and kind cannot silently change. Conflicting accepted requirements in overlapping project/asset scopes return a conflict instead of being reconciled silently. The minimal UI supports manual requirement proposals and Accept/Reject cards; the API supports all four kinds.

## Verification

- Focused backend: **75 passed, 1 skipped** across `test_site_workspace.py` (44 tests), `test_site_workspace_migration.py`, `test_stage1_contracts.py`, `test_stage1_storage.py` and `test_migrations.py`.
- Existing backend regressions: **80 passed, 1 skipped** across engineering evidence/API/analysis, model revisions, building assistant, AI providers, asset catalogue and authentication ownership tests.
- Frontend: **41 passed** across PersistentAssistant, AssistantPanel, ModernAssistantPanel, BuildingAssistant, editor-analysis, useEditableModelEditor and WorkspacePanels. Final run used `--no-file-parallelism --testTimeout=15000`; one existing geometry test exceeded five seconds in the earlier parallel run and passed serially.
- TypeScript `tsc --noEmit`, ESLint, Python compilation and generated-contract consistency checks passed.
- Migration 010 applied to the local database after a backup. Existing project/model/placement/message counts and existing foreign-key violation count did not change. The isolated migration test starts from the prior schema and verifies retained records and immutable artifacts.
- Running API health, OpenAPI and project 317 conversation retrieval returned HTTP 200. Browser inspection verified the new Assistant panel in project 317; automated tests cover message persistence/reload, frozen retries and memory review.

Live PostgreSQL/PostGIS integration was **not run**: no dedicated `STAGE1_TEST_POSTGRES_URL` was configured and Docker/psql CLIs were unavailable. PostgreSQL DDL coverage is not a substitute for a live PostGIS run. SQLite remains the demo fallback and has no asserted spatial parity with PostGIS.

## Next scope

Stop here for this batch. Step 6+ still requires Nebius orchestration, the controlled assistant tool registry, generic proposal lifecycle and the approved deterministic building workflow. Other civil generators remain separate future work. In the current workspace, use Assistant to refresh site facts, save messages and review explicit memory; conversational AI responses are intentionally not enabled yet.

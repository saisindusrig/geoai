# GeoAI local cleanup and architecture refactor

Date: 15 October 2026. Scope: existing local application only. No Git commands, GitHub operations, deployment, installation, paid inference, numerical-method changes or visual redesign.

## Result and safety boundary

The cleanup preserves the existing architecture and engineering evidence, consolidates verified duplication, fixes job polling and unnecessary effect-driven renders, aligns local ports, and adds reproducible inventory/preservation checks. Uncertain source, prototypes, dependencies, launchers and historical engineering outputs remain in place for review. This is deliberately conservative: a filename or absent static import is not proof that a file is disposable.

The detailed evidence is in `docs/project-cleanup/`. All sizes are logical file sizes, not filesystem allocated-block measurements. Inventories exclude `.git` and task backup/acceptance files.

## Verified backups

Before application edits, source and retained assets were archived at `.cleanup-backups/20261015-132113/source.zip`: 65,241 files, 354,831,055 compressed bytes. ZIP integrity and every archived file's SHA-256 were checked. Installed dependencies, build/cache directories and credential files were excluded; credential files were left untouched. Existing engineering/storage assets were included.

SQLite's online backup API produced snapshots of 264 nonempty databases, including historical test databases. Every snapshot passed `PRAGMA integrity_check`. Empty database files were retained in place. `source-manifest.json`, `database-baseline.json` and `inventory-before.json` live beside the backup. The database baseline records table row counts and sorted per-row digests, including duplicate rows, without copying row contents into reports.

Browser acceptance initially intended to use `.cleanup-backups/acceptance.db` and `.cleanup-backups/acceptance-storage-copy`. However, a pre-existing server occupied ports 3001/8001; the isolated launches were refused and the early browser replays reached the original server. Preservation auditing detected this. All writes were stopped, the changed database was preserved as `.cleanup-backups/before-browser-recovery.db`, every changed/added row was traced to the replay workflows, and a concurrent-change check verified that nothing else had changed before SQLite online restore from the verified baseline. Final row fingerprints again matched all 264 original databases. See `browser-database-diff.json` and `browser-database-recovery.json`. Subsequent browser validation used dedicated ports 13001/18001, with a unique backend session marker checked before each test and separate acceptance database/storage. Backend regressions used a separate seeded database copy and separate output storage. Early attempts using an empty database failed because legacy tests require seeded demo tables; those attempts were stopped and replaced by the seeded run. Initial sandbox-restricted runs were stopped after local socket restrictions were diagnosed.

## Audit inventory and removal decisions

The initial complete folder inventory counted 287,732 files and 15,470,138,099 bytes across 332 groups. `inventory-before.json` and `inventory.json` provide counts, sizes, purposes and conservative removal decisions for every group. The source reference audit covers 463 frontend source/test/script files. Configuration auditing records names and reference counts for 49 backend settings, never their values.

Largest retained groups, approximately:

- `backend/.cad-proof-output`: 6,080 MiB / 119,298 files. Contains solver/CAD proof and historical execution environments. Retained because evidence and dependencies are mixed.
- `frontend/.next`: 1,906 MiB before validation. Generated build; rebuilt for production validation, retained.
- `backend/.venv`: 1,196 MiB. Active local runtime, retained.
- `frontend/.next-phase1`: 1,043 MiB. Local review server output, retained while in use.
- `frontend/node_modules`: 993 MiB. Required installed frontend dependencies, retained.
- `backend/.cad-proof-deps`: 809 MiB. CAD proof runtime, retained.
- `backend/storage`: 633 MiB / 55,296 files. User projects, geometry, drawings and solver output, retained and hashed.
- `backend/.venv-civicspan`: 200 MiB. Separate legacy runtime; consumers not disproven, retained.

Static analysis identified 35 frontend files without incoming imports and three packages without direct static imports (`@loaders.gl/core`, `@watergis/maplibre-gl-terradraw`, `cursor-style`). These are review candidates only: framework entrypoints, CSS/config imports, transitive consumers and dynamic loading need separate verification. No dependency or uncertain source was removed. Identical backend function bodies were audited with AST comparison; closure/module context prevents automatic merging of authorization, evidence and orchestration helpers.

Historical `.test-*` databases, `.cache` fixture manifests, CAD/DXF/PDF sources, engineering reports, revisions, original screenshots, Nebius configuration, old launchers and deployment documentation were retained. No mass deletion or broad directory moves occurred.

## Removed and consolidated files

`removal-manifest.json` records every removed or relocated file, its byte count, SHA-256 and reason. Cleanup removed 396 CPython bytecode files with verified interpreter magic under application/tests/scripts caches, plus three pytest-tagged disposable test-cache JSON files: 399 files / 5,950,696 bytes total. Bytecode regenerated by validation was cleared again from those verified paths. Runtime caches can naturally regrow.

The task adds backup and isolated acceptance data, so overall disk usage increases; the removed-byte total must not be described as net disk savings. Large evidence folders were not traded away for a larger headline saving.

- Shared `backend/app/services/design/geometry_metadata.py` replaces identical metadata envelope builders in the road and flyover generators. Existing private import names remain aliases. No geometric calculations, quantities, solver formulas, method versions or evidence authorization logic changed. Alignment/elevation regressions passed.
- Shared multipart transport in `frontend/lib/api.ts` eliminates duplicated request/error handling for survey and drawing uploads. Authentication and structured errors now follow the same transport path.
- Archived one-off polling benchmark and browser replay harnesses are recorded as task-generated relocations; canonical historical verification files are retained.

## Frontend changes

- Job polling schedules its next request only after completion, preventing overlap. Unmount/job changes ignore late responses. Callback changes no longer restart polling. Five consecutive failures pause polling with an error notification and exponential backoff between failures. Completion stops polling. The server-side job is not cancelled by a polling pause; reload the workspace to resume checking.
- Footing flexure, RC flexure and finite bearing history state is keyed by project/revision. A revision change initializes clean loading state before fetching instead of triggering a synchronous loading-state effect and extra render.
- Scene Layers expands on actual selection changes; scrolling remains a DOM effect. Removed an unused test import and replaced explicit `any` annotations in three historical browser specs with inferred/structural types.
- Existing UI layout, engineering forms and numerical displays remain intact.

## Backend and development environment

The existing boundaries remain: FastAPI routes in `backend/app/api/routes`, models/session/migrations in `backend/app/db` and `backend/alembic`, engineering/CAD/geometry/OpenSees calculations in `backend/app/services/design`, AI in `services/ai` and `services/assistant`, and persistent artifacts in `backend/storage`.

The frontend retains routes in `frontend/app`, the 3D scene/editor and engineering panels in `components/model-editor`, shared UI in `components/ui`, lifecycle and project state in `hooks`/`stores`, and transport/math/presentation helpers in `lib`. Moving these files wholesale would create unnecessary reference churn and risk locally modified functionality.

`run-website.bat` remains the preferred offline launcher. Frontend uses localhost:3001 and backend localhost:8001. npm dev/start, Playwright defaults, API/storage fallbacks, backend app-origin default and local setup documentation now agree. Existing environment overrides remain available and secrets were not edited.

The PowerShell launcher uses a named mutex and refuses an occupied port whose health check fails, preventing concurrent launcher startup and duplicate servers. Its existing readiness loop is bounded. Legacy launchers remain because their consumers are not disproven. The launcher was parsed successfully and the local servers/browser were exercised.

The backend full suite exposed generated Assistant API contract drift: `assistantMode` and `requestedModel` already existed in the backend model but were absent from generated TypeScript/schema artifacts. Only the generated outputs were synchronized with the existing model; no backend model or engineering evidence schema changed. The formerly failing contract test and all related contract tests then passed.

## Measured performance

The archived pre-cleanup polling hook and current hook were tested under identical fake-timer/network conditions:

- Unresolved requests after 10 seconds: before 10, after 1 (90% fewer concurrent requests).
- Failed requests over 120 seconds: before 120, after 5 (95.8% fewer requests).
- Current hook ignores completion after unmount and notifies completion once.

`polling-performance.log` contains the measured counts; the archived harness documents the procedure. These are controlled request-load measurements, not claims about production FPS, total bundle reduction or real-network latency. Production build compiled in 34.4 seconds, TypeScript took 25.7 seconds and static page generation took 584 ms. No comparable pre-change production-build measurement was collected, so no build speedup is claimed. The initial broad frontend test run timed out once under load; bounded-worker runs passed all tests. Test wall times are affected by parallel validation and are not application speed measurements.

## Validation and known limitations

- Frontend final unit/component suite: 68 files / 332 tests passed.
- Full lint: passed with zero warnings after the cleanup fixes.
- TypeScript: passed. Production build: passed.
- Full backend run: 1,734 passed, 2 skipped, 1 failed in 526.66 seconds. Its sole failure was generated contract drift; after synchronization the contract suite passed 24 tests. The entire 1,737-test suite was not redundantly rerun after that generated-artifact-only fix.
- Road/flyover alignment and elevation regression: 18 passed.
- Backend engineering coverage in the full run includes OpenSees execution/error/timeout evidence, soil/bearing/settlement, footing demand, nominal RC flexure, input validation, authorization, stale evidence, CAD import/editing and model revisions. Dedicated PostgreSQL integration requires its external test environment and remained skipped.
- Initial browser replay: 15 passed / 4 failed. It passed creation UI, edit/undo/redo/save/reload, Assistant persistence and explicit network retry, and footing flexure authorization/staleness/reload. Failed historical tests included hidden/collapsed controls and stale saved source evidence.
- All six requested projects (793, 794, 788, 802–804) passed separate browser rendering/selection/Inspector/Analysis checks, with screenshots and JSON evidence.
- The finite bearing replay passed on the standard-port server; those test writes were subsequently included in the verified database recovery. That run is not represented as isolated.
- The earlier RC replay for project 804/revision 124 returned HTTP 409 because shared original-server test writes invalidated its upstream demand. After restoring originals and moving to the uniquely attested acceptance session, the complete RC browser replay passed in 47 seconds: exact consent, independent demand, nominal mechanics/layout, rejection cases, staleness and reload. No stale-result rule or source evidence was weakened.
- Two historical CAD browser replays remain failing: the CAD-soil replay cannot find its diagram action after saving/reloading current panel state; the drawing-CAD replay times out in the older UI workflow. Their logs are retained, including an attested isolated CAD-soil reproduction. CAD import/calculation/authorization backend regressions passed. These UI replay failures remain technical debt, not a fully green end-to-end claim.

Browser evidence and final replay logs are retained under `docs/project-cleanup/`. The browser suite is not represented as entirely green. New real cloud inference, PostgreSQL/PostGIS, internet map providers and live Nebius behavior were outside this offline validation.

## Before and after structure

The top-level application structure remains:

```text
backend/
  app/{api,core,db,domain,experimental,middleware,services,workers}/
  alembic/  scripts/  tests/  storage/
frontend/
  app/  components/  hooks/  lib/  stores/  scripts/  e2e/  public/
docs/
run-website.bat
start-copilot-review.ps1
```

Additions after cleanup:

```text
backend/app/services/design/geometry_metadata.py
backend/scripts/project_cleanup_audit.py
frontend/hooks/useActiveJobPolling.test.tsx
docs/PROJECT_CLEANUP_REPORT.md
docs/project-cleanup/{inventories,reference-audits,preservation,manifests,logs,browser-evidence}/
.cleanup-backups/{verified-source-and-SQLite-snapshots,isolated-test-data}/
```

No existing source directory was relocated. Before/after inventories provide the precise file counts and sizes rather than suggesting a wholesale architecture rewrite.

## Remaining review work

1. Review the remaining historical browser replay failures using the attested isolated session. Cleanup does not authorize rewriting immutable results to force acceptance.
2. Refresh historical browser tests for current collapsed sections and prevent inter-test dependence on shared saved evidence. Keep original verification evidence.
3. Manually classify mixed CAD proof environments/evidence before reclaiming their several gigabytes.
4. Review the 35 source and three dependency candidates with dynamic/CSS/framework consumers included.
5. Continue breaking down the large editor/API modules by tested behavior in future focused changes. Do not merge authorization helpers simply because their bodies match.
6. Pydantic emits existing schema-discriminator warnings; FastAPI's test client emits a dependency deprecation warning. No packages were installed or upgraded for cleanup.

## Preservation and local use

`database-preservation.json` compares every backed-up database's table fingerprints against the original files. `storage-preservation.json` hashes every original storage file; final verification found zero changed or missing files across 55,296 originals. Additional task-generated solver evidence and the two test model exports remain retained; no pre-existing storage file was replaced or removed. Reports contain hashes/counts rather than credentials or private database rows.

Local website: http://localhost:3001/projects/793/workspace. Offline startup: `run-website.bat`; backend health: http://localhost:8001/api/health. The standard-port website is the pre-existing original-database server. Temporary attested acceptance servers use separate ports and are stopped after validation. Original data was restored and verified after the initial port-collision incident.

## Final verification snapshot

The final inventory contains 289,697 files / 15,526,411,652 logical bytes across 333 groups, excluding `.git` and task backups. Backups, recovery snapshots and isolated test data retain another 1,481,117,225 bytes. Retention increases total disk use; direct disposable-file cleanup reclaimed 5,950,696 bytes (about 5.68 MiB). Eleven task-generated harness files were relocated out of frontend source discovery. All 264 original databases match baseline rows **and SQLite schema definitions**, and all 55,296 original storage files match their archived hashes. Original generated Next declarations and pre-existing browser-test status artifacts were restored from the source archive after temporary acceptance use. The temporary 13001/18001 servers were stopped; the pre-existing normal website remains at 3001/8001.

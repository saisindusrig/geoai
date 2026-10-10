# GeoAI Phase 3B2B — experimental CAD workspace acceptance

Recorded 10 October 2026 (Asia/Calcutta). This phase integrates the existing native CAD worker with the existing proposal, ModelRevision, lineage and Cesium editor systems. Production CAD Build remains disabled. No new geometry primitive, specialist, AI routing or ModelRevision database schema was introduced.

## 1. Experimental execution architecture

An owned human application command records a conversation message without AI orchestration. A validated `bim-project/1` assembly and existing CAD mapping produce a `cad-geometry/1` snapshot. The snapshot is stored privately and its SHA-256 becomes an immutable requirement of an ordinary CUSTOM proposal. Explicit application approval uses the existing ProposalService hashes, assumption acknowledgements, dependency manifest and state transitions.

The separate experimental execute endpoint runs its supervisor in a thread. OCCT/OCP still executes exclusively in the existing bounded child process. The service verifies results, publishes private content-addressed artifacts and commits an ordinary ModelRevision and existing object lineage. It does not register an AI chat tool or a production executor.

Existing defaults remain 30 s wall time, 20 s CPU, 1024 MiB memory and two process-local worker slots. The prior Linux acceptance remains [the recorded 3B2A run](https://github.com/saisindusrig/geoai/actions/runs/37974990667): 170 passing tests and 533 successful native linkage checks. Phase 3B2B browser/backend integration was tested on Windows; it was not newly deployed on Linux.

## 2. Feature gate

Server access requires all three explicit environment settings: `GEOAI_EXPERIMENTAL_CAD=true`, an integer user allowlist in `GEOAI_CAD_TEST_USER_IDS`, and an integer project allowlist in `GEOAI_CAD_TEST_PROJECT_IDS`. Unset or malformed configuration denies access. Project ownership is checked independently on review, approval, execution, mesh retrieval and CAD-bearing manual saves. Frontend visibility follows the server capability endpoint and cannot authorize execution.

The acceptance helper enables only user 1/project 9001 in its isolated process. It uses an isolated SQLite database, local artifact roots, development authentication and ports 8001/3001. These settings are not written into normal application configuration. Normal deployments must retain their existing authentication requirements. No ordinary chat automatically invokes CAD generation.

## 3. Approval and revision integration

Review requires an owned USER message, a saved clean source revision and valid BIM/CAD contracts. Authored provenance is replaced with server-owned project, revision hash, design identity and version. The fixture command requires a current site profile; normal proposal approval/build checks bind site selection, placement and source dependencies. A stale approval, changed source, wrong actor, wrong snapshot binding or missing approval cannot finalize.

The review UI displays ten component definitions, recipes, materials and metre-based parameters, source revision, exact snapshot hash and explicit engineering/clearance limitations. Approval requires an affirmative assumption acknowledgement. Geometry with declared unresolved connections is rejected for review; the ten-component fixture declares no solved connections. The service never automatically moves supports.

The existing ModelRevision persistence function is reused with an internal CAD publication flag. External manual-save JSON cannot enable that flag. Existing lineage records are retained and trusted CAD lineage is attached through the existing tables. Database schemas are unchanged.

## 4. CAD artifact persistence and publication

Each CAD component stores small references: catalog, definition, B-rep and mesh hashes; semantic component/asset/assembly identity; material; authoritative parameters; source/design revision; proposal/approval; private snapshot reference and engineering status. Native binary B-reps and render triangle arrays are not embedded in ModelRevision JSON.

Publication sequence: finish native compilation; reacquire project/source/dependency checks; verify complete native results and artifact bytes; atomically write private content-addressed files; flush the manifest/catalog; persist the normal revision and lineage; record the idempotent result; transition the proposal to BUILT; commit the database transaction. Worker, storage, database-flush or stale-source failures expose no new ModelRevision and preserve the prior revision. A manual revision created during native work wins; CAD finalization rejects the stale source.

Committed retries verify referenced artifacts and return the original revision without recompilation. Local orphan inventory now includes committed private review snapshots as well as manifests and their B-rep/mesh references. It is an authorized dry-run with deletion disabled; corruption aborts inventory. Rollback can leave unreferenced private bytes, requiring retention/grace reconciliation rather than deletion during active work.

Mesh retrieval checks ownership, experiment capability, catalog membership and SHA-256 integrity. Responses use `Cache-Control: private, no-store`. Browser loading authenticates, reauthorizes cached references and independently verifies hashes before consuming triangles. Corrupt or missing bytes fail closed. Private CAD has no public URL and is omitted from the ordinary public GLB export; that export can still contain unrelated ordinary objects. Private CAD export is not implemented.

## 5. Real Cesium rendering

The existing editable-model renderer consumes the authorized native triangle meshes. It does not substitute boxes. Actual Chrome/WebGL acceptance shows the I-section beams, circular columns and slab opening. Materials and component entity IDs are retained.

Native bytes remain in project-local metres. Editable geometry subtracts the component bounds-center pivot; the normal node transform restores that center and applies rigid rotations/translations. Rendering uses the existing local ENU/heading-to-ECEF conversion. Regeneration rebases a changed pivot while preserving the prior rigid transform; a backend test includes a 90-degree manually rotated primary beam.

The installed Cesium 1.145.0 official browser build is loaded from the existing copied `/cesium` assets. This bounded packaging correction avoids invalid ZIP/WASM template escaping observed in the Next-minified Cesium dependency chunk. It introduces no new Cesium version or vendor service. Missing runtime/mesh failures remain visible and have no approximate-geometry fallback.

## 6. Selection and Inspect

All ten components are selected through the real Layers UI and inspected. A separate real-engine test projects actual triangle centroids, checks Cesium depth picking, clicks the canvas with Playwright mouse input and verifies the corresponding Inspect identity for every component. Test-only engine observation is injected by Playwright; no public test globals or mocked geometry are added to application code.

Inspect displays component, asset, assembly, material, design version, source revision, CAD status, parameters and preview assumptions. Engineering remains `UNVERIFIED`; unknown elevation is explicit. Direct mesh/material/semantic edits, scaling, duplication and deletion are rejected; hiding is supported. Unsupported edits surface an error. A rejected scale change is also saved through the real endpoint to verify authoritative scale remains `[1,1,1]`.

## 7. Save/reload and History

The ordinary editor persists a supported 0.1 m rigid translation, reloads it, compares the revision in History and reports zero added, zero removed and one modified component. Layers hide/show is exercised and saved. Comparison loads authorized meshes for both revisions through the same renderer. Stable component IDs and existing lineage survive ordinary manual revisions.

## 8. Ten-component SUPPORT_FRAME acceptance

The fixture is generated in a real isolated owned project through the explicit review/approval/execution endpoints. Source revision and snapshot binding are captured; the existing native worker compiles all ten components; private hashes verify; a normal ModelRevision contains ten CAD components plus the existing ordinary box. Approval, ModelRevision creation, all-component Layers/Inspect, direct native-triangle picking, hide/show, supported transform, save/reload and History comparison are exercised in the actual application.

The helper uses the existing project/workspace page, FastAPI application, ORM and persistence; it is a test harness, not a second product workspace or revision database. It blocks Nebius HTTP transports and configured cloud storage. No production project or cloud bucket is used.

Final owned-project retrieval confirmed revision number 6, eleven total components, ten CAD components, design version 2, CAD source revision 4 and engineering `UNVERIFIED`. Revision 6 includes the final unchanged-scale save. Only the isolated acceptance servers are stopped after verification; the user's ordinary development server is preserved.

## 9. Parameter regeneration

After explicit site-profile refresh following saved edits, a 5 m to 6 m parameter change is validated and reviewed as a new proposal. Only `primary-0` and `primary-1` enter native recompilation. The other eight retain semantic IDs and the same B-rep/mesh hashes. Browser assertions independently compare those hashes and preserve the manually moved plate. The unrelated existing component is preserved exactly.

Definition hashes advance with the new server provenance even when reusable artifact bytes remain unchanged. Reuse is determined from validated geometric definitions excluding provenance, not by assuming bitwise native reproducibility across platforms. Supports are not repositioned; clearance rules and structural connection adequacy remain unvalidated and explicitly acknowledged.

## 10. Atomicity and ownership tests

Ten new CAD workspace tests cover default-off and ownership denial; approval prerequisite; native revision/identity/idempotency; reviewed parameter propagation and rigid-save preservation; stale, worker and storage failures; unauthorized, corrupt and missing mesh retrieval; forbidden manual CAD authority/scale changes; rollback after revision flush; and manual revision creation during native work. The committed-snapshot orphan check is included.

The existing CAD proof/integration/deployment tests continue to cover native validity, hashes, worker isolation, resource failures and private storage. No resource limit, safety gate or failing assertion was weakened.

## 11. Existing-object and architecture preservation

The test starts with an ordinary retained box. It remains unchanged through generation, manual CAD saves and regeneration. Production Building/Building Patch and AI3D V1/Generic3DExecutor regression tests pass. Qwen PRIMARY, ModelRouter, production executor routing, AI configuration, normal approval behavior and workspace layout are not changed by this phase. Pre-existing unrelated working-tree edits are preserved. No Nebius request was made.

## 12. Exact verification results and evidence

- Full backend: **864 passed, 0 failed, 2 skipped**, 3 warnings, 260.06 s. Includes AI3D V1 44, BIM foundation 20, Building assistant 15, Building Patch 19, Building specialist 25, Building workspace acceptance 1, CAD integration 26, CAD proof 23, CAD deployment 8, CAD workspace 10 and ModelRevision 5 tests.
- Final CAD workspace rerun: **10 passed, 0 failed, 0 skipped**, 1 warning, 16.25 s. Includes the final missing-artifact assertion and review-detail/orphan assertions added after full-suite collection.
- Full frontend: **197 passed, 0 failed, 0 skipped**, 41 files. Final cache-order correction additionally verified by **4 passing CAD mesh tests**.
- TypeScript: `tsc --noEmit` passed. ESLint passed with `--max-warnings 0`.
- Production build: Next 16.2.9 `next build --webpack` passed; compile 14.9 s, TypeScript 10.3 s, all 15 static pages generated. The build ran in an isolated source copy so the user's live development server/cache remained untouched. Tailwind scanning in that copy was explicitly scoped to frontend sources; installed modules and existing static assets were shared. No harness-only build paths/configuration were written into application source.
- Real Chrome acceptance: **2 passed, 0 failed, 0 skipped**, 16.7 s, together on a fresh isolated project using the final production build. The generation/editor/history/regeneration test took 10.8 s; ten-component native-triangle picking and rejected-scale save took 5.0 s. The final helper run identity is `browser-final-5`.

The two existing backend skips are `test_user_cannot_compare_other_users_scenarios` (fixture lacks two scenarios) and `test_postgresql_upgrade` (dedicated PostgreSQL/PostGIS database unavailable). CAD ownership tests execute and pass. The full backend was tested with a fresh seeded file-backed SQLite database; PostgreSQL acceptance is not implied. Warnings are existing Starlette/httpx and Pydantic schema warnings.

Local evidence, deliberately ignored and not published: `backend/.cad-proof-output/3b2b-backend-final-verified.log` and `.xml`; `3b2b-workspace-verified.log` and `.xml`; `3b2b-frontend-verified.log`; `3b2b-types-final.log`; `3b2b-lint-final.log`; `3b2b-build-final-verified.log`; `3b2b-browser-final-verified.log`; `3b2b-browser-picking-verified.log`; and `3b2b-browser-evidence/` screenshots. Private databases/artifacts and native caches are excluded from Git.

Failure evidence is retained. Initial full-backend attempts used thread-local in-memory SQLite, then an unseeded file database; these produced 44 and 14 failures respectively before fresh database seeding corrected the harness. An existing dashboard intent regression was fixed by opening the dialog for `newProject=1`. Next rejected a pre-existing named page export; the unchanged legacy implementation was moved to a component, retaining the same default dashboard. The actual browser exposed invalid minified Cesium ZIP/WASM strings, corrected with the installed official browser runtime. Browser test fixes retain response evidence through an idempotent retry after reload, distinguish the application alert from Next's route announcer, use real integer mouse coordinates and wait for live selection-triggered primitive replacement/rendering. Earlier failing logs/screenshots remain available; tests and resource limits were not bypassed.

## 13. Files changed in this phase

Backend additions: `app/api/routes/cad_experimental.py`, `app/experimental/cad_capability.py`, `app/experimental/cad_workspace.py`, `app/experimental/cad_revision.py`, `tests/test_cad_workspace.py`, `scripts/serve_cad_workspace_acceptance.py`.

Backend updates: `app/main.py`, `app/api/routes/model_revisions.py`, `app/services/design/editable_model.py`, `app/experimental/cad_artifacts.py`.

Frontend additions: `lib/cad-mesh.ts`, `lib/cad-mesh.test.ts`, `lib/cesium-runtime.ts`, `components/model-editor/ExperimentalCadReview.tsx`, `components/dashboard/LegacyDashboardPage.tsx`, `e2e/cad-workspace.spec.ts`.

Frontend updates: `lib/types.ts`, `lib/sandbox-geometry.ts`, `lib/editor-transform.ts`, `hooks/useEditableModelEditor.ts`, `components/map/CesiumView.tsx`, `components/model-editor/ComponentIdentity.tsx`, `components/model-editor/ProfessionalModelEditor.tsx`, `components/dashboard/CreativeDashboard.tsx`, `app/dashboard/page.tsx`.

Documentation: this report. The broader dirty checkout contains work from earlier phases and unrelated user changes; that entire Git diff is not attributed to 3B2B. No commit, push, production deployment or PR update was performed for this phase.

## 14. Unresolved production blockers

Redistribution/legal acceptance remains unresolved: OCCT/OCP/VTK notices, bundled third-party obligations and corresponding-source requirements must be closed against the 3B2A inventory. Build/runtime success is not licensing approval.

Durable fleet admission/queueing, leases, crash/restart recovery and reconciliation remain unimplemented. Concurrency is process-local. Real cloud storage privacy, authorization/durability and remote orphan reconciliation remain unverified. This phase exercised local isolated resources only.

Unknown terrain/elevation, foundations, loads, structural adequacy, clearance/connection rules and code compliance remain unvalidated. Valid B-reps do not certify engineering safety. The UI is an experimental fixture/parameter acceptance path, not broad asset authoring. Production-scale browser memory/performance, CAD export, PostgreSQL integration and wider platform/browser acceptance need separate work.

## 15. Recommended Phase 4 work — not implemented

Next, keep AI output limited to validated `bim-project/1` assembly proposals: component roles, explicit units, parametric dependencies and declared connection intent. Bind identity/evidence/source revisions on the server; present assumptions and unresolved relationships; preserve exact-snapshot human approval; reject unsupported mappings or unresolved connections before finalization. Extend acceptance incrementally with approved parameter changes and stale-context/failure cases. Keep production CAD Build disabled until licensing, storage and durable-worker blockers are closed. No Phase 4 generation, asset specialist or engineering solver is started in this batch.

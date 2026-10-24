# Milestone 3 — Runtime diagnostics and reliability

Completed locally; stop after this milestone. No engineering methods, numerical formulas or authorization gates changed.

## Working interface and runtime
Open http://localhost:3001/diagnostics. Dashboard and Settings link to it; Analysis provides a saved-project/revision context link. The normal project 793 context is http://localhost:3001/diagnostics?project_id=793&model_revision_id=103.

The compact read-only view distinguishes Healthy, Degraded, Blocked and Unavailable. It reports API connectivity, database/schema connectivity, local OpenSees version, offline controls, saved evidence freshness, supported/missing/unsupported/stale capabilities, existing release-warning codes and manual recovery actions. Details are expandable. Original engineering data and credentials are never included in its response.

Reused existing liveness routes, database_status, production warning collection, engineering capability/history adapters, ownership gates, API transport, cards/badges and offline launcher. No provider is contacted. The fixed three-second OpenSees probe only asks Tcl for its version; no model, FEA or artifacts are created.

Confirmed normal runtime: frontend 3001, API 8001, same-origin health succeeds, database connection/schema current, OpenSees 3.8.0, offline deterministic controls, project 793/revision 103 accessible with one current planar result. Production qualification remains BLOCKED. The existing launcher successfully reuses these servers without starting duplicates (launcher-reuse.log).

## Reproducible issues resolved
- The prior normal port 3001 listener served an obsolete production build without the current page/proxy. Its exact repository process was identified and replaced with the existing offline development launch configuration; the compiled build and engineering data were preserved. Initial occupied-port failure remains recorded in web-error.log.
- Installed Windows OpenSees emits the fixed version marker on stderr. The probe now recognizes that marker on either stream; banners, paths and raw stderr are not returned.
- Visual mode/case changes no longer download complete saved histories. Histories are reused for the saved context; backend capability/freshness is still revalidated on navigation and view changes. Manual Refresh invalidates the history cache. Changed model context and completed explicit mutations also refresh it. Stable selection values avoid requests caused solely by a new array reference. Abandoned GETs are cancelled; mutation behavior/idempotency is unchanged.
- Diagnostics clears prior health on refresh/failure, bounds requests at ten seconds, prevents concurrent refreshes and requires manual Retry. No automatic polling or mutation replay.
- Browser inspection found lower cards clipped by the existing page shell; a scoped scroll container now exposes every capability and recovery note.

## Focused verification
- Backend: 30 passed, covering diagnostics/liveness contracts, solver timeout/missing executable, credential redaction, DB outage, ownership, missing records, stale/unsupported results and existing frame authorization/hash gates (backend-final.log).
- Frontend: 24 distinct focused tests across six files passed. Eighteen runtime/workflow/transport tests are in frontend-final.log; six result-identity/selection regressions passed in frontend-targeted.log. The final cached-history change reran only its seven workflow tests (workflow-final.log).
- TypeScript and scoped ESLint passed (typescript-final.log, lint-final.log, workflow-lint.log).
- Fresh Chromium: two diagnostics/recovery tests passed at 1280×900 and 1600×900 (browser-final.log); normal project 793 saved-result/mode-switch smoke passed (workspace-final.log). Tests block modifying and external requests. Transport failure is simulated in the browser; the real API remains running. Recovery checks confirm one request per manual action, no stale healthy cards, keyboard refresh and scroll access. No physical server-kill recovery or complete legacy browser suite was claimed.
- Initial browser recovery assertions failed because Next's route announcer also has role=alert; the selector was scoped to the application. Initial failures remain in browser.log. A reused preservation script initially looked for its output in the prior milestone folder; output routing was corrected and the already completed scan reused (preservation.log, preservation-final.log).
- Existing Starlette/httpx and Playwright color-environment warnings remain; no dependency changes were made.

Screenshots: diagnostics-1280.png, diagnostics-1600.png, capabilities-1280.png, capabilities-1600.png, unavailable-1280.png, unavailable-1600.png and normal-results-1600.png. Browser metadata: browser-1280.json, browser-1600.json, workspace-smoke.json.

## Preservation comparison
Reused existing manifests, without full-project backups or database copies. All 10,266 original database rows and schemas exactly match the Milestone 2 baseline. All 10,500 pre-existing isolated rows remain unchanged, with zero appended rows. Existing spatial evidence: 635 files unchanged; coupled solver evidence: 21 files verified.

The established original-storage scan checked 55,296 storage files and 2,090 CAD/engineering proof files: none changed or missing. All 264 baseline database schemas match, and 263 database fingerprints are identical to the older backup. The development database differs only by 27 rows already present before this milestone; the strict Milestone 2 row comparison confirms this milestone added or modified none. Conversation, usage, authorization and audit rows are included in these checks. See milestone-preservation.json, review-preservation.json, coupled-evidence-preservation.json, preservation-manifests.json and preservation-audit.json.

## Changed source/tests
- backend/app/api/routes/runtime_diagnostics.py (new); backend/app/main.py (route registration).
- backend/tests/test_runtime_diagnostics.py (new).
- frontend/components/settings/RuntimeDiagnostics.tsx and RuntimeDiagnostics.test.tsx (new); frontend/app/diagnostics/page.tsx (new).
- frontend/components/settings/SettingsPageClient.tsx and frontend/components/dashboard/DashboardSidebar.tsx (links).
- frontend/lib/api.ts (optional abort signal for GET only).
- frontend/components/model-editor/GuidedAnalysisWorkflow.tsx and GuidedAnalysisWorkflow.test.tsx (context link, explicit refresh, cached histories, freshness/cancellation and stable selection).
- frontend/e2e/runtime-diagnostics.spec.ts (new). Evidence/scripts/logs live in this folder.

## Remaining release blockers
Existing production-readiness findings remain: development identity/configuration, durable production database/jobs/storage and recovery qualification, previously reported dependency advisories, security/capacity testing and unsupported engineering domains. Dependency advisories were not re-audited or fixed here. Diagnostics does not qualify a production deployment, validate connection capacity or approve engineering safety. Hosted AI and paid inference remain untested and disabled by the normal offline launch. No isolated review server or new demonstration project was needed.

No Git operation, installation, deployment, paid inference, cleanup or further milestone was performed.

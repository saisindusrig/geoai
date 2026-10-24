# Final workflow validation

Labels describe evidence strength, not a production guarantee. No workflow is LIVE VERIFIED in this final run.

| Workflow | Classification | Verified / remaining |
|---|---|---|
| A Authentication | TEST ENVIRONMENT VERIFIED (API), MOCK VERIFIED (components) | Backend JWT/ownership/admin tests, invalid/unauthorized cases, safe postauth URL tests. Full production sign-in/logout/expiry UI journey NOT VERIFIED; local frontend uses existing mock mode unchanged. |
| B Project management | MOCK VERIFIED (browser), TEST ENVIRONMENT VERIFIED (API) | Dialog keyboard, create failure/retained name/retry/open/context return; isolated folders/ownership APIs. Dashboard optimistic rollback and request guards unit-tested. Rename/reopen complete full-stack UI journey NOT VERIFIED; no real project mutation. |
| C Geospatial workspace | MOCK VERIFIED smoke; NOT VERIFIED for full engineering acceptance | Fresh unsupported zero canvases, desktop map/workspace/analysis initialization with synthetic project and offline resources; historical read-only saved-model smoke. Drawing, measurement, actual terrain, selection/undo/save/reopen on disposable full-stack fixture not executed. Existing editor unit tests pass. |
| D AI generation | TEST ENVIRONMENT VERIFIED (job APIs), MOCK VERIFIED (polling) | Queued/running cancellation, failure metadata, timeout and safe errors in isolated process; five-failure same-job polling recovery via mock timers. No second POST on recovery. Full submitted design/preview/completed/export/refresh journey NOT VERIFIED, no paid job. |
| E Engineering analysis | MOCK VERIFIED components; NOT VERIFIED end-to-end | Existing result/solver-evidence/UI regression suite passes; no solver fabricated or numerical algorithm changed. No authorized full-stack analysis executed. |
| F BOQ/cost | MOCK VERIFIED | Populated 100-row cost/BOQ fixtures, zero presentation, missing-data/retry/draft guard and duplicate-save component coverage; cost keyboard scrolling in browser. Actual persisted BOQ save/scenario reload NOT VERIFIED. |
| G Reports/exports | MOCK VERIFIED | Long report fixture, read-only mobile, failed/successful assumption retry, downloaded timeline JSON filename/30 phase and timeline content exactly match fixture; mocked JSON attachment filename/content. Real PDF/CSV/GLB and bearer-authenticated download transport NOT VERIFIED; source risk below. |
| H Settings/providers/admin | MOCK VERIFIED UI; TEST ENVIRONMENT VERIFIED authorization | Unknown/retry/unmount/component states, empty/error/populated tables, browser offset=100 pagination; API permission tests. No live provider outage, key editing or rate/template production mutation. |

Nine browser checks all passed: 
- PASS: project dialog keyboard trap, Escape and focus return
- PASS: project create failure retains name; retry posts once and opens same project
- PASS: populated cost table scrolls by keyboard
- PASS: usage pagination reads offset=100 and preserves table
- PASS: mobile report is read-only; timeline download contains exact fixture
- PASS: report export attachment has expected format, filename and fixture content
- PASS: desktop report save failure preserves draft and successful retry recovers
- PASS: forced-colors and reduced-motion keyboard focus
- PASS: 150-project library renderer and memory observation

**Release risk (P1, source-confirmed transport mismatch):** export links/iframe/window.open use apiUrl directly, while backend get_current_user_id expects Authorization: Bearer when JWT is required. Browser navigation does not attach the localStorage token as a bearer header. The local mock-account download fixture therefore cannot prove authenticated production export. Required resolution: integrate authenticated binary download/preview transport (with server filenames, errors and duplicate guards) across report, cost/BOQ and assistant export entrypoints, then test real protected downloads in an isolated JWT environment. Do not disable authentication or put tokens in URLs. This cross-entrypoint integration remains open; release is NO-GO.

No original project was mutated. Browser application API calls were intercepted; POST/PUT operations used only in-memory fixture responses. Backend API tests used an explicitly asserted separate SQLite database and test storage. No production credentials, paid AI, solver formulas, geometry algorithms, BOQ arithmetic, database migration or authorization policy was changed. Existing unrelated work remains intact.


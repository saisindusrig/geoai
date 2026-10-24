# Test results — current responsive-policy follow-up

22 October 2026, Asia/Calcutta. This report supersedes the earlier 403-test/405-distinct-test summary; original logs remain as historical evidence. Current results distinguish unit/component mocks from read-only browser checks and unexecuted live workflows.

## Executed automated checks

| Check | Actual latest result | Evidence |
|---|---|---|
| Full frontend unit/component suite | **420 tests passed across 91 files**, 21.50s, exit 0. Existing geometry/editor/undo/auth/engineering tests plus device admission, return context, polling resume, provider/admin recovery and missing metrics. | [full log](logs/ui-audit-followup-full.log) |
| Device/return-policy/provider/event-page focused run | 8 passed at that stage; included in subsequent full run. Later added provider-success/admin-empty/return-link tests are included in the current full count. Do not add focused tests to the full total. | [focused log](logs/ui-audit-device-tests.log) |
| Final provider test rerun after explicit Unknown label | 2 passed, exit 0; already included in the full total. | [provider final](logs/ui-audit-provider-final.log) |
| TypeScript | `npx tsc --noEmit` passed; final production build also completed TypeScript. Initial nullable paused-job error was fixed. | [types](logs/ui-audit-followup-types.log), build log |
| Full frontend lint | `npm run lint` passed, zero warnings under max-warnings 0, exit 0. Initial admin-effect warnings were fixed using the existing deferred initial-load convention. Final changed provider file also passed scoped ESLint. | [lint](logs/ui-audit-followup-lint.log), [provider lint](logs/ui-audit-provider-lint.log) |
| Final production build | **Passed**, exit 0. Compile, TypeScript, prerender and route manifest completed. | [build](logs/ui-audit-followup-build.log) |
| Task-scoped Windows-aware Git diff check | **Passed**, exit 0, with normal LF/CRLF notices. New untracked sources are not covered by Git diff and were included in lint/types/tests/build. | [diff check](diff-check-followup.log) |

Vitest still reports the existing environmentMatchGlobs deprecation warning. No backend suite was run; no backend/solver/API-contract implementation was changed. This is not a live generation/export E2E test run.

## F21 device-support evidence

Support predicate: `min-width: 1280px` and `any-pointer: fine`. It is a conservative UI capability rule, not a physical-tablet certification or UA classification.

| State | Actual browser observation | Evidence |
|---|---|---|
| Fresh workspace at 390×844 | Desktop Required heading and exact supplied copy; project #805; Back to Dashboard; **0 canvases**, one main and one main-content ID | [390 screen](screenshots/followup/desktop-required-390.png) |
| Back to Dashboard | Actual navigation succeeded; same local path/query retained; dashboard return link resolved saved project name and `/projects/805/workspace?demo=1` | [context return](screenshots/followup/dashboard-return-390.png) |
| Fresh workspace at 768×900 | Desktop Required; **0 canvases** | [768 screen](screenshots/followup/desktop-required-768.png) |
| Fresh workspace at 1024×900 | Desktop Required; **0 canvases** | [1024 screen](screenshots/followup/desktop-required-1024.png) |
| Desktop at 1280×900 | Saved 3D model, workflow/tools and Fit All present; **1 canvas**; no controls compressed for mobile | [desktop](screenshots/followup/workspace-desktop-1280.png) |
| Admitted desktop resized to 768 | Restriction screen with saved project name; canvas remains mounted but hidden, **0 visible canvases**, one main-content ID | DOM inspection and unit mount/unmount test |
| Restored desktop at 1440×900 | Same saved model/workflow visible again; canvas width 1388 CSS px in viewport width 1440 | [restored desktop](screenshots/followup/workspace-restored-1440.png) |

Unit tests additionally prove that a fresh restricted child never mounts, an admitted child does not unmount during resizing, responsive ordinary pages are not blocked, and project-return URLs reject external destinations. These prove lifecycle/navigation behavior. No live unsaved geometry edit was created to test retention; existing editor/undo regression tests remain passing.

Workspace/model/analysis page contents are behind client dynamic imports and the map inner page is lazy. Browser zero-canvas checks and component mount tests support avoiding renderer initialization on fresh unsupported visits. No network-byte, GPU-use or memory benchmark was performed; framework-prefetched route bytes may still exist.

F21-A is intentional policy, F21-B has these verified checks, and F21-C remains scoped/partial for long-data, populated-chart, zoom and physical-device acceptance. **F21 is not blanket-resolved.**

## Responsive public, management and results checks

At 390×844, current homepage, login, dashboard with retained context, project/folder dialogs, settings, provider status, privacy, cost, timeline, report and admin loaded views were inspected. The homepage/login screenshots were recaptured after initial entrance transitions; loading/half-faded screenshots were rejected as settled evidence. No real sign-in or form submission occurred.

The recorded route checks in [mobile-checks-followup.json](mobile-checks-followup.json) returned innerWidth 390 and document scrollWidth 384, with one main-content ID, for homepage/login/settings/privacy/cost/timeline/admin usage/templates at those checks. Hidden document overflow can mask inner issues, so screenshots and table-scroll tests were also used; this is not a blanket overflow certification.

- [Homepage](screenshots/followup/home-390.png), [login](screenshots/followup/login-390.png), [dashboard context](screenshots/followup/dashboard-return-390.png), [project dialog](screenshots/followup/project-dialog-390.png), [folder dialog](screenshots/followup/folder-dialog-390.png).
- [Settings](screenshots/followup/settings-390.png), [provider status](screenshots/followup/provider-390.png), [privacy](screenshots/followup/privacy-390.png).
- [Read-only report](screenshots/followup/report-390.png), [cost](screenshots/followup/cost-390.png), [timeline](screenshots/followup/timeline-390.png). Report had zero Edit buttons and zero canvases on the checked mobile state; geometry/assumption editing is desktop-only.
- [Rates](screenshots/followup/rates-390.png), [templates](screenshots/followup/templates-390.png), [usage](screenshots/followup/usage-390.png), [audit](screenshots/followup/audit-390.png). Wide tables scroll inside named keyboard-focusable regions with a mobile hint. ArrowRight on the rates region moved its scrollLeft; the region measured clientWidth 328 and scrollWidth 640.

Project/folder dialog open/close and focus return were observed at mobile width. No live creation/save/delete was performed. The existing user dataset changed independently during the audit; no snapshot was reset or overwritten.

Desktop map/model/analysis routes were also opened after lazy-wrapper changes: expected controls/headings appeared and no Something went wrong heading appeared. Workspace Fit All was exercised. [Desktop map](screenshots/followup/map-desktop.png), [model](screenshots/followup/model-desktop.png), [analysis](screenshots/followup/analysis-desktop.png). Renderer/tile resources can load after controls; these are smoke checks, not performance certification.

## F22–F26 regression evidence

- F22: fake timers trigger five failed status reads, then Retry resumes the same job GET, receives completion and clears the error. No generation POST is available/called in that test; the UI banner explicitly says the job may still be running. A real server outage was not induced.
- F23: rates/templates distinguish loading, error, retry and known empty data. Event-page tests verify existing offset query pagination and initial empty-state distinction. No live admin mutation.
- F24: failed provider reads expose a guarded retry; duplicate retries are prevented; unmounted results are ignored. A successful mocked retry replaces errors with returned provider state. No provider configuration change or real outage.
- F25: privacy now has one main/ID; summary links and table regions are named; dashboard copy/type improved. Source-color contrast samples: #657660 on #0c100c = 3.94:1, updated #a4afa2 = 8.43:1; muted #97a58d on #080c08 = 7.58:1. This is a calculation from specified opaque colors, not a full computed-style/contrast census. Screen-reader, zoom and forced-colors testing remain open.
- F26: pure presentation tests cover missing metrics, measured zero, positive quantities and absent comparison evidence. Unknown chart data stays null rather than becoming zero. Empty charts explain missing recorded values. Backend numerical output/formulas unchanged.

## Performance and safety limits

Final build compilation reported **13.3s** locally. Build time is not LCP/INP/CLS or backend engineering runtime. No controlled runtime before/after benchmark was captured, and no numerical runtime improvement is claimed.

The pre-existing local mock account/backend modes were reused without auth/config changes. No standalone Playwright CLI E2E suite, live paid generation/cancel/refresh job restoration, production sign-in, populated GLB/export download, live BOQ/rate/template save, project creation/deletion or upload was run. Expensive/destructive operations were mocked where tested. No push/deploy or backend change.

Full WCAG AA and production workflow certification remain unclaimed. The remaining acceptance work is F21-C and F25 plus the explicit live-workflow limits above, not a proposal to make the engineering workspace mobile.


## Final acceptance addendum — 22 October 2026

The final run supersedes earlier counts and acceptance limits where specifically verified. See [FINAL-ACCEPTANCE.md](FINAL-ACCEPTANCE.md), [FINAL-TEST-RESULTS.md](FINAL-TEST-RESULTS.md), [FINAL-ACCESSIBILITY.md](FINAL-ACCESSIBILITY.md), [FINAL-PERFORMANCE.md](FINAL-PERFORMANCE.md), and [FINAL-WORKFLOW-VALIDATION.md](FINAL-WORKFLOW-VALIDATION.md). Current decision **NO-GO**,428 frontend tests/95files,36 scoped API tests passed/1skipped,9 fixture workflows passed. F21/F25 remain partially verified. Exact live/mock distinctions and new residual export integration risk are in the final reports. Expert score retained3.75/5.

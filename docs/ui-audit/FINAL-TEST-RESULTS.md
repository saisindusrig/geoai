# Final test results

22 October 2026. Counts below are distinct current suites, never summed with historical/rerun counts.

- Frontend: **428 passed, 95 files** — npx vitest run --maxWorkers=2; logs/final-unit-release.log. Initial unrestricted parallel run had 419 pass/one 5s timeout in existing editor-analysis geometry profiling. A two-worker run passed all 420 existing tests before adding the eight new regressions. No numerical implementation or timeout threshold was altered.
- Backend scoped APIs: **36 passed, 1 skipped** — python scripts/final_acceptance_tests.py; logs/final-backend-confirmed.log. Auth/ownership, folders, admin permissions and job reliability. Initial runs exposed missing fixture audit table/template, corrected in the test runner only. This is not a full backend engineering suite.
- Browser workflow: **9 passed / 0 failed** — scripts/final-browser-workflows.cjs; final-workflow-browser.json and logs/final-workflows-release.log. Mock integration, not production E2E.
- Error/missing-data matrix: 96 route/viewport observations, zero page exceptions and axe violations in those states. final-browser-results.json and logs/final-browser.log.
- Final populated matrix: 114 observations, 0 with navigation/page exceptions; 3 route/rule violation entries. See FINAL-ACCESSIBILITY.md. Final JSON is authoritative; intermediate rebuild-overlap sweep was invalidated and rerun.
- Actual browser zoom: 14 routes at chrome.tabs.getZoom()=2, innerWidth=720 on a 1440px browser viewport. final-zoom.json, logs/final-zoom-release.log. Temporary local extension/profile, no user browser setting modified.
- npm run lint: passed — logs/final-lint-release.log.
- npx tsc --noEmit: passed — logs/final-types-release.log (empty output, exit 0). A newly authored test incorrectly used Playwright's exact option with Testing Library; corrected before final build.
- npm run build: passed — logs/final-build-release.log; compilation, TypeScript and prerender completed.

No blanket execution of existing E2E suites: several target existing saved project IDs, structural approvals or generation; executing them wholesale would violate the user's data/provider restrictions. Instead a separate interception-only browser runner blocks unintended mutations and external resources. No production login credentials/live nonproduction full-stack site were available.

No original project was mutated. Browser application API calls were intercepted; POST/PUT operations used only in-memory fixture responses. Backend API tests used an explicitly asserted separate SQLite database and test storage. No production credentials, paid AI, solver formulas, geometry algorithms, BOQ arithmetic, database migration or authorization policy was changed. Existing unrelated work remains intact.

New meaningful regressions cover safe auth redirects (2), draft navigation (2), report assumption recovery/duplicate guard (1), export markup/readability (2), offscreen renderer release (1).

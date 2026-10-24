# Final acceptance — SiteGeoAI

22 October 2026, Asia/Calcutta. Current working tree; no deployment or push.

**Release decision: NO-GO for production launch.** Frontend improvements are reviewable and regression checks pass, but authenticated export transport, comprehensive engineering workflow evidence and residual accessibility/performance requirements prevent reliable launch approval. This is not permission to deploy.

20 route definitions inspected in source (including /projects/new redirect); final browser matrices cover 19 route definitions with project fixture ID999998. The redirect's dialog behavior retains prior evidence, not a fresh final redirect check. Six widths:390/768/1024/1280/1440/1920. 114 populated observations plus 96 missing/error observations; 14 actual 200% zoom visits; nine interaction workflows.

Expert UX score: original **2.85/5**, final retained **3.75/5**. Twenty-principle scorecard in UI-UX-AUDIT.md remains the evidence-backed expert assessment; no arbitrary uplift for additional tests. Principles revalidated against local feedback, context recognition, grouping, native conventions, truthful progress, error recovery, essential desktop complexity and long-data use. Fitts/contrast gaps in the gizmo and performance/production uncertainty prevent stronger claims. This is not a scientific score.

New corrections in this final pass:
- Restrict postauth return destinations to local absolute paths, preserving query/fragment.
- Guard/report failed assumption saves; preserve draft and permit explicit retry.
- Protect BOQ/report drafts on reload/close and ordinary link navigation. Browser Back/Forward and arbitrary programmatic router changes remain outside this guard.
- Name/focus cost and BOQ horizontal data regions without shrinking measurements.
- Separate report Preview from download links, enlarge its target and restore unavailable-card text contrast.
- Release decorative offscreen project-preview renderers; observed scroll canvas growth76→12 after the same interaction.

Existing F01–F20 and F22–F24/F26 fixes retained; no new blanket live verification. F21-A is intentional desktop policy; F21-B verified unsupported experience; F21-C materially expanded but remains partial for physical-device/full engineering-result coverage. F25 remains partial for residual gizmo targets and assistive technology.

Outstanding priorities:
- **P0: none newly observed in sampled checks.** This is not proof of absence.
- **P1: authenticated export integration mismatch** across direct links/iframe/window.open; described in FINAL-WORKFLOW-VALIDATION.md. No insecure workaround applied.
- **P1 release evidence gap:** no complete disposable full-stack map/edit/save/reopen → generation → verified analysis → BOQ → protected PDF/CSV/GLB journey; no production authentication/session journey or representative terrain/hardware acceptance. Requires authorized isolated runtime/credentials/fixtures; no paid actions undertaken.
- P2: desktop camera gizmo target size; comprehensive assistive-technology acceptance; actual map interaction/INP/GPU longevity; earlier workspace CLS0.2413; browser history draft guard gap; dynamic motion preference coverage.

Checks:428 frontend tests/95 files;36 scoped backend passed/1skipped;9 fixture browser workflows;lint/types/build passed. See FINAL-TEST-RESULTS.md for reruns and exact logs.

Changed application/test paths this final pass (beyond the prior55):
- frontend/lib/auth-routes.ts
- frontend/lib/auth-routes.test.ts
- frontend/app/login/LoginPageInner.tsx
- frontend/hooks/useUnsavedChanges.ts
- frontend/hooks/useUnsavedChanges.test.tsx
- frontend/app/projects/[id]/report/page.tsx
- frontend/app/projects/[id]/report/page.test.tsx
- frontend/app/projects/[id]/estimate/page.tsx
- frontend/app/projects/[id]/cost/page.tsx
- frontend/components/project-results/ExportCard.tsx
- frontend/components/project-results/ExportCard.test.tsx
- frontend/components/dashboard/ConstructionPreview.tsx
- frontend/components/dashboard/ConstructionPreview.test.tsx

Added acceptance runners:frontend/scripts/final-ui-acceptance.cjs,final-acceptance-fixtures.cjs,final-browser-workflows.cjs,final-browser-zoom.cjs,zoom-fixture-extension/;backend/scripts/final_acceptance_tests.py. Reproducible artifacts are in docs/ui-audit JSON/logs/screenshots. Test profiles/database are disposable local artifacts, not app data.

No original project was mutated. Browser application API calls were intercepted; POST/PUT operations used only in-memory fixture responses. Backend API tests used an explicitly asserted separate SQLite database and test storage. No production credentials, paid AI, solver formulas, geometry algorithms, BOQ arithmetic, database migration or authorization policy was changed. Existing unrelated work remains intact.

Approval review temporarily blocked a server restart due to account usage; no action executed then. The later continuation passed review and local verification resumed. No unresolved authorization rejection remains for completed checks.

Reports: FINAL-TEST-RESULTS.md, FINAL-PERFORMANCE.md, FINAL-ACCESSIBILITY.md, FINAL-WORKFLOW-VALIDATION.md. No GO based on unit coverage alone.


## Subsequent launch-blocker verification

The 22 October 2026 launch-blocker run corrected authenticated binary exports/previews, desktop gizmo targets and header hydration stability. Current evidence and the remaining NO-GO conditions are in [FINAL-RELEASE-DECISION.md](../release/FINAL-RELEASE-DECISION.md). Current counts: 441 frontend tests / 99 files; 48 backend tests passed / 1 skipped; 10 connected JWT checks plus the editor persistence journey; 16 axe states with zero detected violations. Earlier counts above remain historical. No engineer approval was enabled.

# Implementation report — current audit follow-up

22 October 2026. Updated for the explicit desktop-only engineering requirement. **20 routes inventoried; 26 original finding IDs; 24 addressed within documented scope; F21 and F25 remain partially verified.** F21-A is an intentional product policy, F21-B is implemented/verified, and F21-C tracks individual-page acceptance. It is not blanket-closed. The updated expert principle mean is 2.85 → 3.75/5; this is not a scientific measure or compliance certification.

## Responsive product policy and implementation

Advanced spatial editing/analysis (`workspace`, `map`, `model`, `analysis`, `estimate`, `scenarios`) requires at least 1280 CSS pixels plus a fine pointer. Fresh unsupported visits render the requested **Desktop Required** heading, exact supplied explanatory copy, current project context, and a working **Back to Dashboard** navigation action. The dashboard retains the exact local project URL/query, resolves its saved name and provides a return link.

The gate mounts no engineering route child on a fresh unsupported visit. Workspace/model/analysis page contents were moved intact behind lazy client wrappers; the map inner page is also lazy. No geometry, rendering algorithm, drawing gesture, transform, numerical solver or undo implementation was changed. Fresh 390/768/1024 workspace visits showed zero canvases. At 1280/1440 desktop, the saved model and original controls rendered. A desktop session resized down remains mounted but hidden/inert, preserving drafts and undo state; it returns when supported. No guarantee of zero framework-prefetched asset bytes or GPU savings is made.

Homepage/authentication/dashboard/project management/settings/privacy remain responsive. Cost/timeline/report support lightweight mobile result viewing; report assumptions/site-geometry edits are unavailable on unsupported devices. Admin pages are considered individually: ordinary administrative forms remain responsive, JSON/table content scrolls locally, and read-only event tables have pagination. Long-data/zoom/physical-device acceptance remains within F21-C.

## F22–F26 outcomes

- F22: polling pauses visibly after repeated errors; Retry job status resumes the same job GET polling without a new generation request. Existing terminal/preview callbacks remain. Paused job is never falsely marked failed or complete.
- F23: rates/templates gain skeleton, known-empty and retry states; usage/audit gain loading/empty/retry and guarded limit/offset pagination using already supported backend parameters. Tables expose named keyboard-focusable scroll regions and mobile guidance.
- F24: provider reads support guarded retry, explicit Unknown status, retained successful partial results and failure/success recovery tests. Provider configuration remains untouched.
- F25: privacy's duplicate main/ID removed; dashboard supporting copy enlarged and contrast strengthened; summary links/table regions named. Source-color sample contrast improves 3.94 → 8.43:1. Broader contrast, screen-reader, zoom and hardware validation remain open.
- F26: missing scenario metrics remain null/gaps, entirely unavailable charts explain the absence, known-value counts disclose coverage, measured zero remains zero, and unknown warning counts display a dash. This changes presentation only; engineering formulas and backend payloads are preserved.

Earlier report/timeline crash recovery, BOQ draft/save safeguards, optimistic reversible metadata and four context-appropriate loading patterns remain. LOADING-SYSTEM.md records exact integrations and remaining lifecycle limits.

## Files intentionally changed by this audit and follow-up

**55 frontend source/test paths** below, including moved page contents. Some paths already contained user edits. This list attributes the task's intended scope, not every difference from repository HEAD.

- `frontend/app/admin/audit/page.tsx`
- `frontend/app/admin/event-pages.test.tsx`
- `frontend/app/admin/loading-states.test.tsx`
- `frontend/app/admin/rates/page.test.tsx`
- `frontend/app/admin/rates/page.tsx`
- `frontend/app/admin/templates/page.tsx`
- `frontend/app/admin/usage/page.tsx`
- `frontend/app/dashboard/loading.tsx`
- `frontend/app/dashboard/page.test.tsx`
- `frontend/app/globals.css`
- `frontend/app/layout.tsx`
- `frontend/app/privacy/page.tsx`
- `frontend/app/projects/[id]/analysis/AnalysisPageClient.tsx`
- `frontend/app/projects/[id]/analysis/page.tsx`
- `frontend/app/projects/[id]/estimate/page.tsx`
- `frontend/app/projects/[id]/map/page.tsx`
- `frontend/app/projects/[id]/model/ModelPageClient.tsx`
- `frontend/app/projects/[id]/model/page.tsx`
- `frontend/app/projects/[id]/report/page.tsx`
- `frontend/app/projects/[id]/scenarios/page.tsx`
- `frontend/app/projects/[id]/timeline/page.tsx`
- `frontend/app/projects/[id]/workspace/WorkspacePageClient.tsx`
- `frontend/app/projects/[id]/workspace/page.tsx`
- `frontend/app/projects/result-recovery.test.tsx`
- `frontend/app/settings/api-keys/page.test.tsx`
- `frontend/app/settings/api-keys/page.tsx`
- `frontend/components/dashboard/CreativeDashboard.tsx`
- `frontend/components/dashboard/NewProjectDialog.tsx`
- `frontend/components/dashboard/ProjectReturnLink.test.tsx`
- `frontend/components/dashboard/ProjectReturnLink.tsx`
- `frontend/components/dashboard/dashboard-hub.css`
- `frontend/components/layout/BottomSummaryBar.tsx`
- `frontend/components/layout/DashboardShell.tsx`
- `frontend/components/layout/DesktopWorkspaceGate.test.tsx`
- `frontend/components/layout/DesktopWorkspaceGate.tsx`
- `frontend/components/layout/ProjectHeader.tsx`
- `frontend/components/map/MapViewerArea.tsx`
- `frontend/components/project-results/RiskList.test.tsx`
- `frontend/components/project-results/RiskList.tsx`
- `frontend/components/project/ProjectValidationPanel.tsx`
- `frontend/components/scenarios/ScenarioSelector.tsx`
- `frontend/components/settings/SystemStatusPanel.tsx`
- `frontend/components/ui/loading-feedback.test.tsx`
- `frontend/components/ui/loading-feedback.tsx`
- `frontend/components/ui/skeleton.tsx`
- `frontend/components/ui/table-scroll-region.tsx`
- `frontend/components/ui/toaster.tsx`
- `frontend/components/workspace/LiveGenerationPreview.tsx`
- `frontend/hooks/useActiveJobPolling.test.tsx`
- `frontend/hooks/useActiveJobPolling.ts`
- `frontend/hooks/useWorkspaceDevice.ts`
- `frontend/lib/scenario-chart-data.test.ts`
- `frontend/lib/scenario-chart-data.ts`
- `frontend/lib/workspace-device.test.ts`
- `frontend/lib/workspace-device.ts`

Five requested reports: ROUTE-INVENTORY.md, UI-UX-AUDIT.md, LOADING-SYSTEM.md, IMPLEMENTATION-REPORT.md, TEST-RESULTS.md. Supporting evidence is in screenshots/ (follow-up screenshots under followup/), logs/, source-inventory.json, browser-observations.json and mobile-checks-followup.json. Initial browser observations include intermediate states and are historical; current accepted screenshots and report status take precedence.

## Safety, data and diff attribution

No backend code, database schema, authentication logic, provider configuration, deployment environment, engineering calculations, geometry algorithms or undo semantics were modified. API methods/response contracts remain unchanged; event pagination uses existing supported limit/offset inputs. Read-only browser checks did not submit project, BOQ, rate, template or generation mutations. No billable AI call, destructive action, push or deploy was performed. Existing normal reads may create their normal audit events.

The working tree already contained extensive unrelated frontend/backend/cache changes. Those were neither reset nor attributed to this task. The whole repository diff is therefore not clean or frontend-only. Review/commit the intended changes separately, preserving user work; include the new lazy client files along with their small page wrappers. Existing predev/prebuild asset synchronization and normal local build/test artifacts were produced by repository scripts.

The current task-scoped Windows-aware diff check passes (diff-check-followup.log). The earlier broad-tree check reported pre-existing whitespace-only EOF findings in CesiumView and ProfessionalModelEditor, which this task does not edit. No unrelated cleanup is included.

## Acceptance limits

F21 remains split and only partially closed because long-content, populated-result/administrative-form, zoom and physical-device acceptance is incomplete. F25 remains partial pending comprehensive assistive-technology/contrast testing. Viewport tests are not physical-tablet certification. Desktop-only workspace availability is not counted as a defect.

Live generation/cancel/refresh job restoration, production sign-in, real network outages/provider recovery, populated external exports and full engineering workflows remain unexecuted; mocked regression evidence is identified in TEST-RESULTS. No production readiness or WCAG conformity claim is made. Existing geometry/drawing/edit/undo behavior is covered by the unchanged application's tests plus read-only desktop smoke inspection, not an exhaustive live editing session.


## Final acceptance addendum — 22 October 2026

The final run supersedes earlier counts and acceptance limits where specifically verified. See [FINAL-ACCEPTANCE.md](FINAL-ACCEPTANCE.md), [FINAL-TEST-RESULTS.md](FINAL-TEST-RESULTS.md), [FINAL-ACCESSIBILITY.md](FINAL-ACCESSIBILITY.md), [FINAL-PERFORMANCE.md](FINAL-PERFORMANCE.md), and [FINAL-WORKFLOW-VALIDATION.md](FINAL-WORKFLOW-VALIDATION.md). Current decision **NO-GO**,428 frontend tests/95files,36 scoped API tests passed/1skipped,9 fixture workflows passed. F21/F25 remain partially verified. Exact live/mock distinctions and new residual export integration risk are in the final reports. Expert score retained3.75/5.

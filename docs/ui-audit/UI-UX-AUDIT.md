# UI/UX audit and scorecard

22 October 2026, updated after the responsive-design clarification. **26 original finding IDs: 24 addressed within scope, F21 and F25 partially verified.** F21 is split below; the workspace mobile restriction is an intentional product decision, not a UI defect. The three identified P0 issues remain fixed. F22–F24 and F26 now have implemented corrections and regression coverage; no unaddressed P0/P1 defect is asserted in inspected states. Live workflow and broader acceptance gaps remain.

20 route definitions reviewed, including a creation redirect. Screenshots represent actual local states from this audit. The protected UI was served with its pre-existing local mock admin account. This is not production end-to-end certification. Not every modal or engineering subpanel was executed. Full WCAG 2.2 AA, live generation completion, production authentication and performance thresholds remain unverified.

## Expert scorecard

Scores: 0 critical failure, 1 poor, 2 substantial improvement needed, 3 acceptable, 4 good, 5 excellent. These are expert judgments, not scientific measurements or compliance grades. The mean of these 20 scoped assessments is **2.85 → 3.75 / 5** (updated expert assessment; the previous 3.50 follow-up score is superseded). Unchanged scores deliberately preserve strengths and unresolved limitations. Route-specific scores and reasoning are in ROUTE-INVENTORY.md; no score implies every possible state was tested.

| Principle | Before | After | Findings | Changes | Evidence |
|---|---|---|---|---|---|
| Aesthetic–Usability | 4 | 4 | Existing ink/lime identity, aligned cards and restrained borders are coherent. Supporting dashboard metadata has larger type and stronger contrast; fine engineering copy remains under review. | Preserved brand; loading primitives reuse tokens. | home, dashboard, workspace screenshots |
| Hick’s Law | 3 | 3 | Workspace has many essential actions, but tools are grouped and inspector details are collapsed. Dense legacy map remains. | Preserved grouping; no essential engineering control hidden. | 04-workspace-before / project-map |
| Fitts’s Law | 2 | 3 | Project options and several mobile controls are small. Desktop engineering tools remain dense. | 44px options and scoped mobile dashboard targets; full canvas target audit pending. | dashboard-hub.css / 08-mobile-after |
| Jakob’s Law | 3 | 4 | Familiar dialogs, Save/Cancel, tabs and native destructive confirmation. Rate deletion lacked confirmation. | Named deletion confirmation and consistent pending/disabled behavior. | RatesPage / dialog tests |
| Miller’s Law | 3 | 3 | Site/create/edit/analyze/review workflow and grouped settings preserve context. Technical forms remain complex. | Kept units, parameters and version context; missing evidence explicitly described. | workspace / timeline screenshots |
| Doherty Threshold | 2 | 3 | Several operations lacked immediate local feedback. No interaction-latency benchmark was captured. | Synchronous request locks, immediate metadata update, localized spinners/skeletons. No 400ms claim. | dashboard tests / loading-feedback |
| Proximity | 4 | 4 | Labels/units and analysis controls are near relevant content; result cards and engineering dock group related outputs. | Kept local progress beside action, no global overlay added. | 05-analysis / project-timeline |
| Similarity | 3 | 4 | Mixed loading treatments and error announcements across pages. | Reusable skeleton/spinner/progress components and shared live toast semantics. Legacy loading remains. | loading-feedback.tsx / SystemStatusPanel |
| Common Region | 4 | 4 | Cards, dock, sidebar and inspector delineate tasks. Map has multiple heavy surrounding regions. | Preserved working group boundaries, no extra nesting. | project-map / 04-workspace-before |
| Visual Hierarchy | 3 | 4 | Primary lime actions are clear; empty BOQ and crashed reports obscured purpose. | Clear BOQ state and recovered report/timeline; provider guidance matches status. | estimate-after / 07-report-after |
| Progressive Disclosure | 4 | 4 | Inspector tabs, workflow help, advanced engineering panels and FAQ disclose detail on demand. | Preserved controls; tested FAQ expansion and project dialog. | workspace AX / FAQ browser check |
| Recognition vs. Recall | 2 | 4 | Workspace controls are labeled; map search and result-summary links now have accessible names. | Search/summary names, visible context-return link, explicit Unknown provider status. | MapViewerArea / ProjectReturnLink / BottomSummaryBar |
| Von Restorff Effect | 4 | 4 | Lime primary actions, amber limitations and red failures distinguish important states. | Preserved hierarchy; unavailable risk evidence is a warning, not success. | 07-report-after / RiskList |
| Peak–End Rule | 1 | 4 | Result endpoints and disconnected polling previously blocked recovery. | Recovered report/timeline and same-job status retry with retained drafts/context. | F01/F02/F22 and regression tests |
| Goal-Gradient Effect | 2 | 4 | Stage milestones and absent chart measurements could imply unsupported certainty. | Indeterminate real-stage progress; null chart gaps and known-value counts; recorded zero retained. | OperationProgress / scenario-chart-data tests |
| Serial Position Effect | 4 | 4 | Stable workspace workflow order and dashboard navigation. | No arbitrary rearrangement; mobile navigation keeps project actions discoverable. | dashboard / workspace screenshots |
| Tesler’s Law | 3 | 4 | Desktop-only engineering is intentional complexity management, not a responsiveness failure. | Preserved desktop controls; explicit device requirement; responsive non-engineering/read-only pages. | F21 subrequirements / DesktopWorkspaceGate |
| Postel’s Law | 1 | 4 | Incomplete saved evidence previously crashed pages or became zero chart values. | Explicit missing evidence and null measurements; precise inputs/formulas preserved. | RiskList / timeline / scenario-chart-data tests |
| Occam’s Razor | 3 | 3 | Legacy components and duplicated shell/result heading conventions remain. | Reused existing API/toast/state architecture without dependencies or broad redesign. | source-inventory.json / package unchanged |
| Feedback Loops | 2 | 4 | Request and disconnected-state feedback gaps affected recovery. | Visible polling pause/resume, provider retry, admin skeleton/empty/retry/pagination plus earlier guards. | F07–F24 / follow-up tests |

## Prioritized findings

Impact describes user consequences; effort estimates are relative frontend implementation effort. “Fixed” means the described scope was changed, not that every related product state is verified.

| ID | Severity | Finding | Status | Evidence / correction | Impact | Effort |
|---|---|---|---|---|---|---|
| F01 | P0 | Report crashes when risk evidence is absent | Fixed | Report/RiskList; browser stack and 06/07 screenshots; regression test | High | Small |
| F02 | P0 | Timeline crashes when permissions are absent | Fixed | TimelinePage; browser undefined-length error; recovered timeline screenshot and regression test | High | Small |
| F03 | P1 | Generation displays stage milestones as measured percentages | Fixed | backend/app/services/jobs.py STAGE_PROGRESS; LiveGenerationPreview now indeterminate | High | Small |
| F04 | P1 | Cancelled job can retain active preview UI/animation | Fixed | LiveGenerationPreview terminal guards now include status and stage cancellation | Medium | Small |
| F05 | P1 | Map location field and icon search action lack accessible names | Fixed | MapViewerArea input/button; current browser AX showed unnamed controls | High | Small |
| F06 | P1 | Mobile blocker prevents project management/settings/privacy access | Fixed for these routes | 02-mobile-before versus 08-mobile-after/settings-mobile; responsive shell scoped to these pages | High | Medium |
| F07 | P1 | Dashboard project mutations can overlap without pending feedback | Fixed | CreativeDashboard per-project ref locks, disabled options, spinner and terminal toast | High | Small |
| F08 | P2 | Folder metadata move waits without immediate response | Fixed | Optimistic folder move; rollback and server-authority tests | Medium | Small |
| F09 | P1 | Failed dashboard refresh discards successfully loaded projects/folders | Fixed | CreativeDashboard load catch now retains data; retry has guard and pending label | High | Small |
| F10 | P1 | Failed system refresh silently keeps stale status | Fixed | SystemStatusPanel error alert explicitly identifies last successful result | High | Small |
| F11 | P2 | Initial system-status failure has no recovery action | Fixed | SystemStatusPanel retry and scoped row skeleton | Medium | Small |
| F12 | P1 | Shared loading animations ignore reduced motion | Fixed for loading/preview | globals.css reduced-motion overrides; preview RAF skipped when preference is set at effect start | Medium | Small |
| F13 | P2 | Project loading/error feedback lacks status semantics | Fixed | ProjectHeader status/busy/error roles; ContentSkeleton hides decorative shapes | Medium | Small |
| F14 | P1 | Toast feedback is not exposed as status/alert | Fixed | Toaster per-toast role and atomic announcement | High | Small |
| F15 | P0 | Rate deletion executes without a contextual confirmation | Fixed | RatesPage named confirmation, irreversible consequence, pending deletion and duplicate guard; no live deletion performed | High | Small |
| F16 | P1 | Successful null BOQ fetch leaves a blank content area | Fixed | EstimatePage distinct skeleton/empty/error/retry states; browser and mocked regression | High | Small |
| F17 | P1 | BOQ saves can overlap; scenario switch discards dirty draft | Fixed within current page | EstimatePage synchronous save lock, disabled inputs/selector and discard confirmation; broader navigation remains unguarded | High | Medium |
| F18 | P1 | Scenario comparison errors escape without recovery feedback | Fixed | ScenarioComparePage catches failure, retains selection, ref lock; mocked failure test | High | Small |
| F19 | P2 | Provider setup text contradicts active Cesium status and hardcodes wrong origin | Fixed | ProviderStatusPage neutral capability guidance and deployment-origin instruction | Medium | Small |
| F20 | P2 | Dashboard project options have a very small target | Fixed | Scoped 44px project options target; mobile dashboard controls 44px | Medium | Small |
| F21 | Split | Device support requirements | Partially verified | Reclassified per explicit product decision; subrequirements below, not blanket-closed | Scoped | Mixed |
| F21-A | N/A | Workspace mobile restriction | Intentional policy | Desktop-only 3D/editing is required; no mobile engineering redesign | N/A | N/A |
| F21-B | P1 | Unsupported-device experience | Implemented / verified | Exact Desktop Required copy; Back to Dashboard and project/query context; no fresh renderer mount at 390/768/1024; desktop resize restoration tested | High | Medium |
| F21-C | P2 | Other result/admin/page responsiveness | Scoped checks passed; broader acceptance open | Route-by-route policy in ROUTE-INVENTORY; read-only cost/timeline/report; responsive admin tables; long-data/zoom/physical-device coverage pending | Medium | Medium |
| F22 | P1 | Polling pauses after five errors without a direct recovery action | Fixed | Persistent disconnected banner; Retry job status resumes GET polling for the same job; does not submit another job; mocked pause/resume regression | High | Small |
| F23 | P2 | Admin loading/empty/retry/pagination gaps | Fixed in named pages | Rates/templates skeleton + empty + retry; usage/audit guarded offset pagination; keyboard-scrollable tables with visible mobile hint | Medium | Medium |
| F24 | P2 | Provider request failure has no retry | Fixed | Guarded retry, explicit Unknown state, retained successful partial results, stale-result warning and mocked failure/success recovery | Medium | Small |
| F25 | P2 | Supporting text contrast/type and landmark/accessibility coverage | Partially addressed | Dashboard supporting metadata enlarged; sampled contrast 3.94→8.43:1; duplicate privacy main removed; table/summary names improved. Full AT/contrast/zoom audit remains open | Medium | Medium |
| F26 | P1 | Unknown scenario metrics coerced to zero | Fixed | Null/gap presentation, explicit no-recorded-values state/counts, zero preserved, unknown warnings shown as dash; helper tests cover missing/mixed/zero/comparison evidence | High | Small |

## Before and after evidence

Dashboard before: [desktop](screenshots/01-dashboard-before.png), [blocked mobile](screenshots/02-mobile-before.png). After: [390px](screenshots/08-mobile-after.png), [768px](screenshots/09-tablet-after.png), [1280px](screenshots/10-laptop-after.png). Mobile management works; full engineering canvas support has not been claimed.

Report [crash](screenshots/06-report-error-before.png) → [recovered report](screenshots/07-report-after.png). Missing risks explicitly remain unverified. Timeline recovered: [timeline](screenshots/project-timeline.png). BOQ [blank before](screenshots/project-estimate.png) → [useful empty state](screenshots/estimate-after.png).

## Accessibility and reliability limits

Status/busy/alert semantics, explicit search names, decorative skeleton hiding, focus-preserving existing dialogs, reduced-motion loading and larger scoped targets were reviewed. No screen reader session, automated axe sweep, full contrast census, complete keyboard map editing, 200% browser zoom or forced-colors test was completed. CSS reduced-motion loading is implemented; JS preview animation reads preference at effect start, not dynamically during a running preview.

Remaining work preserves the intentional desktop-only engineering product: finish F21-C long-content/zoom/populated-data/physical-device acceptance and F25 broader assistive-technology/contrast coverage. No mobile engineering redesign is proposed. F22–F24/F26 are implemented; live outage/generation/provider lifecycle coverage is still separate from mocked regression tests.


## Visual comparison

Mobile before:

![Mobile access blocked](<D:/layout project/docs/ui-audit/screenshots/02-mobile-before.png>)

Mobile after:

![Dashboard available on mobile](<D:/layout project/docs/ui-audit/screenshots/08-mobile-after.png>)

Recovered report:

![Report rendered after missing-evidence crash fix](<D:/layout project/docs/ui-audit/screenshots/07-report-after.png>)


## Device restriction evidence and follow-up scope

![Desktop Required on a fresh mobile workspace visit](<D:/layout project/docs/ui-audit/screenshots/followup/desktop-required-390.png>)

[768px restriction](screenshots/followup/desktop-required-768.png), [1024px restriction](screenshots/followup/desktop-required-1024.png), [1280px desktop](screenshots/followup/workspace-desktop-1280.png), [1440px restored desktop](screenshots/followup/workspace-restored-1440.png), [dashboard return context](screenshots/followup/dashboard-return-390.png), [mobile report](screenshots/followup/report-390.png).

Fresh restricted workspace DOM checks: zero canvas elements, one main landmark and one main-content ID. Resizing an admitted desktop session: canvas retained in DOM but hidden/inert; returning to 1440px restored the model. Unit tests verify a fresh restricted child never mounts and a resized admitted child does not unmount. This establishes scoped rendering behavior, not a network-byte or GPU benchmark. Geometry/control/undo algorithms were not modified.

Sampled contrast calculations use WCAG relative luminance on specified opaque CSS colors: old dashboard footer #657660 on #0c100c = 3.94:1; updated #a4afa2 = 8.43:1; general muted #97a58d on #080c08 = 7.58:1. These samples are not a full computed contrast census or conformity claim.


## Final acceptance addendum — 22 October 2026

The final run supersedes earlier counts and acceptance limits where specifically verified. See [FINAL-ACCEPTANCE.md](FINAL-ACCEPTANCE.md), [FINAL-TEST-RESULTS.md](FINAL-TEST-RESULTS.md), [FINAL-ACCESSIBILITY.md](FINAL-ACCESSIBILITY.md), [FINAL-PERFORMANCE.md](FINAL-PERFORMANCE.md), and [FINAL-WORKFLOW-VALIDATION.md](FINAL-WORKFLOW-VALIDATION.md). Current decision **NO-GO**,428 frontend tests/95files,36 scoped API tests passed/1skipped,9 fixture workflows passed. F21/F25 remain partially verified. Exact live/mock distinctions and new residual export integration risk are in the final reports. Expert score retained3.75/5.

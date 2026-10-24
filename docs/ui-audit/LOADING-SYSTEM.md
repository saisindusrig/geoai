# Loading systems

Four patterns are implemented in existing frontend components. They are selected by operation, not displayed together. No dependency, artificial duration, completion-time estimate or fake percentage was added.

## Reusable primitives

`frontend/components/ui/loading-feedback.tsx` exports:

- `ContentSkeleton`: known cards or rows, a single status/busy region and hidden decorative placeholders. Used for dashboard route/data, BOQ rows and initial infrastructure status. Existing Skeleton uses design-system classes. Failed requests exit loading and display error/retry or an explicit empty state.
- `OperationProgress`: indeterminate by default; a measured finite value optionally exposes `aria-valuenow`. Generation intentionally passes no value because backend progress is a fixed stage milestone. A visible label identifies the actual reported stage. `role=status` announces text changes; the graphic itself is not a live region.
- `InlineSpinner`: decorative small icon, used beside visible creation/folder-save, project mutation, system refresh, rate deletion and BOQ save text/state. Request owners disable controls and maintain their own status/error handling. Shared ProjectLoading now exposes status and busy semantics.

Global reduced-motion CSS disables skeleton/spinner/pulse/ping animation. Generation preview RAF also skips animation when reduced motion is set at effect start. These changes do not affect map geometry, drawing state, solver work or job stages. A runtime preference change during an existing RAF loop still needs dedicated coverage.

## Operation decision matrix

| Workflow | Pattern / current status | Completion and recovery |
|---|---|---|
| Dashboard initial route/data fetch | Card skeleton implemented | Error replaces skeleton; retry has local pending label and synchronous duplicate guard; prior data retained on refresh error |
| Dashboard folder create/rename | Inline spinner implemented | Existing form guard, preserved input and alert; no optimistic creation |
| Project folder move | Optimistic metadata implemented | Previous folder saved; per-project synchronous lock; rollback on failure; returned Project replaces optimistic row on success; toast |
| Project deletion | Confirmed mutation + scoped spinner implemented | Remains visible until server success; duplicate lock; failure preserves item and announces error |
| New project | Inline spinner implemented | Existing submit ref guard; focus trap/return and retained failed name; navigate after actual project response |
| Initial project/model/map context | Existing local spinner reused, semantics improved | Existing ProjectError/retry remains; model/map dimensional placeholders require later route-specific work |
| Initial BOQ fetch / scenario change | Row skeleton implemented | Explicit successful-null empty state; error with Retry BOQ; estimates are never optimistic |
| Save BOQ | Inline spinner and guarded confirmed save implemented | Disable editable cells/scenario selection while saving; server result authoritative; failed save retains draft; dirty scenario changes require discard confirmation |
| Initial system status | Row skeleton implemented | Error and explicit retry; no infinite skeleton after rejection |
| Refresh system status | Local inline spinner implemented | Old status remains visible; failure says last successful result is being shown; retry available via Refresh |
| Generation job | Indeterminate bar integrated into existing live map preview | Real stage label; preview explicitly not completion; completed/failed/cancelled removes active preview; existing poller announces terminal results |
| Analysis jobs | Existing operation-local running state retained | No fabricated percentage; long engineering panel jobs not individually changed or live-executed |
| Rate deletion | Named confirmation + inline spinner implemented | No optimistic removal; ref lock; failure alert; no live rate deletion during audit |
| Scenario comparison | Existing comparing state + guarded request and error recovery improved | Selected scenarios retained on failure; Compare retries; absent chart metrics remain an open semantics issue |
| Local map layer / display toggle | Existing immediate local update retained | Pure view state; existing undo/revision architecture preserved; not represented as server-confirmed engineering success |
| Provider status | Row skeleton, guarded retry and explicit Unknown state | Partial successful data retained; visible failure/stale warning; successful retry replaces error with authoritative data |
| Admin tables/templates | Row skeletons, known-empty states and error/retry added | Usage/audit have guarded offset pagination; rates/templates retry without losing drafts; keyboard-scrollable administrative tables |
| Report/export | Existing availability/readiness restrictions retained | No export triggered; complete long-running export lifecycle remains unverified; do not fake progress for ordinary download links |
| Upload | Existing implementation retained | No upload run; determinate bar may only be connected to measured upload bytes, never invented stage percentages |

## Job-system evidence

`backend/app/services/jobs.py` defines STAGE_PROGRESS as fixed queued/analyzing/layout/preview/BOQ/export/save milestones. It also has real job IDs, status/stage, preview-ready data and terminal states. The UI now communicates stage without calling those milestones a percentage of measured work. No backend changes were made.

`useActiveJobPolling` polls every second with exponential retry backoff and stops after five consecutive failures. It handles preview and completed/failed/cancelled notifications; the workspace supplies cancelJob to its map. The existing cancellation endpoint is reused only where passed in. Retry polling does not call it or alter backend job status. No local-only Cancel was introduced. A disconnected-state banner now offers Retry job status and restarts only the same job GET poller; it never starts a new generation. Restoring active jobs after refresh depends on existing project hydration and backend job-store lifetime; this was not live-verified. The current local server reports in-memory jobs. The direct resume/disconnected-status control is implemented (F22) and covered by a five-failures → same-job-completion regression; no live outage or generation was induced.

Optimistic folder updates are low-risk reversible metadata. The entire authoritative Project response replaces the row; only the prior folder field is restored on failure. A per-project ref prevents conflicting local mutations. Dashboard retry is blocked while a project mutation is active. This is not a cross-client concurrency protocol. Engineering, BOQ, model completion, rate deletion and exports remain confirmed operations.

## State and accessibility contract

Loading is local. Busy controls are native disabled controls. Empty content is distinguished from failed content. Errors are alerts; non-error toasts are status messages. Skeleton geometry is hidden from assistive technology. Indeterminate bars omit aria-valuenow. No invented remaining time, approval, certainty or cancellation behavior. No global loading overlay was added.

Open limitations: skeletons are approximate layouts, not CLS-benchmarked; minimum display/delay timers were intentionally not added; extremely short request flicker has not been profiled; comprehensive screen-reader announcement cadence and every asynchronous engineering panel need follow-up.


## Device admission precedes engineering loading

DesktopWorkspaceGate resolves the support media query before rendering advanced route children. Fresh unsupported visits show the lightweight Desktop Required page instead of a spinner or skeleton for content that cannot be used. Workspace/model/analysis client modules and the map route are dynamically loaded when admitted. This avoids renderer initialization on fresh mobile/tablet visits; it does not assert zero framework prefetch/download bytes.

An admitted desktop session remains mounted behind a hidden/inert wrapper during unsupported resizing to preserve local drafts/undo; returning to a supported viewport restores it. This is intentionally different from fresh mobile admission. No fake job completion or data reset accompanies device changes. Homepage, authentication, management/settings/admin and read-only result pages are outside the advanced device restriction.


## Final acceptance addendum — 22 October 2026

The final run supersedes earlier counts and acceptance limits where specifically verified. See [FINAL-ACCEPTANCE.md](FINAL-ACCEPTANCE.md), [FINAL-TEST-RESULTS.md](FINAL-TEST-RESULTS.md), [FINAL-ACCESSIBILITY.md](FINAL-ACCESSIBILITY.md), [FINAL-PERFORMANCE.md](FINAL-PERFORMANCE.md), and [FINAL-WORKFLOW-VALIDATION.md](FINAL-WORKFLOW-VALIDATION.md). Current decision **NO-GO**,428 frontend tests/95files,36 scoped API tests passed/1skipped,9 fixture workflows passed. F21/F25 remain partially verified. Exact live/mock distinctions and new residual export integration risk are in the final reports. Expert score retained3.75/5.

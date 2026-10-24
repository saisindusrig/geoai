# Route inventory — SiteGeoAI

Inspected 22 October 2026 (Asia/Calcutta), from the current working tree. There are **20 page route definitions**, including one redirect, and **194 non-test component files**. All route URLs were opened in the in-app browser; inspection depth varies as stated below. Existing project 805 supplied saved engineering geometry and incomplete report/estimate fields. The backend already exposes a local mock admin account; authentication was not changed or bypassed.

## Actual stack and architecture

Next.js 16.2.9 App Router, React 19.2.4, TypeScript, Tailwind CSS 4, custom CSS, custom UI primitives, Lucide icons, Framer Motion, next-themes and Zustand. React Hook Form/Zod are installed. Maps use MapLibre/Terra Draw, Cesium and deck.gl; 3D also uses Three/React Three Fiber; charts use Recharts. No new package was added.

`app/layout.tsx` owns ThemeProvider, DashboardShell, DocumentTitle, Toaster and SiteUtilities. DashboardShell has separate landing/login, project-entry and application paths. `projectStore` owns geometry, map/editor state, selected scenarios, revisions and active job. `useProjectData` loads project/scenario/model/result context; `useActiveJobPolling` polls jobs and notifies preview/terminal events. `lib/api` centralizes transport/auth/retry. These orchestration contracts were preserved.

Design identity: dark ink/green surfaces, lime primary, square controls, muted green-gray supporting text, monospace metadata and warning/error semantics. Tokens are in `app/globals.css`; dashboard overrides live in `components/dashboard/dashboard-hub.css`. Existing button/input/card/tabs/empty-state/status-pill/resize-handle primitives were reused. No theme replacement.

## Pages, evidence and journeys

All paths below are relative to `frontend/app`; `[id]` was exercised as `805`. A screenshot is evidence of the named state, not proof that every mutation on that route works. Scores are provisional expert assessments, 0–5, across observed states only.

| Route | Purpose / important components | Critical workflow | Findings and limits | Before → after | Screenshot |
|---|---|---|---|---|---|
| `/` | Marketing and introduction: HomePage; terrain presentation; workflow/system tabs; FAQ | Explore workflow → new project | Strong hierarchy and explicit illustrative-site labels; FAQ expansion verified; fine print remains small. | 4 → 4 | [home.png](screenshots/home.png) |
| `/login` | Sign in / register mode: LoginPageInner; email/password form; visibility button | Enter credentials → submit → return path | Labels and visibility action present; successful real sign-in was not exercised; existing local mock account used for protected reads. | 4 → 4 | [login.png](screenshots/login.png) |
| `/privacy` | Data-use notice: PrivacyPage; shared shell | Read policy → return to projects | Readable desktop notice; Nested main landmark and duplicated main-content ID corrected; mobile notice readable. | 3 → 3 | [privacy.png](screenshots/privacy.png) |
| `/dashboard` | Project library: CreativeDashboard; DashboardSidebar; NewProjectDialog; folder dialog; ConstructionPreview | Search/filter/sort → open; organize folders; confirm delete | Fixed mobile blocking, pending mutations, rollback, retained data on refresh errors, loading semantics and touch target. | 2 → 4 | [01-dashboard-before.png](screenshots/01-dashboard-before.png) |
| `/projects/new` | Project entry compatibility URL: Server redirect → dashboard?newProject=1 | Open URL → name-only creation dialog | Redirect and focus return verified; project submission uses existing request contract. | 3 → 4 | [new-project-route.png](screenshots/new-project-route.png) |
| `/settings` | Account, usage and infrastructure status: SettingsPageClient; AuthStatusCard; UsageCard; SystemStatusPanel | Inspect status → refresh/retry → provider details | Fixed local loading, retry, failed-refresh feedback and mobile shell; production account privileges not tested. | 2 → 4 | [03-settings-before.png](screenshots/03-settings-before.png) |
| `/settings/api-keys` | Read-only provider status: ProviderStatusPage; provider cards; tile status | Read live status → setup instructions | Removed unconditional missing-token/account assertions and fixed-port instruction; Guarded retry, explicit Unknown status and retained successful partial results added. | 2 → 3 | [provider-after.png](screenshots/provider-after.png) |
| `/admin/rates` | Regional material/labor rates: RatesPage; editable table; new rate fields | Read rates; update/add; confirm removal | Fixed named deletion confirmation, pending indicator and duplicate deletion guard; rate calculations unchanged; no live mutation performed. | 2 → 3 | [admin-rates.png](screenshots/admin-rates.png) |
| `/admin/templates` | Default design parameters: TemplatesPage; JSON editor; cards | Inspect template → edit JSON → save/cancel | Desktop parameters visible; Skeleton/empty/error/retry added; JSON content scrolls locally on mobile. No live save. | 3 → 3 | [admin-templates.png](screenshots/admin-templates.png) |
| `/admin/usage` | Metered usage history: UsageAdminPage; ApiErrorDetails; table | Read events; recover unauthorized/offline response | Desktop table readable; Loading/empty/error states and offset pagination added; table has a named keyboard-scroll region. Read query creates a normal audit event. | 3 → 3 | [admin-usage.png](screenshots/admin-usage.png) |
| `/admin/audit` | Administrative event history: AuditLogPage; ApiErrorDetails; table | Read security/admin events; retry errors | Desktop table readable with contextual columns; Loading/empty/error states and offset pagination added; table has a named keyboard-scroll region. | 3 → 3 | [admin-audit.png](screenshots/admin-audit.png) |
| `/projects/[id]/workspace` | Integrated engineering workspace: Lazy WorkspacePageClient; ModelEditor; tool rail; inspector; engineering dock; Copilot; map | Load saved geometry → fit view → inspect/edit → save revision → analyze/review | Saved model rendered; Fit All exercised; tool labels, disabled reasons and version context present. Small-screen restriction is intentional; accessible Desktop Required gate and retained project-return link are verified. Generation changes are presentation only. | 3 → 3 | [04-workspace-before.png](screenshots/04-workspace-before.png) |
| `/projects/[id]/map` | Site selection and geospatial drawing: MapSelectionPageInner; MapViewerArea; MapView; layers; assistant; survey/readiness panels | Locate site → boundary/alignment → measure → save geometry | Fixed search input/action names. Dense desktop controls and panels consume viewport; keyboard geometry requires further desktop testing; advanced mobile editing is intentionally unavailable. No project geometry saved. | 2 → 3 | [project-map.png](screenshots/project-map.png) |
| `/projects/[id]/analysis` | Site analysis and map context: AnalysisPage; metric cards; risk list; dynamic MapView | Inspect missing prerequisites → run analysis → inspect features/risks | Rendered not-run state and satellite context. No external analysis run; shared loading/error announcements improved. | 3 → 3 | [05-analysis.png](screenshots/05-analysis.png) |
| `/projects/[id]/model` | GLB/BIM viewer: ModelPage; layer controls; dynamic viewer; inspection toolbar | Toggle layers → navigate/inspect model | Rendered explicit no-GLB state; saved editable workspace geometry is separate from GLB output. Full GLB inspection not exercised. | 3 → 3 | [project-model.png](screenshots/project-model.png) |
| `/projects/[id]/estimate` | Quantity estimate and BOQ: EstimatePage; ScenarioSelector; phase tabs; quantity/rate table; charts | Choose scenario → edit BOQ → save → export CSV | Fixed blank null-data state, localized skeleton/retry, save guard, disabled editing while saving, confirmation before discarding edits on scenario switch. Formulas unchanged. | 1 → 3 | [estimate-after.png](screenshots/estimate-after.png) |
| `/projects/[id]/cost` | Preliminary cost breakdown: CostPage; ScenarioSelector; ChartCard; range cards | Choose scenario → compare low/medium/high estimates | Rendered no-cost-data state with scenario context; no fabricated costs. | 3 → 3 | [project-cost.png](screenshots/project-cost.png) |
| `/projects/[id]/timeline` | Construction sequence and planning duration: TimelinePage; metric cards; sequence; Gantt; download | Read sequence/assumptions → download JSON | Fixed crash on missing permissions; explicit missing evidence; removed completion checkmarks for planned phases; empty Gantt hidden. Durations unchanged. | 0 → 3 | [project-timeline.png](screenshots/project-timeline.png) |
| `/projects/[id]/report` | Reports and export center: ReportPage; ExportCard; validation; assumptions editor; RiskList | Review readiness/assumptions → preview/download | Fixed missing-risk-array crash; missing evidence remains a warning. Disabled DXF/GLB availability retained. Exports not triggered. | 0 → 3 | [07-report-after.png](screenshots/07-report-after.png) |
| `/projects/[id]/scenarios` | Compare alternative scenarios: ScenarioComparePage; filters; pin; compare selection; charts | Select 2–4 completed scenarios → compare → inspect → return | Rendered need-more-scenarios state; comparison failure now announced and selections retained. Missing metrics now remain null/gaps, recorded zeros remain zero, and wholly absent charts show an explicit message. | 2 → 3 | [project-scenarios.png](screenshots/project-scenarios.png) |

## Modal, drawer and panel inventory

Dashboard: new-project name dialog; create/rename/delete folder dialog; per-project folder/delete menu; native destructive confirmation. Existing project dialog traps Tab, supports Escape, restores focus and preserves failed input; unit tests exercise those behaviors.

Workspace/map: collapsible create/import workflow, workflow help, inspector tabs (layers/properties/history/analysis/review), assistant panel, scene/sun-study panel, map import, standard views, display legend, engineering dock, resizable side panels, member/property controls and generated-model layer groups. Their active state and labels were inspected in the saved-model workspace; every engineering subpanel was not individually executed. Existing tests cover many of these controls.

Reports/results: scenario dropdown, BOQ phase tabs/editable cells, report assumptions editing and export cards, scenario selection/filter/pin/compare and timeline download. Admin: template JSON edit mode and rate creation/update/removal. Login includes registration mode and password visibility.

`source-inventory.json` supplies every discovered component grouped by directory, every route's direct imports/state keywords and every source containing a dialog/confirmation. This is a source inventory, not a claim that dormant legacy components render. Only CreativeDashboard is the active dashboard; LegacyGeoAIDashboard remains unused by that route.

## Dependencies and safe boundaries

Project creation → backend project ID → workspace; saved site geometry → generation prerequisites; queued job → reported stage/preview → completed scenario/model → BOQ/cost/timeline/report. Preview readiness does not establish calculation completion. Survey capability depends on backend spatial services. Local editable geometry and exported GLB availability are different capabilities. Export availability/readiness restrictions were retained.

Auth, data schemas, backend provider configuration, geometry/solver algorithms and engineering approval restrictions remain outside these edits. No generation, paid AI, deletion, rate update, provider configuration, export or deployment was invoked against live data.


## Current device policy — user clarification supersedes original F21

The 3D engineering workspace is intentionally desktop-only. This is a product requirement, not a defect or an instruction to compress engineering controls. Advanced tools require **at least 1280 CSS pixels and an available fine pointer** (`WORKSPACE_DESKTOP_QUERY`). At 390, 768 and 1024 pixels the Desktop Required screen is expected. Actual hardware reliability on every tablet has not been certified; coarse-pointer tablets remain unsupported. This policy does not use UA sniffing.

| Routes | Current supported experience | Verification / remaining scope |
|---|---|---|
| `/`, `/login` | Responsive marketing/authentication | Settled 390px screenshots and original desktop inspection; real sign-in not performed |
| `/dashboard`, `/projects/new` | Responsive project management | 390px dashboard/project/folder dialogs, context-return link and desktop layout verified; no live creation/mutation |
| `/settings`, `/settings/api-keys`, `/privacy` | Responsive settings/status/policy | 390px screenshots; provider retry mocked; one main landmark/ID; normal desktop preserved |
| `/projects/[id]/workspace`, `/map`, `/model` | Desktop-only spatial editing and 3D | Fresh restricted visits do not mount renderer; lazy route modules; desktop 1280/1440 smoke and resize restoration verified |
| `/projects/[id]/analysis`, `/estimate`, `/scenarios` | Desktop-first advanced analysis and editing | Same device gate; existing desktop behavior and data tests retained; no mobile compression |
| `/projects/[id]/cost`, `/timeline`, `/report` | Responsive read-only result viewing | 390px rendered states; report assumptions/site geometry edits unavailable on unsupported devices; existing exports/previews retained |
| `/admin/rates`, `/admin/templates` | Responsive administrative forms with local horizontal/JSON scrolling | 390px loaded layouts inspected; no live rate/template edits; long-content and full zoom coverage remains |
| `/admin/usage`, `/admin/audit` | Responsive read-only tables with offset pagination | 390px screenshots, keyboard-scroll regions and mocked pagination; no backend contract change |

The dashboard-return URL retains the local project path/query and resolves its saved project name when available. The original project URL is unchanged by the restriction screen. Existing desktop sessions stay mounted but hidden/inert if resized below the support boundary, preserving local drafts/undo state; fresh unsupported visits never mount the workspace. Module wrappers defer heavy map/model/workspace imports, but no claim of zero framework-prefetched bytes is made.

F21 remains split/tracked: A intentional restriction; B unsupported-device experience implemented and verified; C individual-page responsive acceptance remains partial for unusually long data, populated charts, zoom and physical-device coverage. It is not blanket-closed.


## Final acceptance addendum — 22 October 2026

The final run supersedes earlier counts and acceptance limits where specifically verified. See [FINAL-ACCEPTANCE.md](FINAL-ACCEPTANCE.md), [FINAL-TEST-RESULTS.md](FINAL-TEST-RESULTS.md), [FINAL-ACCESSIBILITY.md](FINAL-ACCESSIBILITY.md), [FINAL-PERFORMANCE.md](FINAL-PERFORMANCE.md), and [FINAL-WORKFLOW-VALIDATION.md](FINAL-WORKFLOW-VALIDATION.md). Current decision **NO-GO**,428 frontend tests/95files,36 scoped API tests passed/1skipped,9 fixture workflows passed. F21/F25 remain partially verified. Exact live/mock distinctions and new residual export integration risk are in the final reports. Expert score retained3.75/5.

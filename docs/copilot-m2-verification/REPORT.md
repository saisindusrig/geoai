# Engineering Copilot Milestone 2 — current local verification

Local URL: http://localhost:3001/projects/793/workspace. Start/reuse the local offline site with run-website.bat. No new FEA method, schema migration, deployment, installation, Git operation or paid inference was introduced.

## Existing work retained and fixes completed

The checkout already contained the prior Copilot Milestone 2 and minimal-UI work. Its shorter reading view, expandable complete explanations, grouped missing requirements, exact saved-component/input/result navigation, resizing and explicit offline labels were inspected and tested rather than rebuilt. Existing stored responses were not rewritten.

This follow-up fixes two remaining status loops: active Assistant-run polling and running site-profile polling used setInterval and kept requesting after failures. They now schedule one read at a time, stop on error and resume only through explicit Retry. Retry reloads persisted state; it does not replay a solver, profile refresh or other mutation. New regressions verify both stop conditions and explicit recovery.

The next actionable task is now visible before the collapsed Advanced requirements list: e.g. “Next: Connection geometry · Geometry source.” Project 788 retains all 233 saved requirements, grouped by component/task and data-entry prerequisite. The ordering is not a structural safety or risk ranking. Review required inputs opens the saved record and its specific source step; it does not fill values or authorize a calculation.

## Fetch failures: root causes and diagnostic limits

1. **Confirmed current service outage:** at the start of this task both localhost:3001 and 127.0.0.1:8001 refused connections. Neither local server was running. A frontend cannot recover data from a stopped backend; error text/retries alone do not fix that condition. Existing offline servers were started and their health/proxy verified.
2. **Confirmed launcher inconsistency:** the old run-website.bat started ports 3000/8000, whereas the review application uses 3001/8001. Reusing an old review URL or frontend against the other backend port can produce connection failures. The batch launcher now delegates to the existing offline review configuration, uses the Selector backend, fixed same-origin /local-api proxy and the same ports for default/backend/frontend modes. Automatic pip/npm installation and .env copying were removed from this entry point. Backend health is required before frontend startup; a healthy proxy frontend is reused instead of starting a conflicting Next instance. The healthy-service reuse path was executed successfully. A complete cold shutdown/relaunch was not separately performed during this follow-up.
3. **Confirmed retry amplification:** two status loops continued after failed reads. The bounded, single-flight polling change removes that repeated traffic. Existing request helpers continue to surface a failure once; writes are never automatically replayed. Old tests expecting hidden GET retries were corrected to match this explicit-recovery contract.
4. **Earlier cross-origin failure evidence, retained accurately:** the prior audit recorded an OPTIONS preflight without the subsequent CAD audit POST. Its direct preflight check allowed the origin/headers/method; an incorrect CORS allowlist was not established. The existing fixed same-origin review proxy removes that cross-origin path. The precise earlier browser-side cause remains unproven. See ../copilot-milestone-2/validation.md and its before-fetch-failure-793.jpg, rather than treating a generic fetch error as proof of CORS failure.
5. **Earlier Windows accept issue:** the existing Selector event-loop launcher is retained. This follow-up does not claim to have newly discovered the previously documented Proactor accept failure.

No endless automatic retries were added, and errors remain visible with explicit recovery. The controlled browser network test aborts one real submission at the transport boundary, retains the draft, observes no automatic repetition, then retries the identical request body/ID. Exactly one saved user message remains after reload. This is a transport-fault injection; the backend was not killed during that browser test.

## Browser acceptance

All four requested projects were exercised at **1280×900 and 1600×900** using the actual local website and backend. Map credentials were replaced only in browser test routing; no inference or numerical responses were mocked.

- **793:** actual CAD column SW selected from Layers; readable selected context; saved bending-moment explanation; exact saved diagram navigation; persisted chat after reload. Both widths passed.
- **784:** saved one-way slab load summary retains 120 kN and units; Open saved results navigates to Analysis; chat persistence and visible composer passed at both widths.
- **789:** saved CAD column selection, drawing-reference explanation and chat reload passed at both widths.
- **788:** missing-input explanation, visible next geometry-source task, all 233 requirements and exact saved-input navigation passed at both widths. No engineering values were entered or saved.
- **Network recovery:** one injected POST transport failure, no automatic repeat, draft retained, explicit Retry sends the same frozen body/request ID, one persisted message after reload.
- **Resize:** real Assistant width drag increases width at 1280 px; blur terminates the drag, later pointer movement does not resize it; composer remains visible.
- **Preview/Apply/Undo/Redo/Save/Reload:** isolated QA project **801**, copied from existing QA project 795, exercised a component-name edit. Saved revisions 118→119→120 preserve history; the final component definitions exactly match initial revision 118. Original engineering projects and QA source 795 were not saved or modified by this edit test.

Browser results: **9 project/recovery tests plus 2 resize/editor tests passed**. No page errors in the passed acceptance runs. No analysis was executed.

## Automated results and limits

- **59 unique focused frontend tests passed** across Assistant persistence/recovery, transport, concise presentation, saved-result gates, exact input navigation, component identity, staged edits, undo/redo and resize cleanup. focused-tests.txt records 35 passes; editor-unit-tests.txt records 25 passes with one shared resize test counted once here.
- **85 backend tests passed** for offline engineering guidance, Assistant runtime, Nebius configuration and environment precedence. Tests use isolated fixture storage and forbidden-provider checks.
- TypeScript noEmit and targeted ESLint passed.
- A broad frontend run is **not green**: it initially reported 299 passes, 17 failures and two unhandled errors. These include obsolete retry expectations, timing-sensitive legacy UI tests and incomplete Cesium/DOM mocks (frustum.fovy and scrollTo). The three obsolete retry assertions were corrected and pass in the focused run. Other unrelated legacy test failures were not represented as passing or expanded into a separate UI/FEA development phase. The full run is preserved in frontend-tests.txt; its stderr details were also reported during execution. A full-suite cleanup remains separate review work.

## Data preservation

Compared **10,063 pre-existing database rows** against the pre-work snapshot. No rows are missing. Original analysis, message-body, model-revision and permission data is unchanged; no new engineering analysis rows were added. All 509 original engineering analysis records remain intact. No existing conversation messages were rewritten or deleted.

Expected operational differences are listed in preservation.json: project updated_at values and four conversation next_sequence counters advanced as persistent conversations were used. An empty conversation was also initialized for project 800; the backend log records its POST. The existing lock_project write advances project activity timestamps. The logs do not uniquely identify the human/tab that opened that conversation. One appended usage event is **file.download for project 789 model.glb**, not inference. No paid inference event was generated.

The isolated QA project adds only new model revisions and related save records; its final component bodies are restored. All original geometry and calculations remain preserved.

## Before / after evidence

“Before” references below are **earlier saved baseline captures**, not fabricated screenshots of the current implementation:

- Earlier fetch failure: ../copilot-milestone-2/before-fetch-failure-793.jpg
- Earlier 793 baseline: ../copilot-milestone-2/before-793-1600.jpg
- Earlier 788 baseline: ../copilot-milestone-1/after-788-missing-1600.jpg

Current after screenshots are in screenshots/:

- after-793-1280.png / after-793-1600.png, moment-1280.png / moment-1600.png
- after-784-1280.png / after-784-1600.png
- after-789-1280.png / after-789-1600.png
- after-788-1280.png / after-788-1600.png, exact-input-1280.png / exact-input-1600.png
- network-outage.png / network-recovered.png
- resized-assistant-1280.png and isolated-save-reload.png

The Assistant is **offline deterministic saved-evidence guidance**. Requested GLM preferences do not mean GLM inference occurred. Actual cloud reasoning, structural safety approval and design-code compliance remain unvalidated or disabled. No paid inference was enabled.

STOP for review.

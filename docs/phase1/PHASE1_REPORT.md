# GeoAI Phase 1 local review

Date: 11 October 2026 (Asia/Calcutta). Phase 2 has not started.

Review website: http://localhost:3001/projects/727/workspace
Dashboard: http://localhost:3001/dashboard
Review API: http://127.0.0.1:8001/docs

The pre-existing servers on ports 3000/8000 were preserved. Review uses the existing database and storage, plus a separate `.next-phase1` build directory. No Git commands, GitHub access, commits, PRs, CI checks, deployment, or paid AI inference were performed.

## Data preservation

SQLite backups of dev.db and planning.db and copies of the initially edited source files are in `.cache/phase1/`. The original dev.db contained 200 project records. An after-test comparison of every original project row found zero changes. Existing projects were not deleted or renamed. Browser tests created additional clearly named audit/acceptance projects; they remain available. Existing model/storage files were retained. The review project's slab was edited from 5 m to 5.5 m and saved as revision 2.

The local launcher overrides settings only in its process: mock AI, explicit offline platform template, cleared paid AI credentials, no Sentry, local file storage, local CORS and file URLs. It does not rewrite `.env` or frontend provider credentials.

## Verified workflows and limits

- **Project creation/save — working in tested paths.** Created project 727 through the real New Project dialog; saved its site boundary and model revisions and verified reload persistence. Projects are backed by the local SQLite database, not a frontend-only mock. SQLite remains limited GIS mode.
- **Site boundary drawing/editing — working in tested paths.** Browser tests cover polygon drawing, rejected invalid/self-intersecting geometry, save failure/retry with retained draft, canceling edits, vertex drag/edit/save and reload at 1440 and 1920 px. Rectangular drawing was also tested manually.
- **Satellite imagery, terrain and Cesium camera — working as visual context.** Satellite imagery and existing world-terrain connection loaded in the browser. Final camera tests passed both token-free and configured-terrain cases. Fit project and Frame selection were exercised. These are visual context, not validated survey elevations. Imported engineering terrain, GCP adjustment and authoritative cut/fill were not exercised end-to-end.
- **Assistant conversations — persistence and chat UI working; general intelligence incomplete in this local mode.** Messages, sources, proposals and chat drafts persist; messages scroll and the composer remains visible. General free-form requests save successfully but honestly report inference unavailable in mock mode. No general LLM answer quality was evaluated. Paid inference is disabled; Ollama integration was not validated.
- **AI-to-3D — offline template working, general generation not validated.** The explicit 5 × 3 m maintenance-platform example produced a reviewed/approved concept with nine objects: four columns, four beams and one slab. Generation now refreshes the active scenario in place. This is a deterministic fixed template, not an AI-designed or engineering-sized structure. Missing profile, unsupported dimensions, too-small site and rejected proposals fail closed.
- **3D selection/editing — working in tested paths.** Selection through Layers and viewport, transforms, undo/redo, dimension changes, save/reload and framed model visibility were exercised by browser acceptance tests. The manual slab dimension persisted at 5.5 m after reload. Numeric fields commit on Enter or blur.
- **Revision history — working in tested paths.** Immutable revisions, comparison of a modified object and saved revision reload passed. Restore remains a reversible draft edit; the complete restore/save sequence was not separately exercised in the browser.
- **Layers and Inspect — working in tested paths.** Grouped components, search, selection and inspection work. Assistant drafts survive switching inspector tabs. Vertical inspector tabs now support arrow keys/Home/End. Lock/hide/isolate paths have existing unit coverage but were not all manually exercised during this audit.
- **Checks — partial engineering functionality.** The browser executed existing spacing, supplied-slope and dimension rules. Passing these rules does not establish structural adequacy. The panel now explicitly states that loads, stresses, deflection, foundations, connections and code compliance are not analyzed. External solver-result imports and professional approval credentials have backend test coverage, but this audit did not issue engineer approval.
- **Import — GeoJSON tested and working for a boundary.** Main workspace now exposes Import. A self-intersecting polygon was rejected, a valid WGS84 boundary was saved and reload verified. KML support exists but was not independently exercised. FeatureCollection import currently uses its first geometry; this is not full CAD/BIM import.
- **Export — partial.** Local audit requests returned GeoJSON (200, parsed FeatureCollection), CSV (200) and PDF (200). CSV/PDF are preliminary report outputs; PDF page layout was not visually audited and estimate completeness/staleness remains a limitation. Formal GLB export correctly returned 409 because the revision lacks engineer approval. DXF returned 501: explicitly unimplemented. Survey terrain exports and native CAD/IFC deliverables were not validated.

## Fixed in Phase 1

1. Sub-1280 desktop layouts were blocked by a full-screen notice. Desktop review now works at 1024/1280/1478 px; the small-screen notice applies below 768 px.
2. Assistant opening in focus mode targeted a drawer whose existence depended on a separate left tools panel. The drawer now recognizes an assistant-only panel.
3. Widened chat on larger desktops, added readable user-message surfaces and spacing, bounded context scrolling, and kept the composer separate from transcript scrolling.
4. On compact desktops, the inspector opens over the right edge without forcing the entire viewport to shrink further. Existing compact Save controls were retained.
5. Newly built concepts were saved but did not appear until manual reload. Successful builds now include scenario identity and notify the project loader, preserving the conversation while refreshing the correct model.
6. Dense preview dimensions repeated a long list inside chat. The list is now expandable; assumptions and safety limits remain explicit.
7. Boundary drag sometimes hit an unready GPU buffer and silently orbited instead. A bounded nearest displayed-vertex fallback fixes the reproduced failure at both desktop sizes.
8. Unresolved zero-elevation concepts could disappear below context terrain. They now use a clearly labeled temporary ground preview. Accepted absolute/legacy elevations stay fixed; no preview height is written to the database. The audit model's saved elevation was rechecked as null with REVIEW_REQUIRED status.
9. Excluded visual geometry was counted as material in backend revision impact, and the UI could show misleading zero or fallback costs. Quantity calculations now honor explicit exclusions; the workspace/dock show unknown values for visual-only concepts, including after save. Existing historical estimates were preserved.
10. Import existed in an older tools panel but was not reachable in the primary workspace. Added a compact Import menu, geometry validation, and truthful failure handling when callbacks are unavailable.
11. Engineering imagery is less saturated/darker for model contrast; Realistic restores full imagery color. Source credentials/providers are unchanged.
12. Separate review builds initially exposed Tailwind scanning generated build binaries. The review output directory is now excluded from CSS source scanning.

## Validation

Frontend lint and TypeScript checks passed. Full frontend suite: 231 passed across 44 test files. Backend focused runs: 88 passed initially, then 72 passed after quantity/executor changes (overlapping tests, not a combined unique count). Final local Edge browser suite: 15 passed, including configured terrain, chat persistence, boundary retry/edit/reload, import, in-place generation, model editing, revision comparison and all three desktop layout sizes. Tests did not invoke paid AI.

Early attempts could not launch the missing bundled Playwright Chromium or sandboxed Edge; final runs used the installed Edge with approved local process access. Initial transient unit-test timing and stale test assumptions were resolved; the final results above are the review evidence. Entire backend/CAD/native-worker suites were not run, and a production build was not required for this local development audit.

## Extendable full-system plan — proposed only

Keep the existing boundaries: typed project/site records → accepted design requirements → specialist proposal/specification → deterministic geometry executor → immutable model revision → revision-bound checks, analysis evidence, quantities and exports. Keep local ENU geometry separate from geographic placement and vertical-reference evidence. Reuse current specialist contracts and object lineage rather than replace the app architecture.

After Phase 1 review:

1. **Phase 2: requirements and parametric structural authoring.** Define units, codes, material grades, loads, site/survey confidence and constraints. Extend semantic components to foundations, columns, beams, slabs, bracing, stairs and connections; validate dimensions, connectivity and supported operations. Optional local Ollama assistance must create bounded proposals and retain human approval.
2. **Phase 3: structural analysis.** Build a revision-bound analysis model and a local solver adapter. Validate benchmark frames, load combinations, boundary conditions, force equilibrium and mesh convergence before exposing strength/serviceability checks. Explicitly track unsupported checks; require professional review.
3. **Phase 4: drawings and quantities.** Generate revision-linked plans, elevations, sections, schedules and traceable takeoffs from material-qualified semantic components. Validate quantities against reference projects and flag stale analyses/estimates.
4. **Phase 5: interoperability and release readiness.** Implement and validate DXF/IFC/analysis exchange, survey-grade ingestion, project round trips and local performance. Add a complete acceptance matrix before separately deciding any hosting or paid-service integration.

No Phase 2 implementation was started.

## Local restart

In a backend terminal from the repository root:

```powershell
backend/.venv/Scripts/python.exe backend/scripts/serve_phase1_local.py
```

In a frontend terminal:

```powershell
cd frontend
$env:GEOAI_LOCAL_REVIEW='true'
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8001'
$env:NEXT_PUBLIC_AUTH_REQUIRE_JWT='false'
npm run dev -- --port 3001
```

Use the already running review instance until those processes are stopped. Avoid starting a duplicate on the same ports.

## Screenshots

- screenshots/workspace.jpg — site context with the persistent conversation and compact controls.
- screenshots/model.jpg — framed 3D concept and readable assistant.
- screenshots/layers.jpg — scene hierarchy.
- screenshots/checks.jpg — bounded checks and explicit limitations.

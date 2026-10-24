# GeoAI advanced mouse milestone — local review

Implemented locally on 14 October 2026. Stop here for user review. No GitHub operations, commits, deployment, AI inference or installations were performed.

## What changed

- Coordinated desktop pointer ownership across camera movement, selection, transforms, drawing and measurement. Camera gestures cannot select components or create model history.
- Middle drag orbits; Shift-middle drag pans; the wheel zooms through the pointer ray, using depth picking where available. Visible Orbit/Pan buttons provide equivalent left-drag controls. Navigation preserves framing, clamps zoom/pitch and respects Site terrain/underground settings.
- Click selects; Shift/Ctrl-click toggles membership. Empty Model-space clicks clear selection. A 5 px drag threshold starts atomic rectangle selection; Shift adds and Ctrl removes.
- Double-click and F focus objects; Home fits the model. The orientation gizmo now uses model/selection bounds in Model view instead of hidden terrain.
- Right-click offers permitted object actions and a named overlap picker. Locked objects remain inspectable. Existing CAD mesh scaling restrictions, assembly constraints, comparison restrictions and engineering validation gates remain in force.
- Transform handles retain a consistent screen size and larger picking targets. Move/Scale handle labels identify axes and planes. Preview solids and edge outlines move together, mapped by stable component identity.
- Axis constraints and exact values work while transforming. Keyboard precision also works without holding a mouse button: select, G/R/S, optional X/Y/Z, value, Enter. Move uses metres, Rotate uses degrees and Scale uses a multiplier. Exact input bypasses increment rounding; regular drag snapping and Alt target snapping remain available.
- Enter confirms; Escape, focus loss, capture loss and tool teardown restore previews and camera flags. Unchanged/canceled transforms create no history; completed transforms create one operation.
- A collapsible Mouse controls panel explains gestures. Sensitivity and inverted zoom are local browser preferences. Shortcuts require viewport focus and preserve typing in inspector inputs.

## Real browser checks

- **QA project 795:** ordinary Move drag changed the steel beam East from 0.5 m to 1.5 m. One Undo restored 0.5 m; Redo restored 1.5 m. Normal Save created revision 3; reload and inspector confirmed 1.5 m persisted.
- **QA 795 exact entry:** X movement of 1.25 m produced East 2.75 m from saved 1.5 m; one Undo restored Saved v3. A Y preview of 2.5 m canceled with Escape without a draft. Rotation of 23.75° and uniform scale 1.075× produced matching inspector values; each was undone. QA remains saved at revision 3.
- **QA selection/navigation:** box-selected all four objects, toggled membership with Ctrl/Shift clicks and cleared by clicking empty space. Orbit/Pan buttons, wheel zoom, F and Home changed views while preserving saved state. Inverted zoom persisted after reload, then was restored to the standard direction.
- **793:** top orientation retained the model on-screen. Right-click listed six overlapping structural objects; choosing column-sw opened the correct inspector. Two alignment points were drawn in Site view and canceled with Escape. Two-point measurement remained functional and correctly reported unavailable elevation as Unverified. Original model stayed Saved v2.
- **789:** original DXF review retained 73 source entities. Source 9C retained `dxf:614f117ae2a74794:9C` and its generated mapping. CAD fitting and direct 3D double-click selected/focused the column without creating a draft. Original model stayed Saved v4.
- **784:** saved result revision 86 remained VERIFIED (numerical verification only; approval disabled). Diagram picking selected beam-south and displayed its stored member values. Orbit/Pan worked over moment results; Displacement and Reactions remained usable. Applied 120.000 kN, reactions 120.000000 kN, residual −2.842e−14 kN and sampled translation 1.024137 mm were unchanged. No solver was run.
- Desktop views were inspected/captured at **1280 × 720** and **1600 × 900**, including CAD and FEA panels. Checked document width without horizontal overflow. Temporary viewport overrides were reset.

## Automated verification and preservation

- **63 tests pass across 6 suites:** gesture ownership, middle-button and Shift-middle dispatch, rectangle operations, cancellation/capture cleanup, locked context actions, model orientation, exact input, axis constraints, preview identity/edges, no-op history, editor undo/redo and existing toolbar behavior.
- TypeScript `--noEmit` and lint for all changed frontend modules/tests pass.
- Full ordered-row SHA-256 hashes match the previous UX milestone for all **8 original model revisions, 46 engineering analyses and 6 engineering authorization audit records** in projects 793/789/784. See `preservation-check.json`. These rows include revision documents, component identities, source references and numerical evidence.
- Only the existing named QA project received a saved model edit. No backend API, schema, solver method or engineering property changes were made.

## Screenshots and review limits

- `before-793-1280.jpg` is the retained screenshot from the preceding UX milestone, before advanced mouse controls. It is an actual browser capture, not a reconstructed mockup.
- `after-793-1280.jpg`, `after-793-1600.jpg`: completed controls and guidance.
- `overlap-selection-793-1600.jpg`: named selection beneath the deck.
- `cad-789-1280.jpg`, `cad-789-1600.jpg`: preserved source plan/CAD review.
- `fea-784-1280.jpg`, `fea-784-1600.jpg`: saved moment results and member picking.
- `qa-save-reload-1280.jpg`, `exact-preview-qa-1280.jpg`, `exact-result-qa-1280.jpg`: saved drag and exact movement evidence.
- Rectangle selection uses projected component bounds and includes obscured components in shown layers; it is not pixel-perfect visible-surface selection. Use the overlap picker for an individual obscured object.
- Browser automation exposes left dragging. Equivalent Orbit/Pan controls were exercised in the browser; native middle-button/Shift-middle ownership was checked in pointer-event tests. Physical mouse sensitivity and feel remain for user review. Touch-specific interactions were not validated in this desktop milestone.
- Existing dense CAD labels, legacy `/model` differences and occasional local asset/API recovery issues remain from the previous audit.

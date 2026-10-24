# GeoAI — Milestone 9

Completed locally on 23 October 2026. Stopped after supervised independent-beam creation. No whole-building generation, numerical analysis, live inference or deployment was started.

## Working beam workflow

`prepare_beam_preview` accepts one independent straight rectangular beam with two explicit numeric local ENU endpoints, width, depth, units (`m`, `cm`, `mm`), current project/revision, null parent and conceptual provenance. Missing dimensions/endpoints, ambiguous object/point references, unsupported geometry and unauthorized or protected source models are rejected. The assistant asks for missing values; it cannot infer which columns to connect.

The existing box primitive and XYZ Euler transform represent the beam. Length is the endpoint distance, position is the midpoint, and local X follows A to B. Section depth follows projected ENU Up; near-vertical members use North as the reference. This deterministic section convention is shown under Orientation details. Endpoint order is retained; reversing the endpoints preserves the rectangular solid and reverses its directed centreline. There is no endpoint snapping or connectivity inference.

The adapter uses existing NumPy/trimesh transform operations and the existing Three.js renderer. No second editor, mesh engine, numerical solver or engineering method was introduced. Bounds are 0.01–100 m for length, width and depth, and ±10,000 m for each endpoint coordinate. Identical and near-identical endpoints are rejected.

The temporary magenta beam is rendered alongside existing geometry using the Milestone 8 source-bound preview. The review shows both endpoints, length, width, depth, direction, project and source revision. Apply is disabled until the renderer confirms visibility. The explicit Apply click revalidates ownership, current revision, document hash and action identity before the existing undoable transaction. Save is a separate user click through the existing revision-save route. Saved confirmation requires the exact component in the actual returned revision document.

Beam metadata retains user-dimension provenance and `UNVERIFIED_GEOMETRY_ONLY`; quantities remain excluded. No materials, strengths, loads, supports, reinforcement, structural connections, capacity or compliance are declared. Geometry coincidence does not create an analytical member or connection. Existing engineering freshness/authorization gates remain in place.

## Reused editor and confirmed transform correction

Inspection covered the manual beam/box creation path, XYZ transforms, snapping, measurements, source-bound previews, commit/undo/redo and saved-revision guards. The existing renderer and saved JSON support 3D box rotations, including inclined and vertical members.

A confirmed handoff defect was corrected: box conversion to the saved GLB previously retained only yaw. Tilted boxes now carry the existing XYZ Euler rotation into the existing trimesh exporter. Tests compare rendered centreline endpoints, section extents and the saved GLB, including its existing ENU-to-Y-up conversion. Yaw-only geometry specs retain their previous representation. No original GLB or saved model was regenerated.

Geometry-spec reading now retains optional XYZ rotation. More importantly, when a scenario identifies a saved revision and that revision cannot be read, the editor no longer substitutes a generated geometry document. Such a substitute could lose identity, conceptual provenance or quantity exclusions. The viewer displays the saved-source error and offers its existing retry workflow; creation cannot proceed from that unavailable source.

## Proposal-state investigation and correction

The Milestone 8 fixture literally named the first object “Cancelled column,” but captured its preview screenshot **before** clicking Cancel. That name was not evidence of an already-canceled proposal remaining actionable. Milestone 9 fixtures use neutral names.

The separate ambiguity in historical tool text was real: a prepared preview receipt could remain visible after a later Apply/Save. The UI now uses explicit current lifecycle states:

- Preview pending: only the current renderer-confirmed editor preview can expose Apply.
- Canceled: temporary geometry is removed; no Apply approval remains.
- Applied but unsaved: the real editor contains the draft addition; Save is still separate.
- Saved in revision: the returned revision contains the exact current component.
- Rejected or stale: no active Apply approval; expired previews also enter this state.

Canceled, saved and rejected review panels have no Apply or Cancel control. Natural-language Cancel affects only an active temporary preview; it rejects applied/saved geometry without deleting it. Preview expiry remains two minutes. Duplicate replay is rejected, and opening or refreshing history does not replay actions.

Live chat cards follow frontend lifecycle evidence. Historical preview receipts are explicitly marked as historical/inactive and do not authorize edits. Stored conversations, initial receipts, usage and accounting records are not rewritten to achieve this presentation.

## Verification

- **116 focused backend tests passed** (`backend.log`). These cover endpoint transforms and reversal, horizontal/oblique/inclined/vertical cases, unit conversion, width/depth, length bounds, real GLB agreement, original-source preservation, missing/invalid/ambiguous inputs, ownership, protected CAD/assemblies, dirty/stale revision rejection, exact action validation, existing assistant behavior and spending controls.
- **71 focused frontend tests passed** across nine files (`frontend.log`). They cover actual Three.js transforms against backend-derived fixtures, unchanged original components, previews, renderer-before-Apply, explicit transactions and Save, undo/redo, expiry, cancellation races, historical-status clarity, exact saved-document confirmation and source-read failure behavior.
- **TypeScript and scoped lint passed** (`typescript.log`, `lint.log`). No dependency installation or unnecessary full-suite run was used.
- **Four fresh Chrome browser checks passed** (`browser.log`) at 1280×900 and 1600×900. Each creation flow used seven mocked assistant turns and one explicit real save in an isolated project. Checks exercised preview dimensions/direction, button and natural-language Cancel, duplicate rejection, stale Apply, rejection of Cancel after Apply, undo/redo, exact saved-revision confirmation and history refresh without replay. Separate checks cover failed saved-source reads and disabled AI.
- Final isolated projects: **991280 / 991600**. Actual saved revisions: **991601 / 991602**. `browser-1280.json` and `browser-1600.json` report zero paid requests, zero unexpected mutation/download requests and zero JavaScript errors.
- Screenshots: `preview-*.png`, `canceled-*.png`, `stale-*.png`, `applied-*.png`, `saved-*.png`, and `load-error-*.png`. The beam and existing geometry were visually checked with the assistant open at both requested sizes. Canceled screenshots contain no proposed beam or Apply button; saved screenshots show a saved revision and inactive history rather than pending approval.

All real browser API traffic was routed to the synthetic API on port 8003. Provider events and unrelated site suggestions were mocked. The existing frontend server was reused without being stopped or reconfigured. The isolated API uses only `isolated/beam-review.db`, isolated storage and isolated assistant history. Successful saves use the normal revision/artifact path; no original project was edited to prove creation. Prior synthetic trials and artifacts were retained; fresh run IDs were used instead of resetting saved fixtures.

`isolated-mutation-evidence.json` verifies identical original fixture components across every saved revision, with zero engineering-analysis and zero usage/accounting events for those projects.

## Preservation

Exact Milestone 9 entry comparisons show all **10,269 original database rows and schemas unchanged**, including every saved revision, authorization and historical usage record. Original assistant history, token reservations and budget accounting are exactly unchanged. No new original accounting events were added.

Retained manifests verify **55,296 original storage files** and **2,090 engineering proof files** unchanged, along with existing live/archived database fingerprints. Prior coupled solver artifact hashes were rechecked without running a solver. The retained archive was read in place without extraction, restoration, backup duplication or destructive cleanup.

Evidence: `preservation.json`, `preservation-audit.json`, `preservation-manifests.json`, `milestone-preservation.json`, `coupled-evidence-preservation.json` and the read-only verification scripts in this directory.

## Remaining limitations

- Numeric user-supplied ENU endpoints only. Existing measurement points are georeferenced/visual evidence, not a revision-bound, verified ENU endpoint registry. “These selected points” or selected column IDs alone are insufficient; the assistant must request explicit coordinates.
- One independent straight rectangular solid beam only; no curves, arbitrary CAD, assemblies, automatic framing, structural connections, reinforcement or whole buildings.
- No user-defined section roll or nonrectangular section. The displayed deterministic section-orientation convention applies, including the North reference for near-vertical members.
- Protected CAD/drawing/parametric/locked/parented model contexts remain blocked. Use their existing reviewed editing workflows.
- A clean current saved metric workspace is required. Unsaved/local sandboxes, stale source contexts, conflicting previews and duplicate actions are not supported for this tool.
- No automatic Apply, Save, analyses, imports, downloads/exports, engineering approval or deployment. Conceptual geometry remains outside quantities and verified results unless independently supported and explicitly authorized through existing application workflows.
- All new provider events were mocked; no claim is made about live model interpretation quality. Nebius Token Factory remains the only AI provider and GLM-5.3-Flash remains the default. No paid inference, offline AI, automatic retries, model escalation or earlier acceptance authorization was used.

No Git operations, parallel agents, Firebase activation, original-data migrations, installations or new deployments were performed. The isolated review launcher is `backend/scripts/serve_beam_review_local.py`; after successful saves, use a fresh `--run-id` rather than resetting its retained fixtures.

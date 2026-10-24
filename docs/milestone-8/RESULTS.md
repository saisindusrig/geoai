# GeoAI — Milestone 8

Completed locally on 23 October 2026. Stopped at supervised primitive creation. No paid inference, whole-building generation, numerical analysis or deployment was enabled.

## Supported creation

The existing site-wide assistant can prepare **one independent, upright rectangular column** in a clean saved metric workspace. The proposal schema requires the project and current revision, name, column type, width/depth/height, units (`m`, `cm` or `mm`), centre in local ENU coordinates, explicit yaw orientation, null parent and `user_dimensions_conceptual` provenance. Missing dimensions, position or orientation must be requested from the user; there are no AI geometry defaults.

Supported sizes are 0.01–100 metres per dimension, centre coordinates within ±10,000 metres, and yaw within ±360°. Tilt is unsupported. The proposal contains no strengths, engineering materials, loads, supports, connections or code claims. Its appearance is conceptual, its provenance is retained in component metadata, and it is excluded from quantities.

`prepare_primitive_preview` and `cancel_primitive_preview` are strict native assistant tools. Ownership, latest revision, document digest and exact action identity are revalidated. The Apply click revalidates the proposal again. Dirty drafts, conflicting previews/comparisons, stale sources, expired proposals, duplicate action replay and protected source models are rejected. No assistant tool applies or saves geometry.

## Existing editor integration

The manual creation path and supervised path share the existing box-component representation. Temporary rendering uses the editor's existing source-bound document preview, without committing a model edit. It displays the existing blue reference geometry alongside a distinguishable translucent magenta column, with dimensions, centre, orientation, project, source revision and provenance visible in the review panel.

Apply stays disabled until the real Cesium renderer confirms that the temporary component is visible beside the assistant. The user's Apply click enters one ordinary editor transaction, retaining attachment validation and undo/redo. The user's separate Save click uses the existing revision-save method and backend revision protections. Save is blocked during a preview. Saved confirmation requires the actual returned revision document to contain the current component; a prepared preview or successful provider response cannot establish a saved change.

Button Cancel and the natural-language cancellation tool remove only the temporary preview. They cannot delete an applied or saved component. A cancelled or already reviewed exact action cannot replay; a new proposal is required. Preview lifetime is two minutes. The original position-only preview workflow remains available.

## User-facing feedback

Progress distinguishes preparing a preview, waiting for approval, applied-but-unsaved geometry, confirmed saved revision, rejected actions and failed/unconfirmed saves. Ordinary editor state drives the feedback. Technical arguments remain in collapsed evidence/details. Opening or refreshing assistant history does not replay geometry changes. The existing assistant and accounting records were preserved.

The camera uses the space beside the assistant when framing the model, and the preview receipt waits for the proposed object's actual screen projection. This avoids acknowledging a proposal hidden behind the chat panel.

## Verification

- **91 backend tests passed**: explicit units, dimensions, centre placement, yaw, required fields, unsupported primitives/engineering fields, ownership, protected sources, dirty/stale revisions, exact document/action validation, read-only preparation, existing assistant behavior and spending controls. `backend.log`.
- **60 frontend tests passed** across seven focused files. Tests cover nonmutating preview/Cancel, renderer-before-Apply, asynchronous validation races, exact saved-document confirmation, duplicate rejection, source edits, explicit Apply/Save, undo/redo, primitive geometry and existing assistant/camera behavior. The final confirmation guard also passed its four focused tests. `frontend.log`, `confirmation-final.log`.
- **TypeScript passed** and **scoped lint passed**. `typescript.log`, `lint.log`, `lint-confirmation.log`.
- **Browser checks passed at 1280×900 and 1600×900**. Each exercised five mocked assistant turns, temporary preview, button Cancel, duplicate replay rejection, natural-language Cancel, explicit Apply, undo/redo and one explicit real save. Final isolated projects were 911280 and 911600; saved revisions were 911601 and 911602. `browser.log`, `browser-1280.json`, `browser-1600.json`.
- Screenshots were visually inspected at both sizes with the assistant open: `preview-*.png`, `applied-*.png`, `saved-*.png`. The proposed geometry and existing model remain visible.
- Browser evidence reports zero paid inference requests, zero unexpected mutation/download requests and zero JavaScript errors. Unrelated site-suggestion responses were mocked. Every actual API request was routed to the isolated fixture API. The existing frontend server was reused without stopping or reconfiguring it.

Browser mutation tests used `isolated/primitive-review.db`, isolated storage and isolated assistant-history paths. They used the real existing revision-save route, including its normal saved artifact generation. No original project was edited to prove creation. Earlier synthetic trials and their revisions/artifacts were retained; new run IDs created fresh fixture projects rather than resetting them. `isolated-mutation-evidence.json` verifies that every original fixture component remains identical and that no engineering-analysis or usage-accounting events were created for the synthetic projects.

Initial review found a missing lineage table in the synthetic fixture schema and an automatic unrelated site-suggestion request. The fixture now initializes the complete existing schema; browser tests mock site suggestions and reject unexpected writes. These trials did not touch original data.

## Preservation

Exact comparison to Milestone 8 entry shows **all 10,269 original database rows and schemas unchanged**, including the two accounting events already retained from Milestone 7. Existing assistant history and token/budget accounting are exactly unchanged. No new original-database usage events were added.

All **55,296 original storage files** and **2,090 engineering proof files** match the retained archive manifests. Existing database/archive checks and prior coupled solver artifact hashes passed. The archive was read in place, with no extraction, restoration, cleanup or backup database writes. Evidence: `preservation.json`, `preservation-audit.json`, `preservation-manifests.json`, `coupled-evidence-preservation.json`.

## Not supported

- Beam creation between selected points, automatic endpoint inference or analytical-member/connection creation. Use the existing manual tools; this milestone adds no endpoint-to-beam method.
- Arbitrary boxes/categories, tilted columns, cylinders, meshes, CAD generation, assemblies or whole buildings through the assistant.
- Adding geometry to models containing protected CAD/drawing references, locked objects, parented components or parametric assemblies. Use their existing reviewed workflows; this milestone deliberately rejects those model contexts.
- Structural properties, strength/material declarations, loads, supports, code compliance, capacity or safety approval.
- Automatic Apply, Save, analysis, imports, downloads/exports or cloud deployment. Navigation and inspection remain governed by Milestone 7.
- Creation from an unsaved/local sandbox or another page's stale context: open a clean current saved supported workspace first.

Nebius Token Factory remains the only AI provider and GLM-5.3-Flash remains the default. All new provider events were mocked. No live language-model quality claim is made, and no earlier spending authorization was reused. No Git operations, parallel agents, Firebase activation, migrations of original data, destructive cleanup or dependency installations were used.

The isolated review launcher is `backend/scripts/serve_primitive_review_local.py`. It initializes only synthetic test storage and requires a fresh `--run-id` after a successful mutation run; it refuses to reset saved fixtures.

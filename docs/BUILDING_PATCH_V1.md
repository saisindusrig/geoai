# Typed Building Patch Operations V1

## Contract and supported operations

`building-patch/1` references the Building/asset ID, exact saved model revision, original BuildingSpec version/hash, and one typed operation. Each operation has an ID, exact component ID, expected component hash, and discriminated parameters. Assumptions use the existing proposal acknowledgement flow. Engineering unknowns remain in the original specification; provenance is derived by the server.

Supported operations are MOVE_COMPONENT and ROTATE_COMPONENT for columns/beams, RESIZE_OPENING, MOVE_OPENING along its host wall, ADD_OPENING to a supported wall, and REMOVE_OPENING. Movement accepts metres or millimetres and normalizes deterministically. Column/beam movement is planar; rotation is about the local vertical axis.

Unsupported: dependent wall/room movement, floor-height changes, vertical member movement, structural sizing/redesign, foundations, stairs, MEP, roof redesign, arbitrary meshes, nonrectangular conversions, code compliance, and engineering analysis. Only implemented move, rotate, and opening capabilities are advertised.

## Validation and execution

Validation checks project ownership, latest saved revision, asset/specification identity and hash, exact target selection/state/lineage, component kind, locks, finite parameters, positive dimensions, footprint containment, opening host relationships, wall bounds, overlap, unique IDs, and resulting document validity. Unsaved editor changes block proposal/application. Ambiguous selection or missing opening width requires clarification.

Opening edits reconstruct only the affected host wall fragments and attached openings through BuildingAdapter. Other saved components remain unchanged. Previously edited or missing host geometry is rejected when it cannot be reconciled deterministically with the source specification.

An approved proposal passes the existing execution router and adapter capability checks. Execution clones the authoritative revision, validates again, saves through the shared model/revision pipeline, and commits the proposal transition and revision atomically. Existing revisions are immutable. Repeated execution returns the already-created revision. Project locking and source revision checks prevent application against newer saved geometry; stale dependencies are rejected rather than rebased.

Retained components preserve asset, original component, specification, generation revision, proposal, and generator lineage. Patch provenance adds patch/version/operation, approval, source/result revision, and timestamp. New opening/fragments receive derived lineage; removed components remain available in the previous revision. Placement remains unchanged and unknown elevation remains unknown.

## Assistant and workspace

The Assistant receives selected saved components, exact hashes, specification references, and opening definitions from `get_model_revision`. It can submit a typed patch through the existing proposal tool but cannot execute geometry directly. A deterministic fixture exercises this tool flow without provider calls.

Proposal Review shows the operation, target, before/after dimensions or transform, host, affected components, and source revision. Approval precedes the **Apply approved building patch** action. Dirty workspace state disables application. Inspect shows patch identity/source provenance. The normal History/comparison view reports the saved changes.

## Acceptance scenarios

- A: column c0-0 moves 500 mm east, producing +0.500 m in a new revision with retained lineage.
- B: window width changes to 1.5 m through a typed opening resize.
- C: an opening moves along its existing host wall.
- D: an added window receives semantic metadata and lineage.
- E: removal affects the new revision only.
- F: stale revision is rejected.
- G: missing component is rejected.
- H: opening extending beyond the host is rejected.
- I: unsupported structural sizing is rejected by the typed contract/capability boundary.
- J: ambiguous two-wall selection asks for clarification and creates no patch.

Additional checks cover all six operation types, component hash mismatch, locks, wrong asset, unsupported dependencies, approval requirement, idempotence, atomic storage failure, missing width clarification, and explicit capabilities.

The real workspace E2E passed on fixture project 517: load the 34-component model, select c0-0, review/approve the fixture proposal, apply, reload, inspect 5.500 m east and retained identity, then compare revisions. Comparison reports zero added, zero removed, and one modified component with a 0.500 m east delta. Screenshot: `frontend/test-results/building-patch-accepted.png`.

## Verification and acceptance

BUILDING PATCH V1 ACCEPTED for the limited operation set described above.

- Full backend regression: 660 passed, 2 skipped, 3 warnings.
- Focused backend suite: 126 passed, 1 warning (included in full regression).
- New BuildingPatch tests: 19 passed (included in both backend counts).
- Focused frontend suite: 40 passed across 6 files.
- Browser/E2E: 1 passed against real workspace/model APIs.
- TypeScript and targeted lint: passed.

The warnings are the existing Starlette/httpx deprecation and two Pydantic schema warnings. No paid evaluation or model request was made.

## Changed files

- Backend contracts: `app/domain/building_patch.py`, `assistant_runtime.py`, `stage1.py`.
- Backend services: `app/services/assistant/building_patch.py`, `building_patch_execution.py`, `building_execution.py`, `building_specialist.py`, `proposals.py`, `foundation.py`, `policy.py`, `prompts.py`, `tools.py`.
- Shared persistence: `app/api/routes/model_revisions.py`.
- Fixture/tests: `scripts/create_building_patch_fixture.py`, `tests/test_building_patch_v1.py`, `tests/test_admin_roles_audit.py` (isolate the audit test from accumulated daily usage).
- Generated contracts: `docs/contracts/stage1.schema.json`, `frontend/lib/generated/stage1.ts`.
- Workspace: `frontend/components/workspace/ProposalReview.tsx`, its test, `PersistentAssistant.tsx`, `ComponentIdentity.tsx`, and `frontend/e2e/building-patch-acceptance.spec.ts`.
- This acceptance report.

## Limits

One operation per proposal. Host edits require original supported host geometry; subsequent edits to an already changed host require reconciliation. No dependent architectural or structural redesign. Models remain conceptual and approval does not imply engineering approval. No live AI requests or production model configuration changes were made.

Next recommended specialist: ROAD SPECIALIST V1. No Road implementation is included.

# Building Specialist V1

## Scope and schema

The specialist is a bounded rectangular architectural/structural visualization pipeline, not BIM or an engineering solver. `BuildingSpec` uses `building-concept/1` and shared strict room, wall, opening, column and beam primitives. It contains building ID/name, closed local rectangular footprint, orientation, 1–10 floors, explicit floor height/slab thickness, spaces, walls, openings, identified columns/beams, constraints, unknowns and explicit preview assumptions.

The existing immutable asset specification version wraps this concept with proposal ID/version, source model revision, selected site/profile references and specialist validation. Its hash/version and dependency manifest remain the authority; the LLM cannot select a server-side source revision or approval identity through tool arguments.

Input dimensions are USER_PROVIDED for direct authenticated specification submissions or PREVIEW_ASSUMPTION for model tool proposals. Tool-submitted claims of user provenance are denied. Preview assumptions are promoted into existing visible proposal assumptions and memory versions, requiring acknowledgement in exact-version approval. Actual site/terrain provenance stays in existing captured profiles/placement rather than duplicated site structures. No engineering-result source is accepted because no engineering calculation is implemented.

## Components and adapter

`BuildingAdapter` registers `building-concept/1` for BUILDING, OFFICE_BUILDING and WAREHOUSE. Deterministic generation creates room/zone surfaces, split walls with real opening gaps, doors/windows, columns, primary beams, floor slabs and a roof slab. Internal walls are explicit wall segments within the footprint. Components use LOCAL ENU metres and apply the spec's orientation before the existing geographic heading/anchor placement.

Each object is converted using the existing editable-model converter and receives a stable semantic component ID, family/kind, building/floor, asset/spec identity/hash/version, proposal/version, approval and generator metadata. Generated quantity flags are false: there is no BOQ or material-estimate side channel. Foundations and excavation from the legacy building generator are not used.

## Validation

Schema validation rejects unsupported versions/types/features, nonfinite coordinates, invalid dimensions/floor counts and extra fields. Specialist validation checks valid closed rectangular footprint, self-intersection, unique source and generated IDs, spaces inside the footprint without overlap, spaces on every floor, wall containment and complete external shell on each floor, valid member references/positions, valid target walls, opening dimensions/containment/overlap and explicit preview assumptions. Execution checks the oriented footprint against the selected local plot. Generated box geometry is checked independently before conversion/persistence.

Validation reports SPEC_VALID and GEOMETRY_VALID, never ENGINEERING_SAFE. Soil, foundation design, survey elevation, loads and adequacy remain unknown/unavailable/unvalidated.

## Execution, revisions and failure behavior

The existing proposal build endpoint delegates to Building execution. It locks the project, verifies ownership, exact current approval and dependency hashes, uses ExecutionRouter's registered capability gate, loads approved typed specifications, validates them and produces geometry deterministically. Existing models require their recorded geographic placement. A first model derives its visual anchor from the saved area centroid, records that derivation, leaves elevation null and requires placement review; it never invents survey coordinates or elevation.

All assets must have supported typed specifications. Unsupported mixed compositions fail with GENERATION_UNAVAILABLE; no generic fallback exists. All generated data are prepared before revision insertion. The source revision is checked again at commit. Failure rolls back; no partial successful revision is retained.

A new ModelRevision preserves unrelated objects and previous revisions, clones the existing anchor/heading/elevation offset/mode/terrain metadata, and sets placement to REVIEW_REQUIRED. Unknown anchor elevation remains null; local geometry Z=0 is labelled LOCAL_VISUAL_REFERENCE. Metadata records source revision, spec hashes, generation version/time, component IDs and placement/terrain provenance. Model-object lineage rows identify generated components; retained lineage is copied for retained components.

Identical repeated build submissions reuse the saved revision. Regeneration through a new approved child proposal replaces only the previously generated asset in a new snapshot; previous geometry stays in the old revision. Site refresh is required after generation changes the captured site/model dependencies.

## Capabilities and workspace

Declared capabilities are conceptual planning/proposal, typed building generation and deterministic concept/spec geometry validation. Structural analysis remains unsupported. The catalogue itself still does not imply generation availability. Generic proposals without BuildingSpec remain ineligible.

The existing proposal review controls offer Generate building concept only for an approved proposal whose assets are eligible. The current panel layout is retained. Saved components use normal workspace box objects, transforms, layers, IDs and revision history, with metadata rather than a parallel viewer format. After generation the panel reports the new revision and asks the user to reload the saved model; it does not discard unsaved editor state automatically.

## Deterministic verification

The positive fixture scenario covers Assistant proposal → visible preview-assumption acknowledgement → exact approval → BuildingSpec validation → adapter → semantic editable revision, idempotent build, null elevation, preserved placement and lineage. Regeneration and first-model generation from a captured area centroid are tested separately. A smaller selected-area test verifies that the project boundary alone cannot authorize a footprint outside the actual selection.

Negative coverage includes self-intersection, zero/negative height, excessive floor count, invalid version/nonfinite values, duplicate source/generated IDs, out-of-wall or missing-wall openings, missing preview assumptions, unsupported MEP/foundation/structural-analysis features, foundation generation without soil, invalid source revision, unapproved/rejected/stale proposals, invalid specification and generation failure. Core Assistant safety-response tests remain active. No live AI or paid evaluation is used.

## Unsupported and next step

Unsupported: nonrectangular building generation, automatic spatial design optimization, stairs, foundations/geotechnical design, authoritative structural calculations, seismic/fire/accessibility/code checks, reinforcement, MEP/HVAC, energy compliance, IFC authoring, BOQ and specialist patch operations. This release requires a saved area/profile and does not prove live-model success at producing full specs within the unchanged token budget. Browser visual QA of a newly generated model remains separate from model-contract and UI fixture tests.

Next complete Building V1 workspace acceptance: test a generated building in the live workspace, inspect/select/transform/layer-toggle it, save a manual revision, compare revisions and verify lineage through that manual-edit path. Then add typed Building patch operations through the same proposal/approval boundary. Do not start Road/Bridge until this building workflow is accepted.

## Changed files

- `backend/app/domain/building_specialist.py`
- `backend/app/domain/building_primitives.py` and `backend/app/services/ai/building_plan.py` (shared pure primitives, legacy imports retained)
- `backend/app/domain/assistant_runtime.py`
- `backend/app/services/assistant/building_specialist.py`
- `backend/app/services/assistant/building_execution.py`
- `backend/app/services/assistant/specialists.py`
- `backend/app/services/assistant/proposals.py`
- `backend/app/services/assistant/tools.py`
- `backend/app/services/assistant/foundation.py`
- `backend/app/services/assistant/policy.py`
- `backend/app/services/assistant/prompts.py`
- `backend/app/services/assistant/context.py`
- `backend/tests/test_building_specialist_v1.py`
- `backend/tests/test_geoai_core_v1.py` (accurate new capability expectations)
- `backend/tests/test_composition_architecture.py` (registered Building adapter expectation)
- generated `docs/contracts/stage1.schema.json` and `frontend/lib/generated/stage1.ts`
- `frontend/components/workspace/ProposalReview.tsx` and its tests
- this report

Verification logs are local ignored artifacts: `backend/building-v1-final-related.log`, `backend/building-v1-pure.log`, `backend/building-v1-complete.log`, `backend/building-v1-full-complete.log`, `frontend/building-v1-ui.log`.

Final results: full backend regression **640 passed, 2 skipped, 3 existing warnings** in 250.63 seconds. Building-specific suite **25 passed**. Related focused suite **136 passed** before the two final area/first-model cases; pure-domain/legacy compatibility checks **40 passed**. Proposal-review UI **4 passed**; frontend TypeScript and targeted ESLint both passed. Counts overlap and are not additive. No live AI requests, additional model evaluations, model configuration changes or Road/Bridge implementations were made.

# Generic 3D Executor V1 acceptance report

Status: **GENERIC 3D EXECUTOR V1 = ACCEPTED**, for the bounded, conceptual primitive executor described below. This does not certify arbitrary civil engineering designs or prove live Qwen output reliability.

No live Nebius requests were made. AI model configuration was unchanged. Production Building generation and Building Patch remain on their existing adapters. No asset-specific specialist was added.

## Baseline checkpoints

- `8d8c8e9`: recoverable checkpoint of the accepted baseline and interrupted Road draft.
- `260c094`: accepted Building baseline with the interrupted Road draft removed and generated contracts synchronized.
- Initial baseline regression: 659 passed, one generated-contract drift failure, two skipped. Regenerating the contract resolved that failure; the drift test then passed. The final full regression below verifies the integrated state.

## 1. Final AI3DDesign schema

Canonical definition: `backend/app/domain/ai3d.py`. Generated JSON Schema: `docs/contracts/stage1.schema.json`; generated TypeScript: `frontend/lib/generated/stage1.ts`.

The strict, frozen, extra-fields-forbidden contract has:

- `schemaVersion = ai-3d-design/1`, `designId`, nullable `sourceModelRevisionId`.
- `siteSelection`: saved ID, version and content hash.
- `coordinateFrame = LOCAL_ENU`, `referencePlane = LOCAL_VISUAL_REFERENCE`.
- `systems`: 1–20 entries containing ID, asset type, semantic type and role.
- `objects`: 1–250 entries containing object ID, system ID, semantic type, role, discriminated primitive parameters, optional parent ID and template-only flag.
- `relationships` and `constraints`: at most 100 each.
- `assumptions`: at most 20 explicit field/value/reason entries.
- `unknowns`: at most 50; defaults retain ground elevation, soil, structural capacity, design loads and engineering approval as unknown.
- `terrainDependencies`: saved references, at most 10; dependent terrain placement is explicitly unsupported in V1.
- `inputSource`: USER_PROVIDED or PREVIEW_ASSUMPTION. Assistant-submitted generic designs require PREVIEW_ASSUMPTION and an explicit assumption.

Coordinates are finite and bounded to ±2,000 metres. Positive dimensions are bounded to 500 metres. Arrays use strict bounded integer counts. Output is limited to 1,000 solids, with additional generated coordinate, dimension and extent checks. No arbitrary code, expression, script or opaque mesh field is accepted.

Proposal IDs, proposal versions, approval IDs and provenance are stamped by the server rather than trusted as AI-authored claims. This deliberately keeps the AI contract data-only.

## 2. Implemented primitives

POINT, PATH, POLYGON, BOX, CYLINDER, SURFACE, EXTRUDE, SWEEP, OFFSET, ARRAY_ALONG_PATH, ARRAY_ON_GRID, PIPE and CHANNEL.

POINT/PATH/POLYGON/OFFSET are references rather than selectable solids. BOX/CYLINDER are editable solids. SURFACE/EXTRUDE create rectangular prisms. SWEEP creates oriented rectangular solids per planar segment. PIPE creates cylinders per path segment. CHANNEL creates three editable solids per segment. Array operations instantiate BOX/CYLINDER templates.

WALL, SLAB, BEAM, COLUMN, DECK, SUPPORT, PIPE, CHANNEL, PAD and ZONE are semantic roles, not separate specialist generators.

## 3. Primitive dependency model

Dependencies come from parent, path, polygon and template references. IDs must be unique; references must resolve. A deterministic topological sort uses stable lexical ordering for simultaneously ready objects. Missing references and cycles fail before persistence.

Generated IDs derive from design ID, source object ID and deterministic instance/segment index. Long IDs receive a deterministic hash. Parent references order execution and preserve metadata; they do not create nested transform inheritance.

## 4. Validator architecture

`AI3DDesignValidator` performs contract validation, dependency compilation, output validation, relationship-reference checks and supported constraint checks. `validate_saved_design` additionally verifies project ownership, frozen selection references, source revision, current model context, project boundary and dirty-editor state.

Unsupported operations, invalid arrays, non-finite values, zero-length paths/cylinders, invalid polygons, unresolved systems, stale context and output outside a selected AREA fail explicitly. Terrain-dependent placement is rejected. The existing approval/build capability and staleness gates remain authoritative.

Reported states distinguish DESIGN_VALID and GEOMETRY_VALID from engineering UNVALIDATED. Constraint checks only report SATISFIED after an implemented check.

## 5. Generic executor architecture

One `Generic3DExecutor` is registered through the existing adapter registry for AI3D_DESIGN. Semantic asset roles do not choose another generator. The pure compiler performs no model call and no creative reasoning.

The existing proposal build endpoint verifies approval, current dependencies and idempotence, then invokes the generic executor. The complete geometry is compiled before calling the existing editable-document/ModelRevision persistence pipeline. Database failures roll back the revision, placement, lineage and proposal transition. Repeated successful builds return the saved revision.

The shared export pipeline can leave an unreferenced generated file if a later database operation fails; it cannot leave a partially successful model revision. This is the existing storage behavior, not a new model execution channel.

## 6. Local-coordinate behavior

Coordinates are local metres in the existing model frame. Backend projection converts saved geographic geometry into that frame and accounts for existing anchor/heading. AI does not calculate Cesium Cartesian positions.

Existing placement is copied through normal revision persistence. A new model uses the selected geometry centroid as its geographic anchor, with elevation unknown and placement REVIEW_REQUIRED. Geometry Z is a conceptual visual reference, not a claimed terrain elevation. Generated objects retain normal editable transforms.

## 7. Terrain behavior

Saved site facts and readiness remain available through frozen context and `get_site_profile`. A bounded SiteAnalysisSummary exposes saved selection/source references, local geometry, origin/frame source, available facts, unknowns and limitations.

No elevation sampling, terrain draping, foundation selection, slope fitting or soil inference occurs in this executor. A design requiring terrain-dependent placement is rejected with TERRAIN_PLACEMENT_UNSUPPORTED. Unknown elevation is not replaced by zero as a factual claim. The existing underground view can reveal reference-plane geometry that would otherwise lie beneath rendered terrain; it does not alter the saved placement.

## 8. Relationships

CONNECTS_TO, SERVES, SUPPLIES, CROSSES, FOLLOWS, AVOIDS, CONTAINS, ADJACENT_TO, ABOVE, BELOW, SUPPORTED_BY, DRAINS_TO, ALIGNS_WITH and OFFSET_FROM are typed and reference-validated.

They are persisted as conceptual intent with RECORDED_NOT_ENGINEERING_VALIDATED status. They do not prove connectivity, structural support, hydraulic behavior or clearance.

## 9. Constraints

Implemented checks:

- WITHIN_AREA: generated footprint containment against the saved AREA.
- START_AT / END_AT: exact referenced POINT endpoint check in local coordinates.
- FOLLOW_ROUTE: deterministic local XY correspondence with the saved route/endpoints/crossing geometry, within 0.001 metres.
- AVOID_AREA: generated footprint intersection check against a referenced polygon.

Selected AREA containment and saved project-boundary containment also run independently of explicit constraints. CONNECT_TO, AVOID_OBJECT, MIN_CLEARANCE, OFFSET, ORIENTATION and MAX_FOOTPRINT remain explicit UNSUPPORTED checks and block execution when requested. No unimplemented check is reported satisfied.

## 10. Provenance

Each generated component and lineage entry retains design ID, system ID, source object ID, semantic role, primitive, executor version, asset/specification ID, specification version/hash, design version/hash, proposal/version references, approval ID, source model/site references and generation ModelRevision ID. SiteAnalysisSummary is retained. Selection/source facts come from owned saved records, not AI-authored provenance.

Prior components and lineage are preserved through the existing revision pipeline. Regeneration of a child proposal replaces only that generic asset's components. Unrelated ID collisions are rejected.

## 11. Warehouse fixture

Passed deterministic compilation and geometry validation. One warehouse produces 10 editable solids: slab, roof, four walls and four arrayed columns. Reference footprint and template remain design references. Dimensions are explicit preview assumptions.

## 12. Road-like fixture

Passed. A three-point planar path produces two editable surface boxes. This is conceptual segment composition, with no pavement, traffic, alignment or road engineering solver.

## 13. Pipeline fixture

Passed. A three-point path produces two endpoint-aligned cylinders. Cylinder transform/export regression checks cover rotation, translation and scale. This is solid visual pipe representation, without hollow sections or hydraulic validation.

## 14. Bridge-like fixture

Passed. Two deck segments and five deterministic support instances produce seven editable solids. Support placement follows path chainage. No load, foundation or structural safety claim is made.

## 15. Drainage fixture

Passed. Two channel segments produce six editable solids. Section thickness is checked against width/depth. No drainage capacity, flow direction or hydraulic safety is inferred.

## 16. Mixed-project fixture

Passed. Two warehouses, parking, access-road composition, drainage and tank produce six systems and 27 editable components. The entire composition uses one AI3DDesign, one approval and one generic executor.

## 17. Elevated bicycle walkway

Passed with an unregistered civil asset role. The same path/deck/support primitive composition produces seven editable solids. No dedicated walkway or bridge generator is required. Unsupported engineering requirements remain unknown.

## 18. BuildingSpec translation

The experimental translator converts the accepted Building adapter's resolved component geometry into AI3DDesign BOX objects. The canonical 34-component fixture preserves component IDs, centres and dimensions. It does not replace production Building generation or reimplement its specialist reasoning.

## 19. Existing object preservation

Backend tests verify unchanged prior revision content, existing components, placement and lineage. The browser fixture starts with 34 Building components; generic generation adds 27, yielding 61. The original office component remains selectable with its identity and position. Only the deliberately edited parking component changes in the later manual-save revision.

## 20. Workspace compatibility

The existing Assistant panel reviews readable systems, primitive composition, dimensions, counts, assumptions and unknowns. Existing assumption acknowledgement and proposal approval are required. Generation uses the current build endpoint; no direct AI mutation was added. Final browser fixture: project 576, starting revision 28, proposal version `ae4397ba-acca-556a-8dfb-1af544b68660`. Fixture setup uses a deterministic provider, not Nebius.

Browser acceptance verified: review → approve → generate → reload; Building identity preservation; generic BOX/CYLINDER identity; frame selection; manual transform/save/reload; History comparison showing zero added, zero removed and one modified component; pipe-layer hide/show; and Cesium rendering without a stopped-rendering error. The existing underground control exposes unknown-elevation reference-plane geometry.

The shared fallback Cesium cylinder renderer and backend cylinder export now respect endpoint direction and object transforms. The main workspace renderer already supported tilted cylinders. Project framing keeps its target on the saved model plane when underground view is enabled; ordinary above-ground framing retains its terrain-height camera safeguard. Underground mode also disables terrain camera collision and hides the globe's opaque back face; ordinary mode restores normal collision/depth behavior. These are compatibility fixes, not a workspace redesign.

## 21. Verification counts

- Full backend: **704 passed, 2 skipped, 3 warnings**. This includes **44 generic executor/schema/integration/translation tests**, existing Building, Building Patch, model persistence, contracts, ownership and export regressions.
- Full frontend unit suite: **192 passed across 40 test files**.
- TypeScript: passed with no diagnostics.
- Full frontend ESLint: passed with zero warnings.
- Production Next.js build: passed.
- Generic mixed-design browser acceptance: **1 passed**.
- Additional read-only visual inspection of the saved unknown-elevation reference plane: **1 passed**; temporary inspection test was removed after its checks were incorporated into the acceptance test.

Warnings are existing Pydantic schema/deprecated test-client notices; neither skipped backend test was converted to a pass. No paid evaluation or live provider request was used. Do not add overlapping focused-suite counts to these totals.

## 22. Files changed

New files:

- `backend/app/domain/ai3d.py`
- `backend/app/services/assistant/ai3d_geometry.py`
- `backend/app/services/assistant/ai3d_validation.py`
- `backend/app/services/assistant/ai3d_executor.py`
- `backend/app/services/assistant/ai3d_building_translation.py`
- `backend/tests/test_ai3d_v1.py`
- `backend/scripts/create_ai3d_workspace_fixture.py`
- `frontend/e2e/ai3d-workspace-acceptance.spec.ts`
- `docs/GENERIC_3D_EXECUTOR_V1.md`

Updated integration: `assistant_runtime.py`; Assistant `building_execution.py`, `context.py`, `prompts.py`, `proposals.py`, `runtime.py`, `specialists.py`, `tools.py`; shared `services/design/editable_model.py`; generated JSON Schema and TypeScript; workspace `ProposalReview.tsx` and its test; `ComponentIdentity.tsx`; map `CesiumView.tsx`; `editor-transform.ts` and its test.

Interrupted Road draft removal is isolated in baseline checkpoint `260c094`; it was not extended into this milestone. No environment or production model configuration file was changed.

## 23. Explicit unsupported features

- PROFILE, PRISM, PLACE_AT_POINT, PLACE_AT_CHAINAGE and ALIGN_TO_PATH as standalone operations.
- General polygon extrusion, arbitrary profile sweep, CAD booleans, watertight joins, curved solids, triangulated authoritative meshes or a full CAD kernel.
- Non-planar SWEEP/CHANNEL; OFFSET beyond a straight planar two-point path.
- Arrays of arbitrary composite templates; automatic tangent rotation of array templates; inherited parent transforms.
- Generic semantic patch execution: normal manual editing works, but Generic3DExecutor.apply_patch explicitly rejects generic patches. Existing Building Patch remains supported.
- Terrain following and elevation resolution; survey, soil, structural, foundation, hydraulics, traffic or code-compliance analysis.
- Relationship engineering validation and the unsupported constraints listed above.
- Arbitrary AI code execution, AI-written Python/JavaScript, and new asset-specific specialists.

Segment boxes/cylinders may meet or overlap at joins; they are conceptual components, not a fabricated construction model. The bounded language can compose unfamiliar objects only when their shape fits these supported operations.

## 24. Remaining work before REAL LIVE FLOW

The integration path exists: saved selection → frozen/tool site context → primary-provider design request → AI3DDesign proposal → existing approval → deterministic build → editable revision. Fixture-provider integration and real workspace persistence are verified.

Still unverified, deliberately without paid requests:

- Whether current Qwen reliably emits this schema, complete system decomposition and accurate local placement within the unchanged model/runtime limits.
- Live clarification and repair behavior for arbitrary requests, unknown site facts and unsupported operations.
- Live output size/truncation behavior for mixed compositions under the existing output limit.
- End-to-end live AREA/ROUTE/POINT/ENDPOINTS requests, including user intent constraints and selected existing-object grounding.
- Quality review of generated assumptions and semantic relationships; geometry validation alone cannot certify that an otherwise valid composition meets the user's full design intent.

A later authorized live acceptance batch should exercise those flows using this unchanged bounded contract and report failures. Additional primitive or terrain capabilities require their own deterministic validation. No such batch was run here.

## 25. Acceptance decision

**GENERIC 3D EXECUTOR V1 = ACCEPTED** for supported conceptual primitives, deterministic compilation, existing approval/revision persistence and normal workspace editing.

**REAL LIVE FLOW = NOT YET VERIFIED.** Structural safety, code compliance, construction readiness and survey validity remain unvalidated. Acceptance is limited to the explicit implementation above; it does not imply those capabilities or unrestricted arbitrary-object generation.

Work stops at this milestone. Building production remains unchanged, model configuration remains unchanged, and no new specialist or live Nebius request was started.

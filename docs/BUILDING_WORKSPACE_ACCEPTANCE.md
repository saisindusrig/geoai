# Building V1 workspace acceptance

Status: **WORKSPACE_ACCEPTED** for the bounded conceptual Building V1 contract.

## Acceptance results

1. **Fixture:** local project 488, scenario 376, generated revision 5. Real saved selection, prepared site profile, immutable proposal, explicit approval, typed BuildingSpec validation, BuildingAdapter and ModelRevision persistence. Rectangular 12 × 10 m office, two floors, four rooms, two internal partitions plus external walls, door, window, eight floor-specific columns, two beams, two slabs and roof: 34 components. No provider calls. Fixture script is a local development tool and creates a dedicated project each time; an earlier incomplete setup also left a draft acceptance project.
2. **Load:** normal `/projects/488/workspace` loads all 34 components through existing model APIs and Cesium. Screenshot verifies the building renders at its selected geographic location. No specialist viewer was added.
3. **Selection:** real browser selects wall `partition-0-end`, column `c0-0`, beam `b0-0`, slab `slab-0`, room `room-0-0`, door `entry` and window `window`. Existing Select matching selects the entire 34-component building. Stable semantic IDs remain intact.
4. **Inspect:** shared curated identity display shows component ID, kind/role, asset, Building ID, floor including zero, source component, specification and proposal, and source revision when present. Placement is REVIEW_REQUIRED, elevation resolution UNKNOWN; null elevation explicitly says local visual reference only. No arbitrary metadata dump.
5. **Transforms:** generated beam position edit modifies the ordinary draft. Existing generic transform unit tests cover move/rotate/scale, locks and cancellation. Existing Cesium browser drag test verifies preview, single commit, undo, Escape cancellation and camera restoration. That physical drag test uses the existing sandbox fixture; not every drag variant was independently repeated on every Building component.
6. **Layers:** generated categories use existing layers. Real browser hide/show works; hiding selected beam clears selection. Generic commit now removes hidden/deleted IDs from active selection. No asset-specific layer manager or hierarchy was added.
7. **Manual save:** browser moves one beam east by 0.1 m and saves through the normal manual-edit endpoint. A new revision is created; generated source revision is not overwritten. Repeated acceptance runs create additional immutable manual revisions.
8. **Lineage:** generic save copies server-owned lineage only for retained object IDs. Asset, original component ID, proposal, specification and generator remain unchanged; generationModelRevisionId stays anchored to the original generation across successive manual saves. Newly introduced IDs cannot acquire lineage merely by supplying client metadata.
9. **Comparison:** existing History comparison reports zero added, zero removed, exactly one modified component, with its position delta. Unchanged IDs remain stable.
10. **Reload:** real browser reload retains the edited position and semantic identity. Backend regression reloads persisted snapshots, verifies original document immutability, unchanged component count, complete lineage and null-elevation placement.
11. **Browser/E2E:** two tests pass using installed Microsoft Edge via Playwright's msedge channel. The bundled headless Chromium executable is absent. Building acceptance uses real backend read/save calls without model route mocks. Includes load, selection, Inspect, preview edit, save, reload, comparison and layers.
12. **Generic fixes:** manual save previously dropped lineage; generic commits left hidden selection active; Inspect omitted semantic provenance. Also removed specialist registry/adapter circular import by extracting shared registration metadata. Existing sunlight tests had outdated selectors; updated tests to current preset/tab and project popup event, preserving their functional assertions.

## Files changed in this acceptance batch

- `backend/app/api/routes/model_revisions.py`
- `backend/app/domain/specialist_metadata.py`
- `backend/app/services/assistant/specialists.py`
- `backend/app/services/assistant/building_specialist.py`
- `backend/scripts/create_building_workspace_fixture.py`
- `backend/tests/test_building_workspace_acceptance.py`
- `frontend/lib/types.ts`
- `frontend/hooks/useEditableModelEditor.ts` and its test
- `frontend/components/model-editor/ComponentIdentity.tsx` and its test
- `frontend/components/model-editor/ProfessionalModelEditor.tsx`
- `frontend/components/sandbox/SandboxWorkspace.tsx`
- `frontend/components/map/WorkspacePanels.test.tsx`
- `frontend/e2e/building-workspace-acceptance.spec.ts`
- this report

## Exact verification counts

- Full backend: **641 passed, 2 skipped, 3 warnings**, 302.21 seconds (`backend/building-workspace-full.log`). The import-contract extraction was additionally verified by the subsequent focused run.
- Final focused backend: **42 passed, 1 warning** (`backend/building-workspace-final-focused.log`); includes **25 Building specialist tests**, manual-save/lineage acceptance, model-revision and composition suites. Counts overlap with full regression and must not be added together.
- Frontend selection/save/Inspect/transform/placement/comparison suites: **49 passed in 9 files** (`frontend/building-workspace-core.log`). Includes failed remote-save preservation and hidden/deleted selection checks.
- Browser: **2 passed** (`frontend/building-workspace-e2e.log`).
- TypeScript: no errors. Targeted ESLint: no errors or warnings.

Screenshot: `frontend/test-results/building-workspace-accepted.png`.

Acceptance applies to conceptual editable geometry, not engineering adequacy. No foundations, MEP, stairs, engineering analysis, Road/Bridge, typed patches or production model changes were implemented.

Recommended next step: **TYPED BUILDING PATCH OPERATIONS**. Recommendation only; not started.

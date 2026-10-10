# Live AI3D Runtime Hardening V1

This milestone changes runtime integration and proposal review only. **No Nebius request or paid replay was made.** Qwen, AI3DDesign, Generic3DExecutor geometry behavior, supported primitives, temperature, token limits and production Building generation remain unchanged.

## 1. Bridge rejection root cause

The runtime compared exact asset-type multisets from classification against the detailed generic design's systems. Classification named PEDESTRIAN_BRIDGE, BRIDGE_ALIGNMENT, BRIDGE_DECK and BRIDGE_SUPPORT. The saved valid design expressed alignment, deck, piers and abutments as four PEDESTRIAN_BRIDGE systems. Exact string/count equality rejected that legitimate decomposition before normal tool validation/persistence.

## 2. Deterministic compatibility algorithm

The generic AI3D path now uses `decomposition_compatibility.py`:

- Canonicalize explicit aliases for bridge, warehouse, parking and road compositions; other asset types require exact identity rather than sharing an overly broad family.
- Trace every system to a classified/requested asset or a bounded allowed component vocabulary. Bridge components include alignment/path, deck, piers, supports, abutments and approaches; warehouse components include shell, walls, columns, roof, slab and foundation.
- If a component could belong to multiple requested assets, an explicit CONTAINS, SUPPORTED_BY or CONNECTS_TO relationship to a known system/object resolves its parent. Ambiguous components are rejected. A relationship cannot authorize an unrelated DAM/AIRPORT/PIPELINE system.
- Retain required-family coverage and specific classified bridge alignment/deck/support component coverage.
- Reuse existing deterministic user-request parsing to recognize explicitly requested additional assets. Negated/ambiguous wording does not authorize extra families.
- Preserve explicit supported user quantities using identifiable root systems; columns and other incidental components do not count as additional warehouses/bridges. Repeated recognized assets in the request also retain their quantities.
- Return DECOMPOSITION_COMPATIBLE, UNEXPECTED_SYSTEM, MISSING_REQUIRED_SYSTEM or QUANTITY_MISMATCH with trace assignments/issues.

This is a bounded compatibility vocabulary, not a new asset generator, general semantic reasoner or unrestricted family whitelist. Ambiguous parentage/counts can require clearer systems in a future model response. Legacy non-generic proposal decomposition remains on its existing check.

## 3. Saved bridge offline replay

The original authenticated payload was replayed without editing it or persisting a proposal. Result:

- DECOMPOSITION_COMPATIBLE, no compatibility issues.
- Normal AI3D validation: DESIGN_VALID / GEOMETRY_VALID, zero issues.
- Five potential editable components.
- Engineering UNVALIDATED; relationships RECORDED_NOT_ENGINEERING_VALIDATED.

This is offline integration proof, not live approval or successful generation. The historical live failure remains preserved.

## 4. Tool argument boundary

After outer ProviderResponse validation, `tool_boundary.py` validates the entire call batch before any dispatch:

1. Reject tool names outside the controlled allowlist.
2. Parse each arguments string as deterministic JSON.
3. Validate the parsed object against the same SCHEMAS contract used by controlled tools.
4. Dispatch only after all calls in the batch pass.

The existing tool-count gate also runs before validation/repair, preventing extra repairs beyond the allowed call budget. Normal tool project ownership, frozen context, stale references, proposal and approval gates still run after this boundary. No speculative comma/bracket/regex correction is used.

## 5. Saved walkway offline classification

The unchanged saved arguments fail with **TOOL_ARGUMENT_JSON_INVALID**, JSON_SYNTAX: “Expecting ',' delimiter”, line 1, column 1895, position 1894. They are eligible for exactly one model repair per call attempt. The offline replay did not invoke that repair, reconstruct the arguments or dispatch a tool.

## 6. Nested repair behavior

Only JSON syntax or tool-schema failures receive one direct PRIMARY completion. The request includes the original frozen/user context, intended tool name, untrusted invalid arguments, sanitized parser/schema errors and the tool's existing argument schema. Its instruction requests corrected arguments only, not a new answer/design or execution.

The returned object is parsed and validated normally again. Success records TOOL_ARGUMENT_REPAIR_SUCCESS; another invalid result or provider failure records TOOL_ARGUMENT_REPAIR_FAILED and aborts. Initial errors are recorded as TOOL_ARGUMENT_JSON_INVALID or TOOL_ARGUMENT_SCHEMA_INVALID. Disallowed names are never repaired. No second nested repair is allowed.

Repair diagnostics stored with the run contain event/tool/error categories and sanitized schema paths, not raw invalid arguments, hidden reasoning or secrets. The repair request carries invalid arguments only as bounded untrusted provider input. Cross-project/site/model authority remains server-owned.

The acceptance capture utility recognizes tool-argument repair schemas and records their outcomes correctly; no live acceptance utility was executed in this milestone.

## 7. Provider completion timeout

New setting: **NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS**, default **45 seconds**. ModelRouter applies it to PRIMARY completions through the existing shared provider/resolver, including bounded repairs. Values outside `(0, 120]` are rejected. FAST retains the existing configurable NEBIUS_TIMEOUT_SECONDS. No model-specific timeout branches, token/temperature changes or unlimited retries were added.

The routed 45-second timeout can permit a legitimate response past the old 25-second deadline. It does not guarantee that the previous timed-out AREA output would have succeeded; no new provider attempt was made to determine that.

## 8. Overall timeout and request bounds

The overall flow remains **120 seconds**, including classification, ordinary structured repairs, nested repairs and tools. A cancellation test proves this overall deadline interrupts a slow response despite the larger provider timeout. PRIMARY provider timeouts retain existing no-retry behavior; nested repair itself has no retry loop.

For a future PRIMARY-only flow, the conservative maximum is now **28 completions**: at most 2 classification attempts, 18 response attempts across 9 tool turns, and 8 nested repairs subject to the tool-count budget. Three such flows have an upper bound of 84 completions; the overall deadline usually limits practical consumption further. This is a bound, not authorization to run them.

## 9. AI-chosen preview parameter review

`preview_parameters.py` deterministically derives the new **AI-chosen preview parameters · PREVIEW_ASSUMPTION** review section from the approved design data. It includes sizes, radius, widths/depth/thickness, heights, spacing, count/grid parameters, heading, offset/chainage and local visual Z, with units. The saved bridge yields **15 entries**, including pier radius and abutment size.

The derived list is persisted inside proposal content before hashing, so existing exact-version approval covers these geometry values. The optional proposal-content field is backward compatible; AI3DDesign itself is unchanged. ProposalReview displays this section using the existing review/acknowledgement flow, without a new workspace or viewer.

USER_PROVIDED designs are not relabeled. Site XY coordinates are not exposed as AI-chosen dimensions or reinterpreted as survey facts. Within a PREVIEW_ASSUMPTION design, dimensions without machine-verifiable field provenance are conservatively listed as preview values; numerical equality to a site measurement does not promote them to SITE_FACT or DETERMINISTIC_DERIVATION. Existing named assumptions and unknowns remain visible. Local visual Z explicitly is not survey elevation.

## 10. Safety and unknowns

No engineering capability/status was upgraded. Soil, survey elevation, design loads, capacity, foundations, code compliance and engineering approval retain existing unknown/unvalidated behavior. Relationship compatibility proves traceability, not structural support or adequacy. Existing AI3D validator, ownership, staleness, unsupported-constraint/terrain, immutable revision and approval checks remain in force.

## 11. Files changed for this milestone

- `backend/app/core/config.py`: PRIMARY completion timeout setting.
- `backend/app/services/ai/provider.py`: bounded routed timeout.
- `backend/app/services/assistant/runtime.py`: nested boundary, compatibility check, explicit unchanged 120-second deadline constant and pre-repair tool budget.
- New `backend/app/services/assistant/tool_boundary.py`.
- New `backend/app/services/assistant/decomposition_compatibility.py`; the existing request decomposition module remains intact.
- New `backend/app/services/assistant/preview_parameters.py`.
- `backend/app/services/assistant/proposals.py` and `backend/app/domain/assistant_runtime.py`: derived optional proposal-review data.
- `docs/contracts/stage1.schema.json` and `frontend/lib/generated/stage1.ts`: generated proposal-content field.
- `frontend/components/workspace/ProposalReview.tsx` and its existing test: preview parameter display.
- New `backend/tests/test_runtime_hardening.py`; updated `backend/tests/test_model_router.py`.
- `backend/scripts/live_ai3d_acceptance.py`: capture nested repair schema/outcome and unavailable usage correctly.
- `docs/LIVE_AI3D_RUNTIME_HARDENING_V1.md`: this report.

Other pre-existing/local changes in the checkout were not incorporated into this milestone. No .env credential/model value, AI3D primitive schema or executor geometry operation was changed.

Offline evidence: `backend/live-results/runtime-hardening-offline.json`. Original authenticated live results remain separate and unchanged.

## 12. Focused tests

Final focused backend suite: **215 passed**, one existing test-client deprecation warning. This includes **21 new hardening tests**, existing Assistant runtime/proposal/tool tests, AI3D tests, provider/router/configuration/diagnostic tests, Building/Building Patch and capture tests. New hardening coverage includes asset/component and multi-asset compatibility, unrelated injections, explicit request/negation, required components, quantities, relationship parentage, malformed JSON, schema errors, one repair, repair failure, disallowed names, dispatch atomicity, successful repaired dispatch, provider timeout configuration, overall timeout and conservative preview derivation. Existing provider timeout/no-retry and unknown-data protections remain tested.

Frontend full unit suite: **192 passed across 40 files**. Updated ProposalReview tests: **6 passed**. TypeScript and full ESLint passed; production Next.js build passed. These overlapping counts are not additive.

## 13. Full backend regression

**734 passed, 2 skipped, 3 warnings in 275.74 seconds.** No live provider calls were made. The final run includes existing Building/Building Patch, provider, proposal/tool, unknown-data, model persistence, export and contract-drift suites. Warnings are existing test-client/Pydantic diagnostics; skipped tests were not represented as passes. A preliminary regression was superseded after final compatibility/test refinements; these counts are from the completed final-source run.

## 14. Exact next live acceptance batch — not run

Subject to separate authorization, retry only the original three saved/frozen-context cases using Qwen PRIMARY:

1. AREA project 577: “Create a small warehouse with parking and an access road here.”
2. ENDPOINTS project 578: “Create a pedestrian bridge between these points.”
3. Selected-road context in project 576, source revision 30: “Create an elevated bicycle walkway over the road.”

Use the new bounded 45-second PRIMARY timeout and existing 120-second overall deadline; unchanged model, token limits, temperature, primitives, geometry and criteria. Capture ordinary/nested attempts and repairs, decomposition trace, schema/geometry results, assumptions and unknowns. Only a valid saved proposal may proceed through captured review and explicit controlled approval. Perform real workspace generation/edit/save/history acceptance on the first successful generated case, preserve existing objects, and stop after the three flows.

**This milestone stops before that batch. No Nebius request was made.**

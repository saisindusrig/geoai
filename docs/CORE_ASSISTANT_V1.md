# GeoAI Core Assistant V1

This batch strengthens the existing orchestration layer. It adds no geometry generator and makes no model-selection or workspace-layout changes.

## Reused architecture

AIProvider and ModelRouter remain the provider boundary. Existing CivilIntent, frozen message context, catalogue/family mappings, capability registry, accepted project memory, controlled tools, immutable proposal versions, dependency manifests, exact-version approval and deterministic execution gates remain authoritative.

## Request understanding

The server policy now provides `request-understanding/1`: objective, intent, individual assets and quantities, families, conceptual relationships, referenced saved objects, site dependency, requested operation, capability requirements, relevant catalogue candidates, required tools, source revision, site selection/profile references, document ENU axes, deterministic translation, unknown engineering fields, assumptions, expected effect and approval requirement.

Catalogue candidates are limited to relevant matches, at most 20. The full catalogue is not placed in the prompt. Original user intent is retained in asset requirements, including modifiers such as elevated and bicycle use.

Two warehouses with parking, road, drainage and water tank remain six assets. Proposed relationships connect buildings to road, site/buildings to drainage, and tank to buildings. An explicitly connected pedestrian bridge links to the warehouse. These conceptual relationships are stored with the immutable proposal; they do not silently modify live composition.

## Clarification and context

Unselected editing requests require selection. Nonblocking material, dimension, soil and loading questions do not prevent preliminary conceptual planning. A model classification cannot override the server into a questionnaire. Saving a proposal still requires the existing saved site-selection/profile references; without them GeoAI explains how to continue and can discuss a concept.

Only relevant tools are advertised and accepted by the runtime. Generic readiness definitions require none; selection questions expose selection; edits require selection and saved revision; site-readiness explanations expose profile/readiness; failed checks expose checks/revision; terrain-sensitive designs expose captured terrain and bounded samples. Identical successful results are cached only within the current operation. Repeated loops retain the existing bounded failure behavior.

## Editing and unknown data

Editing preloads selected objects and model revision through the existing controlled registry before any proposal. `500 mm east` deterministically becomes `[0.500, 0, 0]` in saved document LOCAL ENU coordinates. The proposal service rejects missing or altered translation targets, distance or direction for this explicit request. Existing selection hashes, stale dependencies, ownership, editor-dirty checks and approval hashes remain enforced.

Unavailable elevation, soil, groundwater, survey accuracy, utilities, structural capacity, design loads, datum and compliance remain explicit unknowns. Actual site facts are supplied separately by the frozen context and evidence-bearing tools. No default engineering numbers are introduced. No structural safety conclusion is available without validated analysis. Runtime safety responses remain server-owned.

## Proposals and response presentation

Design tools cannot drop requested asset types/quantities. A successful proposal is not created twice in one operation. If the model ends without a proposal, a bounded server-generated conceptual proposal can preserve the grounded request through the existing ProposalService. The plan includes objective, requested/proposed assets, connections, unknowns, explicit assumptions, accepted memory references, constraints, source references and dependency manifest.

Questions remain read-only. Geometry edits stay preview-only. Approval is an application command; generation stays capability-gated. Responses use GeoAI branding, suppress JSON dumps and reject explicit first-person claims of direct geometry mutation. These presentation checks are conservative guards, not a universal natural-language fact checker.

## Deterministic product coverage

- A: flyover — bridge family, conceptual proposal, no generator claim.
- B: warehouses/parking/road/drainage/tank — six assets and connected planning proposal.
- C: selected P03/P04/P05 — exact 0.500 m east translation, selection/revision provenance, no mutation.
- D: engineering readiness — read-only explanation and relevant site tools.
- E: road avoiding steep terrain — terrain tools, unknown values retained.
- F: bridge safety — server-owned statement that validated analysis is unavailable.
- G: elevated bicycle warehouse and pedestrian bridge — separate connected concepts with capability limits.
- H: retaining wall without selection — blocking selection clarification, no proposal.
- I: drainage — preliminary proposal when saved site references exist; useful explanation when none exist, without invented terrain.
- J: selected objects — only selection retrieval advertised; in-operation cache verified separately.

Tests also cover incorrect translation, irrelevant tool denial, model-requested nonblocking clarification, omitted assets, mutation claims and provider-brand cleanup. All new runtime tests inject fixtures and make no live Nebius calls.

## Remaining limitations and next module

Catalogue matching and relationship suggestions are bounded heuristics, not comprehensive spatial design. Arbitrary edit operations, rotated placement interpretation, advanced relationship refinement and specialist engineering calculations remain future work. Proposal persistence requires a current saved site profile. Long responses can still encounter the existing token/turn limits; this batch does not establish new live-model reliability scores or resolve historical truncation by changing budgets.

Next implement the Building specialist specification/validation adapter using the existing registry and revision pipeline. Start with typed requirements, layout constraints and deterministic concept validation before enabling generation. Keep engineering adequacy separate from architectural concept validation.

## Changed files

- `backend/app/services/assistant/decomposition.py`
- `backend/app/services/assistant/policy.py`
- `backend/app/services/assistant/understanding.py`
- `backend/app/services/assistant/tool_contracts.py`
- `backend/app/services/assistant/runtime.py`
- `backend/app/services/assistant/prompts.py`
- `backend/app/services/assistant/proposals.py`
- `backend/app/domain/assistant_runtime.py`
- `backend/tests/test_assistant_runtime.py`
- `backend/tests/test_geoai_core_v1.py`
- `backend/evals/reporting.py` and `backend/evals/rescore_pilot.py` (historical replay preserves archived instructions)
- `backend/tests/test_geoai_pilot_corrections.py`
- `frontend/lib/generated/stage1.ts` and `docs/contracts/stage1.schema.json` (generated contract synchronization only)
- this report

Verification logs: `backend/core-v1-focused.log`, `backend/core-v1-relevant.log`, `backend/core-v1-last-check.log`, `backend/core-v1-repair.log`, `backend/core-v1-complete.log` (local ignored artifacts).

Final verification: full backend regression **615 passed, 2 skipped, 3 existing warnings** in 244.67 seconds. Relevant focused suite **188 passed**; final runtime/core checks **65 passed**; integration repairs **2 passed**. These overlap and must not be added together. All ten product scenarios A–J passed. There were no live model requests, additional benchmarks, routing/configuration changes or specialist generators added.

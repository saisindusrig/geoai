# Phase 4C-R — Offline packet optimization and truncation diagnosis

## Result and evidentiary limit

UNDERSTAND message content shrank from **17,950 to 6,268 serialized UTF-8 bytes: 65.08% smaller**. The reconstructed complete JSON request body shrank from **20,010 to 7,136 bytes: 64.34% smaller**. Strict contracts, ownership/source checks, support/clearance requirements, model configuration, output cap, timeout and bounded retry policy remain unchanged.

This establishes reduced input/context complexity and successful mocked validation. It does **not** establish that real Qwen will finish within 3,500 output tokens. The original responses cannot distinguish reasoning consumption from verbose structured output. **No new Nebius request was made.**

## Exact request audit

The original logical request was reconstructed from the retained private frozen snapshot, original stage packet, unchanged provider body builder and original repair text before optimization. Credentials/authorization headers are excluded. Its content-byte totals plus the existing 1,024-token conservative framing reserve exactly match both recorded live reservations: **18,974** and **19,185**. Original wire bytes/hash were not retained, so matching serialized sizes does not prove a captured wire hash.

Existing routing uses ModelRouter PRIMARY, model **Qwen/Qwen3.5-397B-A17B**, no tool calls and a **45-second timeout**. Existing NebiusProvider sends two chat messages, temperature 0.1, max_tokens 3,500 and response_format type json_object. The exact authoring JSON Schema is prompt data; JSON mode does not replace the server's strict schema/semantic validation.

Measured original → optimized contributions:

- System prompt: **271 → 468 bytes**. The optimized instruction is more explicit about UNDERSTAND's narrow responsibility.
- Serialized user message: **17,679 → 5,800 bytes**.
- Prompt schema: **2,206 → 1,772 bytes**, **19.67% smaller**. Only presentation titles are removed from transmitted schemas; the actual Pydantic contracts and checked-in schemas are unchanged.
- Capability descriptor within this stage: **2,028 → 403 bytes**.
- Human-request input object: **428 → 428 bytes**.
- Trusted context projection: **12,648 → 3,116 bytes**.
- Duplicate instruction field: **273 bytes → absent** in the provider's user payload; instructions are sent once as the system message.
- Serialized body overhead, including JSON string escaping, role wrappers and controls: **2,060 → 868 bytes**. This is JSON byte accounting, not measured model chat-template tokens.

Individual field-value sizes omit their enclosing keys/separators, so they are not an additive decomposition of the complete message. Exact complete-body/content totals include that overhead.

No transformers, tokenizers, tiktoken or OpenAI SDK is installed in the backend environment, and no usable offline Qwen tokenizer was located in the checked cache. No tokenizer/package/model download was performed. Byte sizes are measured. An empirical estimate using the original 7,143 reported input tokens divided by its content bytes gives **about 2,494 optimized input tokens**; different token density/chat framing makes this an estimate, not a tokenizer result or guarantee. The prepared canary conservatively reserves **7,292 input tokens** (content bytes plus 1,024 framing reserve).

## Removed duplication and stage projections

UNDERSTAND previously received the full recipe parameter catalog and the whole frozen snapshot, including another capability descriptor and another user request. It also carried repeated unavailable relief evidence, broad site metadata and duplicated system instructions. The optimized stage receives the original request once, supported semantic vocabulary/features, exact intent schema, selection/reference bindings, relevant site facts, accepted requirements and explicit unknowns. It is instructed to identify user-supplied dimensions/preferences and missing/unsupported requirements, without creating assemblies, material catalogs, recipes or components.

PLAN receives validated intent and hash, supported component vocabulary, assembly/count/placement limits and section parameter keys needed to create valid shared definitions. EXPAND receives one exact assembly/asset, plan hash, relevant component-operation/recipe parameter descriptors and shared material/section definitions. The plan has no group-to-material/section binding; all its shared definitions remain candidate choices rather than inventing an unsafe subset. RELATE receives exact validated component IDs, types/parameter summaries, assembly references and dependency/support/clearance constraints; material/section catalogs and recipe descriptions are deferred away from this stage.

The short authoritative user requirements remain available downstream so normalized intent cannot hide an explicit dimension or preference. Accepted requirements and exact selected object/evidence IDs remain in every projection. Projection objects are deep copies, preventing an in-process provider/mock from mutating the server snapshot through shared lists.

## Context that remains server-owned

The complete frozen request, project/source identity, clean ModelRevision/document hash, full site/selection payload, accepted requirement versions, evidence identity and full capabilities remain in the private server snapshot. A frozen-context hash binds each projection to it. Existing freshness checks run before provider invocation and again after provider latency. Candidate construction still attaches provenance on the server; model output cannot supply authoritative project/source/approval/validation fields.

UNDERSTAND excludes not-applicable dimensions. Applicable facts retain their verification/source/value/evidence data. Unknown relief retains null values, source kind and reason; repeated evidence identities are retained once as an exact union. Known relief is not replaced with unknown. The full evidence associations and missing-information records remain on the server. Required terrain, soil, loads, foundations, clearance, code, datum and engineering-approval unknowns remain explicit. Final support/clearance validation and finalization blocking are unchanged.

## Reasoning-token investigation

The [official Qwen model card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) documents default thinking, an API-level non-thinking example for supported serving frameworks, and states that Qwen3.5 does not use Qwen3's soft prompt switches. This establishes model/framework capabilities, **not** that Nebius honors the same parameter on this configured route. No thinking parameter was added and reasoning was not disabled.

The local provider integration exposes no thinking/reasoning configuration. Its body contains only existing model/messages/sampling/output/JSON-mode fields. It retains aggregate prompt/completion tokens and safe finish/truncation metadata; it does not preserve reasoning_content, completion_tokens_details or reasoning-token counts. The two original safe ledgers therefore do not establish whether reasoning metadata was present in the discarded provider bodies.

The consulted [Nebius inference overview](https://docs.tokenfactory.nebius.com/ai-models-inference/overview) and [structured-output documentation](https://docs.tokenfactory.nebius.com/ai-models-inference/json) did not establish the thinking-control contract or reasoning-token accounting for Qwen3.5 on this route. Accordingly, whether this route's max_tokens includes hidden reasoning, and which explicit thinking controls it honors, remain **unverified**. Parameters from QwenCloud, NVIDIA or a self-hosted vLLM deployment must not be assumed portable.

Observed: both live calls reported completion_tokens=3,500 and finish_reason=length. Hypotheses: default thinking and/or verbose output contributed. The evidence cannot apportion those tokens. Concise prompting alone is not proven to solve exhaustion.

## Retry analysis

The old second packet added **211 bytes** overall: a 201-byte repair object plus its enclosing field overhead. Original content increased from 17,950 to **18,161 bytes**, and reported input increased from 7,143 to **7,179 tokens**. The repair requested valid stage data without changing stage duties, omitting full context, narrowing expected output or increasing the cap. Thus there is no evidence it reduced expected output complexity. It also truncated at 3,500 tokens.

The existing maximum of two attempts per stage remains. Semantic failures still stop; no dimension repair, fabrication, removal of support/clearance intent or validator bypass was introduced. Future retry success is not guaranteed.

## Offline verification

Verification on Windows, 2026-10-10:

- Full backend: **946 passed, 2 skipped, 0 failed**, 284.84 seconds; three existing dependency/schema warnings. Skips: ownership comparison needs two seeded scenarios; dedicated PostgreSQL/PostGIS database is not configured.
- Focused projection/orchestration/authoring/CAD/BIM/Building/Patch/AI3D/ModelRevision suite: **231 passed, 0 failed**, 38.95 seconds; one dependency warning.
- Final projection/orchestration check after downstream original-user-requirement preservation: **38 passed, 0 failed**, 9.93 seconds; one dependency warning.

Tests use mocked provider responses/recorded safe truncation metadata and block real Nebius transports. They cover the original industrial request, minimal intent through the original schema, all unchanged schema validation leaves, projection immutability, explicit unknowns, retained source/reference hashes, unsupported requests, malformed JSON, simulated truncation, bounded retry and all downstream contracts. Existing authoring tests verify saved proposals with zero native compiler calls/approvals/ModelRevision changes and reject stale source/accepted context. Building, CAD, AI3D and ModelRevision regressions are included.

The full suite used fresh seeded file-backed SQLite and isolated local storage. Final small projection changes were checked again with the 38-test projection/orchestration suite. No failing assertion was bypassed and no timeout/resource/output limit was increased. No new live model response or reasoning measurement was obtained. Initial local snapshot inspection accidentally resolved configured cloud storage and failed closed; subsequent reconstruction explicitly disabled cloud storage and used only the isolated local artifact.

No frontend source or UI wire contract changed. No production switch, provider configuration or ModelRouter changed.

## Files changed

- Modified backend/app/experimental/bim_authoring.py: stage-specific capabilities/context, concise scope instructions, presentation-only schema compaction and shared-definition/reference projections.
- Modified backend/app/experimental/bim_orchestration.py: verified projected context and one system instruction instead of duplicating it in the user packet.
- Modified backend/tests/test_bim_orchestration.py: assert projected site summary instead of full site payload.
- Added backend/tests/test_bim_packet_projection.py: ten offline compatibility/immutability/projection tests.
- Added backend/scripts/diagnose_bim_packets_4cr.py: local logical-request reconstruction comparison and measurements; no provider invocation.
- Added this report.

Ignored evidence is in backend/.cad-proof-output/4cr-original.json, 4cr-measurements.json, 4cr-understand-canary-request.json and 4cr-* regression logs/JUnit files. The Phase 4C terminal run and evidence are preserved; no live run was resumed.

## Proposed canary — prepared, not executed

One UNDERSTAND call only, using the same original industrial-platform request, PRIMARY model Qwen/Qwen3.5-397B-A17B, 3,500 output-token cap and 45-second timeout. Estimated input about 2,494 tokens; conservative input ceiling **7,292 tokens** for the prepared content/framing reserve. No automatic retry, PLAN continuation, CAD Build, approval or ModelRevision change.

Before executing, obtain separate explicit authorization for this one paid call, its 7,292-input/3,500-output token ceilings and isolated owned test actor/project. Use a fresh authorized canary run; do not resume the terminal Phase 4C run. Stop after the single response regardless of success, failure or truncation. Exact serialized packet is prepared locally; no paid call is authorized by this offline batch.

STOP after Phase 4C-R. No Phase 4D or additional model benchmarking was started.

# Phase 4D: prepared multi-model BIM screening

Preparation only, 2026-10-10. Paid inference requests: **0**. No winner or stage model recommendation is established. Qwen/Qwen3.5-397B-A17B remains production PRIMARY; production routing, schemas, engineering gates and CAD settings are unchanged.

Budget update: the user now caps cumulative experimental testing at **$20 USD** from a user-reported $40 account allocation, protecting $20 for development. This supplements, never increases, the token/request limits below. Execution remains blocked pending reliable billing verification and separate batch authorization. See `docs/BIM_TESTING_BUDGET_4D.md`; no batch is authorized by this allocation.

## Account discovery and eligibility

Authenticated `GET https://api.tokenfactory.nebius.com/v1/models` returned HTTP 200 and listed all five exact candidate IDs:

- Kimi-K3: `moonshotai/Kimi-K3`.
- DeepSeek V4 Pro: `deepseek-ai/DeepSeek-V4-Pro`.
- GLM-5.2: `zai-org/GLM-5.2`.
- MiniMax M3: `MiniMaxAI/MiniMax-M3`.
- Nemotron-3-Super-120B-A12B: `nvidia/nemotron-3-super-120b-a12b`.

Catalog evidence: `backend/.cad-proof-output/4d-discovery-a2cb4310f7ec4a87996e8bebc5c20a07/catalog.json`, timestamp 2026-10-10T05:10:45.193720Z. These IDs came from the account endpoint, not guesses. Catalog listing does not prove paid inference entitlement, runtime health, or JSON compliance; those remain untested. An initial sandbox GET failed with ConnectError; its safe evidence remains under `4d-discovery-8564ab49063243c29b1154744f6c0d87`. No credentials, headers or response errors were persisted. Two catalog GET attempts, no completion POST.

## Model-specific capability status

Nebius's official guides show exact-model Chat Completions quickstarts for [Kimi](https://github.com/nebius/token-factory-cookbook/blob/main/models/kimi-k3.md), [DeepSeek](https://github.com/nebius/token-factory-cookbook/blob/main/models/deepseek-v4.md), [GLM](https://github.com/nebius/token-factory-cookbook/blob/main/models/glm-5.2.md), [MiniMax](https://github.com/nebius/token-factory-cookbook/blob/main/models/minimax-m3.md) and [Nemotron](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-super-120B.md).

Kimi and DeepSeek are described as reasoning models, without explicit JSON/thinking wire options in these quickstarts. GLM describes multiple thinking-effort levels without an exact hosted request example. MiniMax's guide mentions `thinking` modes enabled/adaptive/disabled but does not demonstrate the HTTP parameter shape or compatibility with GeoAI's response_format. Nemotron's guide claims structured output without the exact JSON Schema dialect/wrapper. Consequently, **exact-route json_object/json_schema enforcement and thinking-disable/effort/budget settings remain UNVERIFIED for all five**. No upstream option is silently translated to another provider. Generic [Nebius JSON documentation](https://docs.tokenfactory.nebius.com/ai-models-inference/json) is not a per-model confirmation.

Initial screening proposes the same baseline body across models: model ID is the only difference within each scenario; two frozen system/user messages, `temperature=0.1`, `max_tokens=3500`, `response_format={"type":"json_object"}`. No speculative thinking fields, tools, streaming, retries or top_p/top_k overrides. If an option is rejected, record failure, never remove it and replay. Default thinking/sampling differences are a limitation of the common baseline, not evidence of an intrinsic model ranking. JSON Schema or model-specific controls would be separately reviewed experiments.

## Reproducible isolated fixtures

Run `backend/.venv/Scripts/python.exe scripts/prepare_bim_evaluation_4d.py platform|bridge|mixed` from backend with `PYTHONPATH=.cad-proof-deps;.`. Each invocation creates a fresh UUID directory, SQLite database, actor/project 490001, empty baseline revision, owned AREA selection/site evidence, authoring run 1, private frozen snapshot and immutable preparation ledger. The selected fixtures below use direct owned orchestration without starting unrelated app jobs. No production database/storage or historical canary is accessed. Inference transport is explicitly disabled in preparation. All models receive the identical packet for a given scenario and existing server validators.

- Platform: `.cad-proof-output/4d-platform-4005c5d4343f4c81a2e21497f1a2f2c7`; packet `a1335b07a96d7aa3bb9df7b31a363d24d07a2f4ded71bf518372b5b6ec1c0cb7`; reservation **7481**. Three assemblies: columns, framing and slab; 5 m by 3 m at 3 m conceptual height.
- Bridge: `.cad-proof-output/4d-bridge-39f073205971470a9829fd0a9789c693`; packet `54ad313662b2b66d48691a25a117123fa8f285e01f7b58e894816ecc3e7d6cea`; reservation **7445**. Two 6 m spans, 3 m deck width, three support lines, beams/deck/piers/bearing blocks.
- Mixed: `.cad-proof-output/4d-mixed-cd1c0ac81a464aa188be8feb993d192f`; packet `ad93b17b530ac04c843b25ec0bef149a5c7eace6614a3d17cd85014cc1c31268`; reservation **7523**. Road crossing plus separate utility support platform. Pipe routing and road-alignment geometry must be explicitly unsupported.

Directory paths are relative to backend. Each contains `acceptance.db`, `prepared.json`, `understand-request.json` and `evaluation-ledger.json`. Shared synthetic evidence has no surveyed terrain or elevation. Metre dimensions are preview assumptions, not design sizing. Geometry capability comes from the existing packet/recipe registry; no new primitive or specialist was introduced. Existing bridge fixture is not treated as a golden multi-span result: model results must satisfy this request's two-span rubric independently.

Some initial preparation attempts were interrupted while waiting on unrelated app startup; preserve their directories as superseded evidence, do not execute them. An additional earlier platform preparation completed under `4d-platform-bc0f597787fb4d828e3c040914d132cd`; it is not part of the selected matrix. Only the three exact selected packets above are proposed for screening.

## Exact proposed authorization budget

- Maximum **15 paid requests**: five catalog-listed models, three scenarios each, sequential concurrency 1; no automatic retries or replacement models.
- Output maximum **3500 tokens/request**, **52,500 aggregate**.
- Timeout **45 seconds/request**, at most **675 seconds aggregate configured request time** (not total wall time).
- Input ceiling **8192 conservative tokens/request**, **122,880 aggregate ceiling**. Actual prepared reservations sum to **112,245** across the fixed matrix: 5 × (7481 + 7445 + 7523).
- Reservation method remains UTF-8 message bytes +1024 conservative overhead, not a claimed exact tokenizer count. Recheck frozen source, packet identity, gate settings and reservation immediately before future dispatch.
- Stop the entire batch on exhausted ceiling, an incomplete dispatch claim, uncertain timeout/crash outcome or explicit user stop. Never replay a claimed cell. Completed validation/HTTP rejections are scored, not repaired/retried.
- Provider-reported actual cost and reasoning counts are unavailable until responses. No dollar-cost maximum is asserted from public pricing. A monetary ceiling, if desired, requires account-specific price review before execution; token/request limits above are the proposed authorization boundary.

Preparation ledgers are NOT authorizations or dispatch claims. The mock-only evaluator has no live execution CLI. A future authorized batch requires a separate reviewed execution entry point: lock one batch, exclusive per-cell claims, durable intent before transport, pre/post frozen-source checks, unchanged-state hashes, aggregate numeric usage, explicit authorization identity and terminal no-replay handling. Do not wire this to ordinary production routing. Its transport-free/mock implementation is ready for that bounded integration after authorization; there is no callable built-in live provider in this batch.

## Validation scoreboard and rubric

All five candidates currently have **0/3 scenarios executed**, JSON/schema/semantic outcomes **NOT MEASURED**, usage/latency/cost **UNAVAILABLE**, and stage recommendation **UNDETERMINED**. A catalog HTTP 200 is not an authoring pass. No observed zeros are substituted for missing usage or failure-rate denominators.

For each model/scenario record JSON syntax, strict AuthoringIntent acceptance, existing `_validate` semantic-reference/capability checks, requirements preserved, unsupported-feature acknowledgment, explicit unknowns, refusal/truncation, latency and numeric usage/cost. Safe diagnostics exclude response text and reasoning. Counts missing in the provider response stay unavailable. A schema-valid response is only serverAccepted; final semantic/engineering rubric review remains pending, never automatically successful.

Frozen review rubric, identical for all models:

1. Preserve all requested systems, conceptual dimensions/span count and assembly intent. UNDERSTAND lacks structured dimensions, so preservation must be reviewed in its bounded text fields; do not change the schema to make scoring easier.
2. Platform must retain columns/primary and secondary beams/slab and three-assembly intent. Bridge must preserve two spans, beams/deck/piers/bearings and three support lines. Mixed must retain two distinct systems and explicitly decline pipe/road alignment generation.
3. Soil, loads, terrain accuracy, foundations, clearances, code and engineering approval remain unresolved; no invented survey, strength or adequacy claim. Assumptions/unknown explanations are reviewed against the request, not merely counted.
4. Reject unauthorized selection/object IDs, unknown feature enums and incompatible selection semantics using unchanged validators. Unsupported requirements must be explicit rather than silently dropped; absent data is a failure of requirement preservation.
5. Report JSON/schema/semantic acceptance separately. Qualification for expanded tests requires accepted outputs and complete rubric review on all three cases; safety failures disqualify. Rank qualified models by preservation/completeness first, then reliability/latency; cost is secondary. With only one observation/case, rates are descriptive, not statistical reliability guarantees.

## Later phases and architecture decision

No PLAN/EXPAND/RELATE inference is authorized. Select the best two or three only after observed screening results; if none qualify, recommend no expansion. Expanded budget must count UNDERSTAND, PLAN, one EXPAND per planned assembly, RELATE and strict final proposal validation, with a separate authorization and no native compilation. Review component types, IDs, positive metre dimensions, material/section references, existing recipes, dependencies, support paths and clearance unknowns through existing validators. Each candidate keeps independent checkpoints and provenance.

Architecture A is the simplest hypothesis to test first: one qualified model through all authoring stages. B adds a lightweight UNDERSTAND model only if measured performance justifies a split; none of the five is declared lightweight or superior by marketing. C adds a third stage model only if measured gains justify more boundaries. Independent single-model runs must precede a mixed pipeline. No architecture is selected as reliably best before validated data exists.

Stage-specific routing would require an experimental, server-owned, default-off model allowlist; immutable per-stage model/control/packet provenance; model-independent existing validators; explicit stage budgets and no automatic fallback/retry; durable batch/cell ledger; and reviewed request-option capability metadata. The production ModelRouter and Qwen PRIMARY remain untouched. Output mode, thinking and sampling changes need separate capability validation, not schema weakening.

## Engineering limits and verification

Concept models do not establish load capacity, soil/foundation suitability, terrain accuracy, hydraulic/traffic adequacy, support/bearing connection design, code compliance or clearance approval. AREA-based crossing evidence is conceptual, not a validated road alignment. Full proposal acceptance still blocks finalization where engineering unknowns remain. No CAD Build, automatic approval, proposal publication or ModelRevision mutation occurs in preparation.

Verification: **147 passed, 0 failed, 0 skipped**, 24.90 seconds, including 20 new evaluation cases. Existing Starlette/httpx deprecation warning only. JUnit: `backend/.cad-proof-output/4d-tests.xml`. The existing offline regression runner blocks real Nebius HTTP and configured S3. Suites: model evaluation, inference profiles, canary execution, BIM orchestration, BIM authoring and packet projection. Full backend was not repeated for this unintegrated experiment.

Read-only selected-fixture verification confirmed all packet hashes/reservations, catalog eligibility, zero paid calls/dispatches/checkpoints, one unchanged baseline revision per isolated database, zero proposals, approvals and CAD artifacts. Evidence: `backend/.cad-proof-output/4d-preflight.json`. The verifier explicitly sets an in-memory application database before imports and reads selected SQLite files with mode=ro. Its initial invocation emitted a default DB connection fallback during imports; no test data queries/writes were directed to that default database, and the import isolation was corrected before the final rerun.

Changed files: `backend/app/experimental/bim_model_evaluation.py`, `backend/tests/test_bim_model_evaluation.py`, `backend/scripts/discover_bim_models_4d.py`, `backend/scripts/prepare_bim_evaluation_4d.py`, `backend/scripts/verify_bim_evaluation_4d.py`, and this report. Existing changes are preserved. Production PRIMARY and previous canaries remain unchanged.

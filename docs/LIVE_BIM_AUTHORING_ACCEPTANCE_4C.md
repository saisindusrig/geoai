# Phase 4C — One controlled live Qwen scenario

**Decision: FAIL — live authoring acceptance failed at UNDERSTAND.** The orchestration's safety controls held; this is not evidence of an unauthorized mutation or unsafe execution. No valid model stage completed, so this is not a partially completed BIM proposal.

## Authorized scope and environment

The user explicitly authorized one three-assembly industrial maintenance platform scenario on 2026-10-10: Qwen/Qwen3.5-397B-A17B PRIMARY, actor/project 490001, twelve requests maximum, 3,500 output tokens per request, 42,000 total output tokens, 480,000 input tokens and unchanged 45-second timeout. The exact natural-language request from Phase 4C was used.

The scenario used its prepared owned project, synthetic AREA selection, saved site profile and clean empty ModelRevision in a separate SQLite database. Terrain, soil, loads and survey elevation remained unknown. The existing explicit FastAPI checkpoint endpoint was exercised through TestClient. Its authenticated principal was injected through the normal dependency in this isolated process; this verifies application ownership/gating, not production login/session behavior. Experimental flags and allowlists affected only the isolated process. No ordinary project or actual user design was changed.

ModelRouter, NebiusProvider, model configuration, output cap, authoring schemas, validators and geometry execution were unchanged. The existing provider transport was instrumented to enforce the authorized model/timeout/budgets and retain safe metadata only. Native compilation was additionally prohibited by the acceptance harness. No raw provider response text or credentials are included in this report or the safe evidence ledger.

## Per-stage completion

The companion `LIVE_BIM_AUTHORING_ACCEPTANCE_4C.html` contains the completion and request tables.

- UNDERSTAND: two requests, both HTTP 200 and `finish_reason=length`; both consumed 3,500 output tokens. The provider's structured-output gate rejected each as truncated before strict stage schema validation. First result RETRYABLE; second result FAILED / OUTPUT_TRUNCATED. No valid checkpoint identity exists.
- PLAN: not started.
- EXPAND assembly 1: not started; no plan or assembly identity was validated.
- EXPAND assembly 2: not started.
- EXPAND assembly 3: not started.
- RELATE/VALIDATE: not started.
- REVIEW: not started; no proposal saved.

## Actual request evidence

1. UNDERSTAND attempt 1: model Qwen/Qwen3.5-397B-A17B; **7,143 input / 3,500 output tokens**; finish reason **length**; provider latency **25.281 seconds**; endpoint-action latency including isolated startup **31.465 seconds**. Provider HTTP 200; failure class LIKELY_TRUNCATED; structured parse category OUTPUT_LIMIT. No schema-valid or semantically validated output.
2. UNDERSTAND attempt 2, the one existing stage-specific repair: same model/cap/timeout; **7,179 input / 3,500 output tokens**; finish reason **length**; provider latency **24.976 seconds**; endpoint-action latency including startup **31.314 seconds**. Provider HTTP 200; same truncation category. The adapter exhausted its two-attempt stage policy and became terminally FAILED.

Totals: **2 paid requests; 2 transport-successful responses; 0 authoring-successful responses; 2 rejected truncated outputs; 1 retry/repair; 0 provider timeouts.** Actual reported usage: **14,322 input tokens / 7,000 output tokens**, within all approved limits. The remaining ten-request global allowance was not used because the stage was terminally failed. No additional model, scenario or paid benchmark was started.

No provider-reported monetary cost was captured in the usage fields; credit consumption and monetary cost remain unverified. No price-based estimate substitutes for provider billing evidence.

## Parsed/validated counts and final state

- Validated intents, systems, plans, assets, assemblies, components, relationships and dependencies: **0**.
- Valid stage checkpoints: **0**; the server-owned frozen context remains intact in the existing private run snapshot.
- Authoring run: **1**, status **FAILED**, error **OUTPUT_TRUNCATED**, request counter **2**.
- Saved proposals: **0**. Approval records: **0**. Published CAD review/manifest artifacts: **0**.
- ModelRevision count: **1 before / 1 after**; document hashes match. Actual model mutation count: **0**.
- Native CAD Build: **not executed**. Production CAD Build: **not enabled**.
- Engineering and support/clearance conditions never progressed to a candidate; no adequacy, clearance, foundation or structural-compliance claim was made.

## Failure classification and remaining blockers

**Observed model-output failure:** both real responses reached the fixed output-token ceiling during the initial UNDERSTAND stage. HTTP 200 did not constitute a valid authoring response.

**Schema-design issue:** unproven. Output was rejected at the truncation gate before strict authoring schema validation; no field-level schema incompatibility is established by these requests.

**Backend integration failure:** none observed in endpoint execution, routing, budget enforcement, existing one-retry policy, terminal stop or mutation guards. Later stage expansion, dependency validation, proposal saving and live end-to-end acceptance remain untested because UNDERSTAND did not complete.

The evidence does not distinguish verbose structured output from reasoning-token consumption or establish a precise root cause of token demand. Provider-reported reasoning-token breakdown and raw content were not retained. Existing durable-worker and engineering/finalization limitations remain unchanged.

## Targeted next steps

Investigate the UNDERSTAND packet's size and the configured model's response/token behavior offline, using recorded metadata and mocked responses. The input was about 7,100 reported tokens; assess duplicated capability/site/schema context without dropping required evidence or weakening contracts. Separately review whether the existing model's reasoning behavior consumes the limited output budget. These are hypotheses to investigate, not proven causes.

Any proposed prompt/context change should first be reviewed and tested offline. A further paid request, different model, changed provider settings or higher output/timeout limits requires separate authorization. No such change or additional paid test was performed here.

## Files and evidence

- Added `backend/scripts/prepare_live_bim_4c.py`: creates one isolated owned scenario and a zero-call run; never invokes a model.
- Added `backend/scripts/run_live_bim_4c.py`: advances exactly one existing checkpoint endpoint per invocation, wraps the existing transport with the approved budget checks, and records safe usage/results.
- Added this report and the companion HTML completion table.
- Local ignored evidence: `backend/.cad-proof-output/4c-controlled-live/prepared.json`, `live-evidence.json`, `action-01.log`, `action-02.log`, isolated `acceptance.db` and private run snapshots.

Preparation initially used an incorrect test CRS argument; it was corrected to the existing WGS84 contract before any paid request. The failed preparation database was preserved separately. No production code, schema, model routing/configuration or workspace source was modified in Phase 4C.

STOP: the single authorized scenario has ended at terminal failure. Do not resume or launch further paid acceptance without new authorization.

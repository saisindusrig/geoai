# Phase 4C-H2 authorized single-call execution

Outcome: **OUTPUT_TRUNCATED**. The authorized single request completed with HTTP 200, but did not produce valid JSON or an accepted UNDERSTAND checkpoint. Execution stopped; no retry or continuation was performed.

## Authorized identity and preflight

Preparation ID: `e6fe966847524ba189e05ee7745fc680`. Actor/project: 490001/490001. Run ID: 1 in its fresh isolated database under `backend/.cad-proof-output/4c-understand-canary-e6fe966847524ba189e05ee7745fc680/`.

Packet SHA-256: `ddaa8041562b3c1a1d0539a359d48db964dc9da35e594cdf2cb803c05df15d2b`.

Before execution, the command verified the exact authorized packet hash, preparation ledger identity/frozen hash, zero request count, uninvoked transport, no existing execution claim, zero retries, and the model/timeout/output/input limits. The repaired harness regenerated the frozen source and canonical packet, checked clean zero-call run state, verified the original ModelRevision hash, validated request options and limits, and created an exclusive durable dispatch ledger. Existing experimental ownership and feature gates were enforced by the unchanged orchestration path before provider invocation.

## Actual provider results

- Model: **Qwen/Qwen3.5-397B-A17B PRIMARY**, unchanged.
- Paid requests: **1**. Retries: **0**.
- Conservative input reservation: **7,292 tokens**.
- Actual prompt tokens: **2,095**.
- Actual completion tokens: **3,500**.
- Actual total tokens: **5,595**.
- Maximum output tokens: **3,500**; timeout: **45 seconds**, unchanged.
- Request latency: **24.463 seconds**.
- HTTP status: **200**; safe finish reason: **length**.
- Reasoning-token counts: **not provided in the captured numeric usage fields**; no count inferred.
- Provider-reported cost: **not available in the captured cost fields**.
- JSON syntax: **invalid/incomplete**.
- Strict schema acceptance: **not achieved**; JSON parsing failed before the guard could perform schema validation on an object.
- Accepted checkpoints: **0**; completed stages: **none**.

Safe response metadata classified the response as LIKELY_TRUNCATED with OUTPUT_LIMIT; orchestration recorded OUTPUT_TRUNCATED. No raw model response or private reasoning was persisted or printed.

## Stop and unchanged state

The durable ledger records one dispatch, RESPONSE_RECEIVED, terminal=true, replayProhibited=true and planContinuationProhibited=true. The general orchestration adapter labels the authoring run RETRYABLE, but this canary is permanently stopped by its exclusive terminal execution ledger and the single-request authorization. It was not retried or resumed.

ModelRevision documents remain unchanged. Revision 1 retains SHA-256 `e3abf70ebf1d0ddd842c00df3106d4b0c2e464ef59713e82f145e5d788fdd8a8`. Proposals: **0**. Approvals: **0**. CAD artifacts: **0**. No PLAN continuation, native CAD Build, approval, model change or production deployment occurred. Historical runs were not resumed.

Evidence: `backend/.cad-proof-output/4c-understand-canary-e6fe966847524ba189e05ee7745fc680/canary-execution.json`.

This result does not establish how many completion tokens were reasoning tokens. Reduced input size did not guarantee a valid response within the existing output cap. Recommend a **separate offline investigation into Nebius-supported thinking controls** before considering another paid test. No such investigation or additional request was started in this batch.

# Phase 4C UNDERSTAND canary preparation

Prepared on 2026-10-10. Status: awaiting explicit paid authorization. No model request was executed.

The fresh isolated database and private run are under `backend/.cad-proof-output/4c-understand-canary-981cd96192534cfebc42a739366700b5/`. The directory contains `prepared.json`, `understand-request.json`, and `acceptance.db`. Actor and project are 490001; run ID is 1 in this separate database. The original three-assembly industrial maintenance platform request is retained verbatim. The previous terminal failed acceptance run is separate.

The existing PRIMARY route was checked without modification: `Qwen/Qwen3.5-397B-A17B`, 3,500 maximum output tokens, 45-second timeout. The packet contains 6,268 UTF-8 message-content bytes, plus the existing 1,024-token framing reserve: 7,292 conservative input tokens. This is a reservation, not an actual tokenizer count or a prediction of reasoning-token consumption.

The approved candidate scope is one UNDERSTAND request only. Automatic retries, PLAN continuation, native CAD Build, approval and ModelRevision mutation are prohibited. `executionAuthorized` remains false. The preparation entry point blocks the model transport and checks the empty checkpoint list, zero call count, original revision hash and input reservation.

## Execution handoff after new explicit authorization

Use this fresh database and packet only. Do not run the old `run_live_bim_4c.py` runner, which implements the previous multi-call authorization. Before sending, enforce a durable one-request ledger, verify the frozen source and prepared packet hash, enforce the exact model/timeout/output/input limits, and reject any existing request or checkpoint. Persist the request reservation before transport; an uncertain outcome must never be replayed. Invoke only one existing UNDERSTAND advancement, then stop regardless of READY, RETRYABLE or FAILED state. Do not resume the run or execute PLAN.

Capture only safe finish reason, numeric prompt/completion usage, optional numeric reasoning-token counts and numeric provider-reported cost when supplied. `safe_usage` in the preparation script provides an allowlist for numeric usage and completion reasoning counts; three offline checks passed, including exclusion of private text and malformed numeric fields. Do not persist raw provider responses or private reasoning. Missing reasoning counts and cost remain unavailable rather than being inferred.

Report strict JSON/schema and semantic validation outcome, safe usage, latency, request count, zero retries, proposal status and unchanged revision/no approval/no CAD artifact checks. On truncation, stop and recommend a separate offline investigation into Nebius-supported thinking controls. A smaller input does not establish smaller reasoning consumption.

No live JSON validity, truncation outcome, usage or cost is available before execution. Only preparation and offline metadata checks were performed in this batch; the backend regression suite was not rerun.

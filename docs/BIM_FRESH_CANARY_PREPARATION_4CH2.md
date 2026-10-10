# Phase 4C-H2 fresh UNDERSTAND canary preparation

Status: **READY FOR SEPARATE EXPLICIT PAID AUTHORIZATION**. Paid requests in this batch: **0**. No live Nebius transport was invoked.

## Fresh candidate identity

- Actor/project: **490001 / 490001**.
- Authoring run: **1**, in a completely new isolated database. SQLite allocated ID 1 again; this is not the historical run 1.
- Unique preparation identity: **e6fe966847524ba189e05ee7745fc680**.
- Candidate directory: `D:/layout project/backend/.cad-proof-output/4c-understand-canary-e6fe966847524ba189e05ee7745fc680/`.
- Database: `acceptance.db` in that directory.
- Private storage: the sibling directory `4c-understand-canary-e6fe966847524ba189e05ee7745fc680/public-cad-private/`.
- Canonical packet SHA-256: `ddaa8041562b3c1a1d0539a359d48db964dc9da35e594cdf2cb803c05df15d2b`.
- Frozen source/context SHA-256: `cccb46f3705f856355890af117e4e6bcbb6af5011f41ec362a8a0f1d70595986`.

The original three-assembly industrial maintenance platform request was preserved verbatim and checked against the original preparation constant. The optimized Phase 4C-R packet was regenerated from current owned context and matched the prepared canonical hash. Actor ownership, experimental CAD/BIM feature gates and allowlists were verified. The model route remains **Qwen/Qwen3.5-397B-A17B PRIMARY**, maximum **3,500 output tokens**, **45-second timeout**.

Message-content size is **6,268 UTF-8 bytes**; adding the existing 1,024-token framing allowance gives an actual prepared conservative reservation of **7,292 tokens**, equal to the ceiling. This is not actual provider usage or a tokenizer measurement. No inference about reduced reasoning consumption is made.

## Durable ledgers and candidate state

`prepared-request-ledger.json` was created exclusively and fsynced using the repaired guard. It records PREPARED_AWAITING_AUTHORIZATION, the canonical packet hash, frozen hash, reservation, zero requests, no transport invocation and executionAuthorized=false. It is an immutable preparation reservation record, not a dispatch claim or paid authorization.

The paid execution claim has a distinct name, `canary-execution.json`, which does not exist in the live candidate. The repaired runner must create that file exclusively after separately authorized execution preflight. No preparation record or historical terminal ledger needs to be reset, deleted or resumed.

The live candidate remains READY with **0 requests, 0 attempts and 0 accepted checkpoints**. The baseline ModelRevision hash is unchanged: `e3abf70ebf1d0ddd842c00df3106d4b0c2e464ef59713e82f145e5d788fdd8a8`. There are no proposals, approvals or CAD artifacts. UNDERSTAND alone can save an authoring checkpoint; the repaired runner blocks native compilation and does not continue to PLAN or an approval/proposal step. No production configuration was modified.

## Mocked acceptance

A disposable database/private-storage copy was created at `D:/layout project/backend/.cad-proof-output/4ch2-mock-a1315005348340efaafc748ef42fff45/`. The copied manifest was bound to that copy's database. The actual repaired execution runner was invoked with an explicitly fake transport; both synchronous and asynchronous real HTTP sends were blocked.

Results:

- Fake outbound transport invocations: **exactly 1**.
- Safe fake response: valid JSON, strict AuthoringIntent schema accepted, existing orchestration semantic validation passed, exactly one UNDERSTAND checkpoint accepted.
- Observed durable transition: REQUEST_RESERVED → DISPATCH_INTENT_RECORDED → RESPONSE_RECEIVED; final ledger terminal.
- The fake transport read the persisted dispatch intent and single-request count before returning its response.
- A second execution attempt was rejected with `CANARY_LEDGER_EXISTS_NO_REPLAY`; invocation count remained 1.
- The mock copy's ModelRevision remained unchanged; proposals, approvals and CAD artifacts remained zero.
- The actual live candidate's files were unchanged by mocked execution. Its zero-request READY state and unclaimed preparation ledger were independently checked using read-only SQLite and the ledger.
- All five historical failed-run file hashes remain unchanged. Its terminal ledger and claimed attempt were not resumed or reused.

Evidence in the candidate directory: `prepared.json`, `understand-request.json`, `prepared-request-ledger.json`, `4ch2-preparation.json`, and `4ch2-preflight.json`. Mock evidence: `canary-execution.json` and `preflight-result.json` in the disposable copy. Mock token figures are synthetic and are not live model measurements.

## Scope and handoff

New helper scripts: `backend/scripts/prepare_canary_4ch2.py` and `backend/scripts/preflight_canary_4ch2.py`. The existing repaired harness and model configuration were used without changes. The actual mocked end-to-end preflight passed; the previously verified full regression was not repeated for these preparation helpers.

This candidate is technically ready for a new authorization limited to this unique directory, actor/project 490001, run 1, one UNDERSTAND request, 7,292 input-reservation tokens, 3,500 maximum output tokens and 45 seconds. No retry, PLAN continuation, CAD Build, approval or ModelRevision mutation is allowed. No paid authorization has been granted for this fresh candidate. Stop here until the user explicitly authorizes it. Real provider JSON validity, token usage and truncation remain unknown.

# Phase 4D cumulative testing budget

The user allocates **at most $20 USD cumulatively** to Nebius experimental testing and reserves the other **$20** of the stated $40 account budget for development. This is a ceiling, not a spending target. No unused money is automatically spent. Allocation is not permission to execute a batch. Current paid requests in Phase 4D and this update: **0**.

Status: **BLOCKED — reliable live cost ceiling not yet established**. Offline monetary-ledger verification is complete; this is not a live-ready execution claim. Production routing, validators, CAD permissions and frozen screening packets remain unchanged.

## Pricing and accounting investigation

The official [pricing page](https://tokenfactory.nebius.com/pricing) was reached from a Nebius cookbook but yielded no readable rate data through the research tool. Targeted official-domain searches did not verify complete, account-effective rates for the five exact candidate IDs. A public GLM page search snippet mentions pricing but does not establish which exact GLM route, account terms and fees apply. No third-party prices were used to authorize spending. All five candidate input/output rate entries remain **UNVERIFIED**; there is no invented dollar estimate for the 15-call batch.

An [official Nebius cookbook](https://dev.nebius.com/cookbook/openhands-agent-canvas) states that reasoning tokens are included in output usage and billed at the output rate; count them once. It directs users to token counts/current prices or console usage for cost. This supports general accounting, not a verified guarantee that each of the five exact routes' `max_tokens=3500` bounds every billable generated token.

[Billing & Consumption](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new) describes organisation Usage views, automatic bank-card charging and applicable taxes. An account credit balance is not a hard experiment spending cap. Account-effective pricing, current available balance and any applicable fee/tax treatment have not been reconciled. No billing settings were changed.

[Inference Observability](https://docs.tokenfactory.nebius.com/ai-models-inference/observability) says operational dashboards are not for billing reconciliation. Its metrics are described for dedicated endpoints; they cannot establish exact shared-serverless charges for these experiments.

## Conservative reservation policy

One cumulative ledger for every model and evaluation phase: `backend/.cad-proof-output/4d-cumulative-budget.sqlite`. It was exclusively created with opening spend **unavailable**, not assumed zero. It has no authorized batch and no request reservation. Existing historical canary ledgers remain terminal and untouched. Earlier experimental charges have not been silently written off; the opening budget baseline needs explicit reconciliation/scope confirmation before spending.

Use integer nanodollars and Decimal arithmetic, rounding reservations upward. Before any future request, reserve the full **8192 input-token ceiling plus 3500 output-token ceiling** at reviewed account-effective USD rates. Do not assume prompt-cache discounts or average token consumption. Rates must include all relevant fees, have a frozen source-evidence hash and validity deadline, match the exact model, and have reviewed confirmation that every billable token is bounded. Unsupported or stale contracts block reservation.

For reviewed rates P and C in USD per million, reservation = ceil_to_nanodollar((8192×P + 3500×C)/1,000,000). Reasoning is not added twice. This formula is applicable only after the reviewed billable-token bound is established; an arbitrary margin cannot substitute for an unknown bound.

Opening reconciled spending + all held reservations must never exceed $20. SQLite `BEGIN IMMEDIATE` serializes check-and-reserve across processes. The durable reservation is committed before transport; an unfinished reservation blocks later calls after a crash. Never reset or recreate the ledger to recover funds. Other phases use the same ledger and require separately recorded batch authority. No price/authority flags are client-controlled in a future live integration.

Keep each full worst-case reservation held even if actual usage is cheaper. Store independently reconciled actual USD where available; missing cost remains unavailable. Uncertain transport, missing reconciliation or a charge above the reservation halts the entire ledger. Savings are not automatically recycled. A post-response mismatch cannot retroactively protect the account; verified pre-request maximum liability is mandatory before dispatch.

This ledger is an offline-tested, unintegrated component with no provider client. Its synthetic tests do not confirm actual Nebius rates. The review flags in the internal contract are prerequisites recorded by a trusted billing-review process, not a substitute for provider evidence. There is deliberately no paid execution CLI. A future runner must enforce this ledger together with frozen packet/model allowlists, durable at-most-once request claims, explicit human batch authorization and unchanged project-state checks. Do not connect a real transport until the current blockers are resolved and that bounded integration is reviewed.

The local ledger can govern GeoAI experimental requests sent through it; it cannot prevent unrelated account activity from spending the protected development balance. Reliable preservation also needs opening balance reconciliation and accounting for concurrent account charges. No production billing or routing changes are authorized by this task.

## First batch remains unchanged

Prepared screening: five exact catalog-listed models × three scenarios, **15 calls maximum**; sequential; **zero retries**; UNDERSTAND only. Input: **8192/request**, **122880 aggregate ceiling**, prepared reservations **112245**. Output: **3500/request**, **52500 aggregate**. Timeout: **45 seconds/request**. No PLAN/EXPAND, Build, approvals, native compilation or ModelRevision edits. A request that cannot be safely reserved is skipped by stopping the batch, not replaced or automatically retried. Exhaustion/uncertainty stops immediately.

## Offline verification and remaining blockers

Synthetic-budget tests verify cumulative ceilings across batches/phases, upward monetary rounding, unchanged $20 cap, separate authority, denied missing opening baseline, unverified/expired pricing, concurrent atomic reservation, incomplete claim after restart, no reset, and retained reservations on uncertainty/missing accounting/overshoot. Existing tests cover model matrix/body equivalence, strict semantic validation and at-most-once transport behavior with mocks only. Final counts are recorded below.

Combined offline verification: **84 passed, 0 failed, 0 skipped**, 18.03 seconds (`tests/test_bim_testing_budget.py`, `test_bim_model_evaluation.py`, `test_canary_execution.py`, `test_bim_orchestration.py`). JUnit: `backend/.cad-proof-output/4d-budget-tests.xml`. It included an existing Starlette/httpx deprecation warning and an avoidable pytest class-naming warning; the test import was renamed. Final budget-only rerun: **11 passed, 0 failed, 0 skipped**, 0.36 seconds, only the existing deprecation warning. JUnit: `backend/.cad-proof-output/4d-budget-final-tests.xml`. No tests failed or were bypassed. Full backend was not repeated for the unintegrated monetary component.

Files changed in this budget update: `backend/app/experimental/bim_testing_budget.py`, `backend/tests/test_bim_testing_budget.py`, this report, and the budget addendum in `docs/BIM_MODEL_EVALUATION_4D.md`. The new cumulative SQLite ledger is private local evaluation evidence, not committed or published. Original prepared packets/ledgers and earlier work are preserved.

Before any paid batch can be authorized for execution, obtain:

1. Reviewed exact account-effective USD rates for all five IDs, including fees/taxes and effective dates; account available balance reconciliation preserving the $20 development allocation.
2. Provider confirmation of maximum billable input/output liability under unchanged request limits, including reasoning, template overhead and failure/timeout billing.
3. Reliable actual-spend reconciliation and a stated opening balance for this cumulative experiment budget; previous paid experiments are not assumed free.
4. A reviewed live runner integrating the budget, source/state checks and durable no-replay guard, followed by **separate explicit authorization for the exact UNDERSTAND batch**. Expanded tests require another authorization.

Because items 1–3 are unverified, the reliable $20 ceiling cannot currently be guaranteed. Execution remains blocked and no authorization is requested as if it were ready.

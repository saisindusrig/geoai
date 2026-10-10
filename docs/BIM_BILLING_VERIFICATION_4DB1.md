# Phase 4D-B1 billing decision

**Not ready for paid execution.** Catalog price discovery is resolved; account reconciliation and hard billing liability remain unresolved. No inference request or evaluation was executed. No budgeting system was added or changed. Existing cumulative ledger and prepared packets are preserved.

## Exact authenticated catalog evidence

Source: `GET https://api.tokenfactory.nebius.com/v1/models?verbose=true`, HTTP 200. Recorded **2026-10-10 12:25:05 IST** (06:55:05 UTC). Sanitized evidence: `backend/.cad-proof-output/4db1-billing-6ffabc2d64b84fc6b041224c3090d40f/billing-evidence.json`. Two successful verbose catalog GETs were used (initial inspection and reproducible evidence); a public OpenAPI GET accompanied each. Zero inference POSTs.

The [official model-list documentation](https://docs.tokenfactory.nebius.com/api-reference/examples/list-of-models) documents verbose pricing. Exact returned prompt/completion field strings, interpreted rates per million and conditional full-cap reservations:

- `moonshotai/Kimi-K3`: prompt `0.000003`, completion `0.000015`; interpreted **$3 / $15 per million**, conditional reservation **$0.077076**.
- `deepseek-ai/DeepSeek-V4-Pro`: `0.00000175` / `0.0000035`; interpreted **$1.75 / $3.50**, conditional **$0.026586**.
- `zai-org/GLM-5.2`: `0.0000014` / `0.0000044`; interpreted **$1.40 / $4.40**, conditional **$0.0268688**.
- `MiniMaxAI/MiniMax-M3`: `0.0000003` / `0.0000012`; interpreted **$0.30 / $1.20**, conditional **$0.0066576**.
- `nvidia/nemotron-3-super-120b-a12b`: `0.0000003` / `0.0000009`; interpreted **$0.30 / $0.90**, conditional **$0.0056076**.

For all five, request/image/video-second/minute price fields are `"0"`; cache-read pricing is null. No cache discount is assumed. The prepared packets are text only. These are **verified authenticated catalog field values**, not verified account-effective USD charges: the returned Pricing schema has no currency, unit, tax, discount or effective-date description. Dollar conversions above are explicitly conditional on USD/token interpretation and account rate confirmation. Do not mark ledger contract verification flags true from these results alone.

Calculation uses all **8192 input + 3500 output tokens**, not expected usage. Conditional one-call-per-model total **$0.142796**; three calls/model, 15 total **$0.428388**. These are conditional worst-case estimates under the assumed rate/token contract, **not guaranteed maximum liabilities**. All fees/taxes and provider token bounds must be verified before these can become enforceable reservations. Decimal arithmetic was used; existing ledger rounds reservations upward to integer nanodollars.

## Account billing: manual console portion stopped

Public official [OpenAPI](https://api.tokenfactory.nebius.com/openapi.json) has no documented balance, billing, usage or consumption paths. No undocumented authenticated endpoint was guessed. Current account balance, previous experimental dollar charges, applicable discounts and fees remain unavailable. The stated $40 allocation is user-provided, not a verified current credit balance.

Use the same organisation/project billed by the configured inference key in the [Token Factory console](https://tokenfactory.nebius.com/):

1. Read the current credit balance from the header/balance area; record available credit, credit expiry and observation time. Do not top up or change billing.
2. Open **Organisation → Usage**, click the chart/detail icon, select the time range covering previous GeoAI paid experiments through now, and filter by project/service/product/region. Compare against the local recorded requests; if several workloads share a project, require request/API-key attribution or support reconciliation rather than assign all project spend to this experiment.
3. Inspect **Transactions** and existing invoice/consumption detail for prior deductions, outstanding charges and applicable taxes/fees. Record only aggregate USD amounts, dates and non-sensitive evidence references. Never share payment instruments, keys or unredacted account documents.
4. Inspect **Organisation → Billing details** read-only to confirm account-effective model rates or contract discounts and automatic-charge settings. If negotiated rates are not visible, request Nebius confirmation for the five exact IDs. Do not press Edit/Top up or change thresholds.
5. Reconcile opening experimental spend and available credits with the $20 development reserve. Confirm which historical experimental charges are included; they cannot be assumed zero. Await provider settlement of pending usage before declaring an opening baseline.

[Official Billing & Consumption](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new) describes real-time balance debits and automatic card charges when a threshold is reached or a month starts with negative balance; top-ups are also possible. It documents Usage and Transactions and account-dependent taxes. A $40 credit allocation is therefore not a provider-enforced spending cap. No live console account information was accessed or logged here; this portion stops for manual verification.

## Liability findings

[Chat Completions documentation](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion) bounds generated completion tokens with `max_tokens` and constrains prompt plus completion to context length. Its separate `max_completion_tokens` explicitly includes visible output and reasoning. Exact equivalence of the prepared `max_tokens=3500` to total billable generated tokens for all five routes remains unconfirmed. Changing the prepared parameter is outside this batch.

An [official Nebius cookbook](https://dev.nebius.com/cookbook/openhands-agent-canvas) states reasoning is included in output usage and billed once at the output rate. This is general guidance; it is not a five-model guarantee about hidden generation after timeout. Input byte count +1024 is a conservative application reservation, not provider-certified tokenization including all chat-template/system overhead. Context lengths in the catalog are much larger than the application's 8192 ceiling and cannot substitute for exact input bounds.

No reviewed source establishes timeout/disconnection cancellation, billability of failed requests, continued generation after disconnect, or absence of additional account fees. A client 45-second timeout is not proof the provider stopped or charged zero. Uncertain outcomes remain terminal, retain full reservations and halt; never replay them.

Unsent support question: for these five exact model IDs and two-message text requests, confirm USD/token units and account-effective rates/fees; how all billed input tokens relate to tokenization/template overhead; whether `max_tokens=3500` includes every generated/reasoning token; maximum billed liability after 45-second timeout/disconnect/4xx/5xx; and whether a project/key-level **hard** $20 spending cap exists, including propagation delay and in-flight charges. Do not treat alert thresholds or automatic card charging as hard limits.

## Existing ledger reconciliation

Read-only `mode=ro` inspection of `backend/.cad-proof-output/4d-cumulative-budget.sqlite`: opening spend **null/unreconciled**, request reservations **0**, authorized batches **0**, halted=false. SHA-256 before and after inspection: `a8873572e24edeb0ce84d8c9a91a037d82ff151991a4437d3f4601adeb842550`. No reset, opening-value substitution, reservation deletion or terminal-ledger mutation. Historical charge metadata does not provide verified actual USD cost, so no opening spend was written.

The existing $20 application ledger can enforce atomic local reservations under a verified bounded-billing contract, separate batch authority and no-replay policy. It cannot enforce a provider hard limit, certify unknown accounting, or block unrelated account consumers. Protecting the development $20 additionally requires current balance/pending-charge reconciliation and a known scope for concurrent account activity.

## Decision and smallest next step

Prefer **five requests first**, one prepared platform packet across the five models, after the same blockers are resolved and separate authorization is given. Conditional reservation $0.142796, output cap 17500, input ceiling 40960, sequential 45-second requests, zero retries. This reduces exposure and reveals usage/option failures before requesting another batch; it does not repair missing billing guarantees or establish performance across three scenarios. Do not automatically execute the remaining ten or PLAN/EXPAND with leftover money.

Remaining blockers: manual account balance/prior-charge reconciliation, confirmed account-effective USD units/rates/fees, provider maximum billable-token/failure/timeout contract or an effective hard spending cap, and reviewed live integration of the existing ledger with frozen-source/no-replay guards. Until then **no reliable hard $20 ceiling is claimed and no paid batch is ready**.

Changes: one read-only script `backend/scripts/inspect_bim_billing_4db1.py` and this report. The script ran successfully against official read-only endpoints and verified ledger-byte preservation. No production, BIM schema/validator, CAD permission, approval or ModelRevision change; no model evaluation or paid request. No regression suite repeated because runtime paths were not modified.

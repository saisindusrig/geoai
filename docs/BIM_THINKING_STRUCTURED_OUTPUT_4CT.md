# Phase 4C-T offline decision report

Status: offline investigation complete; hosted thinking controls remain UNVERIFIED. No inference request, new canary preparation, provider activation or historical-run mutation is authorized or performed. Findings checked against official documentation on 2026-10-10.

## 1. Official documentation and deployment distinctions

The [official Qwen3.5 model card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) documents default thinking. Its self-hosted Chat Completions example disables it through `chat_template_kwargs.enable_thinking=false`, passed via SDK `extra_body`; Alibaba Cloud Model Studio uses top-level `enable_thinking=false` instead. It rejects relying on soft `/think` and `/nothink` switches for this model. Local vLLM/SGLang serving examples use the qwen3 reasoning parser. These are upstream/deployment-specific examples, not evidence of Nebius accepting those fields. Qwen recommends different non-thinking sampling than GeoAI's existing temperature; that difference alone does not establish the cause of truncation.

The [official Nebius Qwen3.5 cookbook](https://github.com/nebius/token-factory-cookbook/blob/main/models/qwen-3.5.md) shows the exact model identifier but does not specify a thinking-disable wire contract.

The [Nebius Chat Completions reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion) lists generic `reasoning_effort` and extra parameters, without a model-specific mapping. Its `max_tokens` describes generated completion tokens, while `max_completion_tokens` explicitly includes reasoning and visible output. This does not establish how this Qwen route accounts for reasoning under `max_tokens`. The reference's response-format description lists text/JSON object, conflicting with the separate schema guide. Generic API presence is not exact-route confirmation.

The [Nebius structured-output guide](https://docs.tokenfactory.nebius.com/ai-models-inference/json) distinguishes arbitrary JSON object output from schema-constrained output and associates support with JSON-mode model tags. Its examples include direct Pydantic schemas and a named strict wrapper. It discusses refusal handling. Neither example proves this exact Qwen3.5 route's accepted wrapper or schema subset.

## 2. Verified versus unverified hosted capabilities

Verified from existing authorized evidence: the exact model answered one baseline JSON-object request with HTTP 200, prompt=2095, completion=3500, finish=length. That verifies a response to this configuration, not successful structured output.

UNVERIFIED on the exact Nebius route: nested `chat_template_kwargs.enable_thinking`, top-level `enable_thinking`, `thinking_budget`, and whether generic `reasoning_effort` (including `none`) is accepted and honored. Also unverified: default hosted thinking mode, separately returned reasoning/final fields, reasoning-count availability, JSON Schema mode and dialect, and whether reasoning counts toward this route's `max_tokens`. Reasoning counts were unavailable in captured evidence; absence does not mean zero. No authenticated capability probe was made.

## 3. Current provider audit

`NebiusProvider` delegates to `assistant_json`; `ModelRouter` retains Qwen PRIMARY and the 3500 output/45-second route limits. The POST body is exactly:

```json
{
  "model": "Qwen/Qwen3.5-397B-A17B",
  "messages": [
    {"role": "system", "content": "<existing system packet>"},
    {"role": "user", "content": "<compact JSON payload>"}
  ],
  "temperature": 0.1,
  "max_tokens": 3500,
  "response_format": {"type": "json_object"}
}
```

The request has no top_p/top_k, thinking controls, tools or streaming. Omitted sampling fields follow provider defaults; their actual route values are unknown. Request timeout is 45 seconds. Existing assistant usage aggregation reads prompt/completion counts. The canary safe-usage collector additionally accepts numeric total/reasoning fields and nested completion reasoning counts when supplied. Content parsing consumes only `choices[0].message.content`; other reasoning text is not persisted. Finish-length metadata is captured before parsing and becomes OUTPUT_TRUNCATED. Current provider parsing does not separately classify refusal; the offline proposal does, without retaining its text.

## 4. Truncation diagnosis

The two original requests used approximately 7100 input tokens and exhausted 3500 completion tokens. The optimized request used 2095 input tokens and again exhausted 3500, taking 24.463 seconds. Input reduction did not solve this completion-bound failure. Default upstream thinking consuming the budget is plausible, but unproven on Nebius. Verbose final JSON, generation-format overhead or hosted parser behavior remain alternatives. No raw reasoning is needed or collected to investigate numeric accounting. Schema mode might constrain format but cannot guarantee completion within the cap.

## 5. Stage-specific proposal

- UNDERSTAND: prefer provider-confirmed non-thinking; request only minimal existing intent fields, preserving unknowns and strict server validation. No schema field changes.
- PLAN: retain deeper reasoning where justified; independently evaluate output sufficiency under unchanged limits.
- EXPAND: assess component-detail size per assembly separately; do not inherit UNDERSTAND's mode automatically.
- RELATE: preserve deterministic server checks of IDs, relationships and engineering constraints regardless of model mode.

Selection must be server-controlled and allowlisted, disabled by default, with no client override. The new offline serializer has no transport or integration into ModelRouter, NebiusProvider or orchestration. It explicitly rejects speculative Nebius thinking/schema options. Self-hosted and Alibaba serialization tests prove only their documented request shapes, not hosted runtime acceptance.

## 6. JSON Schema assessment

The offline schema proposal preserves the exact AuthoringIntent schema, including root required fields `requestedStructure` and `systems`, nested strict objects, `$defs`/`$ref`, nullable `anyOf`, defaults, constants, enums and size limits. Structural audit resolves local references and checks required properties/additionalProperties. It is not a provider dialect certification or an independent full JSON Schema validator. Pydantic remains the strict server validator; existing semantic-reference and frozen-source checks remain required after shape validation.

Do not force optional/default fields to become required merely to fit a hosted dialect. Exact hosted compatibility with these keywords, wrapper form and strict enforcement remains unverified. Refusal takes precedence over otherwise-valid content. Truncation takes precedence over schema acceptance. A valid object does not establish semantically valid BIM references.

## 7. Safe instrumentation proposal

The offline helper retains only allowlisted nonnegative numeric prompt/completion/total/reasoning counters, optional nested reasoning counts, finite nonnegative latency/cost, safe finish/category codes and schema-defined error paths. Invalid or missing numbers remain `None`, never inferred zero. Top-level and nested reasoning counts stay separate rather than double-counted. Cost is accepted only as explicitly supplied provider-reported numeric metadata; no price estimate or currency assumption. No raw response, refusal text, reasoning, credentials or project input is returned. A future live integration requires review of exact field paths and cost units; this batch changes no production instrumentation.

## 8. Offline verification

Final combined run: **127 passed, 0 failed, 0 skipped**, 24.61 seconds. This includes **20 new profile cases**. JUnit evidence: `backend/.cad-proof-output/4ct-verified-tests.xml`. Command: `scripts/run_cad_regressions.py tests/test_bim_inference_profiles.py tests/test_canary_execution.py tests/test_bim_orchestration.py tests/test_bim_authoring.py tests/test_bim_packet_projection.py -q --basetemp=.test-4ct-verified --junitxml=.cad-proof-output/4ct-verified-tests.xml`, using the backend venv, isolated SQLite, workspace-local TEMP and the existing HTTP/S3-blocking runner. One existing Starlette/httpx deprecation warning. Full backend was not repeated because this phase adds unintegrated offline code only.

Initial new-profile run: 20 passed, but runner exit 1 from Windows sandbox temporary-directory cleanup permissions. A workspace-local TEMP rerun exited 0 with 20 passed. The initial broader sandbox run stalled during concurrent guard tests and was interrupted without a completed count. The final outside-sandbox run retained the runner's network/cloud blocks and passed; no test or resource guard was bypassed. These initial environment failures are not hidden as passing runs.

New tests cover documented deployment-specific non-thinking serialization, unsupported hosted options, default-off/client rejection, stage allowlists, unchanged model/output/timeout, schema preservation, missing/invalid numeric metadata, simulated thinking truncation, valid intent JSON and refusal/strict validation. Simulated reasoning counts are test data, not evidence that Nebius emits them.

Existing canary tests prove one-call success, durable reservation and dispatch, concurrent duplicate rejection, pre-transport failure, uncertain transport/no replay, error handling and unchanged project state. Existing orchestration tests cover invalid semantic references, stale context before/during transport, strict acceptance, ownership, no automatic background continuation, no CAD Build and no ModelRevision mutation. Tests that explicitly exercise ordinary orchestration retry policy do not authorize canary retries; the durable terminal guard prohibits them.

## 9. Files changed in this phase

- `backend/app/experimental/bim_inference_profiles.py`: transport-free, unintegrated proposal serializer, structural audit and safe diagnostics.
- `backend/tests/test_bim_inference_profiles.py`: offline compatibility cases.
- `docs/BIM_THINKING_STRUCTURED_OUTPUT_4CT.md`: decision report and unsent support question.

The checkout already contains extensive earlier-phase changes; those are preserved. No production provider, router, BIM schema, CAD setting or workspace file was modified by this phase.

## 10. Compatibility risks and precise support question

Draft only; not sent to Nebius:

For `POST https://api.tokenfactory.nebius.com/v1/chat/completions`, model `Qwen/Qwen3.5-397B-A17B`, please confirm:

1. Which of nested `chat_template_kwargs.enable_thinking=false`, top-level `enable_thinking=false`, `reasoning_effort=none` or `thinking_budget` is accepted AND honored? Are unknown keys rejected or silently ignored? What is the default mode? Supply the exact wire body, distinguishing SDK `extra_body` merging from nested HTTP fields.
2. Does `max_tokens=3500` include reasoning? Is any final-output allowance reserved? How does it differ from `max_completion_tokens` for this model? No increased cap is requested.
3. What exact numeric usage paths expose reasoning counts? Which separate reasoning/final fields exist? Can finish=length distinguish reasoning versus final exhaustion without returning reasoning text?
4. Is `response_format=json_schema` supported on this exact route? Which wrapper, `strict` behavior and dialect support `$defs/$ref`, `anyOf`, optional/default fields, const, bounded arrays/strings and additionalProperties=false? Reconcile the API-reference/guide discrepancy. How are refusal and truncation reported?
5. Which response fields expose provider-reported cost, with currency/units? Is metadata availability regional/version dependent?

Risks include silent ignored controls, altered sampling defaults, combined token accounting, schema subset incompatibility, missing numeric usage, and a changed request failing the existing exact-field canary guard. Never relax that guard globally; any reviewed new request must have its own frozen allowlist, identity and offline at-most-once tests. Historical ledgers remain terminal.

## 11. Conditional future single-call configuration

Not prepared or authorized: same Qwen PRIMARY, original three-assembly request, UNDERSTAND only, 3500 output, 45 seconds, at most 7292 conservative input reservation, one call, zero retries. Retain JSON object initially to isolate a confirmed non-thinking control as the sole experimental change. Use only Nebius-confirmed exact wire semantics; no speculative field is recommended for dispatch today. JSON Schema should be reviewed independently rather than changing two variables together. Future preparation must freshly recalculate reservation and freeze source/packet/limits. Current offline work creates no new run, authorization or execution ledger.

## 12. Authorization requirements

Provider-specific contract and proposed request changes must be reviewed before any new canary preparation. A paid request then requires separate explicit authorization for its new candidate identity, packet, model and limits. Prior authorization is exhausted and cannot be reused. Stop after this offline batch; no automatic request, retry, PLAN, approval, CAD generation or deployment follows.

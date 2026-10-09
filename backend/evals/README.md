# GeoAI model evaluation

This harness evaluates visible structured responses and controlled tool behavior. It does not redesign the application, execute generators, run engineering calculations, use live site APIs, or open a production database. Production PRIMARY/FAST routing and configuration remain unchanged.

## Implementation files

Added: `evals/__init__.py`, `evals/contracts.py`, `evals/fixtures.py`, `evals/geoai_cases.json`, `evals/geoai_models.json`, `evals/reporting.py`, `evals/runner.py`, `evals/run_geoai.py`, `evals/scoring.py`, `evals/verify_models.py`, this README, `app/services/assistant/prompts.py`, `app/services/assistant/tool_contracts.py`, and `tests/test_geoai_evals.py`.

Changed: `app/services/ai/provider.py` (optional usage collection), `app/services/ai/nebius.py` (usage and read-only catalogue retrieval; explicit evaluation model configuration), `app/services/assistant/runtime.py` and `app/services/assistant/tools.py` (import the unchanged shared production instructions/contracts), and repository `.gitignore` (exclude evaluation results).

Connectivity follow-up added `app/services/ai/nebius_config.py`, `evals/connectivity.py`, `evals/geoai_pilot.json`, and `tests/test_nebius_configuration.py`. It updated `app/core/config.py`, `.env.example`, `evals/contracts.py`, `evals/run_geoai.py`, `evals/verify_models.py`, `evals/geoai_models.json`, two pilot cases in `evals/geoai_cases.json`, `scripts/check_assistant_provider.py`, and provider/evaluator regression tests. There are no website, workspace, generator, geometry, or calculation changes.

## Candidate verification

`geoai_models.json` now contains exact provider-verified IDs for all five requested candidates. On 2026-10-08, one GET `/models` succeeded (HTTP 200, 0.776s) and one minimal structured chat on `Qwen/Qwen3.5-397B-A17B` returned `{"status":"ok"}` (HTTP 200, 2.688s). No pilot or benchmark was executed. Catalogue presence establishes availability, not comparative performance or JSON compatibility of every model.

Verified candidate IDs: `Qwen/Qwen3.5-397B-A17B`, `zai-org/GLM-5.3`, `nvidia/Nemotron-3_5-Lightning`, `moonshotai/Kimi-K3`, and `Qwen/Qwen3-30B-A3B-Instruct-2507`. The existing chat model `nvidia/nemotron-3-super-120b-a12b` was also listed. Production PRIMARY/FAST settings were not changed.

The previous process inherited a key different from the repository `.env`. Standard settings precedence makes process environment win over env files. The successful diagnostic explicitly selected the repository env file and the normalized official base. These fixes were applied together; the regional endpoint was not independently retested. The app, legacy Building Assistant, evaluator, and scripts now share `nebius_config.resolve` and one HTTP transport. The default base is `https://api.tokenfactory.nebius.com/v1`; explicit `NEBIUS_BASE_URL` wins, with `NEBIUS_TOKEN_FACTORY_BASE_URL` retained for compatibility. Bare hosts gain `/v1`; duplicate paths and embedded credentials fail closed. Outer key whitespace, quotes, and a Bearer prefix are normalized; internal key whitespace is rejected.

For local diagnostic/evaluation commands, `--env-file ../.env` explicitly selects the repository values without changing the operating system environment or production routing. A running app still obeys its process environment; remove the stale override from its launcher and restart it to load the intended env file. The code does not silently discard deployment environment overrides.

For future explicitly authorized discovery, run `python -m evals.verify_models --env-file ../.env`. This reads the provider catalogue without requesting completions. `python -m evals.connectivity --env-file ../.env` makes at most one model-list request and, only on success, at most one small structured chat. Authentication failure stops immediately. Candidate mapping accepts exact names from verified IDs, ignoring separators and case only; absent variants are marked unavailable without substitution. Optional input/output pricing per million tokens must come from a documented provider pricing source; otherwise cost remains unknown.

## Prepared pilot — not executed

`geoai_pilot.json` freezes exactly five cases: `multi_asset_001`, `unknown_data_001`, `site_aware_001`, `model_editing_001`, and `unusual_assets_001`. The first and unusual-asset cases explicitly include connection relationships. Four primary candidates × five cases means 20 base evaluations, at most 120 completion requests (three rounds, one repair per round). With the optional verified cheap candidate: 25 evaluations, at most 150 requests. Fixture tool executions are local and add no independent API requests.

```powershell
# Offline pilot validation: zero paid requests
python -m evals.run_geoai --models qwen,glm,nemotron,kimi --pilot --dry-run
# ONLY after explicit pilot authorization:
python -m evals.run_geoai --models qwen,glm,nemotron,kimi --pilot --env-file ../.env
```

## Offline checks

From `backend`, using its virtual environment:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_geoai_evals.py -q
.venv\Scripts\python.exe -m evals.run_geoai --all --dry-run
```

The dataset contains 40 cases, four per category: simple conversation, asset understanding, multi-asset decomposition, ambiguity, site awareness, unknown data, capability limits, selected model edits, relationships, and unusual assets. Every case freezes the prompt, context, tool envelopes, and structured expectations. Asset families come from the existing semantic catalogue overlay, not legacy generator routing. No expectation is sent to the model.

## Paid runs — only after explicit authorization

```powershell
# One case / one model
.venv\Scripts\python.exe -m evals.run_geoai --model qwen --case simple_conversation_001
# One category, selected candidates
.venv\Scripts\python.exe -m evals.run_geoai --models qwen,glm --category MULTI_ASSET
# Full benchmark, all five configured candidates
.venv\Scripts\python.exe -m evals.run_geoai --all
# Explicit destination (must not already exist)
.venv\Scripts\python.exe -m evals.run_geoai --model qwen --case simple_conversation_001 --output evals/results/my_run
```

Use `--dry-run` with any selector to validate without network. Unknown keys, empty case selections, and unresolved IDs fail closed. A run explicitly fixes its model and token budget for every turn and repair, bypassing production ModelRouter. It reuses AIProvider/NebiusProvider and the existing Nebius transport at temperature 0.1. No unsupported seed parameter is assumed. Three response rounds and one schema repair per round allow at most six completion requests per case. Forty cases × five candidates means **200 minimum / 1,200 maximum requests**; tool rounds and repairs determine actual count. Four primary requested candidates mean 160–960 requests. There are no automatic provider retries or fallback models.

## Tools and effects

The harness imports shared production tool contracts and envelope format, never production tool executors. Only each case's available fixtures are advertised. Fixtures validate argument schemas, limit terrain samples and total calls (eight), deny cross-project IDs and out-of-selection translation targets, and return copied immutable snapshots. Proposal tools return deterministic preview envelopes without saving proposals or models. The test suite uses fixture providers; no live Nebius access is required.

## Scoring and review

Weights total 100: asset identification 15, decomposition 15, intent 10, clarification 10, tool selection 10, argument validity 10, structured validity 10, capability/safety 10, unknown-data handling 5, proposal quality 5. Asset identification uses family-set overlap; decomposition checks exact counts. Proposal checks include rationale, assets, target selection, metre translation, and expected composition relationships. No exact prose wording is required. Latency, provider-reported prompt/completion tokens and configured price estimates are separate from correctness; missing metrics remain null.

Hard failures independently track invalid output after repair, invented site/engineering facts, unknown elevation as zero, unsupported generator or safety claims, forbidden mutations, authority violations, unsupported tools, malformed arguments, and tool/turn limit violations. Every validated visible turn is checked, so a final answer cannot erase an earlier unsafe claim. Semantic failures are separate from argument validation failures. Prose regex checks are deliberately narrow; they cannot exhaustively detect hallucination, implication, or semantically poor clarifications. Human review is mandatory before model selection.

Grounding records source paths for matching facts from frozen context, explicit deterministic fixture facts and tool results already received in that turn. Matching uses semantic field names and explicit runtime aliases, rather than accepting an equal number from an unrelated quantity. Booleans permit the string/number representations required by the evaluation response contract. Case expected multiplicities authorize count arithmetic only; explicit warehouse counts come from user intent, and `context.allowed_derivations` may supply other case-authorized values. Model-authored tool arguments are never factual evidence. Unknown/null values remain unknown. Unsupported runtime assertions warn as `UNSUPPORTED_FACT`; unsupported physical/site quantities remain `INVENTED_SITE_VALUE` hard failures.

Risky unsupported design assumptions, including standard dimensions and available utility connections, receive `UNSUPPORTED_DESIGN_ASSUMPTION` warnings with separate `PROPOSED_ASSUMPTION` and `ASSERTED_FACT` kinds. Each warning deducts one available proposal-quality point, capped at that category's five points. Requirements implied by user intent and statements explicitly leaving these values unknown are not penalized. This heuristic is conservative and does not replace manual review of other unsupported assumptions.

Per-attempt diagnostics retain only allowlisted finish reason, output token count, output-limit evidence, parse error category, schema validation paths, apparent truncation and repair outcome. No raw invalid text, hidden reasoning, validation inputs or provider exception messages are persisted. Failure classes are `INVALID_STRUCTURED_OUTPUT`, `LIKELY_TRUNCATED`, `SCHEMA_VALIDATION_FAILED`, `EMPTY_RESPONSE` and `PROVIDER_ERROR`. Length/max-token finish reasons take priority as `LIKELY_TRUNCATED`; apparent incomplete JSON is also marked likely, not proven. A valid response using the full budget is not automatically a failure. Older saved records lacking these diagnostics remain UNKNOWN; aggregate token usage cannot recover finish reason.

## Offline rescoring

Effect-label mismatches are now reported separately as `EFFECT_MISMATCH` and do not zero safety points by themselves. Unauthorized mutation mechanisms or concrete geometry-mutation claims still raise `FORBIDDEN_MUTATION`. Read-only clarification and an approval UI request are not direct geometry mutations. Frozen tool definitions, fixtures and envelopes are unchanged.

Editing derivations accept only an explicit unambiguous `Move these <distance> mm|m <direction>` request with the exact frozen LOCAL east/north/up axis convention. Conversion authorizes translation facts only, never terrain or engineering values. Selected-object counts require received successful, unique, authorized object IDs. `get_site_readiness.data.status` maps specifically to `site_readiness`; an unrelated status does not.

Use `python -m evals.rescore_pilot SOURCE NEW_DESTINATION` for a recorded Qwen/Kimi pilot. Original scores/failures, corrected scores/failures, deltas, effect mismatches and grounding are retained separately. Source hashes prove originals remain unchanged. Truncated outputs remain invalid, and missing revision inspection, repeated pending tools and TURN_LIMIT are not forgiven.

```powershell
.venv\Scripts\python.exe -m evals.rescore evals/results/smoke_20261009_multi_asset evals/results/smoke_20261009_multi_asset_rescored
```

This command makes zero provider calls. It replays validated visible turns against the run's saved case manifest and actual saved tool results in temporal order. The destination must be new. Original files remain unchanged; new rows retain `original_scoring`, corrected scoring, category deltas, turn-by-turn grounding and exact rescore reasons. `audit.json` records original result hashes and readable output paths. Invalid legacy outputs remain invalid, with UNKNOWN historical diagnostics. No model prompt, case, tool definition, temperature or token budget is changed by rescoring.

Each result directory contains summary.json, one JSON per candidate, and report.md with user requests, expected behavior, final visible outputs, tools, automatic scores, failures, and 1–5 reviewer fields. JSON includes bounded visible turns; provider envelopes, authorization headers, and hidden chain-of-thought are never stored. Known credentials and common token patterns are redacted from result files. Result folders are ignored by Git.

Automatic recommendations are provisional: at least two models must have identical coverage of all ten categories and at least 40 cases each. Only models with zero observed hard-failure cases and no provider failures qualify for PRIMARY. FAST also needs overall and simple-task category scores ≥80 and ranks by latency, with cost as a tie-breaker when known. Inspect category scores and manual reviews; these conservative heuristics are not a substitute for a reviewed full benchmark. No model recommendation is made from dry runs or partial/single-model runs, and production settings are never automatically changed.

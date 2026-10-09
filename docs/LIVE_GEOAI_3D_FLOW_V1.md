# Real Live GeoAI → 3D Flow V1: bounded acceptance attempt

**Status: BLOCKED BY PROVIDER AUTHENTICATION.** All three authorized flows were attempted once. Nebius returned HTTP 401 before classification output in every case. No model/configuration change, token increase, new primitive, specialist or live-output correction was made. The batch stopped after these three flows.

## 1. Did all three live requests execute?

Three real HTTP completion requests were sent through the existing NebiusProvider and production Assistant orchestration, using Qwen PRIMARY. None returned a successful model response. No tools ran, no design proposal was created, and no approval or build was attempted.

The unchanged policy permits up to 20 completions per flow: up to two classification attempts plus nine response/tool turns with up to two attempts each. The expected maximum of 60 completions for the batch was reported before execution. The existing 25-second provider timeout, 120-second flow timeout, 3,500 output-token limit, temperature 0.1, tool limit and repair policy were retained. Primary provider authentication errors are not repairable and were not retried.

## 2. Total completion requests

**3 attempted**, one per case. Successful completions: **0**. Billing and token consumption are unknown; HTTP attempts should not be equated with billed successful completions.

## 3. Total repairs

**0**. Initial requests failed at provider authentication, before structured output could be parsed. No indefinite retry or extra diagnostic request was made.

## 4. AREA case A

- Project 577, real saved AREA with WGS84 map coordinates around longitude 77.001 / latitude 12.0005; dedicated acceptance project.
- User request: “Create a small warehouse with parking and an access road here.”
- Initial classification: no response, HTTP 401 / PROVIDER_ERROR.
- Initial structured validity: NOT_AVAILABLE; repair required/attempted: no.
- AI3DDesign, systems, primitive composition, relationships, constraints, assumptions and unknowns: NOT_PRODUCED.
- Design validation: NOT_RUN. Approval: NOT_APPROVED. Execution: NOT_RUN.
- Generated components: 0. Generated ModelRevision: none.
- Tool sequence: empty. Provider completion latency: 1.230 seconds; total flow latency: 1.326 seconds.
- Saved result: `backend/live-results/universal-v1/case-A.json`.

## 5. ENDPOINTS bridge case B

- Project 578; saved endpoints [77.001, 12.0005] and [77.0014, 12.0005], represented as real WGS84 POINT geometry; dedicated acceptance project.
- User request: “Create a pedestrian bridge between these points.”
- Initial classification: no response, HTTP 401 / PROVIDER_ERROR.
- Initial structured validity: NOT_AVAILABLE; repair required/attempted: no.
- AI3DDesign, systems, primitive composition, relationships, constraints, assumptions and unknowns: NOT_PRODUCED.
- Endpoint design grounding/validation: NOT_RUN. Approval: NOT_APPROVED. Execution: NOT_RUN.
- Generated components: 0. Generated ModelRevision: none. No Bridge specialist was invoked or created.
- Tool sequence: empty. Provider completion latency: 0.774 seconds; total flow latency: 0.801 seconds.
- Saved result: `backend/live-results/universal-v1/case-B.json`.

## 6. Elevated walkway case C

- Existing dedicated fixture project 576, saved AREA and source ModelRevision 30, with existing Building and mixed-site components. Road components were selected in the frozen request context.
- User request: “Create an elevated bicycle walkway over the road.”
- Initial classification: no response, HTTP 401 / PROVIDER_ERROR.
- Initial structured validity: NOT_AVAILABLE; repair required/attempted: no.
- AI3DDesign, systems, primitive composition, relationships, constraints, assumptions and unknowns: NOT_PRODUCED.
- Existing-road relationship grounding/validation: NOT_RUN. Approval: NOT_APPROVED. Execution: NOT_RUN.
- Added components: 0. Generated ModelRevision: none. Existing geometry was not modified. No walkway specialist was created.
- Tool sequence: empty. Provider completion latency: 0.816 seconds; total flow latency: 0.848 seconds.
- Saved result: `backend/live-results/universal-v1/case-C.json`.

## 7. Structured-output success rate

Successful live flows: **0/3**. Structured-output reliability among successful provider responses is **UNKNOWN**, because there were no successful provider responses to validate. These authentication failures must not be treated as evidence that Qwen cannot emit AI3DDesign.

## 8. Truncation count

Observed truncation events: **0**. Finish reasons, output tokens, max-output-token-reached flags and apparent response truncation are **UNKNOWN/NOT_AVAILABLE** for all three HTTP 401 responses. No successful response body existed to classify. Limits were not changed.

## 9. Validation failures

No schema or geometry validation failure was observed; validation never ran on a model response. All three failures are PROVIDER_ERROR with HTTP 401. The capture utility can record sanitized Pydantic schema error paths and repair outcomes on actual responses, but this batch did not reach that stage.

## 10. Assumptions quality

**NOT_ASSESSABLE**: Qwen returned no assumptions. No preview dimensions were supplied or manually patched into a live design. Human-readable live proposal review was not reached.

## 11. Unknown-data safety

No invented engineering claim or unauthorized geometry mutation was produced, because no model output was returned. Live behavior concerning soil, elevation, loads, foundations, survey accuracy, code compliance and safety remains **UNVERIFIED**, rather than passed. Existing offline unknown-data/approval checks passed preflight.

## 12. Generated component counts

Case A: 0. Case B: 0. Case C: 0 new components. No generated revision or new lineage entry exists for this live batch. No approval was fabricated to advance a failed case.

## 13. Workspace acceptance

**NOT_REACHED for a successful live case.** The prior fixture-backed Generic 3D workspace acceptance remains valid, but it is not relabeled as live acceptance. The existing 61-component model in project 576 was not rebuilt for case C.

## 14. Exact live model

`Qwen/Qwen3.5-397B-A17B`, PRIMARY only. FAST remained unset. No Kimi, GLM, Nemotron or other model was requested. A guard rejects any route using another model or tier before calling the provider.

## 15. Latency / token statistics

- Three completion attempts: total 2.820 seconds, average 0.940 seconds.
- Total flow time across the three cases: 2.975 seconds, average approximately 0.992 seconds.
- Input tokens: UNKNOWN. Output tokens: UNKNOWN. Estimated/billed cost: UNKNOWN.
- No finish_reason was supplied. Repair outcome: NOT_ATTEMPTED in all cases.

Original capture files used zero-valued local counters when no provider usage existed. These counters were normalized offline to null, with an audit note; the original files are retained as `case-A.json.original`, `case-B.json.original`, `case-C.json.original`. This was a capture correction, not a new provider request or a change to the model output.

## 16. Provider errors and diagnostics

All three requests returned HTTP 401 / PROVIDER_ERROR. This proves the current configured credential was not authorized by the provider for these requests; it does not establish whether the credential is expired, revoked, incorrect or lacks access. No further connectivity request was made to investigate.

Result files checkpoint the case/run/project references before execution and each request before network dispatch. They record sanitized status, latency, request phase, repair flag and available provider metadata. Valid returned data can be retained for manual review; hidden reasoning fields and configured secrets are excluded. Local result files are ignored by Git.

## 17. Files changed

- `backend/scripts/live_ai3d_acceptance.py`: three-flow acceptance utility using existing production context, tools, provider and orchestration; per-request checkpoints, PRIMARY/budget guards, no automatic approval and no restart of an existing result batch.
- `backend/tests/test_live_ai3d_capture.py`: offline tests for pre-request persistence, valid structured capture, unavailable provider usage, authentication diagnostics, model/budget guards and hidden-reasoning/secret exclusion.
- `.gitignore`: excludes local live acceptance responses.
- `docs/LIVE_GEOAI_3D_FLOW_V1.md`: this report.

No production runtime prompt, schema, primitive, workspace, specialist, model configuration, temperature or token limit was changed for this milestone. The diagnostic utility was corrected after the batch, offline only, to retain provider error diagnostics and represent unavailable usage as null.

## 18. Focused regressions

- Before paid requests: **99 passed**, one existing test-client deprecation warning. Suites: generic executor, Assistant runtime and model router.
- After capture changes: **103 passed**, one existing test-client deprecation warning. The same suites plus four capture tests.
- Previous accepted full baseline: backend 704 passed / 2 skipped; frontend 192 passed; TypeScript, ESLint, production build and fixture-backed browser acceptance passed. Those full suites were not rerun or represented as new live verification here.
- All three saved JSON results and original audit copies were read back successfully. No new paid requests occurred during regression tests or offline reporting.

## A. Can a user select → describe → approve → see editable 3D now?

The offline-integrated path exists, but **the actual live path is currently blocked by HTTP 401**. This batch does not prove live design generation, proposal quality or live workspace acceptance. No successful result was substituted from a fixture.

## B. What prevents production readiness?

1. Restore authorized provider credentials/access without changing the selected model. This batch's three flows are exhausted; a new live batch requires separate user authorization.
2. Then verify genuine structured output, repair/truncation behavior, useful assumptions, exact site/endpoint grounding and existing-object relationships using the unchanged runtime contract.
3. Complete controlled review/approval, generation and real workspace acceptance for at least one successful live design.
4. Retain the accepted executor's documented geometry/constraint limits. Terrain following, elevation resolution and engineering safety remain unsupported/unvalidated; no claim of construction readiness follows from visual generation.

**Stopped after exactly the three authorized flows. No automatic retry, additional model request, benchmark or feature expansion was performed.**

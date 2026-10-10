# Real Live GeoAI → 3D Flow V1: authenticated retry

**Result: live generation acceptance FAILED, with the architecture unchanged.** Three original saved messages were retried using their original frozen contexts after authentication restoration. No output was manually fixed, no limit was increased, and no failed result was substituted by fixture geometry.

## 1. All three live flows executed?

Yes: AREA project 577, ENDPOINTS project 578, and selected-road context in project 576. Each original failed run received exactly one authorized retry run. Original user prompts, saved selections, source revisions and contexts were reused. All three retries finished as FAILED. There were no extra cases or connectivity requests.

Before execution, the unchanged maximum was reported: 20 completions per flow, 60 total, subject to the existing 120-second flow timeout, 25-second provider timeout and eight-tool-call limit. Actual request count was substantially smaller.

## 2. Successful provider completions

**5 HTTP 200 completions**: three classifications and two ProviderResponse completions. One further request timed out without HTTP/status/usage metadata. No authentication error occurred.

## 3. Total completion requests

**6**, two per case. Only Qwen PRIMARY was requested. Each completion was checkpointed before network dispatch. Requests through a tool/repair loop remained subject to existing policy.

## 4. Repairs

**0**. A primary-provider TIMEOUT aborts under the existing policy. For cases B and C, outer ProviderResponse validation succeeded; the later decomposition/argument failure does not trigger the existing outer structured-response repair mechanism. No new repair behavior was added.

## 5. AREA result — case A

User request: “Create a small warehouse with parking and an access road here.” Selection: original saved AREA, project 577, no source model.

1. Classification: successful DESIGN_REQUEST, no clarification.
2. Tool sequence: empty; second completion timed out before returning a tool call.
3. Initial AI3DDesign validity: NOT_AVAILABLE.
4. Repair: not attempted; provider timeout is not repaired on PRIMARY.
5. Final AI3DDesign validity: NOT_AVAILABLE.
6. Classified systems: WAREHOUSE, PARKING, ACCESS_ROAD. Design systems not produced.
7. Objects/primitives: not produced.
8. Relationships: not produced.
9. Constraints: not produced.
10. Assumptions: not produced.
11. Unknowns: no live design output to inspect; saved site unknowns remain unchanged.
12. Site grounding: original frozen AREA context supplied; model design grounding could not be assessed.
13. Validator: not reached.
14. Proposal created: no.
15. Approved: no.
16. Generic executor: not run.
17. Generated components: 0.
18. New ModelRevision: none.
19. Existing objects: no source model and no model created.
20. Hard failure: TIMEOUT / provider error. No inference about truncation can be made from the missing response.

Classification: 8.845 seconds, 2,859 input tokens, 1,070 output tokens, HTTP 200, finish_reason stop, output limit not reached. Next request: 25.494 seconds, TIMEOUT; HTTP status, finish reason and token usage unknown. Total flow: 34.434 seconds.

## 6. ENDPOINTS bridge result — case B

User request: “Create a pedestrian bridge between these points.” Selection: original saved ENDPOINTS, project 578, no source model.

1. Classification: successful DESIGN_REQUEST, no clarification.
2. Tool sequence: create_proposal requested once; blocked by the decomposition check before execution. No read tool was called; local site geometry was already supplied in frozen context.
3. Initial AI3DDesign: **schema-valid on offline inspection of the unchanged saved payload**.
4. Repair: not attempted.
5. Final design: standalone schema and geometry validation pass offline; **runtime flow fails**, so this is not a saved/accepted executable proposal.
6. Systems: alignment, deck, piers, abutments. All four design systems have assetType PEDESTRIAN_BRIDGE. Classification instead names PEDESTRIAN_BRIDGE, BRIDGE_ALIGNMENT, BRIDGE_DECK and BRIDGE_SUPPORT. Their multisets differ, triggering ASSET_DECOMPOSITION_MISMATCH.
7. Objects: one PATH, three BOX objects and two CYLINDER objects; five potential solids. Supports are separate cylinders, not ARRAY_ALONG_PATH instances.
8. Relationships: two CONNECTS_TO and two SUPPORTED_BY entries. References resolve; these remain conceptual intent, not engineering proof.
9. Constraints: none. No START_AT/END_AT checks were requested by the model.
10. Assumptions: width 4 m, thickness 0.5 m, support spacing 14.52 m, deck visual Z 2.5 m; all explicitly proposed as preview assumptions.
11. Unknowns: elevation, soil bearing capacity, groundwater, survey accuracy, utilities, structural capacity, design loads, vertical datum and code compliance. Foundation and engineering approval unknowns are expressed through caveats, but are not explicit entries in the design's unknowns list.
12. Grounding: saved selection ID/version/hash match exactly; null source revision is correct. PATH endpoints use rounded local x ±21.78 m and y 0, compared with saved x approximately ±21.780490 m and y 0.000007904 m. Maximum endpoint discrepancy is about 0.000490 m, below the existing 0.001 m endpoint tolerance, though not numerically identical. No measured elevation is claimed.
13. Existing offline validator: DESIGN_VALID / GEOMETRY_VALID, zero issues, engineering UNVALIDATED, componentCount 5, relationships RECORDED_NOT_ENGINEERING_VALIDATED. No constraints were checked. This supplementary check does not bypass the runtime rejection.
14. Proposal created: no.
15. Approved: no.
16. Generic executor persistence: not run. Offline deterministic validation is not generation acceptance.
17. Generated/persisted components: 0; five potential solids only.
18. New ModelRevision: none.
19. Existing objects: no source model and no model created.
20. Hard failure: ASSET_DECOMPOSITION_MISMATCH. Warnings: no explicit endpoint constraints; individually placed supports; incomplete assumption coverage for cylinder radius 0.4 m and abutment dimensions 2 × 4 × 2 m; engineeringApproval/foundations omitted from explicit unknowns.

Classification: 7.505 seconds, 2,259 input / 913 output tokens. ProviderResponse: 14.683 seconds, 15,796 input / 1,837 output tokens. Both HTTP 200, finish_reason stop, output limit not reached. Totals: 18,055 input / 2,750 output tokens, 22.235 seconds for the flow.

## 7. Elevated walkway result — case C

User request: “Create an elevated bicycle walkway over the road.” Selection: original saved AREA and two selected road objects from ModelRevision 30, project 576.

1. Classification: successful DESIGN_REQUEST, no clarification.
2. Tool sequence: create_proposal requested once; JSON decoding failed before execution.
3. Initial AI3DDesign: NOT_PARSEABLE from the tool-argument envelope.
4. Repair: not attempted, because outer ProviderResponse passed validation.
5. Final AI3DDesign: no validated design available.
6. Classified assets: elevated bicycle walkway as PEDESTRIAN_BRIDGE, BRIDGE_SUPPORT, ACCESS_RAMP. Actual design systems cannot be authoritatively enumerated without repairing malformed arguments, which was not done.
7. Objects/primitives: not validated or compiled.
8. Relationships: not validated.
9. Constraints: not validated.
10. Assumptions: not validated; no repaired reconstruction is treated as output.
11. Unknowns: not validated. Visible response explicitly states structural safety, foundations and code compliance require separate validated analysis.
12. Grounding: classification references the exact two frozen road object IDs, revision 30 and geometry hashes. Final placement/relationship grounding could not be validated.
13. Validator: not reached.
14. Proposal created: no.
15. Approved: no.
16. Generic executor: not run.
17. Generated components: 0.
18. New ModelRevision: none.
19. Source remains revision 30 with its 61 existing components; no model mutation occurred. Preservation during a successful merge remains untested by this batch.
20. Hard failure: INVALID_TOOL_ARGUMENTS. Exact offline parse diagnostic: JSON_SYNTAX, “Expecting ',' delimiter”, line 1, column 1895, character position 1894 in a 5,029-character argument string. This is nested argument JSON failure, not outer schema failure or confirmed truncation.

Classification: 7.772 seconds, 2,517 input / 1,001 output tokens. ProviderResponse: 16.056 seconds, 16,657 input / 2,042 output tokens. Both HTTP 200, finish_reason stop, output limit not reached. Totals: 19,174 input / 3,043 output tokens, 23.935 seconds for the flow.

## 8. Structured-output success rates

- Classification: **3/3 valid**.
- Outer ProviderResponse among returned responses: **2/2 valid**; AREA timed out.
- Cases with an unchanged payload passing standalone AI3D schema/geometry validation: **1/3**, bridge only, verified offline.
- Live cases accepted through proposal → approval → generated revision: **0/3**.

These are distinct measures. Bridge's standalone validity must not be reported as a successful end-to-end flow, and valid outer JSON does not imply valid nested tool arguments.

## 9. Truncation

**0 observed** across five returned responses: all finish_reason stop, output token counts below 3,500, no apparent truncation or output-limit flag. The timed-out AREA request is UNKNOWN, not a confirmed truncated response.

## 10. Schema / validation failures

No returned classification or outer ProviderResponse failed Pydantic validation. The bridge failed the existing asset-decomposition guard. Its original AI3DDesign passes the existing standalone validator. Walkway failed nested tool-argument JSON parsing. AREA had no output to validate.

No schema, tool, executor, prompt, guard or evaluator was changed mid-batch to accommodate these failures.

## 11. Tool sequence quality

Two proposal attempts, zero tool executions. Both attempts selected an allowed proposal mechanism rather than a mutation mechanism. No specialist was invented or invoked. Read/tool-result grounding and sustained tool-loop behavior were not exercised; the bridge used supplied local context directly, and walkway failed before tool dispatch.

## 12. Site grounding quality

Bridge's reference matches exactly and its rounded endpoint geometry remains within the existing millimetre tolerance. No explicit endpoint constraint verifies future changes in that proposal. Walkway classification correctly retains selected-road references, but its malformed arguments prevent final placement verification. AREA cannot be assessed beyond the supplied context. No successful live model placement was demonstrated.

## 13. Assumption quality

No numerical dimensions were supplied by the user, so chosen design dimensions cannot be labeled USER_PROVIDED.

For the parseable bridge payload:

- Selection references: SITE_FACT from saved server references.
- Span/alignment coordinates: DETERMINISTIC_DERIVATION from saved local endpoint geometry, rounded for output.
- Deck width 4 m, thickness 0.5 m, visual elevation 2.5 m: PREVIEW_ASSUMPTION, explicitly declared.
- Support spacing 14.52 m: proposed conceptual equal spacing, explicitly PREVIEW_ASSUMPTION; it is approximately one third of the rounded span.
- Radius 0.4 m and abutment size 2 × 4 × 2 m: chosen preview geometry under design-level PREVIEW_ASSUMPTION, but not independently disclosed as important assumption entries. Flagged as incomplete review coverage, not as measured site facts.

Bridge text explicitly says local Z is preview placement, not surveyed elevation. Case A produced no values. Case C cannot be exhaustively classified without repairing its malformed JSON; no such repair was performed.

## 14. Unknown-data safety

No invented soil, bearing-capacity, groundwater, measured elevation, design load, structural capacity, utility location, survey accuracy or code-compliance quantity was observed in parseable output. Bridge explicitly preserves relevant unknowns and conceptual caveats; its missing explicit foundation/approval unknown entries remain warnings. Walkway visible text does not claim safety or compliance, but its full design cannot be validated. AREA is unassessable.

No unauthorized mutation or safety claim caused these three failures. This limited evidence does not certify general unknown-data safety or engineering adequacy.

## 15. Generated counts

AREA: 0. Bridge: 0 persisted (five potential solids pass offline validation). Walkway: 0. No new model revision or lineage was created by any retry.

## 16. Existing-object preservation

Project 576 remains on revision 30 with 61 components. Since generation never ran, no prior geometry was changed. This verifies absence of mutation on failure, not successful live composition merging.

## 17. Workspace live acceptance

**NOT_REACHED**: no successful generated live case existed to inspect, approve, transform, save or compare. Previous fixture-backed workspace acceptance remains intact and was not presented as live proof. No failed output was auto-approved or manually patched into a reviewable proposal.

## 18. Latency / usage

Total flow latency: **80.604 seconds**. Sum of individual completion latencies: **80.355 seconds**. Five successful completions took 54.861 seconds total, approximately 10.972 seconds each; one timeout took 25.494 seconds.

Known successful usage: **40,088 input tokens and 6,863 output tokens**. These are lower-bound known totals because the timed-out request supplied no usage. AREA: 2,859 / 1,070 known plus unknown timeout usage. Bridge: 18,055 / 2,750. Walkway: 19,174 / 3,043. Estimated/billed cost was not available.

## 19. Exact model

`Qwen/Qwen3.5-397B-A17B`, PRIMARY only, FAST unset. The restored repository credential was used through the existing shared settings/provider path. No other model was called.

## 20. Files / saved evidence

Changed acceptance tooling only:

- `backend/scripts/live_ai3d_acceptance.py`: capture tool results and repair outcome; retain unknown usage on requests with no returned usage.
- `backend/scripts/retry_live_ai3d_acceptance.py`: exactly three original frozen-context retries, separate batch directory, no automatic approval, no reuse of an already started batch.
- `docs/LIVE_GEOAI_3D_FLOW_V1_AUTHENTICATED.md`: this report.

Saved readable local results, ignored by Git:

- `backend/live-results/universal-v1-authenticated/case-A.json`
- `backend/live-results/universal-v1-authenticated/case-B.json`
- `backend/live-results/universal-v1-authenticated/case-C.json`
- `backend/live-results/universal-v1-authenticated/offline-audit.json`

Original authentication-failure batch remains separately preserved. All completion records contain request phase, route, latency, repair flag/outcome, structured/schema validity and available sanitized HTTP/token/finish/truncation diagnostics. Hidden reasoning was not retained. No additional provider requests were made during offline inspection.

## 21. Tests

Before live requests: **108 passed**, one existing test-client deprecation warning. Suites: generic executor, Assistant runtime, model router, capture utility and environment precedence. After the final capture-only usage adjustment and before live execution: **4 capture tests passed**. Counts overlap and must not be added.

No genuine production implementation bug was fixed after the three flows, so no post-batch runtime regression was required. Schema/executor/model/prompts/tools/temperature/limits/primitives/workspace/evaluation criteria remained unchanged.

## A. Can a real user select → describe → review → approve → see editable 3D?

**Not reliably demonstrated by this batch.** Authentication works; classification and generic design output were demonstrated. However, all three live flows failed before a persisted proposal, so none reached approval or editable 3D generation. The offline-integrated executor path remains accepted, but the full live path is not accepted.

## B. Exact remaining limitations

1. Current unchanged provider timeout can interrupt an AREA design response; the timed-out response's validity and usage are unknown.
2. Classification and design system decomposition must agree with the existing exact multiset guard. This bridge response does not, despite individually valid geometry.
3. JSON inside `toolCalls[].arguments` must be valid. The current outer structured-response repair policy does not cover the walkway's downstream argument parse failure or bridge decomposition rejection.
4. Important preview dimensions need complete assumption coverage; explicit engineering unknowns and site constraints should not be omitted.
5. A successful live proposal must still undergo captured human-readable review, controlled approval, generation and real workspace editing/history acceptance.
6. Existing generic primitive/constraint limits and unvalidated terrain/engineering scope remain unchanged. No terrain following, survey elevation resolution, structural safety or construction readiness was added.

**Stopped after exactly these three authorized live retries. No extra requests, repairs, cases, benchmarks or architecture changes followed.**

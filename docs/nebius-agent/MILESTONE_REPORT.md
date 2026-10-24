# Nebius one-column AI → FEA milestone

Completed locally on 11 October 2026. No GitHub operations, commits or deployment. No billable inference request was sent. The only actual Nebius network request was the non-inference model catalogue GET.

## Review the application

http://localhost:3001/projects/774/workspace is an isolated saved copy of project 768/revision 59, preserving its actual 45-component platform. In Checks select column-ne, then open **Column engineering agent** in the Assistant. Saved mock proposals, actual OpenSees results and explanations reload from the database. Choose **Mock Nebius · local tests · $0** to prepare another local proposal. Selecting Nebius cloud leaves preparation blocked until a testing budget is explicitly approved and configured on the backend.

The original project remains at http://localhost:3001/projects/768/workspace with its saved model and previous OpenSees benchmark intact. Local API: http://127.0.0.1:8001. Both local services remain running.

## Availability, prices and credentials

The authenticated `GET https://api.tokenfactory.nebius.com/v1/models` confirmed both requested IDs are available to the configured account. This request did not invoke a model. Sanitized check evidence: [catalogue-check.json](catalogue-check.json).

Nebius's published rates checked on 11 October 2026:

- `zai-org/GLM-5.3`: USD 1.40 per million input tokens; USD 4.40 per million output tokens.
- `zai-org/GLM-5.3-Flash`: USD 0.15 input; USD 0.50 output per million tokens.

[Official published model listing](https://nebius.com/services/token-factory/models/glm-models-inference). Prices are a dated public snapshot, not a billing receipt. Account access was confirmed separately from pricing. Live inference behaviour remains untested until budget approval.

The existing credential was copied into ignored `backend/.env`, retaining the repository environment and all other configuration. Its value was never displayed, embedded in frontend code or added to source files. `.env` is already excluded by the existing ignore rules. No Git command was used. The safe local launcher clears inference keys process-locally; the stored credential is retained for a later explicitly authorized cloud test.

## Workflow and safeguards

The existing backend Nebius HTTP client is reused for the OpenAI-compatible `/v1/chat/completions` endpoint. The engineering workflow offers Nebius and an explicitly labelled local mock; it has no Ollama or other-provider fallback. Existing general Assistant functionality remains available when the engineering panel is closed; local ordinary chat retains its previous offline mode.

1. The user selects an actual saved platform column. Backend ownership, model revision, geometry, transforms, metre units and existing connectivity validation are checked.
2. The agent receives only the selected geometry and its explicitly saved engineering input record. Missing material identification/source, modulus, declared solid section/source, axial load/source, spring support/source or isolated-model acknowledgement must be supplied manually in Checks. Rendering materials are not engineering properties.
3. The model returns a strict JSON proposal. Its only tool is `prepare_column_analysis`; arguments are limited to the exact model revision, component ID and existing engineering-input record ID. Numeric engineering overrides, arbitrary code/scripts, additional tools and altered references are rejected server-side. Numeric claims and safety/adequacy/compliance claims in proposal prose are rejected. Authoritative dimensions and inputs are displayed by the application.
4. The review card displays actual geometry, all saved quantitative engineering inputs, their purpose, immutable input identity and proposal hash. The user must check an execution-authorization acknowledgement and press **Authorize and run OpenSees**. This authorizes execution only, never engineering adequacy. Neither preparing a proposal nor entering chat runs the solver.
5. Only the existing validated physical-column service generates and executes the local solver input. Approval is tied to the proposal hash and current saved input/model identities. Authorization retries return the same completed analysis rather than automatically running again. Stale, incomplete, altered or already-failed proposals are blocked.
6. Actual computed displacement, axial force, stress, reaction, equilibrium residual, independent references and limitations are returned to the agent. Its explanation is tied to the exact analysis ID and solver-evidence SHA-256. Quantitative values are shown directly from solver outputs; the AI narrative may not introduce digits or structural-approval claims. AI explanations remain unapproved even when numerical verification passes.
7. Saved model changes, engineering inputs and active previews invalidate results/proposals. Unsaved material/load drafts block the agent UI. Backend freshness checks remain authoritative; the panel refreshes saved statuses every five seconds. Proposals, execution authorization, outputs and explanations are retained without modifying model geometry.

New records use the existing engineering-analysis table. No schema migrations or architectural rebuild. Existing parametric editing, revisions, undo/redo, physical-column analysis and independent 3 m OpenSees benchmark remain available.

## Usage and budget controls

All local demonstrations use `mock-nebius`: requested model ID is shown, actual model is **none**, token counts are **not applicable**, actual inference cost is **USD 0**. Fixture token usage is never presented as real inference usage.

For later authorized cloud testing, the backend requires all of:

- `ENGINEERING_AI_MODE=nebius`
- `ENGINEERING_AI_BUDGET_APPROVED=true`
- `ENGINEERING_AI_BUDGET_USD=<explicitly approved positive USD cap>`
- A valid backend `NEBIUS_API_KEY` and official HTTPS Token Factory endpoint.

These settings are not enabled now. The browser/API cannot approve a cloud budget. Inference is bounded to 1,200 output tokens and a bounded context; no automatic retries. A shared local ledger reserves budget before network requests. Successful responses use reported token counts and published rates to estimate cost; unknown or failed requests retain a conservative reservation and block further spending when exhausted. Actual charged cost is unknown without a provider billing receipt. This is a single-process local testing budget guard, not a distributed billing system or a guarantee of provider charges/pricing.

## Numerical evidence

The test copy's actual saved column-ne is 3.2 m long and has a 0.3 × 0.3 m envelope. Explicit test inputs declare a matching **solid rectangular** area of 0.09 m², synthetic E=200 GPa, centered P=100 kN and prescribed k=100 MN/m. The purpose is VERIFICATION_ONLY, not actual project design data.

After explicit mock-proposal authorization, actual OpenSees produces 0.017777777777778 mm shortening, 1 mm support translation, 1.017777777777788 mm head displacement, 1.111111111111126 MPa compression stress and 100.00000000000102 kN upward reaction. These match PL/EA, P/k, P/A and equilibrium independently.

Changing explicit E to 190 GPa made prior proposal/results/explanation stale. After a new review and authorization, final analysis 135 at saved model revision 69/input 133 gives:

- Shortening: 0.0187134502923974 mm.
- Support translation: 0.999999999999971 mm.
- Head displacement: 1.0187134502923684 mm.
- Axial truss forces: approximately −100 kN (negative is compression).
- Compression stress: 1.1111111111110828 MPa.
- Upward reaction: 99.99999999999709 kN.
- Equilibrium residual: 2.9103830456733704e-9 N.

Actual OpenSees 3.8.0 run: `19a7edd8-e720-40b1-86b6-c2a2e624d31d`. Download solver input/output files and executable/model/input provenance in Checks → physical column analysis. Raw local files: `backend/storage/opensees-benchmark/19a7edd8-e720-40b1-86b6-c2a2e624d31d/`.

Complete proposal, authorization, real solver result, explanation linkage, zero-cost mock usage and stale history: [browser-evidence.json](browser-evidence.json).

## Tests and preservation

- 78 backend tests passed: 15 new agent tests plus 63 existing physical-column/OpenSees tests. Coverage includes missing inputs, explicit authorization, actual local solver execution, evidence-linked explanations, ownership, stale revisions/inputs, forbidden tools/code/argument changes, invented numeric/approval claims, budget lock, mocked OpenAI-compatible transport, token-cost estimates, reservations for unknown usage and no automatic retry.
- 67 frontend regression tests passed: persistent Assistant, parametric platform, attachments, editable-model utilities and editor hook.
- Two Chromium/local-server browser tests passed: full mock-agent → real-solver workflow and read-only saved explanation/original benchmark verification. Tests captured no page exceptions or Cesium error panel.
- TypeScript and targeted ESLint passed.
- All 9,304 pre-existing rows across 62 SQLite tables are unchanged and present. [Preservation evidence](preservation-evidence.json). Original projects and revisions were not edited; tests used a new local copy.
- A test invocation from the repository root unintentionally started an `npx` package-fetch attempt; it was stopped. Subsequent tests used existing workspace executables directly. No application dependency/lockfile change was introduced.

Screenshots: [missing properties](screenshots/missing-inputs.png), [model and computed results](screenshots/agent-final.png), [readable solver explanation](screenshots/saved-explanation.png), [stale agent](screenshots/stale-agent.png).

## Scope and remaining limits

This completes one selected saved vertical column, declared uniform solid rectangle, centered axial compression and prescribed linear axial spring workflow. It does not analyze the complete platform or infer real material/soil/load properties.

Connections, base plates, anchors, foundations, soil constitutive behaviour, bending, buckling, lateral loading, self-weight, load combinations, nonlinear analysis, IS/US code checks and structural safety approval remain unsupported/disabled. AI prose remains unapproved, and server filters are not semantic engineering validation. Actual cloud completions/latency/model-specific structured-response compatibility and billing accuracy require a separately approved testing budget. No further discipline or automatic design modification was implemented.

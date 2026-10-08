# Stage 1 Steps 6–9: proposal review and controlled conversation

Implemented 8 October 2026. This batch adds generic concept proposals, exact application approval, controlled tools, bounded context, policy and Nebius orchestration. Full Stage 1 is **not complete**. The new building execution adapter/vertical slice is still a separate batch.

## Files and integration

New backend modules:

- `app/domain/assistant_runtime.py`: proposal requests/views, alternatives, typed translation preview, tool argument schemas, clarification and structured provider output.
- `app/services/assistant/proposals.py`: immutable proposal/specification versions, alternatives, validation linkage, approval, staleness and build start/commit guard.
- `app/services/assistant/policy.py`: conservative server intent classification/effect limits plus bounded structured provider enrichment and per-asset capabilities.
- `app/services/assistant/context.py`: priority-based context assembly with a strict byte budget.
- `app/services/assistant/tools.py`: server-created ToolContext, allowlist, bounded arguments/results, persisted executions and consistent result envelope.
- `app/services/assistant/runtime.py`: atomic queue integration, bounded run loop, safe progress, response persistence, interrupted-run recovery and frozen-context retries.
- `scripts/check_assistant_provider.py`: optional single generic structured connectivity request, without project data or credential output.
- `tests/test_assistant_runtime.py`: deterministic proposal, API, dependency, tool, context, policy, orchestration and provider transport tests.

Modified backend integration: `app/api/routes/site_workspace.py`, `app/services/assistant/conversations.py`, `app/domain/site_workspace.py`, `app/services/ai/nebius.py`, `app/core/config.py`, `scripts/export_stage1_contracts.py` and the site-workspace test fixture (prevents live provider calls). Generated `frontend/lib/generated/stage1.ts` and `docs/contracts/stage1.schema.json` were refreshed.

Frontend: extended `components/workspace/PersistentAssistant.tsx` and its tests; added `ProposalReview.tsx` and `ProposalReview.test.tsx`. The existing Assistant tab remains the entry point. No separate chat page or workspace redesign.

No migration was needed: this batch uses the existing proposal, specification, approval, manifest, assistant-run, tool-execution, event, memory and conversation tables. Concept ValidationResult records link through the existing EngineeringAnalysis store; this does not claim engineering validation.

## Proposal lifecycle and approval

Commands create an immutable `proposal/1` payload and separate mutable state. The service passes DRAFT → GENERATING → READY_FOR_REVIEW or HAS_ISSUES. Application review can approve or reject; relevant changes make the proposal stale. Revisions create new payload/specification versions; matching asset names/types retain asset identity. Prior reviewed/approved versions become stale. Alternative records and proposed assumption memory versions are retained separately.

The specification is `civil-concept/1`, explicitly non-executable. A typed LOCAL translation preview can describe attached object deltas; it does not modify ModelRevision, ModelPlacement, exports or saved model geometry. The UI shows a distinct textual preview during review and hides it after rejection. A map/3D ghost layer is not implemented in this batch.

Approval binds exact proposal version/hash, dependency hash, validation hash, chosen alternative, assumption acknowledgments and expected source model revision. Authentication uses the existing project-owner dependency. A chat request to approve can only direct the user to the application control. The tool registry has no approval/build/delete/mutation tool. Duplicate identical approvals reuse the same immutable approval record; conflicting alternatives or hashes are rejected.

Warnings permit conceptual review; blockers such as dirty source-editor state prevent approval. A failed validation requires a new proposal version. Acceptance is conceptual review, not engineering approval.

## Dependencies, retries and generation boundary

Manifests cover saved site-selection version, project boundary, active terrain, current site facts, relevant accepted project/asset memory, constraints, source model components and placement. For attached-object requests, model comparisons are scoped to those objects rather than the entire model document. Camera, panel and layer state never enter the manifest. Unrelated component changes do not invalidate the concept when placement and other dependencies stay unchanged.

An older profile or changed accepted memory at proposal creation produces a stale-input error. Dependencies are rechecked before approval and the build boundary. `assert_build_current` also checks the approval/validation hashes and offers a strict expected-model-revision comparison for a future generator's commit transaction. A manual edit fails that gate without overwriting user work.

**No generic execution adapter is enabled.** The build route checks approval and then returns `GENERATION_UNAVAILABLE`; repeated requests create zero jobs or model revisions. The BUILT state and commit guard are groundwork for the next specialist adapter. Actual job dispatch, generated geometry commit and duplicate successful-build revision tests belong to that adapter batch; no working generic build is claimed here. Existing building generation paths were left intact and regression-tested.

Message/run creation is atomic and serialized per project. A second active conversation run is rejected. Repeated message submission reuses the persisted run. Retries create an auditable child run with the original immutable message context, never the current editor selection. Repeated identical proposal tool commands use stable message-and-argument identity, including across run retries.

Runs use FastAPI background work with persisted state, a 120-second execution deadline and a 150-second interruption lease. Interrupted runs become explicitly retryable when inspected; this is not durable automatic worker replay. Old pre-orchestration saved messages can be processed explicitly through the same frozen-context retry control.

## Controlled tools and limits

Available tools:

- `get_site_profile`, `get_site_readiness`, `get_active_terrain`, `sample_terrain`
- `get_selected_objects`, `get_model_revision`, `get_project_requirements`
- `query_nearby_context`, `get_checks`, `get_constraints`
- `create_proposal`, `revise_proposal`, `validate_proposal`

Each returns status OK/PARTIAL/UNAVAILABLE/DENIED, data, evidenceIds, dependencyRefs, limitations and errorCode. Arguments reject unknown fields, arbitrary URLs and supplied authority identifiers. The server creates project/actor/run/message scope. Nested proposal and object references remain project-owned; proposed changes can target only attached objects. Questions cannot invoke proposal effects.

Limits: eight attempted tool calls per run, 25 retained terrain samples, 500 m maximum context radius, 100 selected/model objects, 12,000 bytes per result, 20,000 bytes of accumulated tool results, ten-second database execution guard and 120 seconds per run. SQLite uses a query progress interrupt; PostgreSQL uses a local statement timeout. Tools perform no model-directed HTTP, SQL, filesystem access or Python execution.

Terrain sampling reuses the captured profile's bounded sample artifact; it does not activate another terrain or invent interpolation. Nearby context reuses existing retained profile context; it does not perform a new search or promise exact filtering for a smaller requested radius. These limitations are in tool results. Missing/failed context remains unavailable, not an assertion that no utilities/features exist.

## Intent, policy and context budget

Structured CivilIntent supports questions, site queries, design/change requests, analysis, explanations, approval requests and general discussion. Separate AssetRequests retain independent capability notices for mixed projects. Registered and unregistered civil assets can be discussed; generation and engineering analysis remain unsupported in the Stage 1 registry until specialist modules are enabled.

Server classification caps the maximum effect at READ_ONLY, PROPOSAL_ONLY or APPROVAL_UI_REQUIRED. Provider enrichment cannot escalate that cap. Missing attached objects prompt clarification. Structural-safety requests receive a server-owned statement that no validated analysis capability exists. Recorded rationale is supplied through proposal/decision context; prompts explicitly forbid inventing a missing explanation.

Required context has a 24,000 UTF-8-byte bound, a conservative token upper bound independent of a particular tokenizer. Current message, capability/safety limitations, frozen selection, site facts/unknowns/readiness, accepted memory and active proposal have priority. If these cannot fit, the run fails explicitly with CONTEXT_BUDGET_EXCEEDED instead of silently removing hard requirements. Relevant components/checks, up to six recent messages and up to eight supporting evidence records are added only while they fit. Whole models, full conversation histories and full terrain sample sets are not sent. Fixed schemas and separately bounded tool outputs add to the transport payload outside this context budget.

## Nebius configuration and recovery

Server-only configuration: `NEBIUS_API_KEY`, `NEBIUS_CHAT_MODEL`, optional `NEBIUS_BASE_URL`. When the latter is unset, the existing `NEBIUS_TOKEN_FACTORY_BASE_URL` remains in use. Existing building-provider behavior is preserved.

Provider states are MISSING_KEY, MISSING_MODEL, UNREACHABLE, TIMEOUT, RATE_LIMITED, INVALID_RESPONSE and PROVIDER_ERROR. No fallback fabricates a successful reply. Transport has a 25-second timeout, a response byte limit and bounded output tokens. One schema repair is allowed per structured response. Invalid intent/tool payloads cannot become loose-prose commands. User messages remain stored through provider/tool/validation failures. Safe progress events are persisted; no chain-of-thought is requested or stored.

One live connectivity smoke test was attempted with configured server credentials and model, sending only a generic JSON check. Result: **PROVIDER_ERROR**. Live structured connectivity therefore remains unverified; no model quality claim is made, and the live request was not repeated. Fixture-based orchestration is verified independently of that provider failure.

## UI and verification

The Assistant displays persisted replies, clarification options, tool progress, per-asset capability notices, proposal review cards, assumptions/warnings, evidence inspection/source links and frozen-run Retry. Review requires explicit assumption/scope acknowledgment and an alternative selection when applicable. Approval never calls generation. Existing geometry editing, revisions, export, Checks and Engineering Dock remain separate.

Verification runs:

- Broad backend regression run: **195 passed, 2 skipped**, including the then-current 40 runtime tests, 75 foundation/site/migration tests and 80 existing model/engineering/building/provider/catalogue/authentication tests.
- Final expanded focused backend suite: **88 passed** (44 runtime tests and 44 site/conversation/memory tests).
- Frontend regression run: **45 passed** across eight test files. Final affected UI checks: **10 passed**.
- TypeScript, ESLint, generated-contract consistency and Python compilation checks pass.
- Local API was restored after its old development process stopped listening; health returns 200. Browser verification loaded the updated Assistant in project 317. No extra live provider conversation was submitted during browser verification.

Live PostgreSQL/PostGIS tests remain **not run**: no dedicated `STAGE1_TEST_POSTGRES_URL` and no Docker/psql CLI were available. Compiled DDL and SQLite tests do not establish live PostGIS or production concurrency parity.

## Next building vertical slice

Connect the existing building specification/validator/generator as a versioned capability adapter; translate approved typed building proposals deterministically; dispatch through the existing job/outbox path; call the start and commit dependency gates; preserve placement and write the existing editable model/revision/lineage pipeline. Then test duplicate successful builds, worker restart recovery, real generation/manual-edit races, architectural/structural layers and exports end to end. Add a spatial preview layer if desired. No new road, bridge, dam, drainage or tunnel generator was introduced here.

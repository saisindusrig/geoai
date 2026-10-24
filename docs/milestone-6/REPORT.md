# GeoAI — Milestone 6: site-wide Nebius assistant

Implemented locally on **23 October 2026 (Asia/Kolkata)**. Stop after this milestone.

Open [the local website](http://localhost:3001/dashboard) and choose **GeoAI Assistant**. The shared panel is mounted at the application root and stays available across navigation. Existing workspace, map and building-assistant entry points open this same panel. **Paid inference remains disabled. No live completion was requested or tested.** The running review backend returns an honest unavailable/budget-approval error; it never substitutes offline chat.

## Implemented behavior

The workflow is: user request → server-owned saved context → model response/tool plan → allowlisted read tools or preview preparation → explicit review in existing tools → server tool results → bounded model verification → persisted result.

- Flash (`zai-org/GLM-5.3-Flash`) is pinned as the default. Advanced (`zai-org/GLM-5.3`) requires manual selection. There is no provider/model fallback, automatic escalation or automatic inference retry.
- Genuine Nebius SSE deltas are forwarded as they arrive. Native function names and fragmented JSON arguments are assembled and validated before the entire tool batch can begin. Incomplete streams, wrong models, invalid tools, excessive output, unavailable models and HTTP failures fail closed. UI progress and the tool-plan card describe actual requested operations; they are not fabricated model replies.
- Context contains the current route (explicitly treated as untrusted), owned project facts, saved revision/document hash, selected-object identity/geometry/transforms, saved CAD references and engineering evidence. Existing stale and unsupported statuses remain visible. Large contexts retain identities and hashes while explicitly identifying omitted details and bounded counts.
- The interface displays task progress, tool outcomes, evidence, preview controls and errors. History follows the user across pages, is scoped to their existing authenticated identity and rechecks current project ownership. Each stored task includes its captured context and model. Earlier project conversations remain readable without rewriting their offline provenance.
- Position proposals open the existing 3D inspector's visual preview. Backend selection/ownership/current-revision checks, a fresh document-hash check, and editor state checks reject obsolete proposals. Preview does not apply or save. The user must explicitly press **Apply**, then **Save model**, through the existing editor. Existing undo/redo, source protections and result invalidation remain responsible for the edit.
- Analysis, CAD/file operations and exports are directed to existing application tools. Opening a tool never authorizes an analysis or writes a file. Existing engineering authorization, exact proposal/input hashes, ownership, source hashes, freshness and supported-method gates were not relaxed.
- Legacy `/api/projects/{id}/ai/chat` and `/chat/stream` return 410 instead of regex/offline replies or simulated streaming. Legacy conversation POSTs also return 410; saved messages and existing evidence remain readable. Production UI contains no mock-provider selector.

## Server tool registry

Implemented in `backend/app/services/assistant/site_tools.py`:

| Tool | Actual application capability |
|---|---|
| `read_context` | Existing saved engineering-evidence adapter, selected geometry and CAD identities |
| `list_projects` | Up to 50 authenticated user's projects, with owned-project total |
| `read_quantities` | Existing saved estimate/calculated-summary queries; no recalculation |
| `read_capabilities` | Existing authoritative supported-method and current/stale result service |
| `read_diagnostics` | Existing diagnostics, including a fixed bounded solver **version-only** probe |
| `navigate` | Allowlisted dashboard/project/editor/CAD/analysis/results/quantities/export/diagnostics/settings destinations; target project ownership is checked again before navigation |
| `prepare_position_preview` | One selected unlocked independent component's East/North/Up position proposal, without applying or saving |

No arbitrary HTTP, shell, code execution, filesystem write, approval, model-save or numerical-analysis tool is exposed to the model. Argument schemas forbid additional fields. The existing preview/save/analysis backends remain the authority; model prose is never an authorization token.

## Provider verification and spending gates

A real **non-inference** authenticated model-catalogue GET confirmed both exact IDs for the configured account. The public [Nebius OpenAI-compatible API schema](https://api.tokenfactory.nebius.com/openapi.json) confirms `/v1/chat/completions`, `stream`, `stream_options`, `tools`, `tool_choice`, `max_tokens` and `reasoning_effort`. [Nebius's GLM listing](https://nebius.com/services/token-factory/models/glm-models-inference) documents the model family and published rates. Evidence: `provider-verification.json` and `provider-openapi.json`. These checks do **not** verify live generation quality, latency or actual billing.

Keys remain in the backend's existing credential resolver. Requests are restricted to the official HTTPS Token Factory endpoint, without redirect following. Model/tool/user text cannot change backend spending approval.

The new assistant requires backend `ASSISTANT_INFERENCE_APPROVED=true`, a positive `ASSISTANT_BUDGET_USD`, and valid backend credentials before any catalogue/inference request in its turn handler. None was enabled for this milestone. The normal review launcher explicitly keeps approval false and its budget zero. `.env` credentials were not edited or displayed; `.env.example` documents the controls.

Limits:

- At most **two completion requests and three tools per user turn**; one tool batch, followed by a verification response without tools. No autonomous unbounded loop.
- Each completion is limited to 90,000 serialized input bytes, 4,096 output tokens, 1.5 MB of SSE data and a bounded streaming timeout. A selected model's catalogue access is checked before inference. Client requests also have message, selection, identifier and route bounds.
- Durable transactional reservations serialize at most two active turns globally and one per user. A user is limited to 10 accepted turns/minute and 100/day, plus the configured conservative token quota.
- Default daily token reservation limit is 200,000. A worst-case two-request turn reserves 188,192 units, so this conservative default normally permits **one accepted turn/day**, even if reported actual usage is lower. Configure any larger allowance only with an explicitly approved spending policy.
- The assistant-specific global budget accounts all reservations, across users. Reservations survive errors, cancellation, restart and unknown usage. Successful requests also retain the conservative reservation; it is **not** presented as actual charged cost or refunded optimistically. Provider-reported usage is stored separately. Published-rate reservations are approximately $0.031096 per Flash turn or $0.2880448 per advanced turn at the configured maxima, not billing receipts.
- Request IDs prevent a transport retry from replaying a completed task/tool batch. Interrupted leases expire after five minutes and preserve their spending reservation. Another attempt requires manual user action and remains subject to quotas.

The separate new operational store defaults to `backend/assistant-history.db` (ignored by source control). It stores only new assistant tasks/reservations and leaves original application tables unchanged. The reservation budget is separate from historical engineering-agent ledgers. No historical usage was reset, refunded or altered.

## Verification

| Final check | Result / evidence |
|---|---|
| Focused backend | **100 passed**, `backend-final.log`: assistant, Nebius configuration, private-beta ownership/security, capabilities and physical-frame safeguards |
| Focused frontend | **37 passed**, `frontend-final.log`: shared assistant, stream transport, actual error envelopes, inspector preview/apply, editor and saved-result regressions |
| TypeScript | Passed, `typescript-final.log`; also passed in final Next build |
| Scoped ESLint | Passed with zero warnings, `lint-final.log`, including the consolidated workspace entry point |
| Production build | Passed on existing Next 16.4.2 and installed dependencies, `build-verified.log` |
| Real Chrome | **4 passed**, 1280×900 and 1600×900, `browser-verified.log` |
| Actual bounded context | Projects 793/revision 103, 794/revision 105, 804/revision 124 retain selected identities/document hashes within 12 KB and 24 KB snapshots, `context-boundaries.json` |

Backend tests cover ownership and history access after ownership changes; unknown selections; forbidden tools/arguments; current/dirty preview restrictions; no model writes; native SSE argument fragments; wrong model, quota, timeout and incomplete streams; conservative token/request/budget/concurrency rejection; persisted failure and request identity; no fallback and no automatic retries. Existing focused engineering regressions retain their exact authorization and stale-result checks.

Browser tests use the **real disabled backend** for missing approval/credentials, honest 503 messages, preserved drafts and exactly two manually initiated attempts. Successful conversational/preview responses are **explicit automated-test fixtures only**, not live model inference. They use real saved project 793 context, open a genuine 3D preview, verify it remains unapplied, cancel it, and navigate to existing results and diagnostics. All other modifying browser requests and external hosts are blocked. No model save or numerical analysis was performed against an original project. No page exceptions, forbidden mutations or horizontal overflow were observed in the final matrix.

Earlier browser failures are retained: the page-link utility intercepted Send until the assistant stacking order was corrected; a test-only mocked task was not initially retained on reopening; and the new transport initially missed the application's structured error envelope. Those were corrected before the final matrix. Initial backend tests also caught a new-store SQL placeholder mismatch, fixed before the passing runs. Restricted Windows-sandbox TestClient runs stalled; they were stopped and the isolated checks ran successfully outside that sandbox, with unmocked provider transport explicitly forbidden. No dependency installation or browser download was used. Existing Starlette/Vitest/Playwright warnings remain.

Screenshots include `unavailable-1280.png`, `unavailable-1600.png`, `preview-1280.png`, `preview-1600.png`, `editor-preview-1280.png`, `editor-preview-1600.png`, and navigation views. Success screenshots contain the automated fixture label; they are not live inference evidence.

## Preservation

- **10,267 development-database rows and all schemas exactly unchanged** against this milestone's initial fingerprint (`milestone-preservation.json`). The additional row compared with the previous milestone's reported 10,266 existed before this milestone's baseline; it was not removed or rewritten.
- **10,500 pre-existing isolated rows**, zero appends, and **635 spatial solver files** unchanged (`review-preservation.json`).
- **55,296 original storage files** and **2,090 CAD/proof files** unchanged. **66 live database schemas**, **198 archived-only historical database fingerprints**, and 263 older identical/archived fingerprints verified in place (`preservation-audit.json`). The older development-database fingerprint difference predates this milestone and is reconciled by the strict current-row baseline.
- **21 coupled native solver artifacts** remain unchanged (`coupled-evidence-preservation.json`).
- No original databases were copied, restored, repaired or migrated. Existing compressed preservation archives were only read in place. Original geometry, revisions, calculations, engineering inputs, authorization, audit, conversation and usage records were not changed. Normal operational request/build logs and caches can append or refresh; they are not engineering evidence or claimed byte-identical.

## Unsupported and deferred

1. **Live inference remains untested and disabled.** Model-specific generation reliability, tool-choice behavior, latency, reasoning token usage and billing cannot be claimed from catalogue/schema/mocked tests. No explicit paid test permission was given or used.
2. The assistant prepares **position-only previews**, not arbitrary CAD editing, component creation/deletion, rotation, scaling, assembly regeneration or automatic building generation. Former building-assistant entry now opens the shared assistant; specialized legacy code/data is retained but not advertised as a second chat interface.
3. Model saving, imports/uploads, export generation/download, settings changes, engineering proposal authorization and numerical execution remain manual actions in existing application tools. Chat cannot execute them. Browser acceptance deliberately did not approve an original-project save or solver run.
4. One native batch cannot perform arbitrary dependent multi-tool exploration. Longer tasks require another explicit turn. Evidence/history bounds are visible: 30 new tasks, two bounded previous turns in model context, up to five older conversations on demand, and existing adapter limits on engineering records/selections/CAD references. Full-history pagination and complete model inventory are not implemented.
5. Generated prose remains engineering-unverified. Source-linked evidence and authoritative method gates do not make an LLM a safety reviewer or validate unsupported methods. No formulas, numerical methods, design-code checks, whole-building analysis capability or structural approval were added.
6. This is a local implementation, not production/private-beta approval. Shared identity/session policy, security headers, durable distributed jobs/storage, operational recovery and inherited dependency findings remain under the previous milestone's qualification gates. The new SQLite task/reservation store needs a shared transactional implementation and operational qualification before distributed hosting.
7. Firebase remains future architecture: the existing authenticated-user dependency is retained as the integration seam. No Firebase SDK, deployment, data migration, cloud resource or billing change was made.

No Git operation, parallel AI agent, installation, deployment, destructive cleanup or paid inference. Milestone 6 stops here.

# GeoAI — Milestone 6.1: acceptance readiness and quota usability

Completed locally on **23 October 2026 (Asia/Kolkata)**. [Local website](http://localhost:3001/dashboard). **Inference remains disabled. No paid completion was executed.** Stop after Milestone 6.1.

The assistant now reserves each completion from its actual serialized request rather than reserving two maximum-size requests up front. The default 200,000-token daily allowance is unchanged. Short conversations can fit without weakening the transactional spending, rate, concurrency or ownership gates. A guarded manual procedure is prepared in [LIVE_ACCEPTANCE.md](LIVE_ACCEPTANCE.md); it has not been activated.

## Reservation and accounting policy

1. Build the exact UTF-8 JSON body, including system instructions, bounded history, current context, tool schemas and any tool results. The same serialization is sent to Nebius, and its SHA-256 is retained. Bodies above 90,000 bytes are rejected before inference.
2. Reserve an input-token ceiling equal to serialized bytes plus **1,024 protocol units + 64 per message + 256 per exposed tool**. Add the actual configured 4,096-output-token cap once for this completion. This is conservative byte/protocol accounting, not an exact tokenizer count. Output includes reasoning tokens.
3. Calculate the reservation from the selected model's published-rate assumptions. Money is rounded upward to twelve decimal places, and global cap checks sum decimal values inside the SQLite write transaction. The backend must reserve sufficient token and USD headroom before a completion can start.
4. If the model requests tools, validate the entire allowlisted batch, execute its existing read/preview adapters, build the actual continuation payload, and reserve that second completion separately. If it does not fit, stop with a specific quota error. There is no upfront unused second-request reservation, no third completion, no additional tool round, model escalation or automatic paid retry.
5. Complete, consistent, nonnegative integer provider usage within the bounds replaces that completion's reservation with **reported-token accounting and a cost estimate**. Totals and reasoning-detail consistency are checked; reasoning already included in completion tokens is not added twice. This also works when usage arrives before a later stream/validation failure. Settlement is exactly once.
6. Missing, malformed or conflicting usage retains the full reservation. Interrupted requests retain unknown usage. A request demonstrably never handed to the inference transport, such as a catalogue failure, is marked `NOT_SENT` and its unused token/cost reservation is released; the accepted turn still counts against request limits. No provider usage is fabricated for that state.
7. Usage beyond the bounds retains at least the higher reservation/reported estimate and blocks further inference for accounting review. A missing or different returned model also retains the reservation and blocks inference; requested-model prices cannot settle an unconfirmed model. These are **Disabled** review conditions, not temporary rate-limit messages. No browser/API approval or ledger-reset action is exposed.

Actual provider tokenization/chat-template expansion and invoicing remain external assumptions requiring controlled live qualification. The byte/protocol allowance is deliberately conservative but is **not a provider billing guarantee**. Contradictory evidence fails closed. Published rates, estimates, reservations and reported token counts are never labeled actual charges; all actual-charge fields remain `UNKNOWN` without billing evidence.

Historical tasks and their accounting are not repriced or retroactively refunded. The existing SQLite schema is reused; new request/settlement metadata lives in new tasks' JSON. This assistant budget remains separate from historical engineering-agent accounting. The USD ceiling is cumulative across all users, including retained unknown reservations; changing it is not an automatic daily reset or credit grant.

### Dry-run examples — no reservations committed, no inference

`provider-readiness.json` contains calculated Flash quotes using the real system/tool definitions and authorized saved context:

| Example completion | Serialized bytes | Token reservation | Estimated maximum USD |
|---|---:|---:|---:|
| Ordinary website help, without history | 5,799 | 12,839 | 0.00335945 |
| Project 793/revision 103 saved context | 17,619 | 24,659 | 0.00513245 |
| Synthetic long provider-wire payload | 74,236 | 81,276 | 0.013625 |

These are per-completion bounds at the configured output cap, not actual usage or charges. Context/history changes the quote. The former **188,192** units were reserved for every turn regardless of size or whether verification was needed.

Tests demonstrate **eight short turns** within an explicitly configured **200,000-token / USD 0.02** allowance using synthetic reported usage of 1,800 prompt + 160 completion tokens per turn. The final accounting is 15,680 tokens and an estimated USD 0.0028, not actual spending. A separate test fits **six short turns with no usage reports** within **200,000 tokens / USD 0.05**, retaining every full reservation. Atomic competing claims cannot exceed the configured global allowance. Long continuations are denied before another completion if remaining headroom is insufficient.

Unchanged limits: two active turns globally, one per user, ten accepted turns per minute, 100 accepted turns per rolling 24 hours by default, configured rolling token allowance, at most two completions and three tools per turn. Durable reservations and request IDs survive failure/restart; replay reads the existing task rather than rerunning its tools. Unknown historical accounting may still consume allowance; do not delete it to make room.

## Provider and user-interface readiness

- The credential-safe diagnostic confirmed a stored backend credential and official HTTPS endpoint, and a **non-inference model-catalogue GET** confirmed both exact IDs: `zai-org/GLM-5.3-Flash` and `zai-org/GLM-5.3`. No key value was printed, copied to the frontend or changed. The retained official schema confirms the streaming, native-tool, usage and reasoning parameters. Evidence: `provider-readiness.json` / `.log`.
- The normal review launcher deliberately removes inference credentials from its process and forces spending approval false/budget zero. Its state is **Awaiting spending approval**. This does not contradict the diagnostic finding a stored backend credential. `runtime-status.json` records the review process's distinct state and configuration booleans without secrets.
- The UI distinguishes **Available for an approved request**, **Disabled**, **Rate-limited / allowance reached**, and **Awaiting spending approval**. “Available” is permission/configuration/headroom for an attempt, not a claim of proven provider health. A particular larger payload may still exceed remaining allowance.
- Structured HTTP and streamed errors preserve their quota/provider codes. Refresh availability and Refresh history are manual reads. Stop response aborts the client and closes server transport where cancellation is delivered; it is not a promise that provider billing stops. There is no automatic retry or silent model selection change.
- Server and client SSE parsing handle incremental UTF-8 and CRLF. The server bounds received bytes before waiting for a newline, rejects oversized lines/malformed encoding, enforces native call/argument limits and requires a confirmed matching returned model. Input, output, response, HTTP/stream timeout and two-request bounds remain enforced. Existing 40-second HTTP / 45-second completion deadlines, bounded catalogue timeout, 115-second client abort and five-minute interruption lease remain finite; cancellation retains uncertain usage.
- Flash remains the default; advanced selection is manual. The interface explicitly states that arbitrary CAD editing, automatic building generation and engineering execution are unavailable in chat. Existing position-only preview, Apply/Save, authorization, source hash, current-result, ownership and supported-method gates remain unchanged. No engineering tool was added.

The new `backend/scripts/serve_assistant_acceptance.py` is a **dormant, manually activated launcher**, not an agent or inference runner. Only its help/refusal paths were executed. It refuses missing approval and invalid/oversized caps, starts no inference, uses loopback only, retains the ledger, limits accepted turns to three per user/24h, and blocks guarded legacy provider/engineering paths. The live checklist covers three manual help/context/read-only-tool turns, local quota rejection without a fourth completion, error evidence, sanitized accounting and shutdown back to disabled review mode. No positive-budget activation was executed.

## Focused verification

| Check | Result / evidence |
|---|---|
| Backend | **74 passed**, `backend-final.log`: assistant, quota/accounting, native SSE, ownership, history, preview restrictions, provider configuration and failures |
| Frontend | **17 passed**, `frontend-final.log`: availability, manual refresh/retry/model choice, Stop, structured quota errors, UTF-8/CRLF and retained inspector preview/apply behavior |
| TypeScript | Passed, `typescript-final.log`, and in the Next production build |
| Scoped lint | Zero warnings, `lint-final.log`, limited to changed frontend implementation/tests and the targeted browser file |
| Build | Passed with existing Next 16.4.2/dependencies, `build.log` |
| Real Chrome | **6 passed** at **1280×900 and 1600×900**, `browser.log` |

Quota tests include short/long/Unicode byte sizing, realistic mocked reported usage, unknown usage, exact-once settlement, continuation refusal, cancellation/transport closure, known-not-sent requests, model-identity contradictions, out-of-bound accounting, cross-user atomic budget contention, all availability states and rate rejection. Existing ownership, stale/dirty previews and history-access regressions remain in the focused set. No full numerical-method suite or paid provider test was run.

The browser matrix uses the real disabled backend for honest approval errors, retained drafts and manual retry. Availability/quota and successful preview/navigation messages are explicitly test-only fixtures. Existing real project 793 context opens a genuine unapplied preview, then Cancel, existing results and diagnostics; original-project saving and numerical execution are blocked. Final runs observed no page exceptions, forbidden writes or horizontal overflow. Screenshots at both widths include `quota-state-*`, `unavailable-*`, `preview-*` and `editor-preview-*`; 1280 quota and 1600 disabled views were visually inspected.

Initial test-only failures are retained: the new fixture needed its existing `site_db` fixture imported, and a fixed 40k continuation-test allowance did not actually exhaust the measured payload; the test now explicitly uses a fitting-first / refusing-second 20k allowance. All final checks pass. Existing Starlette/Vitest/Playwright tooling warnings remain. No packages or browsers were installed.

## Preservation

Existing manifests were reused rather than replacing originals or creating database copies. `preserve.py` reads the Milestone 6 baseline; `verify_review.py`, `preserve_evidence.py` and the retained-archive verifier read their established hashes. The full storage/archive scan was run once in this milestone; final row/history checks are read-only.

- **10,267 original development-database rows and schemas** unchanged (`milestone-preservation.json`).
- Existing assistant conversations/accounting unchanged; the local sidecar had **zero pre-existing tasks** and remains empty because all real submissions were disabled and success fixtures never persisted (`assistant-history-preservation.json`).
- **10,500 isolated rows**, zero appends, and **635 spatial solver artifacts** unchanged (`review-preservation.json`).
- **55,296 original storage files**, **2,090 CAD/proof files**, **66 live database schemas**, **198 archived-only historical database fingerprints**, and 263 older matching/archived fingerprints verified (`preservation-audit.json`). The older development fingerprint difference predates this milestone and is reconciled by the strict current baseline.
- **21 coupled native solver artifacts** unchanged (`coupled-evidence-preservation.json`).

Original geometry, CAD/model data, solver calculations, authorization/audit records, saved conversations and engineering evidence were not edited. Operational logs and build/type caches can refresh. No Git operation, additional AI agent, destructive cleanup, installation, deployment, Firebase resource/billing change, or numerical-method modification was performed.

## Remaining blockers

1. Human approval of a precise controlled live-test scope and spending ceiling is still required. Inference is **off**; catalogue and mocked results are not live acceptance.
2. Real model-specific tool choice, completion latency/quality, usage reporting, strict returned-model identity, byte/protocol reservation assumptions and billing accuracy remain unqualified. The 4,096-output cap can produce a genuine incomplete-response error; do not increase it or retry automatically.
3. Actual provider charges cannot be guaranteed by an application-side estimate. Provider/tokenization/rate contradictions stop further calls for review. Unknown reservations and historical holds can legitimately exhaust allowance.
4. Arbitrary CAD/model generation, consequential file/settings/model changes and engineering execution remain outside chat's capabilities. Existing manual approval flows retain authority; generated prose is engineering-unverified.
5. Shared production identity, distributed ledger/storage/jobs, operational recovery and inherited security qualification remain under the previous milestones' gates. Firebase remains future architecture.

Stop after **Milestone 6.1**. Do not activate paid inference automatically.

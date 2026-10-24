# GeoAI — Milestone 6.2: Live acceptance report

Status: **Controlled backend shut down; ordinary review mode restored during the subsequent UI task.**

A later read-only ledger inspection found three user-submitted successful tasks and five Flash completions, with USD 0.0024219 estimated accounting and 14,487 tokens. No new live request was made by the UI task. See `../assistant-ui/acceptance-summary.json` and `../assistant-ui/status-final.json`. Historical narrative below describes the initial handoff; it is not a claim that the full three prescribed acceptance prompts were independently verified.

## Scope and outcome

The supplied request specifies Nebius Token Factory, `zai-org/GLM-5.3-Flash` only, at most three manually submitted turns, a cumulative application-accounting ceiling of USD 0.05, and no automatic retries or consequential engineering operations.

**Zero live turns and zero completion requests were submitted.** Real Nebius streaming, saved-context reasoning and native read-only tool calling remain **untested**. No successful live acceptance is claimed. Actual provider charges are unknown; application estimates are not invoices.

An initial activation attempt was rejected before execution because approval was supplied in pasted text. The user subsequently confirmed directly in chat: Flash only, up to three manually submitted live turns, cumulative USD 0.05 ceiling, no automatic retries. The controlled backend was then activated under that authorization. No prompt has been submitted by the agent.

## Completed preflight — no inference

- Read Milestone 6.1 report, manual acceptance procedure, controlled/review launchers, provider configuration, transport, tool registry and accounting code.
- Existing status: `AWAITING_SPENDING_APPROVAL`, `enabled=false`, official endpoint, no offline assistant fallback.
- Ledger inspection: zero tasks, USD 0 accounted, zero running requests and no accounting-review flag. Headroom under the proposed ceiling: **USD 0.05**; daily accounted tokens: zero. Ledger was not reset or replaced.
- Backend resolver finds a credential and the official Nebius endpoint without printing the credential or changing credential files. The review runtime deliberately clears its process credential.
- Authorized project 793/revision 103 context is accessible and not stale. CAD column SW has stable component ID `drawing-cad:614f117ae2a74794:9C`. Exact selection in the user interface and response comparison remain pending.
- The normal review backend identities were checked. Existing frontend on port 3001 and same-origin proxy were left running.

## Acceptance-only safeguard

The existing controlled launcher exposed both models. Its process-local model allowlist now contains Flash only. The ordinary provider implementation and review launcher are unchanged. An isolated launcher check used a stubbed server/event-loop invocation, made no provider request and confirmed Flash-only rejection of the advanced model before transport, three accepted turns per user per rolling 24 hours, USD 0.05 budget and loopback port 8001. Existing two-completion/three-tool bounds and no automatic retry behavior remain in force. No engineering feature was added.

## Preservation

The existing manifest comparison confirms all **10,267 original development-database rows and schemas exactly unchanged**. Existing assistant history/accounting was empty and remains retained. No engineering project, geometry, model revision, saved evidence, authorization, audit entry, solver artifact or credential file was intentionally changed. No new numerical analysis, Git operation, installation, deployment or Firebase operation occurred. Full storage/solver archive hashing was not repeated in this preflight; previous manifests remain available.

Evidence: `preflight.json`, `status-before.json`, `launcher-check.json`, `milestone-preservation.json`, `assistant-history-preservation.json` and the authorized saved-context baseline in this folder. No credential-bearing request capture was made.

## Remaining manual procedure

After direct confirmation and successful activation, the user must submit each approved prompt manually, one at a time, stopping after any failure or other specified stop condition. The agent must not click Send or issue an inference POST. Inspect each result/accounting record before guiding the next turn. At completion or a stop condition, stop the verified controlled process, restart `serve_copilot_review_local.py`, verify disabled `AWAITING_SPENDING_APPROVAL`, retain all new history/reservations, and update this report with actual evidence. Do not retry, change models, clear ledger entries or raise caps to continue.

## Activation and current handoff

- Stopped only the reverified normal review backend processes (13704 and its child 25244); verified port 8001 was free before starting the controlled launcher.
- Controlled launcher PID: 21976; server child PID: 27552. Startup log confirms loopback `127.0.0.1:8001`. The existing frontend on port 3001 was preserved.
- `/api/assistant/status` is `AVAILABLE`, `canSend=true`, backend credential configured, official endpoint, and models contains **Flash only**. Existing bounds: at most two completion requests and three tools per turn; zero automatic retries. Controlled launcher sets three turns/user/24h and USD 0.05 cumulative cap.
- Activation snapshot: zero live turns, zero completion requests, zero accounted tokens/cost, no active turn and no accounting-review flag. Remaining application headroom: USD 0.05, not an actual-charge guarantee.
- Opened the dashboard assistant, verified Flash selection and Available status, and staged the first prescribed question in its composer. **Send was not clicked.** The user must submit it manually and report completion/error before the next turn is prepared.
- `status-activated.json` and `manual-turn-1-ready.png` retain sanitized activation/UI evidence. Ordinary startup logs show the existing local SQLite and in-memory job-store configuration; this is not a production qualification.

Controlled inference remains active solely for this acceptance handoff. Shutdown back to disabled review mode and final preservation comparison are pending the approved tests or a stop condition. Milestone 6.2 is not complete.


## Subsequent shutdown evidence

The UI improvement task verified and stopped controlled launcher PID 21976/server PID 27552 after observing all three test turns consumed. It restored `serve_copilot_review_local.py`. Final status is `AWAITING_SPENDING_APPROVAL`, enabled false. The three existing history/accounting rows were fingerprinted and remain exactly unchanged. Full historical response-quality qualification remains outside the subsequent UI-only verification.

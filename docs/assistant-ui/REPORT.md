# GeoAI Assistant — Conversation UI improvement

Completed locally on 23 October 2026. No new paid inference was requested. Inference is disabled in the ordinary review backend (`AWAITING_SPENDING_APPROVAL`).

## Delivered

The site-wide assistant now uses separate You/GeoAI messages, 15px conversation text with comfortable spacing, safe Markdown rendering (bold, emphasis, headings, lists, links, inline/fenced code and quotations), and a compact composer. Model configuration, token accounting, reservation estimates, captured context, raw tool outputs, earlier conversations and verbose request events are collapsed under Details or message/evidence disclosures. HTML is escaped rather than executed; unsafe link schemes are rejected. This is a deliberately bounded Markdown renderer using existing React dependencies, not a full GitHub-flavored Markdown engine; complex tables and embedded HTML/images are not supported.

A single prominent status follows actual request events: Ready, Thinking, Checking your project, Preparing an action, Waiting for your approval, Completed, Connection error or Usage limit reached. Disabled configuration is shown as Unavailable with the backend reason. Manual Stop returns to Ready with an explicit stopped/unknown-usage notice. No fictional timed progress or new template AI responses were added.

The status API now reports the specific concurrency, request-count, token or cumulative-budget gate. An approved three-turn-test block explicitly says **all 3 turns are used**, not that money or tokens are exhausted. Spending estimates remain clearly distinct from actual charges.

Tool summaries use plain action names. Navigation requires an allowlisted target and an authenticated project read; the confirmed project name is shown after the route/context or inspector acknowledgment. Preparing a link is not labeled a completed action. Position previews offer Preview and Cancel; dirty/stale/source gates remain in the existing editor. Cancel clears only an active matching visual draft and does not Apply or Save. After a verified visual preview, Review in editor reveals the existing approval controls. Engineering execution and unsupported CAD generation remain unavailable in chat.

The panel expands and resizes by pointer or keyboard (focus the left separator and use arrow keys), stays within half the desktop viewport, and has an explicit close button/Escape behavior. New content follows the bottom only when the reader is already there; scrolling back preserves position and offers New message. History loading cannot overwrite a response that is actively streaming.

## Verification

- **50 backend tests passed**: exact status reasons, existing assistant permissions, bounded provider/tool calls, accounting and quota regressions. Temporary test databases and mocked provider transports only (`backend-tests.log`).
- **24 frontend tests passed**, including Markdown safety/rendering, streamed messages, context/model selection, retained history, explicit same-ID transport retry, native tool summaries, navigation acknowledgment, stale/dirty preview gating, matching-preview cancellation, cancellation isolation between older and newer proposals, structured quota reasons and no automatic replay. The final changed chat component was rechecked separately (11 tests; `frontend-final-changed.log`).
- **4 final Chromium checks passed**, at **1280×900 and 1600×900**: real 3D editor visible with assistant open; Markdown, lists/links, hidden details, action acknowledgment, expansion/keyboard resizing, history refresh, scroll retention/newest-message button, quota/service failure, pending request/Stop, retained draft and exactly one mocked request on cancellation (`browser-final-pass.log`).
- Two before-screen capture checks passed. TypeScript, scoped lint and production build passed with existing dependencies. No installation or full numerical suite was required.
- Every browser inference POST was intercepted; other mutating operations were blocked. The backend was inference-disabled before UI testing. New assistant-history rows: **zero**.

The browser checks exposed a Stop/Send DOM-reuse bug in the new composer: a cancellation click could become a submit when React reused the button. Distinct keyed buttons and prevention of Stop's default action fixed it. The regression now checks exactly one intercepted request. Subsequent Escape focus behavior was corrected as well. Initial failed test artifacts/logs are retained; final evidence is identified above.

## Before / after evidence

Screenshots use sanitized test messages and mocked assistant events, with the actual saved 3D scene. They do not claim new live provider responses.

| Viewport | Before | After |
|---|---|---|
| 1280×900 | [Before](before-1280.png) | [After](after-1280.png) |
| 1600×900 | [Before](before-1600.png) | [After](after-1600.png) |

Additional screenshots: `expanded-*`, `action-*`, `quota-*`, `failure-*`, `thinking-*`, `stopped-*`.

## Existing live evidence and preservation

Read-only inspection found **3 existing SUCCEEDED tasks**, **5 provider completions**, and exact requested/returned Flash identities. Stored events include successful `list_projects`, `read_context` and `read_capabilities` results. The combined recorded accounting is **14,487 tokens and USD 0.0024219 estimated cost**. These are historical acceptance records, not UI test requests or actual provider charges. This UI task did not independently validate every historical answer against the originally prescribed acceptance prompts.

The exhausted controlled process was stopped after verifying its identity, and the ordinary review backend was restored. Final status and unchanged accounting are saved in `status-final.json`; the historical rate-limit snapshot and sanitized task metadata are retained in `acceptance-status-before.json` and `acceptance-summary.json`. No quota entries, reservations, credentials or approval records were reset or rewritten.

The established Milestone 6 preservation manifest was reused: **all 10,267 original development-database rows and schemas are exactly unchanged**. All **3 pre-existing assistant history/accounting rows are exactly unchanged**, including their JSON payloads. Evidence: `milestone-preservation.json`, `assistant-history-preservation.json` and retained hash baseline. Original CAD/model/solver/storage content was not edited; the prior full artifact manifests remain available, and their entire archive was not rehashed for this UI-only change.

No engineering formulas or method support changed. No Git operation, additional agent, paid inference, deployment, Firebase action, destructive cleanup, credential-file edit or new package was used. Build caches and local operational logs were refreshed. Work stops after this UI improvement.

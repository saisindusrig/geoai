# GeoAI Engineering Copilot — Milestone 1

Local review: [Project 793](http://localhost:3001/projects/793/workspace). The existing frontend runs on port 3001; port 3000 was unavailable. The review page is left open in the in-app browser. Work stops here for review.

## Audit and scope

[Initial audit](audit.md), captured before implementation, identified generic unsupported analysis answers despite saved OpenSees records, hidden context, a fixed Assistant width, ambiguous cloud/model labeling and poor fetch-error recovery. Existing conversation persistence, idempotency, proposal review, engineering forms and authorization were retained.

The new workflow is explicitly **ENGINEERING_OFFLINE**. It reads actual saved evidence and generates deterministic fixture responses. It is not a live LLM, and its tests do not establish GLM reasoning quality. Existing Nebius credential, budget and execution controls remain in place; no paid inference was requested.

## Implemented

- Project, saved revision and selected component context, including dimensions, ENU position, orientation, appearance and declared section/material provenance.
- Explanations of saved load cases, slab transfer and stored bending-moment extrema, with units, record references, solver version, staleness and unsupported conditions.
- Persistent user/assistant turns and operation progress using the existing conversation/run storage. Technical snapshots, source hashes and captured component IDs are expandable.
- Missing-input groups and navigation to existing inspect, CAD, input and result tools. Navigation waits for asynchronous forms; saved diagrams are opened by exact analysis/revision identity without a new solve.
- Resizable Assistant with local width persistence. Selecting objects while chatting updates context without automatically replacing the Assistant with the inspector.
- Frame input groups: Geometry and section, Material properties, Supports and connections, Loads, Engineering assumptions; existing analysis/proposal/results sections remain separate. The connection form presents missing information first.
- Explicit GLM-5.3-Flash default and GLM-5.3 optional preference. Every new response records the requested model and labels the actual producer as a deterministic offline adapter, with actual model **none**. No escalation.
- Recovery of saved frame input forms after an initial failed read, without posting an edit or solver request.

The initial connection fixture exposed a truncated list of 150 items. The final adapter preserves all **233** saved missing inputs. Larger lists have an explicit 1,000-item display bound and total count. Earlier test snapshots remain in conversation history and are labeled as potentially incomplete; they were not silently rewritten.

## Actual browser acceptance

| Project | Observed checks | Result |
|---|---|---|
| 793, revision 103, v2 | Three analyzed members selected; column explanation; Horizontal, Gravity and Self weight loads; optional model preference; reload; saved diagram follow-up | Saved analysis 421, OpenSees 3.8.0; combined moment samples −28.809726 to 24.756664 kN·m. Optional model preference persisted on its response with actual model none. Conversation survives reload. |
| 793 | Temporary 0.5 m East move; dirty chat; undo/redo/undo; orbit while chatting | Draft marked stale, saved result actions disabled, new stale response withheld current extrema. Undo restored Saved v2. Orbit retained three members and created no edit. No model save occurred. |
| 793 | Review engineering inputs after asynchronous loading | Frame form opens to its grouped inputs; original proposal/solver controls retained. |
| 784, revision 86, v2 | Saved slab-load question; follow-up to Results; Bending Moment display | Analysis 301: 24 m², declared 5 kN/m², 120 kN applied/transferred, computed reactions approximately 120 kN. Explicit one-way allocation and excluded self-weight/plate-shell FEA. Existing frame diagram shown with −28.271072 and 22.694564 kN·m extrema. Solver checkbox remained unchecked. |
| 789, revision 98, v4 | CAD-source explanation; expanded evidence; Review CAD sources; select generated CAD column SW; return to chat | Six source mappings with DXF entity/drawing/geometry identities. Column SW 0.3 × 0.3 × 3.26 m. No matching current declared E/A/I; no material inference. |
| 788, revision 93, v2 | Blocked/missing-input questions; grouped list; Review engineering inputs; unsupported Python/safety request | Input assessment 354, 233 missing entries. Connection form remains BLOCKED_MISSING_ENGINEERING_INPUTS, shear excluded/unsupported; Run authorized actual contact calculation disabled. Script execution/design approval refused. |
| Layouts | 1280 × 900 and 1600 × 900 across all four projects; drag Assistant from 400 to 500 px | Viewer remains available; model selector, chat, input and follow-up controls accessible. Width restored to 400 px and temporary viewport override reset. |
| Recovery | Interrupted submission and conversation reads | Retry recovered the saved conversation; submission retry retained its original request/context. Local transport failures remain intermittent, described below. |

Only chat turns and ordinary existing read/download logs were added. Original engineering inputs, proposals and authorization were inspected; no original-project proposal, authorization, solver run or geometry save was performed.

## Automated checks

- **84 backend tests passed:** engineering guidance, existing Assistant runtime, Nebius configuration and environment precedence. Coverage includes project/revision scope, unknown selection rejection, saved SI units, stale result refusal, complete/bounded missing lists, offline provider exclusion, persistence/idempotency and allowed model IDs.
- **48 frontend tests passed:** persistent Assistant, exact-record result navigation, frame-read recovery, existing transforms/gesture arbitration, staged inspector edits, component identity and non-destructive analysis.
- TypeScript `tsc --noEmit`: passed.
- Targeted ESLint on changed frontend implementation and test files: passed.
- A CPU-heavy existing geometry-profile test timed out when run alongside compiler/lint jobs; the final test run used one worker and all 48 passed. Existing Vitest configuration emits a deprecation notice.
- Tests use isolated fixtures. No test contacted Nebius or solved against an original project.

## Preservation evidence

[Baseline](baseline.json) and [final preservation check](preservation-check.json) use ordered database-row SHA-256 comparisons.

- All 10 model revisions for the four review projects: unchanged.
- All 49 engineering analysis records: unchanged.
- All 8 engineering authorization/audit records: unchanged.
- Original 1,935 usage records: unchanged. One `file.download` event for project 789 was appended during review; it is not an inference event.

Source drawings, geometry files and provider credential files were not edited. No migrations, backend engineering schema changes, new numerical methods, GitHub operations, commits, deployment or installations were performed.

## Browser screenshots

Before: [existing Assistant at 1280 px](before-assistant-793.jpg).

| Project | 1280 px | 1600 px / additional evidence |
|---|---|---|
| 793 | [Persistence](after-793-persistence-1280.jpg), [resized panel](after-793-resized-1280.jpg) | [Review chat](after-793-review-1600.jpg), [selected context](after-793-selected-chat-1600.jpg), [saved diagram](after-793-diagram-1600.jpg), [staleness](after-793-stale-1600.jpg), [grouped inputs](after-793-input-groups-1600.jpg) |
| 784 | [Chat](after-784-loads-1280.jpg) | [Load explanation](after-784-loads-1600.jpg), [saved diagram](after-784-results-1600.jpg) |
| 789 | [Selected CAD component](after-789-selected-chat-1280.jpg) | [CAD explanation](after-789-cad-chat-1600.jpg) |
| 788 | [Missing inputs](after-788-missing-1280.jpg) | [233 missing inputs](after-788-missing-1600.jpg), [blocked form](after-788-blocked-inputs-1600.jpg) |

[Browser frame transcript](browser-frame-transcript.txt) records the persisted explanations and the stale-draft response.

## Limitations and remaining confusion

- This milestone delivers offline evidence guidance and an explicit model preference, not a production live GLM chat deployment. Model availability, conversational reasoning and paid provider execution remain untested. Requested IDs came from the user; credentials and cloud inference were not unlocked.
- Proposal preparation, review, exact-hash authorization and execution remain in their existing specialized forms. Chat guides navigation and never performs these steps automatically. The original-project full authorization/solver cycle was intentionally not repeated.
- Intermittent `Failed to fetch` reads still occur in the local browser setup, including the CAD audit panel. The separate offline review launcher uses an explicit Windows selector loop to avoid observed Proactor accept failures; this does not establish that every transport problem is fixed. Chat Retry and frame read recovery were tested. The launcher is for offline review; other Windows async subprocess workflows were not validated with it.
- Evidence queries are bounded to 100 recent engineering records, 30 returned supported records, 100 selected objects and 100 CAD mappings. This is sufficient for these acceptance projects; larger histories require pagination in a later milestone.
- Technical evidence is still JSON-oriented. Missing paths and provenance remain engineering terminology; guided per-field editing is a future improvement. Long replies require scrolling, and navigating to Analysis temporarily replaces the Assistant panel; closing the inspector restores history.
- Agent walkthrough and responsive checks establish observed behavior, not independent first-time-user research or structural approval.

Stop for review before further milestones.

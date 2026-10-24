# GeoAI Engineering Copilot — Milestone 2

Local review: http://localhost:3001/projects/793/workspace

Status: implemented and stopped for review. Offline deterministic guidance only. No paid inference, provider credential changes, GitHub operations, commits, deployment, installation, new solver methods or schema migrations.

## Audit and fixes

| Priority | Observed issue | Change |
|---|---|---|
| P0 | CAD audit showed “Failed to fetch”; its preflight arrived, but the actual POST did not. Saved-result panels mounted many cross-origin requests. | Local review now uses the fixed same-origin `/local-api` proxy. GETs no longer send unnecessary JSON Content-Type headers. Backend ownership, revision checks and authorization still execute unchanged. |
| P0 | Starting the frontend before the backend finished initialization produced connection-refused failures. | Added `start-copilot-review.ps1`, which waits for local backend health before starting the frontend, with a finite startup limit. Local proxy failures now explain how to recover. |
| P1 | A read helper cloned every response body and retried transport failures automatically; context failures polled indefinitely. | Removed the cloned-body read and automatic transport retry. Assistant context polling stops on failure and exposes explicit Reconnect. Message Retry retains the existing request ID and frozen context. |
| P1 | Long responses repeated raw paths and source IDs. | Short presentation summaries, expandable complete saved explanations, and collapsed technical evidence. Slab summaries retain the saved pressure, area and total load. Existing stored responses are not rewritten. |
| P1 | 233 missing requirements were hard to act on. | Grouped by connection geometry, contact properties, assumptions and each individual anchor; suggested entry steps, source prerequisites, and a next-requirement action. This order is explicitly data-entry guidance, not structural risk or solver approval. |
| P1 | Inspect used the current selection rather than the explanation’s captured selection. Input navigation could fire before saved forms loaded. CAD navigation assumed a wrapper that project 789 does not have. | Inspect restores the captured component IDs atomically after project/revision checks. Input links wait for the saved record, check its exact ID, choose the correct anchor and focus the field. CAD navigation also supports the directly mounted source panel. |
| P2 | Auto-scroll could hide the start of an answer; resize cleanup missed focus loss. | Jump to latest positions the start of the latest message; older-message loading preserves scroll position. Resize sessions finish on pointer cancellation, focus loss and unmount. Context loading has a visible status. Offline model metadata is compact, with full provenance in Technical evidence; the context disclosure no longer clips its summary. |
| P2 | “reconnection” accidentally matched “connection” in deterministic routing. | Word-boundary matching plus a regression test. A new browser question confirmed the correct CAD-reference response. Historical responses remain preserved. |

## Fetch investigation: findings and limits

1. **Confirmed service-unavailable cause:** local requests produced `ECONNREFUSED 127.0.0.1:8001` while the backend was stopped or initializing. This was reproduced deliberately. The readiness launcher addresses cold startup; explicit recovery addresses a later outage.
2. **Confirmed failing path:** before the transport change, project 793’s CAD frame audit displayed “Failed to fetch.” The server recorded OPTIONS but no audit POST. A direct local preflight returned valid origin/method/header allowances, so an incorrect basic CORS allowlist was not established. After routing review traffic through the frontend origin, the same audit POST reached the backend with 200 and the browser displayed its actual geometry audit. The automatic GET retry was removed during verification.
3. **Unnecessary preflights:** the shared client sent JSON Content-Type on bodyless GETs. This header was removed. Authentication headers remain intact and can still legitimately require preflight outside local review.
4. **Previous Windows issue:** the existing explicit Selector event-loop launcher is retained. Earlier Proactor accept failures were documented in Milestone 1; this milestone does not present that previous mitigation as a newly discovered fix.
5. **Diagnostic limit:** the precise browser/network reason the earlier cross-origin preflight did not progress to POST cannot be uniquely determined from the available logs. The failing cross-origin review path has been removed and the replacement tested. This is not a claim that every possible network failure is eliminated. Existing request logs record response-header success before full body delivery, so browser-visible results were used as acceptance evidence.
6. One CSS chunk load failed during initial development startup; reload recovered. It did not recur in the stable-build acceptance workflows. Development hot reload during an outage can remount the page; the final outage test was repeated without code edits.

## Browser acceptance

Real in-app browser interactions, not mocked browser screenshots. Projects were inspected at both 1280 px and 1600 px widths.

| Project | Actual checks and outcome |
|---|---|
| 793 | Saved revision 103, analysis 421, OpenSees 3.8.0. Audit now loads. Chat opens the exact saved bending-moment diagram, −28.809726 to 24.756664 kN·m. Inspect restores the captured three CAD members. Assistant context shows their readable names. Visible Orbit drag preserves selection; Fit model works. Assistant resized from 320 to 420 px at 1280 px without obscuring the whole viewport. |
| 784 | Saved revision 86, analysis 301. Concise summary reads 5 kN/m², 120 kN over 24 m², one-way load transfer only. Open saved results opens record 301; Show Results displays its existing frame diagram. Stored bending-moment extrema remain −28.271072 / 22.694564 kN·m. |
| 789 | Saved revision 98. Six generated CAD identities remain available. Selecting CAD column SW selects source entity `dxf:614f117ae2a74794:9C`; Assistant context updates to CAD column SW. CAD source navigation, saved history reload, offline labeling and both desktop widths passed. |
| 788 | Saved revision 93, blocked input 354. All 233 requirements are represented: geometry 5, contact 21, assumptions 11, and 49 for each of four anchors. The next requirement is displayed before the explanation and technical metadata; its button is also visible at 1280×720. It focuses Saved geometry evidence category. Anchor 2 material link selects index 1 and focuses Anchor material identification, with the exact saved path shown. Authorization/run remains disabled. No engineering inputs were saved or supplied. |
| 795 — existing isolated QA | QA steel beam East position 1.5 → 1.6 m: Preview, Apply, Undo (1.5), Redo (1.6), Save revision 116/v5, reload confirmed 1.6. Restored 1.5 and saved revision 117/v6. Final component definitions equal the original QA revision 109. Original engineering projects were not saved. |

### Network recovery

The finalized frontend was tested with the offline backend deliberately stopped. The typed draft remained visible; submit returned actionable recovery text; context refresh stopped and displayed Reconnect. Before Retry, the test phrase had zero saved user messages. After the backend was restored, Reconnect and Retry created exactly one user message and one response. Reload retained the conversation. A later, independent send of the same wording tested the routing correction; that is a second deliberate request, not an automatic duplicate.

## Automated validation

- **54 frontend tests passed across 11 files.** Assistant persistence/context, exact analysis navigation, requirement ordering, no automatic read/mutation retry, explicit recovery, async exact-record/anchor navigation, stale record rejection, resize cleanup, existing transform/selection behavior, staged Apply/Cancel, and component identity.
- **85 backend tests passed.** Offline guidance, routing correction, Assistant runtime, Nebius configuration and environment precedence; provider-forbidden fixtures remain in place.
- TypeScript `--noEmit` passed.
- Targeted ESLint passed for changed frontend source and focused tests.
- PowerShell launcher parsed without syntax errors. Its server-start commands were exercised during review; the launcher as a complete fresh-session workflow was not separately relaunched against occupied ports.
- All testing used existing dependencies. Backend tests used isolated fixture storage and no actual inference.

## Preservation

See [machine-readable check](preservation-check.json) and [baseline](baseline.json).

- All **509 existing engineering analysis rows** unchanged; no new analysis rows.
- All **115 original model revision rows** unchanged. Only QA project 795 gained revisions 116 and 117.
- All **144 original message rows** unchanged. Five intentional offline test exchanges appended ten message rows.
- All **1,936 usage rows** unchanged; no inference usage events added.
- All 96 original engineering audit events unchanged; two QA save audit events appended.
- The 119 conversation records remain; sequence/update metadata advances for conversations receiving the new test messages. Conversation metadata is therefore not byte-identical, and is not claimed to be.
- Rendering, numerical algorithms, source drawings, component identities, authorization implementation and provider credentials were not changed. Existing permission gates remain active.

## Screenshots

“Before” images for 784, 789 and 788 are the accepted Milestone 1 browser captures, reused explicitly as the prior state rather than recreated after editing. Project 793 also has a fresh Milestone 2 baseline and the actual fetch-failure capture.

| Project / width | Before | After |
|---|---|---|
| 793 / 1600 | [Fresh baseline](before-793-1600.jpg) | [Short response and selected context](after-793-review-1600.jpg) |
| 793 / 1280 | [Prior accepted state](../copilot-milestone-1/after-793-persistence-1280.jpg) | [Resizable chat](after-793-resized-chat-1280.jpg) |
| 784 / 1600 | [Prior accepted state](../copilot-milestone-1/after-784-loads-1600.jpg) | [Load summary](after-784-load-summary-1600.jpg) |
| 784 / 1280 | [Prior accepted state](../copilot-milestone-1/after-784-loads-1280.jpg) | [Load summary](after-784-load-summary-1280.jpg) |
| 789 / 1600 | [Prior accepted state](../copilot-milestone-1/after-789-cad-chat-1600.jpg) | [Correct CAD reply](after-789-fixed-cad-reply-1600.jpg) |
| 789 / 1280 | [Prior accepted state](../copilot-milestone-1/after-789-selected-chat-1280.jpg) | [Correct CAD reply](after-789-fixed-cad-reply-1280.jpg) |
| 788 / 1600 | [Prior accepted state](../copilot-milestone-1/after-788-missing-1600.jpg) | [Short answer and requirements](after-788-short-answer-1600.jpg) |
| 788 / 1280 | [Prior accepted state](../copilot-milestone-1/after-788-missing-1280.jpg) | [Next requirement](after-788-short-answer-1280.jpg) |

Additional evidence: [compact 1280×720 layout](after-788-compact-1280.jpg), [fetch failure before](before-fetch-failure-793.jpg), [audit after](after-793-audit-loaded-1600.jpg), [frame diagram](after-793-diagram-1600.jpg), [slab diagram](after-784-diagram-1600.jpg), [exact geometry field](after-788-exact-input-1600.jpg), [anchor 2 field](after-788-anchor2-input-1280.jpg), [network outage](network-outage-final-789-1600.jpg), [recovery](network-recovered-789-1600.jpg), [QA reload](qa-save-reload-1600.jpg).

## Remaining limits for review

- The Assistant remains a deterministic saved-data adapter. GLM preferences are recorded, but no GLM model produced these offline responses. Fixtures do not validate actual model reasoning.
- The full low-level cause of the earlier browser preflight transport interruption remains unconfirmed; the tested same-origin review path avoids it.
- The requirements order is suggested entry guidance. It cannot supply missing engineering evidence or establish physical adequacy.
- Exact field focus is implemented for the existing connection-input schema; other supported workflows navigate to their existing saved form/result sections. Unsupported analysis and design approval remain unavailable.
- Earlier persisted wording, including the old truncated snapshot and pre-fix routing response, remains in history. New presentation warns about incomplete older snapshots and preserves the complete original text.
- Temporary viewport overrides were used for acceptance and are reset after capture. Stop here for review; no next milestone started.

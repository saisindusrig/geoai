# GeoAI Milestone 7

Completed locally on 23 October 2026. Stop at Milestone 7; no deployment or live inference acceptance was performed.

## Working behavior

The existing Nebius assistant now exposes strict, bounded adapters for owned-project opening, paginated saved-component discovery, exact-ID selection, camera focus, saved-property reads, model/site presentation, current saved-result discovery, exact-case evidence reads, and supported saved-result display. The application revalidates ownership, current revision, document digest, result identity, method and load case. Dirty drafts, previews and comparisons block workspace actions. Unsupported, missing and stale evidence does not trigger a calculation or substitute another result.

Workspace tool responses are prepared receipts. Selection confirms after editor state updates, camera focus confirms after its flight completes, and result display confirms through the real renderer. Frontend outcomes are retained separately from existing assistant billing/history records. Failed and unconfirmed actions are distinguished from completed actions. Reopening history does not replay actions. Existing position Preview → Apply → Save remains separate and unchanged.

Latest task status and current inference availability are separate. Disabled inference explicitly blocks new messages while retaining history. Technical evidence remains collapsed. Multi-step activity follows actual validated operations.

## Viewer findings and fixes

Project 804, revision 124, contains 56 visible saved box/cylinder components. It is not an empty model. It has no eligible current engineering results in its recorded capability baseline.

Confirmed failure paths addressed:

- Result isolation from another project/revision could hide geometry; overlays are scoped to their saved source, with a Restore full model control.
- Primitive readiness could precede camera completion and produce an apparently empty scene. Saved-model readiness now waits for camera framing.
- A repeated result render could lose its camera fit while still acknowledging display. Assistant-requested saved results explicitly refit their authoritative visual geometry.
- An ordinary editor rerender could cancel an in-flight project-open validation. Validation now checks current committed project/revision/draft state. A genuinely changed revision still rejects the action.
- Failed saved-model loading could fetch a legacy GLB. The saved-model editor now avoids that fallback, keeps the loading error visible, and offers Retry saved model.
- Historical prepared actions could show Completed without frontend receipts. They now show Awaiting workspace confirmation.

The viewer distinguishes loading, empty component lists, all-hidden components, camera-outside-model state, saved-result isolation, saved-model read failure, CAD mesh failure and renderer failure. No original geometry was changed.

## Verification

- Backend: 68 focused tests passed, using mocked provider behavior and temporary test databases. Evidence: `backend-fresh.log`.
- Frontend: 56 focused tests passed across six files; the final hook implementation additionally passed its five targeted tests. Evidence: `frontend-fresh.log`, `race-fresh.log`.
- Browser: six fresh Chrome checks passed. Selection, focus, exact result 421 / revision 103 / frame / Horizontal moments and deformation, project 804 navigation, empty and hidden models, failed-load recovery, disabled messages, no history replay, no unexpected mutation requests, and no JavaScript errors. Tests used mocked provider events with real validation and saved geometry/results. Evidence: `browser-fresh.log`, `browser-1280.json`, `browser-1600.json`.
- Screenshots at 1280×900 and 1600×900 were visually inspected with the assistant open: `moments-*.png`, `deformation-*.png`, `project-804-*.png`, `load-error-*.png`. Empty/hidden fixtures have separate screenshots.
- Scoped lint passed; TypeScript and production build evidence are in `lint-fresh.log`, `typescript-fresh.log`, and `build-fresh.log`. Webpack was used after a Turbopack CSS subprocess failure. No dependencies were installed.
- No paid provider request, model escalation, paid retry, solver run, geometry save, result generation, import, export or settings mutation was part of acceptance. Mock assistant outcome persistence was tested without changing original assistant accounting.

## Preservation

All 10,267 original database rows and schemas remain intact. All 55,296 original storage files and 2,090 engineering proof files match retained manifests. The archive audit reads the existing compressed backup without extraction/restoration. Existing assistant history/accounting fingerprints are unchanged. Prior coupled solver artifact hashes were rechecked.

Exception retained transparently: the first loading-error browser fixtures caused two automatic legacy-GLB reads, appending two `file.download` usage events to `usage_events`. The final database has 10,269 rows. These append-only accounting events were not deleted or rewritten. The viewer fallback was fixed; final browser tests explicitly reject such GLB reads. No original row was removed or changed. See `milestone-preservation.json`, `preservation-audit.json`, `assistant-history-preservation.json`, and `coupled-evidence-preservation.json`.

## Unsupported operations and limits

- Arbitrary CAD creation, automatic building generation, arbitrary geometry edits and engineering execution from chat.
- New analyses, automatic result regeneration, stale result substitution, inferred material/support/load declarations, safety certification or design approval.
- Foundation deformation and frame slab contours; other modes without actual supported visual geometry fail with the existing results workflow as the next step.
- Ambiguous names such as “left column” require discovery and disambiguation; an invented component ID is rejected.
- Unsaved drafts, active geometry previews/comparisons, cross-owner projects, mismatched revisions, document/result hashes or load cases are rejected.
- Existing inference orchestration remains bounded to three tools per turn. Discovery and action can require separate turns. No live model quality claim is made: inference stayed disabled, and all new provider events were mocked.

No Git operations, parallel agents, deployment, billing changes, migrations, cleanup or installations were used.

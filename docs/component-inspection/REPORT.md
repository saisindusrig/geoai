# Intuitive model inspection and Layers — local review

Website: http://localhost:3001/projects/793/workspace (also 794 and 788).

## Implemented

- Shared display-only names: Column NW, Beam North, Slab, Footing SW, Base plate SW, Connection SW and Stair 01 · tread, Stair 02 · tread. Tread numbering comes from stable source indices, not guessed construction labels. Existing CAD prefixes and authored names remain distinguishable. Stable IDs and stored names are unchanged; full IDs are available in tooltips/Inspector.
- Layers searches readable names, original names, stable IDs, categories and CAD source records. Filters: All, Selected, Visible, Hidden and Locked. Structural bracing, plates and connections join the structural group. Selected groups expand; a Reveal selection action recovers selections outside the active search/filter.
- Inspector shows the same selected member name, dimensions, position, role, stable identity, geometry source, appearance and explicitly unverified engineering material status. Existing preview/apply editing and assembly restrictions remain. Actions include focus, existing analysis, isolate, hide and visibility restore.
- A genuine browser failure identified that canvas selection preserved an already-open Layers tab. The selection handler now explicitly opens Inspect. Another failure exposed that hiding clears selection: the empty Inspector now retains Restore visibility. Hidden selection is deliberately cleared by the existing editor; selecting a member again is explicit.
- Isolation and visibility restoration preserve the original visibility map, including previously hidden objects. Nested isolation restores the original snapshot. Show selected/Show all and normal undo remain available. Restore previous visibility is scoped to the current workspace session; saved visibility remains part of the existing model editing workflow.
- Expandable envelope-overlap warnings identify pairs and allow selecting them for review. Exact identical geometry/transform definitions are identified separately as duplicate geometry. Envelope intersection is conservative, not a solid-clash test, a verified connection or a capacity check. Touching boundaries alone are excluded. Unsupported/unavailable external mesh geometry is not certified by this check. Nothing is deleted, moved or automatically connected.
- Toolbar guidance explains selection modifiers, geometry-changing actions, axes, undo and possible analysis staleness.

## Verification and preservation

- Full frontend suite: **324 passed across 64 files**. Full evidence: frontend-results.json. This includes naming/identity and envelope tests, tests restoring initially hidden members, and the existing editor, Copilot, camera, analysis and permissions regressions.
- TypeScript no-emit checking passed.
- Actual Chromium workflows: **three baseline and three final cases passed**, projects 793, 794, 788 at 1280x900. Final cases exercise readable stair selection, Inspector fields, isolate/restore, hide/restore after selection clears, selected filtering, focusing, actual canvas hover/click and automatic Inspector opening.
- Browser assertions were retained during fixes. An initial test incorrectly expected hidden selection to remain selected; it now explicitly reselects after restoring visibility. The separate assertion requiring a canvas click to open Inspect caught the actual tab-handler bug and passes after the fix.
- Consistent pre-work database backup: .cache/component-inspection/dev-before.db. Final comparison: **10,143 original rows unchanged, no additions or deletions**, including original visibility, projects, components, FEA evidence, conversations, permissions and revisions. See preservation.json.
- Browser visibility operations create reversible local draft edits through the existing editor. They were restored and were not saved to the original projects; therefore no new project revisions or analysis records were created. Draft indicators can remain until the local editing session is discarded, even after restoring the same values.

## Genuine screenshots

The screenshots directory contains before-{project}-layers.png and after-{project}-layers.png for all three projects, plus after-{project}-inspector.png and after-{project}-canvas-inspection.png. The former Inspector captures show the original saved state; canvas-inspection captures follow reversible visibility edits and correctly show the draft state.

No rendering redesign, camera-method changes, FEA methods, engineering defaults or authorization changes. No Git operations, installs, deployment or paid inference. Engineering approval remains disabled.

**Stopped for visual review.**

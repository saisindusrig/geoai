# GeoAI UX milestone 2 — local review

Review: http://localhost:3000/projects/793/workspace

## Audit and focused changes

The audit preceded implementation and used current browser captures in projects 793, 789 and 784. See [audit](audit.md).

1. Model review — usable, weak visual hierarchy. Added role-based illustrative finishes, soft key/fill lighting and restrained specular response. Thin geometry edges remain; selected outlines use muted blue. Removed mesh selection labels and hid dimensions by default with an explicit toggle. Existing shadow support remains renderer-dependent.
2. Selection and editing — confusing automatic edits. Selecting a member opens its inspector, with readable name, role, metre dimensions, East/North/Up position, orientation, revision status and appearance/material distinction. Inspector fields now stage changes; Preview does not alter the document, Apply submits one patch through the existing editor gates, and Cancel discards pending values. Invalid fields block partial Apply. Untouched rounded displays preserve exact coordinates.
3. Camera and panels — discoverability and overlap. Added Isometric, Top, Front, Side, Fit model and Fit selection. Kept Model/Site separate and retained the user's orbit inversions. Automatic inspection briefly waits for double-click arbitration and retains the first picked identity through viewport resizing. Inspector width is adjustable. Browser testing exposed a covered resize target; it was corrected and verified from 344 to 444 px.
4. Drawing review — initial recoverable load failure. CAD evidence subsequently loaded with 73 source entities. Source outlines, existing generated components and source identity now have distinct labels. CAD focus no longer draws duplicate cyan envelopes and labels over every component. Create/Import closes after choosing an action; retry errors provide a recovery instruction and expandable diagnostic.
5. Saved results and saving — hard to discover. Added result-section shortcuts and Workflow help. Member node/force evidence is collapsed by default. Removed the workspace inspector's duplicate model-save button; site-save and model-save have explicit scope explanations. Assistant has a visible label and retains its supported next actions without making engineering-verification claims.

## Actual browser checks

| Check | Evidence / outcome |
| --- | --- |
| 793 single selection, hover, empty selection | Friendly hover and muted selected member; automatic inspector; no edit history from selection. |
| Overlapping selection | 793 context menu named Platform slab, CAD slab and CAD beam South; selecting CAD slab then Inspect showed its actual synthetic material declaration separately from the concrete-style appearance. |
| Multi-selection and rectangle | Shift click selected two QA objects; a rectangle selected 48 intersecting bounds in 793. Fields explicitly edit the primary member; viewport transforms operate on the group. |
| Camera | Named Top, Front, Side, Isometric and double-click fit exercised. Visible Orbit/Pan drags and pointer wheel changed the camera while saved state and selection remained intact. |
| Inspector edits | 793 column width 0.300 → 0.350 m: preview remained Saved v2; Apply produced one undo; Undo/Redo/Undo restored Saved v2. No original revision was saved. Cancel discarded a later pending edit. |
| Invalid dimensions | Negative Y dimension plus a valid X edit could not partially Apply. Error explained recovery; Cancel restored both fields; original project remained Saved v2. |
| Transform interaction | QA X handle drag created one undo operation. Numeric G → X → 2 preview canceled with Escape without a commit; Enter created one edit, reversed by one Undo. |
| CAD mapping | 789 source 9C reported Already generated. Selecting generated CAD column SE linked source AE. Authorization and geometry-only acknowledgments remained in place; no new CAD proposal or authorization was submitted. |
| FEA diagram | 784 saved moment diagram displayed and fitted; clicking its beam selected the member and exposed existing solver inspection. No solve was run. |
| Save / reload | QA project 795 saved v4 and browser reload retained steel beam size 3 × 0.4 × 0.75 m, position [1.5, 0, 0.5], orientation [0,0,0], scale [1,1,1]. This is the only saved model change in this milestone. |
| Desktop layout | Current browser captures of 789, 793 and 784 at 1280×720 and 1600×900; inspector scrolls and model viewport remains usable. |
| Assistant | Opened and closed its next-step guidance. No prompt was sent and no paid inference was used. |

The visible Orbit/Pan controls exercise the same navigation controller. Physical held-middle-button drags were covered by existing gesture tests, not independently exercised with a hardware mouse in this run. Rotation/scale math, CAD rigid-transform restrictions, attachment checks, gesture cleanup and history behavior retain their existing test coverage; not every combination was retested live.

## Preservation and automated checks

- TypeScript `tsc --noEmit`: passed.
- ESLint on changed source/test files: passed.
- 73 focused tests across nine suites passed: inspector staging/invalid values, numeric confirmation, presentation immutability, navigation arbitration/double-click, transforms, editor gates/history and workspace tools. The final two changed suites were rerun after the last interaction fixes.
- Original projects' 8 model revisions, 46 engineering-analysis records and 6 authorization/audit events match the pre-edit row hashes exactly. See [preservation check](preservation-check.json). Geometry and drawing references embedded in those saved documents remain identical.
- No backend or schema code was changed. No GitHub operations, commits, deployment, installation or new analysis method.

## Walkthrough and remaining friction

This was an agent walkthrough using visible workflow controls, not an independent novice user study. Create/Import → Review CAD drawing opened the existing source; Review 3D and a member click exposed the inspector; staged editing, saving in QA and Analyze/Results completed the supported path. The UI now explains Apply versus Save and numerical verification versus unsupported engineering checks.

Remaining: engineering input panels are still lengthy; attachment edits require opening Assembly tools and parameters; rectangle selection intersects screen bounds and does not fully exclude occluded parts; front/side views are shallow perspective elevations rather than a separate orthographic CAD camera. Appearance is illustrative, and shadows depend on scene settings and GPU support. Intermittent local CAD fetch failures were observed and recovered, but their underlying service/network cause was not established. Some small tool icons and provider labels still need a later accessibility/content pass. No new drawing upload, engineering authorization or human first-time-user study was performed.

## Browser screenshots

| Project / workflow | Before 1280 | After 1280 | Before 1600 | After 1600 |
| --- | --- | --- | --- | --- |
| 793 model | [Before](01-before-793-1280.jpg) | [After](05-after-793-1280.jpg) | [Before](01-before-793-1600.jpg) | [After](05-after-793-1600.jpg) |
| 789 drawing | [Load failure](03-before-789-1280.jpg) | [CAD review](07-after-789-1280.jpg) | [Load failure](03-before-789-1600.jpg) | [CAD review](07-after-789-1600.jpg) |
| 784 results | [Before](04-before-784-1280.jpg) | [After](08-after-784-1280.jpg) | [Before](04-before-784-1600.jpg) | [After](08-after-784-1600.jpg) |

Additional captures: [old inspector](02-before-inspector-793-1600.jpg), [new inspector](10-inspector-793-1600.jpg), [1280 inspector](10-inspector-793-1280.jpg), [unapplied preview](06-preview-793-1600.jpg), [double-click focus](11-double-click-focus-793-1600.jpg), [invalid edit recovery](13-invalid-edit-793-1600.jpg), [QA reload](09-qa-reload-1600.jpg), [Assistant](12-assistant-793-1600.jpg), [overlap chooser](14-overlap-793-1600.jpg), [CAD material inspector](15-cad-inspector-793-1600.jpg).

Captures show real browser states, including the initial CAD load error and a resize transition in the 784 before capture; they are not pixel-matched camera comparisons. Work stops here for milestone review.

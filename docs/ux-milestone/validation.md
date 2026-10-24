# GeoAI UX milestone — local review

Completed 14 October 2026. Main workspace: http://localhost:3000/projects/793/workspace

## Implemented

- Isolated Model view with close initial framing; Site view retains geographic context. Camera refits when display placement resolves, without changing engineering coordinates.
- Lit surfaces with roughness/metalness finish, material-name appearance tints, mesh silhouette edges, selected edges, real hover feedback and fit selection.
- Distance-limited, offset platform dimensions. Analysis diagrams suppress unrelated geometry and dimensions and remain visible through solid members. Stored diagram values and display scaling formulas are unchanged.
- Bundled installed Cesium widget CSS rather than a separate fragile stylesheet load. Guarded destroyed-viewer cleanup and added explicit 3D retry.
- Viewport first, Assistant closed by default, inspector space reserved at desktop sizes, and one visible side panel at a time. Assistant has an explicit Close action.
- Visible Site → Create/Import → Review 3D → Edit → Analyze/Results → Review → Save model actions. Existing import, creation and authorization workflows are retained.
- Inspector summary: component name, role, dimensions in metres, appearance-only status and fit/move actions. Source identities and assembly tools remain accessible in disclosures.
- Advanced numerical tools and evidence collapsed by default. Draft, Needs Inputs, saved revision and existing stale/verified solver states derive from actual state. No whole-project engineering approval badge is invented.
- Exact Undo back to the saved document clears the dirty flag; Redo restores the draft state. This avoids falsely stale results after a fully reverted edit.
- Assistant provides Find a component and Inspect saved results navigation. Removed the unconditional cloud-provider claim. No inference was sent during this milestone.
- Bounded retry on read transport failures, including interrupted response bodies. Mutations and solver requests are never automatically retried. CAD evidence and 3D loading have explicit recovery controls.

## Real browser validation

- Audited 793, 789 and 784 before implementation.
- 793: layer selection, direct 3D object inspection, fit selection, beam move 3.0 → 3.5 m, exact Undo/Redo, then Undo without saving the original project.
- Real hover: a visible column shows its name, pointer cursor and highlight; saved revision remains unchanged.
- Camera: top orientation, real viewport drag, Fit model and Model/Site switching. Model state remains saved during camera changes.
- 789: original DXF plan with 73 entities beside generated 3D; selection of source 9C retains dxf:614f117ae2a74794:9C. Direct 3D column selection matches the source identity. No CAD proposal was applied or authorized.
- 784: saved displacement, axial, shear, moment and reaction diagrams switch to their matching modes. The one-way slab record still reports 120.000 kN applied, 120.000000 kN reaction, and residual −2.842e−14 kN. Bending moment extrema remain −28.271072 / 22.694564 kN·m.
- Stale gating: a reversible component-name edit shows Draft and hides stale plots. Exact Undo restores Saved v2 and the verified revision-86 result.
- Existing geometric constraints: moving a connected platform beam is rejected with “The referenced beam must touch the column top at this joint.” The model remains unchanged.
- Save/reload: separate local project 795, “[Local UX QA] Save and reload validation”, contains four visual QA objects. The real Save model action created revision 2; the 0.5 m move survived reload. Original projects were not used for persistence testing. This clearly named QA project is retained for inspection.
- Assistant: open, useful next actions, switching between Assistant and inspector, and Close. One side panel is visible at a time. No message or paid AI operation was sent.
- Desktop: actual DOM viewport dimensions checked at 1280 × 720 and 1600 × 900. No horizontal document overflow. CAD and FEA screenshots captured at both widths.

## Checks and preservation

- 71 tests passed across 8 targeted suites: editor, transforms, tool rail, numeric confirmation, Assistant, elevation display and read retry.
- TypeScript no-emit check passed. ESLint passed with zero warnings on changed TypeScript files.
- No backend numerical implementation was edited. No solver was run and no engineering authorization was granted.
- SHA-256 checks match the earlier baseline for all 8 original model revision rows, all 46 engineering analysis rows, and all 6 engineering authorization audit rows in 793/789/784. Full row hashes include component identities, revision documents, source references and stored numerical evidence. See preservation-check.json.
- Local development only. No GitHub operations, commits, deployment, paid inference or dependency installation.

## Remaining for review

- The legacy /model viewer still uses the older terrain/layer interface; use /workspace for this milestone.
- Complex CAD labels and long generated attachment names need a later focused pass.
- Initial local API/assets or external map-provider loading can still require Retry. Recovery is now explicit and bounded; availability is not certified.
- Some icon tools still rely on tooltips. Generated assemblies must be edited through their existing parametric/authorization controls.
- Independent beginner comprehension has not been tested with a human participant. The visible workflow and next actions are ready for your review.

## Screenshots

- before-793-1280.jpg and after-793-1280.jpg: matching project and desktop size.
- before-789-1280.jpg: initial workspace; after-789-cad-1280.jpg and after-789-cad-1600.jpg: CAD plan and 3D review.
- before-784-1280.jpg and before-784-1600.jpg: initial viewport and analysis layout.
- after-784-displacement-1600.jpg, after-784-moment-1600.jpg and after-784-moment-1280.jpg: saved solver diagrams.
- after-cad-selection-1600.jpg: source-linked direct selection.
- qa-save-reload.jpg: isolated save/reload evidence.

Engineering appearance is not material certification, FEA evidence or safety approval. Stopped after this milestone for user review.

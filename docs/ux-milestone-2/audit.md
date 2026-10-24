# Milestone 2 — current-browser audit

Goal: open a drawing, understand the 3D model, inspect/edit a member, save, and inspect existing results. Captures are from this run at 1280/1600 px.

1. **Open workspace / review model (793): usable, presentation weak.** The model is framed, but slab, steel and footings share gray finishes. Dimensions are always visible. Standard named views are missing; the axis gizmo requires interpretation. See 01-before-793 screenshots.
2. **Select and inspect (793): usable, confusing editing.** Selection adds bright lime edges/text. Inspector leads with platform-deck / Generated material and tiny coordinate residuals. Fields apply on blur without a Preview/Apply distinction. Three model/site save locations compete. See 02-before-inspector-793-1600.
3. **Open drawing (789): recoverable blocker.** Create/Import stays open after its action. Drawing evidence displayed Failed to fetch with a Retry control; the failure prevented initial source inspection. Model revision remains Saved v4. See 03-before-789 screenshots.
4. **Open existing results (784): supported, hard to discover.** Analysis requires two nested expansions before saved results. Numerical verification and exclusions are truthful; the initial inputs/proposal text is lengthy. Moment diagrams and Fit Analysis work. See 04-before-784 screenshots.

Priority: staged editing with clear actions; role-based display finishes and restrained selection; named views/annotation toggle; useful component summary; single model-save action plus clear site-save explanation; adjustable inspector; CAD source/generated labels and recovery copy.

Visible accessibility concerns: small icon targets rely on tooltips; inspector precision text is difficult to scan; selected label/outline density obscures geometry. Keyboard/screen-reader completeness and independent beginner success cannot be established from screenshots alone.

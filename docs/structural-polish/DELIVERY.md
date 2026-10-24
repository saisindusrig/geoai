# Structural 3D visual polish

Open [project 793](http://localhost:3001/projects/793/workspace) or [slab project 794](http://localhost:3001/projects/794/workspace) and select **Analysis**.

## Before and after

- Bending, 1600 px: [before](before-793-forces-1600.png) / [after](after-793-forces-1600.png).
- Shear, 1280 px: [before](before-793-shear-1280.png) / [after](after-793-shear-1280.png).
- Axial, 1600 px: [before](before-793-axial-1600.png) / [after](after-793-axial-1600.png).
- Slab, 1280 px: [before](before-794-slab-1280.png) / [after](after-794-slab-1280.png).
- Foundation, 1600 px: [before](before-814-foundation-1600.png) / [after](after-814-foundation-1600.png).
- [81-second real-browser recording](visual-polish-demo.webm), 1600 × 1000. [Playback metadata](video-metadata.json), [actual video frame](walkthrough-frame.png).

The complete paired captures cover all seven modes at 1280 and 1600 px, including supported slab and isolated synthetic foundation evidence. Unsupported views retain their existing warnings and actual CAD context.

## Visual changes only

- Camera distance follows the viewport's limiting field of view and displayed geometry bounds, including slab regions and diagrams. The analyzed structure is larger and centrally framed.
- Bending uses amber ribbons, shear uses cyan combs and axial force uses violet dashed ribbons. The original centreline is thin dashed grey; computed deformation remains lime.
- Force legends state signed units, the existing per-frame normalization and the equivalent display offset. These display scales are not physical displacement or stress contours. Actual deformation retains its explicit magnification and unscaled mm values.
- Labels use measured text bounds and collision-aware placement. Selected components take priority. Crowded labels yield to selectable yellow markers; full saved values and component names remain available on selection and in the inspector. Warning reasons are retained verbatim. Labels appear after animated framing settles rather than competing during camera motion.
- Camera changes animate over 0.5 seconds. Unsupported modes preserve the CAD view rather than hiding it. Structural/foundation view ownership and restoring visibility remain read-only display operations.

## Verification

- **Seven browser workflows passed**: [verification](browser-release.log) covers all seven modes at 1280/1600 px, three source projects, force-type legends, collision boxes, picking, load cases, visibility restoration and isolated foundation handover. All modifying HTTP requests are blocked.
- **357 frontend tests passed across 73 files**: [regression](frontend-release.log). The final display batching also passed all 14 targeted tests: [log](targeted-release.log). [TypeScript and scoped ESLint passed](quality-checks.log).
- [Display tests](../../frontend/lib/structural-display.test.ts): perspective framing, collision-free placement with selection priority, exact warning/value text preservation and dimensional diagram scales. Existing saved-result projection/immutability tests remain in place.
- [Before capture evidence](before-capture.json), [after capture evidence](after-capture.json), [recording evidence](demonstration.json).
- The final six force screenshots additionally verify measured label boxes and clearance from force curves at both widths: [verification](force-label-verification.json). Adjacent ribbon segments are batched into a few display polygons to avoid unnecessary rendering work.
- [Database preservation](milestone-preservation.json): all 10,245 development rows and the schema are unchanged. This also matches the previous milestone baseline, including all six retained additional records.

An initial full test run under concurrent browser load hit the existing editor-profile timeout and delayed Assistant scroll-mock errors. Its log is retained as `frontend-regression.log`; the isolated release rerun is recorded separately. No unrelated Assistant or numerical implementation was edited.

No backend calculation, saved result, source identity, CAD revision, authorization rule or unsupported-analysis warning was changed. No installations, deployment, paid inference, Git operations or cleanup were performed. Work stops after visual verification.

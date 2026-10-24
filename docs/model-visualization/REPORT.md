# Professional 3D model visualization — local visual review

Open http://localhost:3001/projects/793/workspace (also projects 794 and 788).

## What changed

- The default structural camera uses actual component corner projections, view angle and viewport aspect, replacing the oversized union-sphere fit. Tight ENU component boxes also replace inflated Earth-fixed boxes for camera/selection bounds. This is display metadata only.
- **Focus Structure** fits members classified as columns, beams, slabs, stairs, bracing, connections, plates or foundations. **Fit All** fits all currently visible rendered model components. Both change the camera only. Existing visibility choices are respected; no geometry is modified or hidden. On these projects all components are structural, so both modes can produce the same view.
- Front, Side, Top and Isometric presets now use the same projected fit. When members are selected, presets orient around that selection; Fit selection supplies a close-up. Existing camera gestures remain available.
- Cooler steel, silver stairs/connections and warmer concrete-style slab/footing finishes have distinct edge contrasts and balanced studio shading. Subtle object-anchored procedural surface grain requires no image textures or remote assets. Selection uses thin cyan edges and a restrained 10% surface tint; hover tint is 12%, preserving surface detail.
- Display legend explicitly distinguishes illustrative finishes/conceptual geometry from sourced material evidence and saved computed analysis diagrams. No engineering property is inferred from a rendering finish.

## Verification

- Full frontend suite: **320 tests passed across 62 files**, zero failed/pending tests and no unhandled errors. Complete machine-readable details: frontend-results.json. Command: `node node_modules/vitest/vitest.mjs run --fileParallelism=false --reporter=default --reporter=json --outputFile=../docs/model-visualization/frontend-results.json`.
- TypeScript: `node frontend/node_modules/typescript/bin/tsc --noEmit -p frontend/tsconfig.json` passed.
- New mathematical tests independently project every box corner into front/side/top/isometric view axes at three viewport aspects and verify containment, scale behavior, role-focused framing and unchanged entity visibility/identity.
- Browser verification uses actual local Chromium/Cesium on projects **793, 794 and 788**, each at **1280x900 and 1600x900**. Six baseline cases passed before rendering edits. Six final workflows exercise default fit, Focus Structure, Fit All, every preset, saved component selection, actual canvas hover/click, member close-ups, stair close-ups and no horizontal page overflow.
- Database preservation: **10,143 original rows unchanged**, no added or missing rows. This includes model documents, revisions, analysis evidence, conversations and permissions. See preservation.json. Consistent pre-work SQLite backup: .cache/model-visualization/dev-before.db.

## Genuine screenshot comparisons

Each before/after `isometric` pair uses the same project, viewport, heading **25 degrees**, pitch **-30 degrees** and unchanged model geometry. Camera distance intentionally changes to demonstrate improved fitting; these are matching-angle comparisons, not identical camera-position comparisons. Default pairs likewise use heading 0.45 radians and pitch -28 degrees. No screenshots were synthesized or retouched.

Examples at 1280px:

- Before: screenshots/before-793-1280-isometric.png
- After: screenshots/after-793-1280-isometric.png
- Selected member: screenshots/after-793-1280-closeup.png
- Stairs: screenshots/after-793-1280-stair-closeup.png

The screenshots directory contains matching pairs and close-ups for all three projects at both widths.

## Limits and preservation

No backend or numerical solver methods changed. No new analyses, material-property defaults, engineering approvals or design-code checks. No Git operations, software installation, deployment or paid inference. Existing OpenSees evidence remains unchanged in the database.

Rendering reuses existing Cesium primitives, normals and mesh edges. Added surface coordinates cost one three-float attribute per vertex; procedural detail adds no textures or draw calls. This milestone verifies interactive browser operation, not hardware-independent frame-rate guarantees. Rendering remains an illustrative engineering viewport, not a physically measured material representation or capacity visualization. Existing overlapping/offset saved geometry remains visible as authored.

**Stopped for visual approval.**

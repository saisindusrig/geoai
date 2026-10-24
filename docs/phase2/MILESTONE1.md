# Phase 2 milestone 1: maintenance-platform parameters

Review URL: http://localhost:3001/projects/767/workspace
Existing project remains http://localhost:3001/projects/727/workspace (unchanged).

Inspect now offers length, width, local deck-top height, slab thickness, beam width/depth and column width/depth in metres. Preview draws the candidate assembly without changing the document. Apply commits all nine members as one edit. Cancel restores the displayed draft. Existing undo, redo, save and immutable revision comparison are reused. Pending previews cannot be saved, and document changes invalidate their source snapshot.

The deterministic box assembly keeps the deck centre, common horizontal rotation, column-base plane, component identities, visibility, materials, unrelated components and document metadata. It rebuilds member positions, including previous individual translations, as explicitly described in the controls. Slab bottom touches beam tops; beam bottoms touch column tops; end beams meet the inside faces of the transverse beams. Column cross sections remain inside the deck footprint. There must be positive clear spans and positive column height. All dimensions must be positive finite numbers; locked, incomplete, scaled, independently rotated or uneven-base assemblies are rejected.

Length, width and deck height appear in the Cesium viewport in metres. All member sizing is conceptual/unverified; geometric contact does not model connection details or establish structural adequacy. No analysis solver, load combinations, foundation design, drawings or further Phase 2 scope was added. This first editor recognizes the existing industrial-platform-5x3 assembly IDs only.

## Local verification

- Browser acceptance passed twice: invalid input, preview, cancel, apply, undo, redo, save, reload, persisted nine-member parameters and comparison showing 0 added / 0 removed / 9 modified; no page errors or Cesium error panel.
- Full frontend suite: 239 tests across 45 files passed with two workers. Initial unrestricted parallel run timed out in an existing terrain profile test; reduced concurrency passed without changing that test.
- Additional preview-state regression added afterward: targeted 24 tests passed, including save blocking, source immutability and stale-preview clearing.
- TypeScript and ESLint passed.
- Snapshot comparison: all original 240 project rows, 539 scenario rows and 53 model revisions unchanged. Test revisions belong solely to a new local review project.
- Before-work SQLite snapshot: .cache/phase2/dev-before.db. Original edited source copies: .cache/phase2/source.
- Local backend remains on port 8001 using the offline mock launcher; frontend on port 3001. No GitHub operations, commits, deployments or paid AI calls.

Screenshots: screenshots/platform.png, screenshots/comparison.png and screenshots/preview.jpg. The open browser has a 7.5 m unapplied preview on the review copy; the last saved test model is 7 m long. Your original model and its revisions are unchanged. Further Phase 2 work waits for review.

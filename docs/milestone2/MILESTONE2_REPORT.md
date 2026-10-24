# GeoAI Phase 2 — Milestone 2

Review the working model at http://localhost:3001/projects/768/workspace. Open **Inspect → Attached components**. **Frame assembly** fits the platform and entire stair flight. This separate local review project preserves the original projects, including projects 727 and 767.

## Implemented scope

- Foundations and base plates: individual rectangular solids attached to column bases. The column base equals plate top; foundation top follows plate bottom. Footprints must cover their referenced column and, where present, the plate.
- Bracing: solid round diagonal members defined by radius and two distinct column references. The lower endpoint is the first column base; the upper endpoint is the second column top. Radius must fit both column sections. This milestone supports column-to-column diagonals.
- Stairs: a straight south-edge flight, with editable width, going, maximum riser, tread thickness and round-stringer radius. Rise follows platform height; the riser count rounds upward to keep equal risers. Each tread is a real box; both stringers are real cylinders. Every tread intersects its stringers; the last tread touches the deck edge at deck-top height; the lower stringer endpoints reach the local base plane. The panel reports actual riser count, rise and run.
- Beam–column connection placeholders: solid joint envelopes at a referenced beam/column contact. These require the beam bottom to meet the column top and its footprint to overlap that column centre. No bolts, welds, gussets or connection-strength claims are included.
- Add, select, edit and delete: additions, parameter edits and whole-assembly deletions use an unapplied geometry preview with Apply/Cancel. Components are selectable through Layers and the viewer; **Edit selected attachment** opens their parameter record. Deleting a selected generated part previews deletion of its entire assembly. A stair deletion includes all its treads/stringers.
- Resizing the main platform regenerates attached assemblies in the same undo transaction. Footings, plates, diagonals, joints and stairs follow their member references. Tread identities remain stable where their indices still exist; changing the riser count adds/removes the necessary treads.
- Existing undo/redo, revision save, reload, comparison, visibility, locks and materials are retained. Free transforms that disconnect generated members are blocked. Core platform members cannot be deleted while attachments remain. A locked affected attachment blocks resizing, editing or deletion.

Parameters are stored in the existing document's versioned `generator_parameters.platform_attachments` records. Each generated component stores its attachment ID and member references. No database migration or editor architecture replacement was required. Backend save validation independently checks dimensions, parameter schema, references, expected solid geometry, identities and conceptual scope; disconnected or tampered assemblies are rejected with HTTP 422.

## Engineering assumptions and limits

All added parts and member sizes are **conceptual / unverified**. The column-base plane is a local geometric reference; absolute elevation, surveyed ground and soil properties remain unknown. Footings/plates extend below that plane. Foundations have assumed rectangular dimensions, with no reinforcement, bearing, settlement or anchorage design. Braces and stair stringers use assumed solid round sections. Stairs are an open-tread geometry concept without landings, rails or stair-code clearance validation. Joint blocks represent contact envelopes rather than detailed fabrication connections.

Geometry validation establishes the specified contacts and parameter consistency. It is not structural analysis. Loads, load combinations, stress, deflection, buckling, fatigue, foundation resistance, connection strength and code compliance have not been assessed. Added parts remain excluded from engineering quantity/cost estimates. Existing geometric export uses these actual solids.

This milestone is limited to the existing complete industrial-platform-5x3 core assembly, with a common horizontal rotation and unit scales on referenced members. Unsupported/skewed references, invalid sizes, insufficient support footprints, missing parts, impossible stair dimensions and orphan records are rejected. Editor resource limits are 64 attachment assemblies, positive dimensions up to 500 m, and 2–200 stair risers; these are software limits, not engineering acceptance criteria.

## Local verification

- Full frontend regression suite: **263 tests passed across 46 files**. After the final core-reference guard, **47 targeted tests passed** for attachments, platform regeneration and editor history.
- Backend: **34 tests passed**, including attachment geometry, model revisions and existing geometric-layout validation. The isolated test client initially stalled under sandbox networking; the same local tests passed with mock AI and cloud storage disabled outside that sandbox restriction.
- Browser workflow at localhost:3001 passed: invalid input, cancel, add all five types, select a generated tread, edit stair going, deletion preview/cancel/apply, undo/redo, resizing, save, reload and immutable comparison. The 5 × 3 × 3 m draft has 42 components; resizing to 6 × 4 × 3.6 m produces 45, including three additional stair treads.
- Saved-model browser review passed: whole-flight deletion from a selected tread, blocked disconnected movement, preview/save protection and full-assembly camera framing. All 45 component pick positions were available; no browser page errors or Cesium error panel occurred.
- Direct picking of a generated stair tread was also verified in the live in-app browser. Assembly framing uses a conservative isometric range so existing terrain camera protection does not interrupt an excessively close flight; no model elevations are changed.
- A deliberately detached brace was rejected by the local API with HTTP 422, preserving the saved revision.
- TypeScript and ESLint passed.
- Database snapshot comparison: all original **241 project**, **540 scenario** and **56 model-revision** rows unchanged. The before-work database and edited-source snapshots are in `.cache/milestone2`.
- The broader database comparison checked **9,205 original rows across 62 tables** and found no changes to any original row.

The local frontend remains on **localhost:3001** and the offline API on **127.0.0.1:8001**. No GitHub operations, commits, deployment, paid AI calls, dependency installs or further engineering phases were performed.

## Review artifacts

- `screenshots/assembly.jpg`: saved model with foundations, plates, bracing, stairs and connection envelopes, alongside stair parameters.
- `screenshots/preview.jpg`: unapplied stair-geometry edit with Apply/Cancel controls.
- `screenshots/comparison.png`: immutable revision comparison after coordinated resizing.

Milestone 2 is complete. Structural analysis and subsequent phases await user approval.

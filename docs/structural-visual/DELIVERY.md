# Structural visualization milestone — final review

## Open the working local application

- [Project 793 — saved unequal CAD frame](http://localhost:3001/projects/793/workspace): select **Analysis**.
- [Project 794 — saved CAD slab and two support frames](http://localhost:3001/projects/794/workspace): select **Analysis**.
- [Project 804 — preserved RC foundation reference](http://localhost:3001/projects/804/workspace).
- [Isolated foundation demonstration 814](http://localhost:13001/projects/814/workspace): Analysis → Whole-structure evidence and unsupported transfers → Foundation and soil response. The existing foundation visual controls remain available below.

[Real recorded walkthrough — 73 seconds, 1600 × 1000](structural-walkthrough.webm) · [frame force screenshot](793-forces-1600.png) · [slab screenshot at 1280 px](794-slab-1280.png) · [foundation screenshot](demo-foundation-1600.png). Local video playback and dimensions were verified: [metadata](video-metadata.json), [actual video frame](walkthrough-frame.png).

## Compact feature/status summary

- **Implemented — structural topology:** saved member identities, both analyzed slab-support frames and explicitly declared rigid arms. Capacity is unverified. No connection is inferred from touching CAD geometry.
- **Implemented — loads/reactions:** saved signed nodal loads, applied moments, distributed member loads and support forces/moments, with units. Arrow lengths are normalized and are not force magnitudes.
- **Implemented — deformation:** actual saved planar displacement samples, adjustable magnification, unscaled mm labels, original/deformed toggle and computed rigid-arm motion. No shell/slab deformation or out-of-plane response is invented.
- **Implemented — member forces:** signed saved bending, shear and axial samples; diagram offsets are normalized separately from real displacement.
- **Implemented — slab allocation:** saved one-way tributary polygons and beam allocation. The saved 120 kN imposed pressure allocation transfers 60 kN to each supporting beam. This is not slab plate/shell FEA or a stress contour.
- **Implemented with bounded evidence — foundations:** existing reviewed synthetic foundation pressure and settlement can be displayed using the existing foundation overlay generator. Project 804 remains the reference; real frame-to-footing/soil transfer remains unverified. No loads are silently imported into a foundation study.
- **Implemented — inspection/workflow:** click labels or components, inspect available saved calculations, switch and compare available saved load cases, isolate the analyzed system and restore visibility. Display isolation/transparency do not commit a CAD revision or change saved material/visibility.
- **Explicitly unsupported/unverified:** connection capacities, unsaved/missing force transfers, unmodeled context, real soil/site response without reviewed evidence, slab shell fields, torsion and general 3D frame response. No structural safety or code-compliance claims.

Numerical details, source identities, coverage warnings and legacy analysis tools are secondary expandable content. The previous foundation reinforcement, shear and report workflows remain available. Structural inspection keys are isolated from foundation check keys, and changing tools hands over the view without a polling takeover.

## Validation and engineering evidence

- Full frontend regression: **72 files / 353 tests passed**. [Release log](frontend-release.log).
- Relevant backend calculations, independent reference checks, OpenSees, CAD/slab transfer, foundation, RC and authorization checks: **289 tests passed**. [Log](backend-verified.log).
- Seven read-only browser workflows: projects 793/794/804 at both 1280 and 1600 px, plus isolated foundation interoperability. [Release log](browser-release.log). Each blocks modifying HTTP requests. Acceptance JSON files record errors and write attempts.
- TypeScript and changed-file ESLint: [checks](quality-checks.log).
- Independent summation of saved nodal/distributed loads and reactions: eight saved frame/case records satisfy force and moment equilibrium within 0.001 N / N / N·m. Signed force conversion, displacement magnification, North-plane identity and exact saved slab polygon positions also have independent projection tests. [Numerical checks](independent-projection-checks.json), [script](independent_projection_check.py), [frontend tests](../../frontend/lib/structural-visual.test.ts).
- [Recording evidence](demonstration.json): real application recording, no page errors and no modifying HTTP requests.

Earlier failed browser attempts remain in their logs: a test initially selected the preserved legacy slab instead of the analyzed CAD slab; a development hot-refresh during editing also triggered a diagnostic request. The corrected selection and stable release run are recorded separately. A sandboxed numerical run stalled; the existing local runtime completed all 289 tests with isolated test databases and plugin autoload disabled. No dependency installation was performed.

## Preservation and six-row provenance

All **10,245 development-database rows and its schema are exactly unchanged during this milestone**, including the six retained additional records. [Milestone comparison](milestone-preservation.json).

The earlier recovery manifests confirm all **10,239 original rows**, **55,296 original storage files**, **2,090 engineering-proof files** and **264 database schemas** remain preserved. 263 databases retain exact older baseline fingerprints. The development database still differs from that older baseline only by the six already known additions. The strict mismatch is retained rather than hidden. [Audit](preservation-audit.json), [strict manifests](preservation-manifests.json).

The normal-backend access log records successful calls to the separate-study copy route for project 804 and the preview route for study 805. Study metadata binds revision 125 to source 804/revision 124. Both copied drawing references match their original source hashes. The foundation proposal remains awaiting review, not an authorized calculation. Logs do **not** identify which browser or person initiated the requests. No record was deleted or restored. [Six-row provenance](six-row-provenance.json).

Original CAD geometry, source identities, revisions and saved solver files were not edited. Modifying numerical tests use temporary/in-memory databases; application browser validation and recording are read-only. The foundation demonstration uses the existing attested isolated database and ports 13001/18001. Normal local development remains on 3001/8001.

## Performance and scope

Cesium reuses its existing batched overlay primitives. Member labels are reduced to one peak per component; distributed-load arrows retain numerical labels at representative positions. Stable opacity/focus keys avoid rebuilding the model mesh for each force, case or magnification change. Camera framing uses the analyzed graph and an oblique angle for slab regions. Temporary translucency exposes diagrams through the CAD envelopes.

No validated numerical method, engineering authorization rule or unrelated UI design was changed. No Git operations, deployment, installation, paid inference, destructive cleanup or full-project backup was performed. The local services remain running. Work stops for final visual review.

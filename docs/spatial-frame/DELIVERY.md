# Connected spatial-frame review milestone

Local synthetic verification only. No building safety, connection-capacity or code-compliance approval.

## Open the application

- Normal website: [localhost:3001](http://localhost:3001/projects/793/workspace). Original projects 793, 794 and 804 retain their existing planar, slab and foundation workflows.
- Connected two-storey demonstration: [isolated project 823](http://localhost:13001/projects/823/workspace), Analysis tab.
- One-storey prerequisite demonstration: [isolated project 822](http://localhost:13001/projects/822/workspace).
- [Recorded walkthrough](./spatial-frame-walkthrough.webm): 81.28 seconds, real 1600×1000 Chromium capture; playback verified.

The demonstration deliberately lives in the existing isolated database, not the original development database. Keep backend 18001 and frontend 13001 running to inspect it. The normal website uses backend 8001 and frontend 3001. Both use the installed runtimes and offline provider; no paid inference, deployment, Git operation or installation was performed.

## Completed features and bounded status

- **Within implemented method:** shared-node 3D linear elastic beam/column mechanics, six DOF per node, both bending planes, axial response and torsion. Native installed OpenSees `elasticBeamColumn` with `Linear` transformations; independently assembled 12-DOF stiffness reference.
- **Within implemented method:** separate reviewed 2×1-bay synthetic models, first one storey and then two storeys after the six-DOF benchmark gate. Two-storey model: 26 members, 18 nodes, four load-only slabs, 8×4 m floor plan, 3 m storey height. Rigid coincident centreline connections and fixed bases are explicit assumptions.
- **Within implemented method:** declared gravity, nonuniform East/North nodal lateral actions, and their linear sum. These are unfactored synthetic actions, not code load combinations. No unrequested member self-weight is added.
- **Within implemented method:** saved geometry/source binding, A/I checks against unrotated CAD boxes, reviewed local axes, exact-hash authorization, ownership, latest-revision checks, stale-result rejection, immutable solver artifacts and download of full calculation evidence.
- **Within implemented method:** all seven visualization modes; Mz/My/Vy/Vz/N/T diagrams with units, distinct styles and normalized diagram-scale legends; actual computed 3D displacement with labeled display magnification; node loads/reactions; floor filtering; native 3D member picking; slab/member inspection; restore visibility. Visualization does not execute the solver or alter geometry/results.
- **Within implemented method:** reviewed equal-span, one-way uniform slab load allocation to two parallel support beams. This adds loads only and does not constrain in-plane floor motion.
- **Not verified:** real connection capacity, physical column-to-foundation transfer, soil restraint/flexibility and the suitability of the declared material stiffness for a real structure. The foundation mode shows prescribed base reactions and warns about these gaps. Existing foundation calculations remain separate.
- **Not supported:** slab plate stresses or deformation, diaphragm stiffness, member releases/offsets, rotated/parented source boxes, nonlinear materials, cracked RC stiffness, P-delta, buckling, dynamics, earthquake/wind code generation and design approval. These are not silently approximated.

The API has defensive limits of 80 nodes, 150 members and four cases; the delivered benchmark/browser evidence covers the explicit one/two-storey review fixtures. This is not a claim that arbitrary larger buildings have been validated.

## Independent calculation evidence

[Independent calculations](./independent-calculations.json) contains closed-form expectations, actual OpenSees values, independent stiffness comparisons, source/input hashes and each case run identity. [Full review records](./demo.json) retain the original saved responses.

- Six-DOF cantilever: axial, two bending directions and torsion, tested along all three global axes in SI and N-mm. For the East-oriented 3 m benchmark, the independently calculated local translations are 0.00075 mm, 2.5875 mm and 1.546875 mm; twist is 0.00015 rad.
- Uniformly loaded fixed beam: 4 m span, 10 kN/m, E=30 GPa, I=0.000675 m4. Closed-form midspan displacement is −0.329218107 mm; absolute end/midspan moments are 13.333333/6.666667 kN·m. This checks recovered internal section actions and the load-dependent displacement term, not only nodal output.
- Slab allocation: 16 m2 × 5 kPa = 80 kN per slab; each supporting beam receives 10 kN/m across 4 m. Two slabs give 160 kN per floor; two-storey base vertical reactions total 320 kN.
- Combined two-storey reactions: East −15 kN, North −7.2 kN, Up +320 kN. Largest nodal translation is 1.078970 mm. Global force/moment equilibrium residuals are below 5e-10 N/N·m in the saved demonstration.
- Mesh refinement, stiffness scaling, superposition, local-axis permutation, unit conversion, invalid inputs and applicability rejection are tested independently.

Synthetic E=30 GPa, G=12.5 GPa and J=0.001 m4 are declared inputs, not real RC stiffness/capacity determinations. Section A and bending inertias are bound to the 300 mm square source boxes. Uniform-load member displacement is recovered using Euler–Bernoulli interpolation plus the exact uniform-load particular term. Seventeen saved section samples per member are shown; sample maxima are not presented as exact design envelopes.

## Tests and visual evidence

Release verification: **366 frontend tests, 262 backend tests (26 spatial tests), and 8 browser workflows passed**. TypeScript and scoped ESLint passed. The release logs and acceptance files in this directory are the detailed test record. Frontend tests cover saved-result immutability, all seven projections, actual ENU deformation, floor filtering, real local forces, unsupported warnings, dirty/stale display suppression and read-only interaction. Backend regressions include the pre-existing planar, CAD slab, RC and foundation services as well as the new spatial tests. Browser acceptance covers both synthetic models at 1280/1600 px, all modes, all six force components, three cases, component/floor/slab inspection, restore visibility, exact review/authorization on a separate isolated project, and read-only normal projects 793/794/804.

- [Frontend release log](./frontend-release.log), [backend release log](./backend-release.log).
- [Machine-readable final verification](./test-results.json), [verified implementation hashes](./implementation-manifest.json).
- [Browser release log](./browser-release.log), [authorization details](./authorization-browser.json).
- [TypeScript](./typescript-release.log), [scoped ESLint](./lint-release.log).
- [1280 px bending](./forces-1280.png), [1600 px bending](./computed-My-1600.png), [actual displacement](./actual-deformation-1600.png), [floor/member selection](./floor-2-member-inspection.png), [slab inspection](./slab-inspection-1600.png).
- [Recording integrity](./demonstration.json), [video metadata](./video-metadata.json).

The initial browser run correctly blocked an automatic site-suggestion request on unbounded synthetic sites. Explicit synthetic display-site bounds resolved it; no original data was written. An initial authorization assertion allowed only five seconds for the benchmark-plus-solve sequence; the final test waits for the actual completed result. A new test mock initially failed Vitest hoisting and was corrected; release logs identify the final checks.

## Preservation

[Current milestone preservation](./milestone-preservation.json) compares every current original development row and schema against the fingerprint taken before this work: **10,245 rows unchanged**. [Original manifests](./preservation-manifests.json) rehash the 55,296 original storage files and 2,090 original CAD proof files and compare 264 database schemas. All original files and schemas are preserved; 263 database fingerprints exactly match the older backup baseline. The original development database retains its six previously documented additional rows relative to that older baseline. [Append-only audit](./preservation-audit.json) records that distinction; no rows were deleted or restored to force a match.

All newly created review projects and modifying browser work are confined to `docs/foundation-system/isolated/foundation.db`. Native demo artifacts are in `docs/spatial-frame/solver-evidence/<run_id>/`; raw Tcl, displacements, reactions, local end forces, executable hash and manifests are retained. Existing recovery backups, environments, Git metadata, drawings, solver evidence and model revisions were preserved. No full-project backup or cleanup was performed.

## Reproduce and continue locally

- Start the existing normal launcher `run-website.bat` as usual.
- Isolated backend: existing `backend/.venv/Scripts/python.exe docs/spatial-frame/run_isolated.py` from the project root. It refuses to fall back to the original database.
- Isolated frontend: existing Next runtime on port 13001 with `GEOAI_LOCAL_REVIEW=false` and `NEXT_PUBLIC_API_URL=http://127.0.0.1:18001`.
- `prepare_review.py` intentionally creates **new** isolated review projects, performs explicit saved-input review and authorizes the exact hash. Do not rerun it merely to view existing projects 822/823. `spatial_review.fixture()` is the deterministic parametric source.
- Review the input/source assumptions in the expandable panel before using “Prepare exact saved review” and “Authorize exact local OpenSees run.” These are separate actions; changing a mode, case or floor never authorizes a new calculation.

Authoritative mechanics references: [OpenSees 3D elastic beam-column](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/elasticBeamColumn.html), [linear local-axis transformation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/geomTransf/Linear.html), [3D uniform element loads](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/pattern/PlainPatternloadcommands/eleLoad.html), [local end-force implementation](https://opensees.berkeley.edu/OpenSees/api/doxygen2/html/ElasticBeam3d_8cpp-source.html). The installed executable is hashed in every saved case; native numerical tests establish behavior for this local runtime.

Stopped for final visual review. This evidence is not an engineering safety certificate.

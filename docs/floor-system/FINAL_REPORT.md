# GeoAI — Visual 3D floor system and load transfer

Local synthetic engineering review. No structural safety, connection-capacity or code-compliance approval.

## Use the integrated workspace

[Open the validated two-storey project 823](http://localhost:13001/projects/823/workspace), then select **Analysis**. The existing result remains revision 150 / analysis 684. [Normal website](http://localhost:3001/projects/793/workspace) remains available on port 3001.

1. Select a translucent floor face. Every panel is labeled **LOAD-ONLY**. The tributary strips identify its two reviewed supporting beams.
2. Inspect the magenta route, choose a reachable prescribed base, or expand “Follow an adjacent analytical connection” to move from floor to beam, joint and column. Select a yellow load arrow or a green base reaction for its distinct saved evidence.
3. Use “Isolate this floor,” the floor selector, and “Show complete route across floors” to control temporary visibility. Restore full geometry at any time.
4. Select “Deformed versus original,” choose a magnification factor, and animate. The four-second display cycle interpolates the saved static case from zero to full displacement and back. It is **not dynamic analysis**, a load-history calculation or a vibration mode. Stopping shows the full saved static case. LOAD-ONLY surfaces remain undeformed.
5. Default labels show the selection and floor identities, capped at seven. Compact overview and all-value options remain available; colliding labels are suppressed. Numerical details and evidence downloads are expandable.

## What the visual route establishes

The saved slab declaration supplies a one-way tributary allocation to two named parallel beams. Thereafter the explorer follows explicit saved member–node connectivity and ends at a prescribed fixed base. Slabs are never used as intermediate structural links between beams. Unreviewed CAD proximity does not create a connection. A zero-pressure case has no slab gravity arrows.

Magenta represents a **topology route**, yellow applied loads, and green support reactions. A reachable base is a graph result, not a statement that a selected load is carried exclusively along that route. Member actions and reactions belong to the **whole saved case**. Individual-load contribution tracing has not been solved and is not invented.

Actual joint, base-plate, foundation and soil connection capacity remain **NOT VERIFIED**. Fixed supports and rigid coincident joints are analytical assumptions. Existing foundation workflows remain separate and unchanged.

## Numerical evidence

The new owned, revision-bound `/engineering/spatial-frame/684/floor-evidence` endpoint performs read-only checks against the existing result. It does not execute OpenSees, save an analysis, modify a revision or change solver inputs. Stale or nonverified results are rejected. Nonfinite/inconsistent source evidence is rejected; failed conservation is not repaired into a passing result.

- Each 4×4 m floor panel has 16 m² area. At 5 kPa, its gravity is 80 kN. Each of the two 8 m² tributary strips contributes 40 kN, or 10 kN/m over a 4 m supporting beam.
- Four panels across two storeys give 320 kN gravity. The original combined-case reactions remain East −15 kN, North −7.2 kN, Up +320 kN. No new load combination or member self-weight was added.
- At every node, all six saved member end actions are rotated from local axes to ENU and checked against applied nodal actions plus support reactions. The maximum residual for the delivered three cases is below 5e−13 N for forces and below 1e−18 N·m for moments. Tributary aggregation exactly matches the saved uniform beam loading in these fixtures.
- Displacement animation is display-only: `x_display = x_source + magnification × phase × u_saved`, with `phase = (1 − cos(2π × display_seconds / 4))/2`. No animated plate deformation or computed stress contour is created. The saved numerical values remain unscaled.

[Saved floor-transfer evidence](./floor-evidence.json) includes every tributary polygon, allocation, node balance, case/run identity and source hash. The in-app “Download floor-transfer evidence” exports that same source-bound data; real-browser tests inspect the downloaded contents. The original [independent frame calculations](../spatial-frame/independent-calculations.json) and native solver manifests remain intact.

## Diaphragm and slab mechanics investigation

The investigation uses the installed OpenSees executable in separate artifact folders, without creating or changing project/database records. [Full research results](./mechanics-investigation.json) retain actual values, independent expectations, executable hash and raw Tcl/output locations.

- **Rigid-plane kinematics benchmark passed:** a retained node and three constrained nodes with declared linear springs, using a Transformation constraint handler. Native results agree with an independent three-DOF condensed stiffness calculation and the small-rotation constraint equations. This verifies that isolated constraint setup; it does not establish that a real floor is rigid.
- **Thin-plate bending benchmark passed within its stated scope:** a simply supported 4 m square, 0.04 m thickness, E=30 GPa, ν=0.3, −100 Pa uniform pressure. Independent Navier central displacement is −0.591478548 mm. ShellMITC4 results at 4×4, 8×8 and 16×16 meshes are −0.578436159, −0.589178993 and −0.591907969 mm. Relative errors decrease from 2.205% to 0.389% to 0.0726%; vertical reactions total 1,600 N. The 101/201-term reference difference is about 1.67e−13 m. In-plane and drilling DOFs are restrained for this pure-bending experiment; membrane behavior is not validated by it.
- **Building integration remains DISABLED.** The existing LOAD-ONLY floors have no reviewed shell mesh, diaphragm master/slave mapping, slab material/section model, edge restraints, offsets or beam–shell compatibility. Those integrated mechanics and their mesh sensitivity have not been benchmarked. Isolated benchmark success is not permission to change the saved building formulation.

Primary references: [OpenSees rigid-diaphragm equations and assumptions](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/mp_constraint/rigidDiaphragm.html), [elastic membrane/plate section](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/231.htm), [official ShellMITC4 example](https://opensees.berkeley.edu/OpenSees/manuals/ExamplesManual/HTML/876.htm), and [NASA TM 100928, simply supported square-plate reference](https://ntrs.nasa.gov/api/citations/19880019811/downloads/19880019811.pdf). The independent thin-plate series agrees with the rounded reference coefficient of 0.00406 in the NASA tables.

## Validation and visual delivery

- Complete frontend regression: **375 tests** across 76 files passed. Relevant backend regression: **272 tests** passed, including ten new floor-evidence tests and preserved spatial, planar, slab, RC and foundation workflows. TypeScript and scoped ESLint passed.
- Real Chromium validation at **1280 and 1600 px** covers direct floor-face and load-arrow picking, connected routes through columns to bases, floor isolation, sparse nonoverlapping labels, all seven modes, actual animation phase changes, download contents, restoration of visibility and no write requests. Normal projects 793, 794 and 804 also pass read-only browser checks.
- [Frontend log](./frontend-final.log), [backend log](./backend-final.log), [browser log](./browser-verified.log), [TypeScript](./typescript-release.log), [lint](./lint-release.log).
- [Recorded walkthrough](./floor-system-walkthrough.webm): 68.32 seconds at 1600×1000, with playback verified. [Recording integrity](./demonstration.json), [video metadata](./video-metadata.json).
- [Final verification index](./test-results.json), [verified implementation hashes](./implementation-manifest.json).
- [Floor overview](./floors-overview-1600.png), [selected floor and route](./selected-floor-route-1600.png), [beam transfer inspection](./beam-transfer-inspection-1600.png), [column inspection](./column-transfer-inspection-1600.png), [selected load](./selected-load-1600.png), [animated static deformation](./animated-deformation-1600.png), [isolated floor](./isolated-floor-system-1600.png), [base restraint](./prescribed-base-1600.png).
- [1280 px floor workflow](./floor-transfer-1280.png), [1280 px animation](./deformation-1280.png), [1600 px acceptance](./acceptance-1600.json).

An initial browser check exposed floor picks falling through into CAD Inspect; engineering overlay picks now capture the selection before the editing handler. Another check found excess selected-load labels; default labels are now capped. Historical failed runs are retained separately, and final logs identify the passing release checks.

## Preservation and operation

[Original development database fingerprints](./milestone-preservation.json) confirm **10,245 existing rows and schemas unchanged**. [Review preservation](./review-preservation.json) confirms **10,478 existing isolated rows unchanged** and **635 previous spatial solver files unchanged**. No project, revision, analysis or solver result was updated or added by this milestone.

[Original preservation manifests](./preservation-manifests.json) verify 55,296 original storage files, 2,090 original CAD proof files and 264 database schemas. The older backup baseline still differs only by the six previously documented development rows; those rows were retained, and the current milestone fingerprints include them unchanged. No cleanup, restoration, dependency installation, paid inference, Git operation, deployment or full-project backup was performed.

The existing normal launcher remains unchanged. The isolated backend still uses `docs/spatial-frame/run_isolated.py` and the existing isolated database; frontend 13001 points to backend 18001. Do not run the prior fixture-creation script merely to view project 823: no new review project is needed for this display-only milestone.

Stopped for final visual review. Unsupported integrated mechanics remain disabled; this report is not an engineering safety certificate.


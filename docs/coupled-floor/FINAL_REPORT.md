# Coupled slab–frame visual review — local synthetic scope

Open http://localhost:13001/projects/828/workspace and select **Analysis**. The normal local website remains at http://localhost:3001. Project 828 exists only in the isolated review database. No original project was converted to a shell model.

## Delivered scope

A separate, prescribed one-storey 4 × 4 m slab–frame model now has genuine shared-node ShellMITC4/frame interaction, saved native results, seven visual modes, selectable shell faces and members, actual slab/frame displacement animation, units/legends, temporary surface visibility, and downloadable evidence. Colors represent cell means of actual nodal vertical displacement. Geometry uses actual computed nodal translations; quad rendering triangulates between those nodes. Neither display constitutes a stress field.

This is a bounded synthetic verification example, not a general floor-design solver, building approval, or engineering safety certificate. The existing two-storey frame remains LOAD-ONLY. Arbitrary floor geometry, two-storey shell coupling, lateral shell behavior, diaphragm integration, shell stresses, reinforcement/capacity checks and physical connections remain disabled.

## Explicit analytical model

- SI units: N, m, rad; local East/North/Up coordinates, horizontal slab midsurface at z = 3 m.
- One 4 × 4 m rectangular slab, thickness 0.160 m, E = 30 GPa, ν = 0.20, isotropic uncracked elastic section, density zero. No automatic self-weight.
- Uniform prescribed gravity pressure −5,000 Pa, total −80,000 N. It is a declared synthetic action, with no load factors or code load-combination claim.
- Counterclockwise ShellMITC4 quads. The final mesh has 16 × 16 quads and 289 slab nodes; 64 perimeter nodes are actual frame nodes. Four additional fixed base nodes give 293 total nodes.
- Four edge beams, subdivided into 64 analytical segments; four 3 m columns. Each segment and column has its own saved CAD component identity in this new project. All sections are 300 mm square: A = 0.09 m²; Iy = Iz = 0.000675 m⁴. G = 12.5 GPa; J = 0.001 m⁴ is a prescribed synthetic input, not an RC torsion-capacity calculation.
- All six DOFs are shared at beam–shell perimeter nodes. Beam centrelines coincide with the shell midsurface; offsets are explicitly zero. Column tops meet corner nodes. No edge hinges, releases, inferred physical connections or rigid diaphragm constraints are introduced. These coincident section assumptions are synthetic and do not establish the physical composite behavior of an actual beam–slab joint.
- Four fully fixed bases. Foundation flexibility, joint/base-plate/soil capacity and cracking are not calculated.

Each quad contributes pressure × area / 4 to each of its four vertical nodal actions. The frame input contains **no load-only slabs, no tributary loads, no beamUniform loads and no added member weight**. Thus shell loading and tributary allocation cannot both occur in this supported formulation. Existing LOAD-ONLY calculations remain separate.

## Independent calculations and native checks

The existing plate/Navier and rigid-diaphragm benchmark implementations were reused without modifying their prior artifacts. New prerequisite runs are under `prerequisite-evidence/`, with source hashes in `reused-benchmarks.json`. The simply supported thin-plate 16 × 16 mesh differs from its independent Navier center solution by 0.07260%; the rigid-diaphragm spring/condensation test reproduces small-rotation kinematics. Neither result alone validates a real floor diaphragm.

For the coupled model, an independent five-field Mindlin Ritz calculation uses tensor-product Legendre trial functions and Gaussian integration. It does **not** consume native shell stiffness, shell forces or displacements. It combines independently integrated plate membrane/bending/shear energy with the existing independently assembled 12-DOF Euler–Bernoulli frame stiffness. It uses D = Et³/[12(1−ν²)], the isotropic membrane/bending matrices, and transverse shear stiffness (5/6)Gt. Plate fields are u, v, w, rx, ry; the independent drilling rotation is half the in-plane curl. The distinct drilling/discretization assumptions are disclosed; exact agreement is not claimed.

Native coupled center displacement:

- 8 × 8: −0.9211946742 mm.
- 12 × 12: −0.9337937759 mm (exact retained value in the saved evidence).
- 16 × 16: −0.9379720211 mm.
- Final 12 → 16 relative change: 0.445455%.

Independent Ritz center displacement, using the same 16-segment-per-edge frame:

- Polynomial order 4: −0.9423666797 mm.
- Order 6: −0.9433513060 mm.
- Order 8: −0.9434907042 mm.
- Order 6 → 8 change: 0.014775%.
- Native final mesh versus independent order 8: 0.584922% center displacement difference.
- Independent versus native member-end force error normalized to the whole-case force peak: 2.154154%; moment error normalized separately to the whole-case moment peak: 1.500118%. These are not individual small-component percentage errors.

Every shell's actual 24 global nodal resisting forces are retained. Summing them at shared nodes and subtracting from the externally applied boundary loads gives the net frame actions. The independent frame stiffness solve then reproduces native interface displacements, base reactions and member end forces. Interior shell nodal balance and whole-model force/moment equilibrium are also checked. This transfer check is conditional on native shell actions; it is distinct from the independent Ritz prediction.

The final model returns four +20 kN vertical base reactions, balancing the 80 kN pressure load. Exact residuals, native nodal displacements, member forces, shell nodal forces, local axes, meshes and reference results are downloadable in saved analysis **693**, bound to the exact project revision/document hash. Native Tcl, stdout/stderr and numerical output files have SHA-256 hashes.

Verification gates are numerical tolerances, not code or safety allowables: interface displacement < 10⁻⁸ m/rad; force/moment balance and conditional frame errors < 0.01 N/N·m; center mesh change < 1%; Ritz order change < 0.1%; independent center difference < 1.5%; separately peak-normalized force/moment differences < 3% / 5%. Coarse meshes are evidence only and are not offered as verified alternatives.

## Authorization, preservation and unsupported work

Creating a review does not run OpenSees. Execution requires authorization of the exact latest saved proposal ID and hash. Ownership, revision freshness, document hashes, replay behavior, failed runs and unsupported geometry are tested. Unsaved/preview/comparison states clear the saved overlays; stale/failed results do not become verified views. Any alteration of this fixed synthetic geometry or formulation requires new validation. No saved CAD change is silently applied.

The original development database remains at 10,245 rows, unchanged from the milestone baseline. The older preservation baseline has 10,239 rows; its six already-existing additions remain preserved. All 10,479 pre-existing isolated review rows are unchanged; only five rows were appended for project 828: project, scenario, model revision, proposal and analysis. Existing original storage/proof manifests and all 264 original database schemas were checked. The 263 other original databases match; the older development-database fingerprint difference is the six retained prior additions, not deletions or restoration. All 635 prior spatial solver files remain unchanged. See preservation audit JSON files for exact assertions. No cleanup, backup relocation, full-project backup, installation, Git operation, deployment or paid inference was performed.

Rigid diaphragm integration remains disabled because a spring-only kinematics test does not validate this finite-membrane floor's lateral behavior, retained/slave mapping, redundant constraints or physical rigidity assumptions. Two-storey coupled extension remains disabled because no separate coupled two-storey reference and convergence suite has passed. The existing two-storey frame and its LOAD-ONLY floor workflows are preserved. No real connection, foundation or soil capacity is assumed.

## Validation and visual review

Final results are recorded in `test-results.json`, frontend/backend logs, browser acceptance JSON, screenshots at 1280/1600 px and the actual Chromium walkthrough. Browser acceptance blocks all modifying requests. Tests that modify models use only temporary in-memory databases or the attested isolated review database. Original projects 793, 794 and 804 are exercised read-only on the normal website; project 823 retains LOAD-ONLY floors.

The first browser run found a stopped/stalled normal website; its identified GeoAI processes were restarted and the original-project workflows rerun. The first frontend run found two incorrect test matcher names in the new tests; those were corrected before the final full suite. Failed-run logs are retained alongside final evidence.

References: [official ShellMITC4 command](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/640.htm), [isotropic section](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/231.htm), [shell global resisting-force semantics](https://opensees.berkeley.edu/OpenSees/api/doxygen2/html/ShellMITC4_8cpp-source.html), [elastic plate bending/shear tangent](https://opensees.berkeley.edu/OpenSees/api/doxygen2/html/ElasticPlateSection_8cpp-source.html), [small-rotation rigid-diaphragm constraints](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/mp_constraint/rigidDiaphragm.html). They document element/constraint mechanics; they do not establish building or code approval.

Stopped for visual review. No structural safety or engineering approval is claimed.

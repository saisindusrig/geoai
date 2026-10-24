# CAD-derived saved 3D → real OpenSees frame verification

Local review website: http://localhost:3001/projects/791/workspace.

Open **Analysis**, select the saved analysis members, then use **Frame Model**, **Show Results / Fit Analysis** and the Displacement, Axial Force, Shear, Bending Moment, Reactions and Evidence tabs. Member inspection includes the original DXF entity and geometry identity. Results and diagrams use actual saved OpenSees output.

## Original geometry and explicit resolution

Original project **789 / revision 98** is unchanged. The new review project **791 / initial revision 99** copied all 51 components exactly, with the original DXF bytes and engineer corrections retained through owned, traceable copied references. Stable CAD identities are unchanged: SW column source 9C, South beam source 96, SE column source AE. The 73-entity drawing remains **SYNTHETIC VERIFICATION**, not a real construction project.

The initial SW column was 3.260 m high, the SE column 3.200 m, and the beam centreline at 3.250 m. Their physical endpoint differences were [-0.150, 0, -0.010] m and [+0.150, 0, +0.050] m in ENU. The existing validated frame solver rejects unequal-height columns. Preview and analysis were blocked; no automatic alignment was implemented.

For the **synthetic browser verification only**, an explicit CAD mapping correction changed the review copy's SW top from 3260 to 3200 mm. The test entered a source/reason stating that this was a synthetic solver-domain investigation, previewed it, authorized the exact geometry and saved **revision 100**. This is not an engineer-approved construction correction. The original project still has its 3.260 m SW column, and the unequal-height copy snapshot remains immutable as revision 99. The other 50 components are unchanged.

After that declared correction, the equal-height frame is supported with physical column centreline span **5.700 m**, column height **3.200 m**, full saved elastic beam length **6.000 m**, constant North coordinate **0.150 m**, and explicitly approved massless rigid-arm offsets [-0.150,+0.050] / [+0.150,+0.050] m in analytical East/Up. No physical connection capacity is established by this idealization; it retains the full saved beam elastic length rather than silently choosing a clear span.

## Explicit verification inputs

All values below were entered as **synthetic verification assumptions**, not measured/manufacturer data or verified project properties:

- E = 200,000,000,000 Pa for each member.
- Columns: declared solid 300 × 300 mm rectangle, A = 0.090 m² and in-plane I = 0.000675 m⁴.
- Beam: declared solid 200 × 300 mm rectangle, A = 0.060 m² and in-plane I = 0.000450 m⁴.
- Both column bases explicitly fixed in ux, uy and rotation; foundation/soil stiffness was not modeled.
- Total 20,000 N East load, explicitly split into 10,000 N at each retained column head; no gravity, slab loading or self-weight inferred.
- Two elements per member, canonical SI. Both short rigid-offset idealizations explicitly declared and individually acknowledged.

Nominal CAD boxes do not establish a real steel profile. Arbitrary A/I substitutions are rejected by this narrowly supported solid-rectangle method. Material, section, load, support and joint sources are required. The offline AI first returned a missing-input proposal; only after explicit inputs were saved did it prepare an authorization-ready restricted proposal. Cloud proposal requests return 403. Model-generated code is never executed.

## Actual solver and independent evidence

**OpenSees 3.8.0**, analysis **384**, saved model revision **100**. Exit and convergence codes are zero. Input/output files, logs, solver executable hash, model Tcl hash, source drawing/review hashes, component identities and independent comparison evidence are retained in the immutable solver manifest.

- Column-head horizontal displacement: **0.409948585 mm** at both heads.
- Head vertical displacement: SW **+0.000656477 mm**, SE **−0.000656477 mm**.
- Head rotation: **−0.000129798113 rad** at both heads.
- Maximum stored sampled translation magnitude: **0.420692401 mm**, on the beam. This is a sample-based result, not a claim of a globally optimized extremum.
- Each base horizontal reaction: **−10.000000 kN**.
- Base vertical reactions: SW **−3.692681445 kN**, SE **+3.692681445 kN**.
- Each base reaction moment: **+21.475857880 kN·m**.
- Beam internal shear: **−3.692681445 kN** using the stored directed-member convention.
- Beam internal start/end bending moments: **+11.078044336 / −11.078044336 kN·m**.
- Each beam rigid-arm offset contributes **+0.553902217 kN·m** to retained-node moment transfer under this load case.
- Global equilibrium residual [Fx,Fy,M]: **[1.0914e−10 N, 4.5475e−12 N, −2.9104e−10 N·m]**.

The existing separate global stiffness implementation independently agrees with solver nodes, element forces, reactions and joint equilibrium. A further independent symmetric strain-energy calculation uses H=3.2 m, column span B=5.7 m and actual elastic beam length ell=6 m:

U = 12 E Ic/H³ u² + 12 E Ic/H² u θ + 4 E Ic/H θ² + E Ac/H v² + 6 E Ib/ell³ (2v − Bθ)².

Taking derivatives of U − P u gives three condensed equations. Independent substitutions then give column reactions, beam shear, end moments and rigid-arm couples. Maximum head displacement difference is **1.789e−18 m**; maximum reaction difference is **1.092e−10** in corresponding SI force/moment units. Beam moment differences are below **5.1e−11 N·m**. The common vertical arm offset produces no beam axial work for this symmetric equal-horizontal-load case; this hand reduction is not used for arbitrary loading.

See `independent-hand.json` and `numerical-evidence.json` for values, formulas, exact inputs, comparison errors and artifact hashes. Canonical axes are analytical X=East, Y=Up, rotation about −North; origin [.150,.150,0] m ENU. Retained node coordinates are [0,0], [0,3.2], [5.7,3.2], [5.7,0] m. Beam elastic ends retain their actual offset coordinates.

## Tests and preservation

**303 backend regressions passed**, including 22 new CAD-to-frame checks. The enhanced independent beam force/diagram and source-staleness checks also passed. Coverage includes:

- Original unequal-height blocking and no geometry mutation; corrupt/unknown source identity and hash rejection.
- Missing E/A/I, source, load and support rejection; inconsistent section properties, unapproved joints and wrong offsets rejected.
- Actual OpenSees meshes with 1/2/4 elements per member; SI and N-mm conversions; half-load scaling and half-E displacement scaling.
- Independent equilibrium, strain-energy head/reaction equations, beam shear/moment formulas and offset-induced moment transfer.
- Actual solver results and offline explanations becoming stale after source-file or engineer-review changes, in isolated databases/files. Existing tests cover engineering-input/model-revision staleness.

**Two browser tests passed**: complete explicit geometry correction → mapping preview → missing-input offline proposal → explicit properties/joints/loads → authorization → real solver → saved results; then actual viewport member picking, DXF identity inspection, all computed diagrams, solver manifest/input evidence, unsaved geometry preview staleness, cancellation, save/reload and responsive desktop layout. Invalid original geometry returns 422, missing-input execution and forged authorization return 409, invalid material/joint inputs return 422, cloud inference returns 403. No page errors occurred. TypeScript and targeted ESLint checks passed.

Snapshot comparison checked **9,730 pre-existing database rows**: zero changed and zero missing. No original project, component, model revision, engineering evidence or inference ledger row was changed. Initial copy components exactly match project 789. Only the review copy's SW column changed through the declared synthetic correction. Original and copied DXF SHA256 both match **614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18**. **Zero new live inference calls**. A local database snapshot was retained before work.

## Unsupported and review status

Engineering approval and code checks remain **DISABLED**. Numerical verification does not establish structural adequacy. Unequal-height saved geometry remains outside the existing solver domain until explicitly resolved; no broader solver method was added. Real steel section/material properties, real construction loads and actual restraint/connection behavior are still unverified.

Slab participation, footings/foundation/soil stiffness, physical connection capacity, releases, out-of-plane/rotated members, arbitrary profiles, long offsets, shear deformation, buckling, nonlinear or whole-building analysis, and IS/US code compliance are unsupported here. Existing geometry, prior OpenSees workflows and versioned code-check architecture remain preserved.

This milestone is complete and **stopped for review**. No GitHub, commits, deployment, software installation or paid AI inference occurred.

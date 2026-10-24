# Original unequal-height CAD frame — local numerical verification

Website: http://localhost:3001/projects/792/workspace. Open **Analysis**, select the saved analysis members and use **Frame Model / Fit Analysis**. Displacement, Axial Force, Shear, Bending Moment, Reactions and Evidence show stored real solver output. Expand **Compare with saved equal-height verification**, explicitly select project 791 / analysis 384, and compare.

## Geometry preserved

Project 792 is a separate copy of original **project 789 / revision 98**, not the equalized geometry in project 791. All **51 components exactly match the original**. Its sole model revision is **101**. No geometry correction or additional model revision was made. Projects 789 and 791, their drawings, components, revisions, saved calculations and evidence are unchanged.

Stable selected identities are `drawing-cad:614f117ae2a74794:9C` (SW column), `drawing-cad:614f117ae2a74794:96` (South beam), and `drawing-cad:614f117ae2a74794:AE` (SE column). Original DXF source IDs retain the corresponding `dxf:` prefix. The drawing and all verification inputs are **SYNTHETIC VERIFICATION**, not measured construction material or an approved real project.

- SW column height **3.260 m**, centre [.150,.150,1.630] m ENU.
- SE column height **3.200 m**, centre [5.850,.150,1.600] m ENU.
- Beam length **6.000 m**, centre [3.000,.150,3.250] m ENU; physical elastic ends at [0,.150,3.250] / [6,.150,3.250] m.
- Retained column span **5.700 m**, common base elevation 0 m, constant North .150 m.
- Analytical origin [.150,.150,0] m ENU; retained nodes [0,0], [0,3.260], [5.700,3.200], [5.700,0] m East/Up.
- Exact observed short rigid offsets: SW **[−.150,−.010] m**, SE **[+.150,+.050] m** East/Up. Lengths .150332964 / .158113883 m.

The retained head chord slopes, while the actual physical beam remains horizontal at 3.250 m. `geomTransf Linear -jntOffset` maps the independently reviewed rigid arms to those actual elastic beam endpoints; no snapping, forced equal elevation or automatic connection is used. Each joint requires its own approval flag, exact signed offset and source. Overlap/touching is never accepted as joint adequacy.

## Supported extension and explicit assumptions

The dedicated `cad-planar-unequal/1` scope supports exactly two independent vertical CAD box columns and one horizontal CAD box beam in a common plane, with common base elevation and bounded short rigid offsets. Unequal height difference is bounded to .5 m; arms are bounded by the existing min(.5 m, .2 × minimum span/height) rule. Rotation, scaling, nonplanarity, different base elevations, unsupported members, incorrect section values, unknown references and unreviewed/wrong offsets are rejected.

For this milestone, unequal geometry supports the explicitly declared **equal horizontal column-head load pattern only**. Named gravity/distributed/self-weight/superposition cases are blocked for this extension. Existing equal-height gravity workflows remain preserved. Broader loading requires separate validation rather than silently reusing another method.

The following values were explicitly entered as synthetic verification assumptions:

- Each member E = **200 GPa**, with source evidence identifying a synthetic elastic assumption.
- Columns: declared solid 300 × 300 mm rectangle, A = **.090 m²**, I = **.000675 m⁴**.
- Beam: declared solid 200 × 300 mm rectangle, A = **.060 m²**, I = **.000450 m⁴**.
- Both bases fixed in ux, uy and rotation, explicitly sourced as a numerical restraint assumption, not footing/soil stiffness.
- Total **20,000 N East**, explicitly split into 10,000 N at each actual column head. No inferred gravity, slab participation or self-weight.
- Two elements per member; canonical SI; both rigid arms independently acknowledged.

The offline restricted proposal first reports required inputs and cannot execute while they are absent. With saved inputs, the exact proposal hash and a separate explicit solve authorization are required. No paid/cloud inference is used. Geometry envelopes do not establish actual steel profiles or material grades.

## Real OpenSees results

Installed **OpenSees 3.8.0**, saved analysis **398**, revision **101**, algorithm **physical-frame/4-unequal**. Exit/convergence codes zero. Input Tcl, node/force/reaction output, logs, manifest, executable hash, source hashes and exact component identities are retained.

- SW head ux **0.424252077 mm**, uy **+0.000677267 mm**, rotation **−0.000130963741 rad**.
- SE head ux **0.416273910 mm**, uy **−0.000664802 mm**, rotation **−0.000131929087 rad**.
- Maximum stored sampled translation magnitude **0.427242568 mm**; sample-based, not a guaranteed global extremum.
- SW base Fx **−9.855849037 kN**, Fy **−3.739512463 kN**, M **+21.488379045 kN·m**.
- SE base Fx **−10.144150963 kN**, Fy **+3.739512463 kN**, M **+21.796399918 kN·m**.
- Beam internal axial force **−0.144150963 kN** and shear **−3.739512463 kN**, following the directed-member convention.
- Beam internal start/end bending moments **+11.204057195 / −11.233017580 kN·m**.
- Global equilibrium residual [Fx,Fy,M]: **[3.638e−11 N, 1.364e−12 N, −1.164e−10 N·m]**.

## Independent full formulation

No symmetric-frame hand formula or symmetry constraint is applied. A new independent reference reads raw saved component coordinates and sizes directly, without calling the existing mesh, stiffness or offset helpers. It independently assembles **12 retained DOFs**, fixes six base DOFs and solves all **six independent head DOFs**.

Member stiffness is obtained by exact three-point Gauss integration of axial strain and Hermite curvature energy: integral(EA BaᵀBa + EI BκᵀBκ) dx. Measured physical endpoint transforms independently apply uphysical = uretained + [−ry θ, rx θ]. Assembly gives Kff uf = Ff, reactions R = Ku − F and physical member end forces. This reference uses full nonsymmetric geometry; the elastic stiffness remains reciprocal/symmetric, and the response is not constrained to symmetry.

Actual OpenSees retained displacements, reactions and complete physical member end forces agree with that independent reference. The existing separate 2D stiffness implementation also checks every mesh node and element, reactions and joint equilibrium. `independent-reference.json` and `numerical-evidence.json` contain the complete matrices, DOF ordering, residuals, errors, source provenance and artifact hashes.

## Equal versus unequal comparison

The read-only comparison uses original saved equal case **project 791 / revision 100 / analysis 384**, with identical declared E/A/I, loads and fixed restraints. It never edits either model or substitutes equal geometry into the unequal solve. Stale cases, different load magnitudes, mismatched sections or drawing identities and inaccessible projects are rejected.

The equal case has both columns at 3.200 m and both vertical beam-arm offsets +.050 m. Both head horizontal displacements are **.409948585 mm**; Fx reactions are −10.000 kN each; vertical reactions are ±3.692681445 kN; base moments are 21.475857880 kN·m each.

Retaining the original 3.260 m SW column changes its stiffness and head elevation, and changes its vertical arm from +.050 to −.010 m. Head movements differ by **+.014303492 mm SW / +.006325324 mm SE** from the equal case; reactions and beam axial force redistribute. The external moment of the same horizontal forces increases from **64.000 to 64.600 kN·m** because they act at different heights. These are actual numerical differences under declared synthetic assumptions, not capacity or safety conclusions.

## Verification and preservation

- **322 backend regression tests passed**, including 19 unequal-frame tests. Additional final unequal tests passed after source-label refinements.
- Actual 1/2/4-element meshes, SI/N-mm conversions, half-load and half-E scaling, nonuniform synthetic E, full energy/stiffness verification and equilibrium passed.
- Rejection coverage: scope, each unreviewed joint, each wrong signed arm, bad references, rotation/nonplanarity, different bases, long arms, excessive height difference, slab selection, missing E, wrong I, unsupported gravity and arbitrary scripts.
- **Two browser workflows passed**: original geometry/mapping, individually reviewed joints, explicit inputs, proposal/authorization, all computed diagrams, owned equal-case comparison, real half-load execution, stale/mismatched comparison rejection, restored 20 kN save/reload, actual viewport member/source picking, full six-DOF evidence and responsive layout.
- **Two frontend comparison applicability tests passed**, preventing cached comparisons from appearing for a different active result or a stale result. TypeScript and targeted ESLint passed.
- Snapshot comparison checked **9,750 pre-existing database rows**: **zero changed, zero missing**. All 51 copy components equal original revision 98; the copy still has exactly one model revision (101).
- Original/copy drawing SHA256 matches **614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18**. Projects 789 and 791 and their numerical evidence remain unchanged. **Zero new live inference calls**.

## Limitations and stop point

This remains small-displacement planar linear Euler-Bernoulli numerical verification with synthetic solid sections, short massless rigid joints and fixed-base assumptions. Physical joint capacity, shear deformation, foundation/soil capacity, slab participation, buckling/geometric stiffness, nonlinear/dynamic or whole-building FEA are unsupported. Unequal-frame gravity/distributed loads are not enabled in this milestone. Actual material/section properties and real construction loads remain unverified.

**Engineering approval and Indian IS/American design checks remain DISABLED.** No safety approval follows from a VERIFIED numerical status. No GitHub, commits, deployment, software installation or paid AI inference occurred. **Stopped for review.**

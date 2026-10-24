# CAD slab to unequal-height frame load path

Local website: http://localhost:3001/projects/794/workspace · Analysis. Current model revision 105, analysis #431. SYNTHETIC VERIFICATION; engineering approval and IS/US checks DISABLED.

Project 794 is a separate copy of project 793 revision 103. The initial copy is revision 104. Original SW/SE columns (3.26/3.20 m), beam elevation 3.25 m, original CAD slab 6×4×0.2 m, all other components and all source projects are preserved.

The original 73-entity DXF has a north beam outline (97) and north column outlines (A5/B7), which were missing from saved CAD geometry. The workflow retains the initial blocker until the user selects source entities, enters elevations/dimensions/material identification, previews, authorizes and saves. Browser verification entered explicitly synthetic north geometry: beam 6×0.2×0.3 m at 3.25 m, NW/NE columns 0.3×0.3 m with 3.26/3.20 m heights. These elevations and depths are declarations, not deductions from a plan. New components remain geometry envelopes until separate analytical inputs and joints are reviewed.

Exactly three source-linked components were added in revision 105; all 51 prior component bodies match exactly. Undo/redo and comparison showed 3 added / 0 removed / 0 modified. Original DXF entities, units, corrections and file bytes remain unchanged.

The 45 legacy platform components overlap part of the CAD slab. They remain saved and visible as context, but this verification requires an explicit complete separate-system exclusion with evidence/reason. The server rejects incomplete exclusions or hiding CAD support members. Unmodeled transverse CAD beam outlines 98/99 remain unsupported; no transverse sharing or complete building system is silently created.

Declared analytical idealization: one-way North slab span onto two full-length parallel East beams at North 0.15/3.85 m, each at slab underside 3.40 m. Support spacing 3.70 m, equal free edge overhangs 0.15 m. Explicit tributary widths 2.0/2.0 m must match geometry and carry a source. Simple vertical slab support lines transfer no slab support moment or torsion. This is load allocation, not plate/shell slab stiffness or capacity. Two independent planar frames are solved; shared-frame coupling is unsupported.

Synthetic engineering inputs: E=200 GPa, columns A=0.09 m² and I=0.000675 m⁴, beams A=0.06 m² and I=0.00045 m⁴, explicitly solid rectangular verification sections. Both bases of each frame are fixed in East, Up and rotation. Four individual massless rigid-joint idealizations use actual offsets [-0.15,-0.01] / [+0.15,+0.05] m (East, Up). All joints need separate explicit review, and the exact saved proposal hash gates solver execution.

Load accounting and numerical results:
- Imposed uniform pressure p=5 kN/m²; slab area A=6×4=24 m²; P=pA=120 kN.
- Tributary width b=3.70/2+0.15=2.0 m each; q=p b=10 kN/m; qL=60 kN per actual saved 6 m beam.
- Sum transferred loads =120 kN; no loss or double counting. Member/slab self-weight is excluded from this case. Existing project 793 self-weight results remain separate and unchanged; no slab pressure is added a second time as a generic frame UDL.
- Total actual computed upward reaction: 120.000000000 kN; balance error -1.421e-14 kN.
- drawing-cad:614f117ae2a74794:96: OpenSees 3.8.0, convergence/exit 0/0; maximum stored sampled translation 0.553628855 mm.
  Local base node 1: Fx=9.961989189 kN, Fy=29.953701030 kN, M=-10.857803904 kN·m (analytical rotation about -North).
  Local base node 4: Fx=-9.961989189 kN, Fy=30.046298970 kN, M=10.593899776 kN·m (analytical rotation about -North).
- drawing-cad:614f117ae2a74794:97: OpenSees 3.8.0, convergence/exit 0/0; maximum stored sampled translation 0.553628855 mm.
  Local base node 1: Fx=9.961989189 kN, Fy=29.953701030 kN, M=-10.857803904 kN·m (analytical rotation about -North).
  Local base node 4: Fx=-9.961989189 kN, Fy=30.046298970 kN, M=10.593899776 kN·m (analytical rotation about -North).

Independent verification: the existing independently integrated full 12-DOF nonsymmetric-geometry reference checks six independent column-head DOFs, reactions, physical end forces and every stored displacement/N/V/M sample. Uniform-load consistent forces and exact axial/quartic particular solutions are included. The reciprocal stiffness matrix remains symmetric; no symmetric-frame response shortcut is applied. Real OpenSees 3.8.0 executes the saved geometry and explicit loads.

A separate whole-slab global statics check reads raw saved slab area/centroid and actual column-base coordinates. It balances pLW at the slab centroid against base forces and r×F plus support couples in saved ENU, including the analytical rotation sign. This verifies static force/moment conservation, not three-dimensional stiffness or foundation behavior.
Global ENU force residual [N]: [-4.001776687800884e-11, 0.0, -7.275957614183426e-12]
Global ENU moment residual [N·m]: [-2.9103830456733704e-11, 0.0, 7.275957614183426e-11]

Independent fixed-fixed beam example with the same 6 m length, E and I and q=-10 kN/m: each reaction 30 kN, end moments ±30 kN·m, midspan displacement qL⁴/(384EI)=-0.375 mm. Actual OpenSees results are checked against closed-form deflection, moment and shear at all stored samples. The portal deflection differs because columns/rigid offsets supply finite flexibility; the fixed-beam example is not substituted for the portal boundary condition.

Verification tests: 368 backend tests passed, including 24 new CAD load-path/source checks. Tests cover missing north geometry, raw CAD identity, tributary widths, 1/2/4 meshes, SI/N–mm, half pressure, force/moment balance, independent reference comparison, section/joint/support/geometry rejection, ambiguous scope, two-way sharing, self-weight rejection, source-byte/review staleness, authorization and saved artifacts. TypeScript and targeted ESLint passed.

Three browser tests passed: source selection → explicit geometry → preview → exact authorization → undo/redo → save → revision comparison; explicit slab/frame engineering inputs → actual OpenSees → both frames/all diagrams → stale pressure → save/reload → reauthorization; actual north member picking/source identity → explicit three-member audit → saved independent evidence. Responsive 1280 px layout passed; no page errors. The previous three-member audit was extended to require explicit selection when multiple CAD frames exist.

Preservation: 9,799 original database rows checked against the before-milestone SQLite snapshot; zero changed or missing. All 51 original components are identical in the copy; original/source projects, prior calculations and revisions remain intact. All DXF bytes match SHA-256 614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18. Zero paid inference calls, installations, GitHub operations, commits or deployment.

Physical foundation interface remains BLOCKED. SW/SE CAD footing outlines are geometric placeholders; north CAD footing outlines are not generated. Actual plate/anchor/column-footing connections, physical support stiffness, reinforcement and soil information are missing/unverified. Reported reactions are demands at synthetic fixed column bases, not computed footing stress, settlement, bearing capacity or foundation safety.

Other unsupported behavior: slab stiffness/capacity/reinforcement, openings, asymmetric/two-way sharing, transverse coupling, sloping/out-of-plane or shared-frame assemblies, unknown load paths, nonlinear/buckling/whole-building FEA, physical connection capacity and IS/US compliance. Synthetic declared properties are not measured or manufacturer-verified. Engineering approval stays DISABLED.

Inspect numerical-evidence.json for explicit inputs, stable source identities, matrices, actual member samples, joint transfers, global statics, reactions and solver file hashes. Inspect browser and preservation evidence alongside this report. Local solver artifacts include model.tcl, nodes/forces/reactions, stdout/stderr and revision-bound manifests.

STOP for review. No additional phase started.

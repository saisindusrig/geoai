# Unequal-height CAD frame gravity and distributed loads

Local review: http://localhost:3001/projects/793/workspace · Analysis tab. Saved revision 103, analysis #421, OpenSees 3.8.0. SYNTHETIC VERIFICATION ONLY. Engineering approval and IS/US code checks DISABLED.

Project 793 is a separate copy of project 792 revision 101. All 51 components match in both new revisions. Revision 102 is the initial copy; revision 103 corrects the copy ancestry metadata without changing geometry. Projects 789, 791 and 792 and their calculations are unchanged.

Saved physical mapping: SW column 3.260 m; SE column 3.200 m; beam elastic length 6.000 m at Up=3.250 m; column-axis span 5.700 m. Retained analytical heads remain at 3.260/3.200 m. Separately approved massless rigid arms are [-0.150,-0.010] and [+0.150,+0.050] m (East, Up). No snapping, member shortening or implicit connection. Stable drawing-cad component IDs and original DXF entity IDs are retained.

Explicit synthetic assumptions: E=200 GPa for each solid rectangular member. Columns A=0.09 m², I=0.000675 m⁴; beam A=0.06 m², I=0.00045 m⁴. These are declared solid-rectangle verification sections, not an inference about real rolled steel. Both bases restrain East/Up/rotation. Euler–Bernoulli linear 2D elastic members; no shear deformation, buckling or connection capacity. Each arm idealization needs individual engineer review; exact saved proposal authorization gates execution.

Named inputs:
- Horizontal: total +20 kN East, half at each actual column head.
- Gravity: -1 kN Up at each column head and -2 kN/m beam uniform load over the actual 6 m elastic beam. No slab sharing.
- Self weight: separately declared 7850 kg/m³ for each member; g=9.81 m/s² along saved -Up. Weight/m = density × explicit A × g. Only actual elastic lengths carry weight; massless rigid arms do not.
- Linear sum: explicit unit factors on these three independently solved cases. It is checked against a separate actual combined-load solve and is not a code combination.

Computed evidence:
- Horizontal: vertical applied/reaction -0.000000000/0.000000000 kN; max stored sampled translation 0.427242568 mm.
  Base node 1: Fx=-9.855849037 kN, Fy=-3.739512463 kN, M=21.488379045 kN·m.
  Base node 4: Fx=-10.144150963 kN, Fy=3.739512463 kN, M=21.796399918 kN·m.
- Gravity: vertical applied/reaction 14.000000000/14.000000000 kN; max stored sampled translation 0.110905210 mm.
  Base node 1: Fx=1.992397879 kN, Fy=6.990734547 kN, M=-2.171576951 kN·m.
  Base node 4: Fx=-1.992397879 kN, Fy=7.009265453 kN, M=2.118763869 kN·m.
- Self weight: vertical applied/reaction 72.495801900/72.495801900 kN; max stored sampled translation 0.257813448 mm.
  Base node 1: Fx=4.602947979 kN, Fy=36.434304727 kN, M=-5.017221154 kN·m.
  Base node 4: Fx=-4.602947979 kN, Fy=36.061497173 kN, M=4.894561866 kN·m.
- Linear sum: vertical applied/reaction 86.495801900/86.495801900 kN; max stored sampled translation 0.565537230 mm.
  Base node 1: Fx=-3.260503179 kN, Fy=39.685526811 kN, M=14.299580939 kN·m.
  Base node 4: Fx=-16.739496821 kN, Fy=46.810275089 kN, M=28.809725653 kN·m.

Maximum global equilibrium residual across cases: 1.164e-10 N/N/N·m. Maximum independent force/moment sample or reaction difference: 4.132e-10 N or N·m. Extrema in the interface use stored samples, not a claim of continuous extrema.

Independent verification: a separate implementation reads raw saved geometry and raw explicit load-case declarations; it does not call the existing mesh, stiffness or load-normalization helpers. Exact three-point Gauss integration builds EA axial strain and EI Hermite curvature energy and consistent uniform-load vectors. A full 12-DOF retained-node system is assembled through independently measured rigid-arm transforms. Six independent head DOFs are solved. The stiffness remains reciprocal/symmetric; geometry and responses are nonsymmetric. No symmetric-frame hand formula is used for the unequal frame.

Physical end forces = k u_local - f_equivalent. Interior displacement includes q_axial x(L-x)/(2EA) and q_transverse x²(L-x)²/(24EI). Every stored sample is independently checked for displacement, N(x), V(x), M(x); reactions and retained heads are checked as well. Rigid-arm force/moment transfer and joint equilibrium are verified, including distributed-load fixed-end effects.

Independent hand prerequisites:
- Actual fixed-fixed beam: L=4 m, E=200 GPa, I=8×10⁻⁶ m⁴, w=-2 kN/m. Each vertical reaction 4 kN; end moments ±2.666667 kN·m; midspan v=wL⁴/(384EI)=-0.833333 mm. Actual OpenSees 2/4 meshes, N–mm and half-load runs agree at all stored samples.
- Exact equivalent-load check for a separate 6 m beam: f_local=[0,wL/2,wL²/12,0,wL/2,-wL²/12]; with w=-2 kN/m, fixed-end magnitudes are 6 kN and 6 kN·m. For EI=90 MN·m², fixed-fixed midspan displacement is -0.075 mm. This is a hand reference, not the actual portal support condition.
- An actual axial uniformly loaded cantilever is checked against u(x)=q(2Lx-x²)/(2EA), N(x)=q(L-x), R=-qL, for 1/2/4 elements.

Tests:
- 344 backend regression tests passed, including 22 new gravity checks and existing CAD/OpenSees/contact/drawing/engineering methods. Mesh 1/2/4, SI/N–mm, half loads, E scaling, exact sample forces and deflections, superposition and equilibrium are tested.
- Unsupported slabs/foundations/load paths, unknown/duplicate references, missing density/source/gravity, NaN, wrong section/offset, unapproved arms and tampered/missing result samples are rejected.
- Browser workflow: saved member selection, mapping preview, explicit input review, offline missing-input proposal, 422 missing source/unreviewed joint rejection, 409 forged/obsolete proposal rejection, real solver execution, case switching, every result diagram, stale-load save/reload, reauthorization, responsive 1280 px layout and no page errors.
- Both browser tests passed. Actual member picking retained SW height 3.26 m and original DXF source identity; each case manifest retains saved revision 103; offline explanation is bound to Gravity case evidence; unknown artifacts return 404 and Nebius proposals return 403. TypeScript, targeted ESLint and two UI regression tests passed. Earlier restricted backend test execution stalled in Windows asyncio local socket initialization; the complete suite passed with local loopback access and cloud budget explicitly set to zero.

Preservation: 9,768 pre-existing database rows checked against a SQLite backup; zero changed or missing. Both review revisions retain all 51 original component bodies. All drawing bytes match SHA-256 614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18. Zero new paid inference calls.

Solver evidence includes actual model.tcl, node/member/reaction files, stdout/stderr, exit/convergence codes, run IDs, hashes, model revision, CAD source identity and independent matrices. Each saved case manifest is bound to the exact model revision and input record. Numerical evidence and file hashes are in numerical-evidence.json; browser and preservation records are alongside this report.

Unsupported: slab load sharing or plate/shell FEA, unknown load paths, foundation/support behavior beyond explicitly fixed bases, out-of-plane or rotated/sloping assemblies, long/unapproved offsets, releases, nonlinear behavior, buckling, physical connection capacity, whole-building FEA, reinforcement/soil/capacity and IS/US design compliance. Synthetic values do not establish real material or support properties. Engineering approval remains DISABLED.

Milestone complete. Stop for review; no further phase or paid inference authorized.

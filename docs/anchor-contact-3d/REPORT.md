# Three-DOF plate contact and four-anchor mechanics — local review

Open [project 787](http://localhost:3001/projects/787/workspace) → **Analysis** → **3D base plate contact + four individual anchors**. Current saved synthetic result is **351**, model revision **91**. This separate review copy preserves all 45 component objects and origin from project 786, revision 89. Original project geometry, revisions, calculations and OpenSees artifacts remain intact.

## Actual geometry and blocked engineering case

The actual saved base plate is **650 × 650 × 25 mm**. Four declared anchor positions are **(−0.24,−0.24), (−0.24,+0.24), (+0.24,−0.24), (+0.24,+0.24) m** relative to the column center. These are previously declared unverified locations, not saved physical bolts.

The plan geometry is now supported by the three-DOF model. Actual analysis remains **BLOCKED** because effective contact stiffness/calibration, each anchor axial stiffness/source and a reviewed fixed-ground tension load path are absent. Actual demands remain linked to immutable interface **315** and OpenSees **3.8.0** evidence: **N=30 kN**, **V=−10.765081 kN East**, **Mx=0**, **My=−11.753694 kN·m about North** at the saved column base. No benchmark properties or forces are assigned to that case.

## Supported nominal mechanical model

The massless rigid plate has downward translation **u** and slopes **sx, sy**:

**w(x,y)=u+sx x+sy y**; physical rotations about East/North are **[−sy,sx]**.

Nominal homogeneous compression-only contact is **p=kc max(w,0)**. Each independent tension-only anchor is **Ti=ki max(−w(xi,yi),0)**. Positions, both signed lever arms, individual stiffnesses, sources, fixed spring ground, zero pretension and excluded horizontal shear are explicit reviewed inputs. The endpoint accepts only separately labeled synthetic verification scope; the actual project stays blocked.

The plate rectangle is clipped by the exact contact half-plane. Polygon area and degree-two moments give exact integration of the linear pressure field. A bounded Newton/line-search solve enforces:

**C−ΣTi=N**

**Qy−ΣyiTi+Mx=0**

**−Qx+ΣxiTi+My=0**

Here **Qx=∫x p dA**, **Qy=∫y p dA**. Independent triangle quadrature verifies active area, compression force and both first moments. Pressure and anchor tensions are nonnegative. Complete inputs, active polygon, pressure vertices/samples, individual forces, rotations and iteration residuals are saved.

## Independent benchmark evidence

Five independently worked cases use explicit synthetic **kc=1 GN/m³** and individually declared **10/20 MN/m** springs. These are not inferred concrete/anchor properties.

- **Symmetric:** full contact, u=0.2 mm; **C=84.5 kN**, area **0.4225 m²**, p=**200 kPa**, all anchors slack.
- **Uniaxial:** sx=−0.001, sy=0; half-strip contact, **C=34.328125 kN**, area **0.21125 m²**, pmax=**325 kPa**; two East anchors each **2.4 kN** from explicit identical stiffnesses and openings.
- **Asymmetric:** same plate state but individually unequal East-anchor stiffnesses; tensions **4.8 and 2.4 kN**. Applied **Mx=−0.576 kN·m** balances the unequal transverse spring moment. Equal forces are not assumed.
- **Biaxial:** sx=sy=−0.001; half-square triangular contact, **C=45.770833 kN**, area **0.21125 m²**, pmax=**650 kPa**. Only the northeast anchor is active at **4.8 kN**. Net **N=40.970833 kN**, applied **Mx/My=[+8.589760,−8.589760] kN·m**, rotations **[+0.001,−0.001] rad**.
- **2D reduction:** original **600 × 500 mm** geometry and spring declarations; matches the previously verified 2D solution: **C=22.5 kN**, contact area **0.15 m²**, tensions **4.0 and 2.4 kN**, pmax **300 kPa**, North slope zero.

For the biaxial hand calculation, a=0.325 m and w=−0.001(x+y). Active contact is the triangle x+y≤0. **A=2a²**, **C=(4/3)a³ kc·0.001**, **Qx=Qy=−(2/3)a⁴ kc·0.001**. Anchor opening at (+0.24,+0.24) is **0.48 mm**, so **T=10 MN/m×0.48 mm=4.8 kN**. These independent Decimal calculations reproduce all three applied load components and the saved result. Current residuals are **[7.276×10⁻¹² N, 0 N·m, 1.819×10⁻¹² N·m]**.

See [independent-evidence.json](independent-evidence.json) for all five hand calculations, quadrature comparisons, 2D reduction, actual geometry/blocked inputs and verified source artifact hashes.

## Local verification and preservation

**179 backend tests passed**, including 22 new 3D tests and all earlier OpenSees/interface/contact regressions. Verified signed biaxial equilibrium, exact clipped area, pressure/tension constraints, 2D reduction, proportional scaling, SI/mm conversion, reflection, invalid/nonfinite stiffness and loads, missing sources/load-path review, duplicate/outside anchors, inconsistent lever arms, arbitrary-code rejection and out-of-domain rotations.

**Three browser workflows passed**: complete five-case workflow; saved pressure/rotation/evidence review; and previous 2D workspace regression. Tested actual geometry audit, missing stiffness, forged authorization, each case, half-load scaling, pressure and rotation diagrams, stale inputs, geometry edits, undo/redo, saved model revision staleness, reauthorization, reload and responsive desktop layouts. TypeScript and targeted ESLint passed.

Snapshot comparison checked **9,626 pre-existing rows across 62 tables**: **zero changed or missing original rows**. All 45 source components remain unchanged. Full numerical evidence is immutable and downloadable; the history endpoint omits duplicate benchmark sample arrays only from its response. **Zero paid inference calls**, Git/GitHub operations, commits, deployment or installs.

## Display and limitations

The 3D workspace shows the computed active contact polygon, pressure profile, compression resultant, individual anchor forces and both plate rotations. Synthetic diagrams are offset **1.1 m East** for visibility; this does not move saved geometry. Pressure height is explicitly scaled **0.4 m/MPa**, and plate deformation is **×200**. The region highlight is geometric, not an invented stress-color field.

This is a nominal elastic contact-bed/spring model, not physical concrete/contact FEA or structural capacity design. Horizontal shear/torsion, anchor strength/embedding resistance, concrete breakout/crushing, plate bending, prying, weld behavior, material nonlinearity, footing/soil capacity and IS/US compliance remain **NOT VERIFIED**. Engineering approval remains **DISABLED**. Actual-project analysis stops at the missing-input gate.

Evidence: [browser results](browser-evidence.json), [test results](test-results.json), [preservation audit](preservation-evidence.json). Screenshots: [pressure/forces](screenshots/final.png), [both rotations](screenshots/final-rotations.png), [actual case blocked](screenshots/actual-blocked.png), [benchmark evidence](screenshots/benchmarks.png), [responsive layout](screenshots/responsive.png). Tests used local Chromium. Development stops here for review.

# Four CAD footings and verified reference-point demand transport

Local website: http://localhost:3001/projects/797/workspace · Analysis. Separate copy of project 796 revision 110. Initial copy revision 111; authorized CAD additions revision 112. Engineering approval and IS/US checks DISABLED. Actual soil pressure remains BLOCKED.

Original DXF FOOTINGS_CONCEPT outlines A3/B5 were inspected and explicitly selected in the existing CAD editor. Browser verification supplied synthetic 1200×1200 mm plan dimensions matching the source outlines, depth 450 mm, top Up=0 and bottom Up=-0.45 m, source evidence and geometry-only declarations. Depth/elevation are supplied verification inputs, not inferred from the plan. Preview and exact authorization were required before applying or saving. Undo/redo and revision comparison passed: two additions, zero removals, zero modified components. Both south footings and all original 54 component bodies remain identical.

The four stable mappings are SW 9C→9A, SE AE→AC, NW A5→A3, NE B7→B5, using full drawing-cad source identities. Original OpenSees 3.8.0 analysis #431 in project 794 revision 105 remains the immutable demand source. Slab/frame source geometry and drawing/review hashes are rechecked; no new solver run is presented as necessary for a static reference transform.

Explicit reference idealization: exact saved column-base centre O, engineer-declared concentric intermediate plate/interface P, and corresponding saved footing underside centre Q. In this verification O=P at Up=0, Q at Up=-0.45 m. The intermediate reference does not create or validate a saved physical base plate. Assumptions/sources and individual review acknowledgments are required. Wrong or duplicate mappings, wrong column-base elevation, wrong underside depth, laterally displaced or out-of-domain intermediate reference, missing source, unreviewed links and nonfinite values are rejected.

Sign and coordinate conventions:
- Saved coordinates are right-handed East/North/Up metres. Force components are N; moment components are N·m.
- Solver reactions act on the structure. The applied foundation demand is the opposite wrench: F=[-R_E,0,-R_Up]. Compression N is reported as -F_Up.
- A source analytical positive moment is about -North: reaction ENU My=-M_source; opposite foundation demand ENU My=+M_source.
- r=old reference−new reference. M_new=M_old+r×F, while F_new=F_old. Stating r in the reverse direction without changing the sign would be incorrect.
- Sequential column→declared-interface→footing transport is compared with direct column→footing transport. Each wrench is checked about a common global origin; totals are independently summed component by component.

Transported demands at footing underside (synthetic reference assumptions, not capacity or soil pressure):
- drawing-cad:614f117ae2a74794:9C → drawing-cad:614f117ae2a74794:9A: N=29.953701030 kN; V_E=-9.961989189 kN, V_N=0.000000000 kN; Mx=0.000000000, My=-15.340699039, torsion Mz=0.000000000 kN·m.
- drawing-cad:614f117ae2a74794:AE → drawing-cad:614f117ae2a74794:AC: N=30.046298970 kN; V_E=9.961989189 kN, V_N=0.000000000 kN; Mx=0.000000000, My=15.076794911, torsion Mz=0.000000000 kN·m.
- drawing-cad:614f117ae2a74794:A5 → drawing-cad:614f117ae2a74794:A3: N=29.953701030 kN; V_E=-9.961989189 kN, V_N=0.000000000 kN; Mx=0.000000000, My=-15.340699039, torsion Mz=0.000000000 kN·m.
- drawing-cad:614f117ae2a74794:B7 → drawing-cad:614f117ae2a74794:B5: N=30.046298970 kN; V_E=9.961989189 kN, V_N=0.000000000 kN; Mx=0.000000000, My=15.076794911, torsion Mz=0.000000000 kN·m.

For SW/NW, the additional My is 0.45×(-9.961989189 kN)=-4.482895135 kN·m. Adding the source foundation moment -10.857803904 gives -15.340699039 kN·m. For SE/NE, the reversed shear adds +4.482895135 to +10.593899776, giving +15.076794911 kN·m. No scalar moment or shear is discarded. Mx/Mz are zero for this planar case; the generic method is separately benchmarked for nonzero mixed-axis moments and torsion.

Independent hand benchmarks:
- F=[0,0,-100000] N, old=[0.2,0,0] m, new=origin: r×F=[0,+20000,0] N·m.
- F=[10000,0,-30000] N, Mold=[0,10000,0] N·m, old Up=0,new Up=-0.45: Mnew=[0,14500,0] N·m. N–mm check: 10,000,000+450×10,000=14,500,000 N·mm.
- F parallel to r gives zero offset couple; original moment remains unchanged.
- F=[0,10,0] N at East offset 2 m gives torsion Mz=20 N·m.
- General 3D: F=[10,20,30] N, Mold=[3,4,5] N·m, O=[2,-3,4] m,Q=[-2,1,-1] m: r=[4,-4,5], r×F=[-220,-70,120], Mnew=[-217,-66,125] N·m.
- Reversed-reference transport restores the original moment; sequential/direct transport and proportional half loads agree. Invalid/nonfinite vectors are rejected.

Independent global-origin source and transported moment totals are [-240000,360000,approximately 0] N·m for the full saved 120 kN gravity case. The stored component-wise residual is [0,0,0] N·m. Each retained force is unchanged by transport. This is static wrench equivalence, not a 3D stiffness/soil solution.

3D workspace shows the original CAD slab/beams/columns, four reviewed footing envelopes, reference planes and markers, and symbolic transport arrows. Coincident column/declared interface references are labeled together. Demand magnitudes and signs are authoritative numerical values in the result panel; planes are geometric references, not stress colors. Long source/mapping/benchmark evidence is expandable.

Authorization/staleness: exact saved proposal hash, current original source evidence and current geometry are required. A newer saved mapping stales old results and rejects obsolete proposals. Draft edits display STALE and disable authorization; unsaved CAD changes, previews and revision comparisons block transport. The authorization checkbox remains disabled during proposal refresh to prevent consent being reset mid-refresh. Save/reload and explicit reauthorization passed.

Tests: 398 prior and new backend engineering regression tests passed; final 18 mapping/transport tests passed with the complete mixed-axis benchmark. Browser geometry workflow passed (48.9 seconds), and transport workflow passed including source reference review, authorization, planes, invalid mapping/elevation, forged/obsolete rejection, saved reload, stale mapping and responsive 1280 px layout. TypeScript and targeted ESLint passed. No page errors in passed browser runs.

Preservation: 9,850 pre-existing database rows were compared against the snapshot. No rows are missing and no original model, revision, solver/calculation, drawing or existing message rows changed. Three operational metadata differences were observed during the session: updated_at on projects 792/796 and one project conversation next_sequence counter. These are explicitly listed in preservation-evidence.json; the report does not claim every database row is identical. All original 54 components remain byte-equivalent as JSON bodies; only north CAD footings A3/B5 were added. DXF bytes match in original/copy projects. No paid inference, installations, GitHub operations, commits or deployment.

BLOCKED/unsupported: physical base-plate/anchor/column-footing resistance; concrete strength, reinforcement, footing flexure or shear capacity; soil-bearing capacity, contact stiffness, settlement or actual soil-pressure distribution; nonlinear, whole-building or code-compliance/safety approval. A mathematical wrench transport cannot prove the connection can transmit that wrench. The north foundation depth/elevation and transfer assumptions are synthetic verification declarations. No missing physical/geotechnical input was invented.

Inspect numerical-evidence.json for source audit, stable identities, explicit reference vectors, benchmark hand answers, all transported demands, per-wrench/global residuals and exact saved proposal binding. Browser and preservation evidence are alongside this report.

STOP for review.

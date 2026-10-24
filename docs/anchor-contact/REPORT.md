# Compression and anchor-tension benchmark — local review

Open [project 786](http://localhost:3001/projects/786/workspace) → **Analysis**. This is a separate copy of project 785, revision 88. Current synthetic benchmark evidence is analysis **321**, copied geometry revision **89**. All 45 source component objects and origin are unchanged; original solver and interface evidence remain intact.

## Actual project: blocked, no forces invented

The copied project reads original interface **315** and its OpenSees provenance: **N = 30 kN**, **V = −10.765081 kN**, **M = +11.753694 kN·m about −North**. Four synthetic anchor locations were previously declared; no physical anchor objects, stiffnesses or resistances were saved.

The actual project cannot be analyzed with the supported benchmark assumptions. Missing inputs are explicit effective contact stiffness and its source; each anchor’s axial stiffness and source; a reviewed fixed-ground tension load path; and effective lever-arm/active-plane declarations. Existing anchors have nonzero North offsets; the implemented model supports only one planar centerline and excludes biaxial coupling. The UI lists these issues and keeps the actual case **BLOCKED**. Benchmark stiffnesses, loads and geometry are never assigned to the actual project.

## Narrowly supported mechanical model

A **separate synthetic 600 × 500 mm nominal massless rigid plate** uses downward displacement **w(x)=u+θx**, nominal elastic compression contact **p(x)=kc max(w,0)** and each independent anchor **Ti=ki max(−w(xi),0)**. Anchors act only in tension; negative pressures and tensions are prohibited. Every signed lever arm must equal the explicitly declared position relative to the column-center reference. All anchors lie on the North centerline.

Contact is integrated exactly over the active compression interval. A bounded Newton/line-search active-set solution enforces **C−ΣTi=N** and **Q−ΣxiTi+M=0**, where **Q=∫x p dA**. Independent two-point Gauss integration checks force and moment equilibrium. Iteration residuals and the complete input record are saved. This is a nominal spring idealization, not plate/contact FEA or calibrated concrete behavior.

The explicit synthetic contact stiffness is **kc=1 GN/m³**. Individual anchors have positions/stiffnesses **−240 mm / 10 MN/m**, **−200 mm / 20 MN/m**, **+200 mm / 20 MN/m**, and **+240 mm / 10 MN/m**. Each value has its own source declaration. Fixed spring ground, zero pretension, small rigid-plate displacements and excluded shear are reviewed assumptions. No equal-force allocation is assumed.

## Independent benchmark calculation

Prescribe **u=0**, **θ=−0.001 rad**. Contact spans **−300 to 0 mm**, with maximum pressure **300 kPa**:

- **C = ½ × 300,000 Pa × 0.3 m × 0.5 m = 22,500 N**.
- Contact centroid **−0.2 m**; **Q = −4,500 N·m**.
- Anchor at **+0.2 m** opens **0.2 mm**: **T=20 MN/m × 0.2 mm=4,000 N**.
- Anchor at **+0.24 m** opens **0.24 mm**: **T=10 MN/m × 0.24 mm=2,400 N**.
- Negative-East anchors are slack: **T=0**.
- **N = 22,500 − 4,000 − 2,400 = 16,100 N**.
- **M = 4,500 + 0.2×4,000 + 0.24×2,400 = 5,876 N·m**.

The numerical solution matches these independently worked values. Force residual is **1.535 × 10⁻⁹ N**, moment residual **0 N·m**. Independently integrated pressure and every anchor tension are nonnegative. Decimal hand evidence and source artifact hash checks are in [independent-evidence.json](independent-evidence.json).

## Verification and preservation

**157 backend tests passed**, including 18 new unilateral-model tests and all previous engineering regressions. Tests cover individual tension, zero/slack anchors, compression interval, units, proportional half loads, reversed moment, centered loading, missing/negative/nonfinite stiffness, false load-path assumptions, unsupported North offsets, inconsistent lever arms, duplicate anchors, actual-project scope rejection and out-of-domain rotation.

**Three local browser workflows passed**: complete new benchmark workflow, saved benchmark review, and previous contact-interface regression. Tested missing-stiffness rejection, forged authorization, reviewed inputs, unequal calculated tensions, half-load results, save/reload, staleness, blocked actual project and responsive desktop views. TypeScript and targeted ESLint checks passed.

Snapshot comparison checked **9,613 pre-existing rows across 62 tables**: **zero changed or missing original rows**. All 45 original components remain unchanged. Source solver artifact hashes were verified against local files. No Git/GitHub operations, commits, deployment, paid inference or installs occurred.

## Limitations and stopping point

The diagram is explicitly a separate synthetic benchmark above the saved model; it shows actual benchmark pressure shape and calculated forces, with units, rather than stress colors or actual-project anchor results. Anchor strength, embedment/breakout, concrete crushing, plate bending, prying, welds, footing reinforcement, soil capacity, settlement and IS/ACI/AISC compliance remain **NOT VERIFIED**. Horizontal shear transfer is excluded. Engineering approval remains **DISABLED**.

Actual-project analysis stops because the required mechanical properties and a supported load path are absent. Supplying geometric anchor positions alone is insufficient. No physical connection capacity or foundation safety is claimed.

Evidence: [browser workflow](browser-evidence.json), [test results](test-results.json), [preservation audit](preservation-evidence.json). Screenshots: [synthetic force diagram](screenshots/final.png), [actual-project blocked inputs](screenshots/actual-blocked.png), [responsive view](screenshots/responsive.png). Local browser tests used Chromium.

# Rectangular and square bearing-capacity review

Local project: http://localhost:3001/projects/802/workspace
Source: project 800, immutable revision 115. Review copy: project 802, current revision 122. No original geometry or engineering record was modified.

## Supported method and evidence

The new versioned method is `FHWA_SURFACE_RECTANGLE_PHI_ZERO_V1`. Reference: FHWA GEC No.6, Shallow Foundations (2002), https://www.fhwa.dot.gov/engineering/geotech/pubs/010943.pdf — Eq.5-2, Table5-1 and Table5-2, specifically the **phi=0 row**, printed pp.51–56; shape-factor table is PDF zero-based page61. That row uses **sc=1+B/(5L)**, not the nonzero-friction expression. Implemented scope is a rough rigid horizontal surface footing, homogeneous undrained total-stress half-space, phi=0, vertical concentric compression, B<=L<5B. Square designation requires B=L. Longer rectangles are rejected rather than silently converted into strips.

Equations: Nc=pi+2; sc=1+B/(5L); q_ult=su*Nc*sc; A=B*L; Q_ult=q_ult*A. At Df=0 and phi=0, surcharge and unit-weight contributions vanish; net and gross ultimate pressure are equal. Applied pressure=N_total/A. A separately declared global factor defines a **strength-only allowable reference**, q_reference=q_ult/FS. This is not an allowable site pressure or a code design resistance.

### Synthetic square hand calculation

B=L=1.2 m; explicitly prescribed su=50 kPa; phi=0; surface/ground Up=0 m; total vertical load=100 kN including any footing weight; declared reference FS=3. These are synthetic verification declarations, not measured/correlated site data.

- Nc=5.141592653589793; sc=1.2; A=1.44 m².
- q_ult=50*5.141592653589793*1.2=**308.495559215388 kPa**.
- Q_ult=308.495559215388*1.44=**444.233605270158 kN**.
- Strength-only reference=**102.831853071796 kPa**, or **148.077868423386 kN**.
- Applied pressure=100/1.44=**69.444444444444 kPa**.

### Synthetic rectangle

B=1.2 m, L=2.4 m, otherwise identical inputs: sc=1.1, A=2.88 m², ultimate pressure=**282.787595947439 kPa**, ultimate force=**814.428276328623 kN**, strength-only pressure reference=**94.262531982480 kPa**, applied pressure=**34.722222222222 kPa**.

Verification includes an expanded high-precision Decimal calculation separating the strip term and shape increment, a separately evaluated limiting bearing factor, and N/mm²–N unit conversion. Tests verify strength/load/factor scaling, quadrupled area under doubled dimensions, reference-elevation translation and the zero unit-weight contribution within this scope. The shape correction is an established reference formulation; checking its implementation is not an independent physical soil experiment or a new 3D collapse solver. Full source inputs/results: numerical-evidence.json and browser-numerical-evidence.json.

## Scaling-description correction

The earlier archived strip evidence had stale text: the doubled-strength case declared su=100 kPa numerically but retained a source description saying 50 kPa; analogous geometry/load/factor descriptions could retain defaults. The test fixture generator now generates descriptions from the actual scaled values. Corrected strip cases are included in numerical-evidence.json, with explicit confirmation that the original numerical results are unchanged. The original archived JSON and all immutable database records remain untouched. This report is their provenance erratum.

## Workflow and safeguards

Open Analysis → Advanced analysis → Square / rectangular bearing. Load the clearly labeled synthetic verification inputs, review all values and sources, preview the proposal, then explicitly authorize that exact saved proposal. Loading and request states lock inputs; no late refresh can silently mark an intervening edit current. Every result binds to the exact revision, source drawing/review hashes, copied/reference soil-profile hashes, input/source declarations and proposal hash. A new proposal invalidates older authorization. Changed inputs clear the owned diagram and mark results stale. Persisted inputs/evidence reload from the backend.

Actual CAD pressure/capacity remains BLOCKED. Strength, loads, dimensions, reference planes and source records must be explicit. Unknown groundwater, corrections, layered soil, nonzero friction/embedment, eccentricity, horizontal forces, any moment/torsion, nonzero slopes, invalid dimensions, missing source text, unreviewed assumptions and actual physical connection load paths are rejected. No site soil properties are taken from copied synthetic profiles. The model assumes only a synthetic directly applied load at the bearing plane; it does not validate column/plate/footing transfer.

The 3D viewer shows the finite footprint, an applied-load arrow, a clearly labeled ultimate-reference arrow (not an actual reaction) and an illustrative failure-section schematic. No soil stress/deformation or failure surface is numerically computed. The finite diagram has scoped clearing so late reads in hidden legacy panels cannot erase it; other non-null analysis diagrams can still replace it. The strip UI filters by its own method so it cannot label finite forces as kN/m.

## Tests and preservation

- **232 backend tests passed**, covering new finite calculations/API authorization and existing strip, bearing/contact, settlement, soil-profile, gravity, unequal-frame and slab regressions, including actual local OpenSees runs. See backend-tests.txt. No numerical OpenSees method changed.
- **325 frontend tests passed across 65 files**; final targeted finite-panel test also passed after loading protection. TypeScript checking passed. See frontend-tests.json. Existing model undo/redo, edit staging, permissions, revisions and Copilot regressions remain intact.
- Browser workflow exercises square/rectangle calculations, independent numerical comparisons, invalid-input rejection, original-project method blocking, wrong/obsolete proposal hashes, load scaling, stale diagram clearing and save/reload at 1600px and 1280px. Screenshots are genuine local browser captures.
- Database audit: **10,143 original rows unchanged; no original rows missing**. New records belong to the separate review project. The 56 copied components exactly equal source revision115, including all CAD footings. Original and copied DXF bytes match SHA256 `614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18`. Details: preservation.json. Backup: .cache/rectangular-bearing/dev-before.db.
- An initial review-copy source binding pointed to an inconsistent inherited revision/profile pair. It was corrected by adding revision122; revision121 remains immutable. Original project800 and all of its evidence remain unchanged. Test attempts add immutable synthetic proposal/result records only in project802.

No installation, Git operations, commits, deployment or paid AI. No soil suitability, actual foundation safety, concrete/anchor/footing strength, settlement combination or IS/US compliance is enabled. **Engineering approval remains DISABLED. Stopped for review.**

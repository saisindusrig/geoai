# RC footing nominal flexure — local review milestone

Review website: http://localhost:3001/projects/804/workspace . Open Analysis → Advanced analysis → RC footing nominal flexure. Source project 803 and all earlier projects remain unchanged.

## Scope and distinctions

The actual saved synthetic CAD footing is 1200 × 1200 × 450 mm, with the original centered 300 × 300 mm column envelope. All 56 copied components retain their stable IDs and drawing provenance. Reinforcement is a temporary synthetic analytical layout, not saved construction detailing or a modification of the footing geometry. Actual concrete and steel inputs remain blank.

The inherited full-width column-face bending demand is **12.15 kN m, unfactored** (10.125 kN m/m). It is shown only as a source reference. The separate **250 kN m** action is an independently declared synthetic nominal-equilibrium target, not a factored version of that demand and not a code design action. No ratio is treated as an adequacy verdict.

## Mechanical model and evidence

Singly reinforced rectangular section; no axial section force, compression steel, prestress or orthogonal mat. Plane sections remain plane. Concrete tension ignored. Declared rectangular compression block: alpha=beta=0.85; extreme compression strain 0.003. Elastic–perfectly plastic steel, Es=200000 MPa, fy=500 MPa. Synthetic cylinder strength fc=25 MPa. Supported fc range is narrowly 20–28 MPa; yielded steel only, with explicit declared benchmark strain bound 0.05. That bound is not certified steel ductility evidence.

The archived [FHWA-HRT-05-056 discussion of rectangular stress blocks and strain compatibility](https://www.fhwa.dot.gov/publications/research/infrastructure/bridge/05056/chapt3a.cfm) documents the mechanics basis. It is not a claim of current ACI or IS compliance. Constitutive assumptions are synthetic; numerical agreement is not experimental validation of site materials.

For eight 20 mm straight bottom bars and 75 mm cover:

- d = 450 − 75 − 20/2 = **365 mm**.
- As = 8 π 20² / 4 = **2513.274122872 mm²**.
- T = As fy = **1256637.061436 N**.
- a = T/(0.85 fc b) = **49.279884762 mm**.
- c = a/0.85 = **57.976335014 mm**.
- eps_s = 0.003(d−c)/c = **0.01588701657**, above yield strain 0.0025 and below the declared 0.05 bound.
- C = 0.85 fc b a = T; reported force residual **0 N**.
- Mn = T(d−a/2)/10^6 = **427.709062636 kN m** — nominal mechanics resistance only.
- For the independent 250 kN m nominal target, inverse equilibrium gives **1424.356469288 mm²**, c=32.857127319 mm and eps_s=0.03032610272. This is NOT code-required design steel.
- Eight bar centerlines are spaced **147.142857 mm**, purely a geometric arrangement. No code spacing/minimum steel check is implemented.

Independent checks include a 40-digit Decimal hand calculation, bisection of C(c)−T(c) using the strain-compatible steel law, a separate inverse bisection in neutral-axis depth, SI/N-mm conversion, and proportional-width/steel/action scaling. Both force equilibrium and nominal target reconstruction are checked. Source implementations and complete inputs/outputs are retained in immutable proposal/result rows with SHA-256 digests.

## Review controls and restrictions

Synthetic input loading is explicit. A source/assumption checkbox precedes preview; a second exact-proposal authorization precedes calculation. Any input edit invalidates consent and removes its diagram. Changed model revision, drawing/review evidence, source demand or newer proposal makes prior results stale. Saved results retain their original evidence. Dirty model/preview/revision comparison blocks calculation.

Country, jurisdiction, standard and edition may be recorded only as an explicit complete context. They do not change the synthetic stress block, enable factors or certify compliance. Nominal resistance and nominal-equilibrium target steel are separate from design strength and code-required steel; those latter outputs are null/disabled.

Unsupported: actual connection transfer, reinforced-concrete footing safety, strength factors, minimum reinforcement, detailing, development/anchorage, cracking, one-way shear, punching, physical bar strength approval, soil suitability and IS/US compliance. Engineering approval remains DISABLED.

## Local verification

- **284 backend tests passed**, including 18 new RC service/API tests and existing footing, soil, slab-transfer, unequal/gravity-frame and actual local OpenSees regressions. One existing Starlette/httpx deprecation warning; no installation performed.
- **329 frontend tests across 67 files passed**, including new review/blank-material/staleness tests and existing editor undo/redo/revision tests. TypeScript noEmit passed.
- Actual Chromium workflow at **1600×1000 and 1280×900**: blank actual materials, source demand distinction, explicit preview/authorization, bar layout, ten invalid input cases, wrong-hash and superseded-proposal rejection, action change to 300 kN m, stale diagram blocking, restoration to 250 kN m, reload persistence and full-model visibility restoration.
- No geometry edit was needed for this milestone; existing editor undo/redo regression coverage passed. Immutable analysis records are not undone or deleted.
- Initial browser test exposed an unrounded demand label; fixed. Screenshot review exposed an opaque-pass overlay occlusion; the RC centerline overlay now uses the translucent render pass with depth testing disabled. This scoped display correction does not affect numerical methods or saved geometry. Gold x-ray line widths are illustrative; declared bar diameters and their synthetic surfaces retain actual metric geometry.

## Preservation and artifacts

`preservation.json` compares every original row by primary key and full contents against the consistent pre-work SQLite backup. **10,208 original rows unchanged; none missing.** All 56 copied components equal the source and both drawing byte hashes match. Only the separate review project, its scenario/generated file/revision, copied source records and new immutable review evidence are added. See final preservation JSON for exact added-row counts.

See `numerical-evidence.json`, `browser-evidence.json`, `frontend-tests.json` and `screenshots/`. No Git operations, deployment, installations, paid inference or material-property promotion were performed. Stop here for review.

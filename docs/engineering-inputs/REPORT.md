# Real project engineering input workflow — local review

Review website: http://localhost:3001/projects/788/workspace. Open **Analysis**, then **Actual connection · engineering inputs**. Use **Fit actual connection geometry** for an isolated inspection; **Show full saved model** restores the surrounding members. This is a separate copy of project 787, which preserves the inherited physical geometry and original interface/solver evidence from projects 785 and 784.

## Delivered

- Structured, persistent input drafts for each of the four stable declared anchor identities, concrete contact and mechanical idealization. No contact/anchor stiffness defaults.
- Explicit anchor diameter, effective embedment, threaded tensile area, material designation, steel modulus, individual effective axial stiffness, tension/opening applicability bounds and tension-load-path description.
- Contact stiffness in N/m³, concrete material identification, contact-law justification and pressure/compression applicability bounds. Concrete strength and soil modulus are never automatically converted into contact stiffness.
- Evidence categories: measured, manufacturer data, engineer-declared assumption and synthetic verification. Each property requires source identification, method, applicability and reviewer attribution. GeoAI does not authenticate source documents or certify user-entered declarations as experimental verification.
- Missing-input explanations grouped by saved geometry, contact model, mechanical assumptions and the four individual anchors. Incomplete drafts can be saved; synthetic provenance blocks actual calculation.
- Exact-hash authorization only after server validation. The bounded, existing 3D contact kernel is reused unchanged. Force/moment equilibrium and independent triangle quadrature are checked before publication. Responses exceeding declared contact/anchor applicability bounds are rejected.
- Immutable input and result records, optimistic draft concurrency, exact model/source hashes, authorization attribution and stale evidence after input, source or revision changes. Run authorization is idempotent and does not modify the input evidence.
- Actual computed pressures/anchor forces, rotations, contact area and SI equilibrium residuals have a gated display path for future complete inputs. **That path was not run on the saved actual project: physical inputs are unavailable.**
- Close connection camera, temporary display isolation of the saved column/plate/footing, explicit display scale for future pressure diagrams and expandable source evidence. Geometry remains unchanged.

## Actual source evidence and present blocker

Source interface **315**, source revision **88**, inherited from the real OpenSees **301** calculation, source model revision **86**, solver **3.8.0**. Every saved source solver artifact was rehashed and matched its immutable manifest; details are in `independent-evidence.json`.

Retained source actions at the column-base reference point:

- N = **30.000000 kN**, compression.
- East shear = **−10.765080571577306 kN**; displayed magnitude **10.765081 kN**.
- Moment about East/North = **[0, −11.753693592818216] kN·m**; displayed magnitude **11.753694 kN·m**.
- Plate = **650 × 650 × 25 mm**; footing = **1200 × 1200 × 450 mm**.
- Declared anchor lever arms are **(±240, ±240) mm**, with four stable IDs. These are prior **synthetic locations**, not measured/saved physical bolt objects. Prior diameter 20 mm and embedment 300 mm are also synthetic; neither fills the actual input form.

The final review is **BLOCKED_MISSING_ENGINEERING_INPUTS**, input record **354**, current model revision **93**. All physical stiffness values remain blank. **Zero actual contact results** exist for project 788.

To progress, supply source evidence for saved dimensions/anchor locations; each anchor's dimensions, threaded area, material/modulus and effective embedment; individual effective axial stiffness with derivation/calibration and valid force/opening range; a reviewed fixed-ground tension load path; concrete identity and justified homogeneous compression-bed stiffness with limits; and explicit reference-plane, rigid-plate, zero-pretension and shear-exclusion assumptions. Changing the declared arrangement requires a separate geometry/source-demand review.

The retained eccentricity magnitude M/N = **391.789786 mm** exceeds the plate's **325 mm half-width** (kern = **108.333333 mm**). Compression alone cannot equilibrate that N/M demand. No anchor forces or contact pressure were invented to resolve it.

Horizontal shear transfer and moment transport from shear to the plate underside are **UNSUPPORTED** and excluded. Anchor strength, embedment resistance, concrete breakout, plate bending/prying, weld adequacy, footing/soil safety and IS/ACI/AISC compliance remain **NOT VERIFIED**. Engineering approval stays **DISABLED**.

## Independent numerical evidence

Existing mechanical verification was repeated using independent Decimal hand integrals and triangle quadrature. The numerical solver equations were not changed. These are separate **synthetic verification cases**, never actual-project physical properties:

- Symmetric full contact: 650 mm square, kc = 1 GN/m³, w = 0.2 mm. C = **84.5 kN**, p = **200 kPa**, area = **0.4225 m²**, each anchor T = 0.
- Biaxial triangular half contact: C = **45.770833333 kN**, area = **0.21125 m²**, pmax = **650 kPa**, only the fourth spring T = **4.8 kN**. Rotations East/North = **[+0.001, −0.001] rad**.
- Asymmetric individual springs: T3 = **4.8 kN**, T4 = **2.4 kN**; forces are not assumed equal.
- 2D reduction: C = **22.5 kN**, T3/T4 = **4.0/2.4 kN**, net N = **16.1 kN**, moment magnitude = **5.876 kN·m**, matching the previous planar benchmark.
- All five preserved reference cases satisfy independent force and both-moment equilibrium within **1×10⁻⁶ N / N·m**. Unit-conversion, scaling, unilateral pressure/tension and coordinate checks pass.

## Tests and preservation

**213 backend tests passed:** 34 new input/authorization/applicability tests and 179 existing contact, slab transfer, gravity, eccentric and beam/frame regression tests. Existing local OpenSees was used by the FEA regression suite. No software installed. One existing Starlette dependency deprecation warning remains; no dependency changes were made.

**Three browser workflows passed** at localhost:3001:

1. Separate project draft edits, synthetic-input rejection, server-side blocked-run rejection (422), forged authorization (409), save/reload, four individual anchor forms, geometry preview/apply, undo/redo, revision saving and stale authorization (409). No actual result is exposed and no runtime browser errors were captured.
2. Final saved review, connection focus/full-model restore, diagram camera and responsive 1600×1000 / 1280×820 layouts. Offscreen pick-point counts are not a total model-component count; preservation is independently checked against the saved document.
3. Read-only original project 787 regression: its saved synthetic 3D pressure and rotation diagrams still work, with C = 45.770833 kN, pmax = 650 kPa and area = 0.21125 m².

TypeScript and ESLint checks pass for the modified UI files and input workflow tests.

Database comparison across **62 tables / 9,667 pre-existing rows**: **zero changed, zero missing**. All **45 source component objects and origin coordinates** match the original revision exactly. Original projects, calculations, revisions and the 22-record existing inference usage ledger are preserved. **Zero live inference calls**, no Git/GitHub operations, commits, deployment or paid service use.

## Review artifacts

- `screenshots/final.png` — saved actual input workflow and focused geometry.
- `screenshots/anchor-inputs.png` / `contact-inputs.png` — blank physical inputs and source requirements.
- `screenshots/responsive.png` — compact desktop layout.
- `screenshots/preserved-benchmark.png` — original numerical benchmark regression.
- `browser-evidence.json`, `independent-evidence.json`, `preservation-evidence.json`, `test-results.json` — inspectable local evidence.

Stopped at this milestone. Actual contact calculation remains blocked pending physical information and explicit authorization. No capacity or design-code systems were implemented.

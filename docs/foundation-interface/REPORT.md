# Steel-to-concrete foundation interface — local review

Open [project 785](http://localhost:3001/projects/785/workspace) → **Analysis** → **Steel column → base plate → concrete footing**. This is a separate copy of project 784, revision 86. Current interface evidence is calculation **309**, copied model revision **88**, linked to immutable OpenSees source **301**. All 45 source component objects and the source origin are unchanged.

## What is implemented

The interface reads stable saved IDs, dimensions, parent/reference relationships, positions and object status. The selected `column-sw` has a saved **650 × 650 × 25 mm** base plate and **1.2 × 1.2 × 0.45 m** footing box. Their centers and column/plate/footing contact elevations align. All are **conceptual/unverified**, not engineered steel/concrete capacity models. No anchor bolts or reinforcement bars exist in the original saved model.

The UI requires explicit dimensions matching the saved geometry, dimension sources, plate steel E/yield strength, concrete strength and cube/cylinder basis, anchor status and geometry, reinforcement information, soil assumptions, contact idealization and review authorization. Undefined reinforcement/soil information must be declared as excluded; this does not supply missing design data. The synthetic fixture leaves review/authorization boxes unchecked. New anchor coordinates are stored as engineering-input declarations, displayed with their embedment and clearly distinguished from original model objects.

Actual source support reactions are converted into opposite actions on the connection at the saved column-base reference point:

- Compression **N = 30.000000 kN**.
- East shear **V = −10.765081 kN**.
- Moment about −North **M = +11.753694 kN·m** (ENU moment vector is about +North with the opposite signed scalar).

The demand record preserves all components, solver version **OpenSees 3.8.0**, run ID, source analysis/revision, numerical comparisons and artifact hashes. Translating full shear/moment to the plate underside and footing is not verified. A force-path overlay shows the actual saved column, plate and footing outlines, declared anchor locations/embedment, symbolic demand arrows and actual values. No stress colors are used.

## Independently verified narrow calculation

The full source reaction has nonzero shear and moment. Full-reaction concentric mode therefore **rejects it**. The supported review explicitly isolates **only its axial component**, retains the excluded demands and labels the complete connection **NOT YET VERIFIED**.

Nominal full-contact, massless rigid plate assumption:

**A = 0.65 × 0.65 = 0.4225 m²**

**p = N/A = 30,000 / 0.4225 = 71,005.917160 Pa = 71.005917 kPa = 0.071005917 MPa**

Independent Decimal calculation in millimeters: **30,000 N / (650 × 650 mm²) = 0.071005917 N/mm²**. Integrating pressure over the plate returns **30 kN**, with independent equilibrium error **−3.64 × 10⁻¹² N**. The application also integrates 64 equal area patches and verifies N–mm²/SI equivalence.

Known-answer benchmark: **100 kN / (500 × 400 mm²) = 0.5 N/mm² = 500 kPa**, with integrated reaction **100 kN**. Half-load scaling, invalid/uplift loads and invalid dimensions are tested. This is pressure arithmetic, not actual plate/contact FEA or a bearing-capacity formula. Anchor holes/contact loss are not represented; the result uses nominal gross rectangular area. Steel and concrete strength declarations are **unused** by this calculation.

The fixture explicitly declares synthetic plate **E = 200 GPa, yield = 250 MPa**, concrete **30 MPa cylinder strength**, and four new **Ø20 mm** anchor positions at **±0.24 m** East/North from the column center with **300 mm** embedment. These are user-reviewable synthetic declarations, not discovered material properties or saved original bolts. Footing reinforcement and geotechnical properties remain undefined and excluded.

## Verification and preservation

- **117 backend tests passed**: 33 new interface tests plus 84 prior solver tests. The final interface recheck passed after adding complete model matching and demand reference-point metadata.
- **Four local browser workflows passed**: the new foundation workflow, final saved foundation review, original frame workspace regression and original slab-transfer regression. Tests cover missing sources, geometry mismatch, unsupported full moment demand, forged authorization, diagram selection, material change staleness, unchanged pressure when unused yield strength changes, undo/redo, save/new revision, reapproval, reload and 1600 × 1000 / 1280 × 820 layouts.
- TypeScript and targeted ESLint checks passed. Database comparison checked **9,588 original rows across 62 tables**: **zero changed or missing original rows**. All original model components, revisions, calculations and solver files remain intact.
- **Zero paid inference calls**, no Git/GitHub operations, commits, deployment or software installation. Existing cloud lock remains in place.

See [independent numerical evidence](independent-evidence.json), [browser evidence](browser-evidence.json), [test results](test-results.json), and [preservation evidence](preservation-evidence.json). Source Tcl/output hashes were verified against local files. Evidence download is available in the UI.

## Limitations and review

Moment-bearing distributions, anchor tension/shear, plate bending, weld behavior, footing reinforcement, soil capacity, settlement and physical connection/foundation safety are **NOT YET VERIFIED**. The footing remains a conceptual box with no validated reinforced-concrete design. There are no IS/ACI/AISC checks, strength utilization, automatic design changes or engineering approval. This calculation must not be used as verification of the full reaction case.

Screenshots: [force path and pressure](screenshots/final.png), [unsupported checks](screenshots/unsupported.png), [responsive view](screenshots/responsive.png). Tests used local Chromium. Use Chrome/Edge if the Codex in-app browser cannot load local assets. Development stops at this milestone for review.

# Rigid base-plate contact assessment — local review

Open [project 785](http://localhost:3001/projects/785/workspace) → **Analysis**. Current assessment **315** uses saved revision **88** and original OpenSees evidence **301**, version **3.8.0**. Geometry and solver methods are unchanged.

## Current actual demand

The saved column-sw interface has **N = 30 kN compression**, **V = −10.765081 kN East shear**, and **M = +11.753694 kN·m about −North**. The actual plate is **650 × 650 × 25 mm**.

- **e = M/N = 391.789786 mm**.
- Middle-third/kern limit: **B/6 = 108.333333 mm**.
- Physical footprint half-width: **B/2 = 325 mm**.
- Resultant lies **66.789786 mm beyond the plate edge**.

**Compression-only plate contact cannot equilibrate this full N/M demand.** A nonnegative pressure supported on the plate must have its centroid inside its footprint; this resultant lies outside it. The result is `RESULTANT_OUTSIDE_FOOTPRINT`, with `compression_only_equilibrium = IMPOSSIBLE`. The application returns **no minimum/maximum contact pressures** for this case. **71.005917 kPa = N/A** remains an explicitly labeled axial mean reference, not an equilibrating contact distribution.

Horizontal shear transfer remains separate and **NOT YET VERIFIED**. No anchor tension, anchor moment resistance, partial-contact pressure or physical connection adequacy is inferred.

## Verified full-contact calculation and conventions

For a nominal gross rigid rectangle and uniaxial N/M, only when **|e| ≤ B/6**:

**A = BL; I = LB³/12; p(x) = N/A − Mx/I**, where x is positive East and M is the applied moment about −North. Thus **p(−B/2) = N/A(1 + 6e/B)** and **p(+B/2) = N/A(1 − 6e/B)**.

The scalar e=M/N is measured toward −East; the upward contact centroid has East coordinate **−e**. Independent integration checks **∫p dA = N** and **∫x p dA = −M**, so applied and contact moments sum to zero. Decimal N/mm² conversion separately verifies both edge pressures.

Independent worked example: **N=100 kN, B=600 mm, L=500 mm, M=+5 kN·m** gives **e=50 mm**, **A=300,000 mm²**, **S=30,000,000 mm³**, and edge pressures **0.5 / 0.166666667 N/mm²**, a range of **166.666667–500 kPa**. Integrated force is **100 kN** and resisting contact moment **−5 kN·m**. Reversed moment swaps edges; proportional half N/M retains eccentricity and halves pressure. Zero moment gives **333.333333 kPa**. The kern boundary has a zero-pressure edge and maximum **666.666667 kPa**.

When **B/6 < |e| ≤ B/2**, contact loss is detected and classified `CONTACT_LOSS_PARTIAL_UNSUPPORTED`; no partial-contact pressure is calculated. At the footprint boundary, a finite-area distribution is not invented. Beyond **B/2**, compression-only equilibrium is impossible. Invalid/nonfinite loads, uplift/zero N, invalid dimensions, missing reference/acknowledgement and arbitrary calculation arguments are rejected.

These are synthetic verification examples and a nominal rigid-pressure law, not plate/contact FEA or material-capacity checks. Saved holes/contact loss, biaxial moments, plate bending, shear transport, welds, anchors, footing reinforcement, soil capacity, settlement and IS/ACI/AISC compliance remain unverified. Actual N/M is assessed at the saved column-base reference plane; horizontal shear translation to the plate underside is explicitly excluded. Engineering approval stays **DISABLED**.

## Testing, evidence and preservation

**139 backend tests passed**, including contact known answers, units, signed equilibrium, scaling, boundaries, missing-input rejection, authorization/source staleness and all prior real OpenSees regressions. **Four browser workflows passed**: actual demand assessment; saved assessment and benchmark evidence; existing frame workspace; existing slab workspace. Browser tests covered consent, forged authorization rejection, save/reload, input staleness, disabled stale plots and desktop responsive layouts. TypeScript and targeted ESLint passed.

All **45 original component objects** remain unchanged. Snapshot comparison checked **9,607 pre-existing database rows across 62 tables**: **zero changed or missing original rows**. Prior calculations remain immutable in history; superseded input results are marked stale. Original source solver artifact hashes were verified. **Zero paid inference calls**, Git/GitHub operations or deployment.

Evidence: [independent calculations](independent-evidence.json), [browser tests](browser-evidence.json), [test results](test-results.json), [preservation](preservation-evidence.json). Screenshots: [actual infeasible contact](screenshots/final.png), [verified benchmarks](screenshots/benchmarks.png), [responsive view](screenshots/responsive.png). Local tests used Chromium; open the URL in Chrome/Edge if the in-app browser cannot load local assets.

Development stops here for review.

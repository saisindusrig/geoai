# CAD footing bending-demand milestone

Review website: http://localhost:3001/projects/803/workspace

Source project **802**, immutable revision **122**; separate review project **803**, revision **123**. The 56 saved components and their stable IDs are unchanged. This milestone adds a demand-only statics method, not reinforcement design or a new footing FEA solver.

## Saved geometry and explicit mechanical hypothesis

Selected CAD footing SW: `drawing-cad:614f117ae2a74794:9A`, source entity `dxf:614f117ae2a74794:9A`, dimensions **1.2 × 1.2 × 0.45 m**, center East/North=(0.15,0.15) m, bottom Up=-0.45 m, top Up=0 m.

Reviewed CAD column SW: `drawing-cad:614f117ae2a74794:9C`, source entity `dxf:614f117ae2a74794:9C`, envelope **0.30 × 0.30 × 3.26 m**, same plan center, bottom Up=0 m. These are synthetic CAD envelopes, not verified concrete/steel sections. A coincident center and touching elevations do not prove a physical connection.

For this verification only, the engineer explicitly reviews a **hypothetical direct distributed column patch** on the footing top. Actual steel-column/base-plate/RC-footing load transfer remains BLOCKED. Unknown connections cannot be passed to the demand method. The saved 300 mm envelope is not assumed to describe base-plate contact or a verified monolithic RC column.

## Formulation and independently worked calculation

Version: `CAD_FOOTING_CANTILEVER_DEMAND_V1`. A full-width vertical cut at each column face is treated as a one-way cantilever under prescribed uniform upward **net** pressure. Reference for the idealization: [VDOT ASD Manual, section 4.4.11.1.1](https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/technical-guidance-documents/structure-and-bridge/VDMASD.pdf), which describes footing cantilever action and taking moments of external forces on one side of a column-face section. This reference documents mechanics only; no VDOT/AASHTO/IS/US compliance is implemented.

Explicit synthetic case: column force **N=144 kN** downward; uniform net reaction **q=100 kPa=100 kN/m²** upward; footing self-weight deliberately excluded. No density, concrete grade or footing self-weight is invented. Pressure is prescribed independently and is **not** imported from project802's bearing resistance or any soil-profile result.

- Footing area A=1.2×1.2=**1.44 m²**.
- Integrated upward force qA=100×1.44=**144 kN**, equal to N; vertical equilibrium residual=0.
- Each projection a=(1.2−0.30)/2=**0.45 m**.
- One-metre strip line load w=q×1 m=100 kN/m.
- Column-face moment per metre m=w a²/2 =100×0.45²/2=**10.125 kN·m/m**.
- Full-width cut moment M=m×1.2=**12.15 kN·m**, independently obtained as (q×1.2×0.45)×(0.45/2)=54×0.225.
- The outside-cut upward resultant is **54 kN** on each full-width cut. These cut regions overlap; their four forces must never be summed as independent support reactions. The full-footing 144 kN integration counts each area once.
- At distance s from a column face toward the free edge: m(s)=q(a−s)²/2, reducing from 10.125 at the face to zero at the free edge. This is an idealized strip-demand diagram, not plate/shell stress or deformation.

Separate verification uses rectangular-cell pressure integration at 1, 2, 8 and 32 cells per axis and numerical first moments on each cut, without calling the production face-moment expression. A high-precision Decimal calculation and independent N/mm² units give 0.1×1000×450²/2=**10,125,000 N·mm** for a one-metre strip, equivalent to 10.125 kN·m. Doubling N and q gives **20.25 kN·m/m** and **24.30 kN·m** per full cut. Geometry scaling and coordinate-reference translation are also tested independently; the saved-geometry API rejects dimensions or elevations that do not match its actual selected components.

Sign convention: East/North/Up right-handed axes; upward pressure +Up. Its external first moments on the four cuts are East −My, West +My, North +Mx, South −Mx. Opposite faces cancel globally. Internal resisting cut moments are opposite; the UI reports demand magnitudes without asserting reinforcement placement or adequacy.

## Review workflow and restrictions

Open Analysis → Advanced analysis → CAD footing bending demand. Select saved footing/column IDs and explicitly enter their dimensions, load, pressure and reference planes. Source/evidence fields and two review declarations are required. Preview saves the exact physical-to-analytical mapping; a separate checkbox authorizes that exact proposal hash. The calculation is not performed by preview alone.

Immutable results bind the current revision/document hash, selected component IDs, reviewed geometry and CAD entities, original drawing bytes/review hashes, all input/source declarations and reference-only copied profile hashes. New proposals invalidate old authorization. Input changes immediately mark demand stale, reset consent and clear only the owned diagram. Loading and request states lock edits against late responses. Evidence and inputs save/reload through the backend.

The 3D view uses the **actual saved footing and column meshes**, with reviewed face outlines, projection lines, upward pressure arrows, a downward synthetic load arrow and parabolic moment-demand curves. Numeric values and units remain in the results panel. Diagram ordinates are scaled demand display heights; arrows have illustrative lengths. Neither is a displacement field. Analysis focus temporarily displays the selected pair; Restore complete CAD model returns all existing visibility without editing any component.

Unsupported inputs are rejected: nonconcentric geometry or loads, rotated/scaled/unknown source envelopes, non-square/non-symmetric geometry, invalid or mismatched dimensions, column/footing gaps, missing sources/review, pressure/load disequilibrium, uplift/nonuniform reaction, unknown actual load paths, horizontal force or applied moment, automatic self-weight and real-project classification. No automatic soil-capacity reuse or soil model is involved.

## Tests and preservation

- **266 backend tests passed**, including new independent hand/units/integration/API tests and existing bearing/contact, soil-profile, settlement, slab-transfer, unequal-frame and actual local OpenSees regressions. See backend-tests.txt.
- **327 frontend tests passed across 66 files**; TypeScript no-emit checking passed. Full regression evidence: frontend-tests.json. New tests require explicit footprint/path review, prevent pending-request edits, and enforce stale results/authorization reset. Existing model undo/redo, preview/apply, revision, permissions and Copilot checks are retained.
- Actual local browser workflow passed, including 15 invalid cases, wrong/obsolete hashes, all four face values, doubled load/pressure, stale diagram clearing, save/reload, restoration and 1600/1280px screenshots. See browser-evidence.json.
- All **10,182 original database rows unchanged**, none missing. All 56 components equal source revision122 exactly. Source/copied DXF SHA256: `614f117ae2a74794b128ea983f99f10ed9898a069882666bcdb60ee1a2934e18`. See preservation.json. Pre-work backup: .cache/footing-flexure/dev-before.db.
- New project/scenario/revision, copied reference records and immutable synthetic demand records belong to project803. One new operational usage record is `file.download` for project803; it is not inference. Original FEA/bearing calculations, profiles, conversations, revisions and permissions were not rewritten. No model geometry was edited or model revision saved during browser testing.

## Limits

Calculated demands do not establish reinforcement strength, effective depth, cracking/stiffness, one-way shear, punching shear, contact/anchor/weld strength, actual soil response or foundation safety. Orthogonal cuts are an idealization, not a two-way plate/shell solution. Actual project steel-to-concrete transfer is unverified even where the geometric envelopes touch.

**Engineering approval, reinforcement adequacy, shear capacities, actual footing safety and IS/US checks remain DISABLED/BLOCKED.** No Git operations, commits, deployment, installation or paid inference. Stopped after this milestone for review.

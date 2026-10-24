# Synthetic shallow bearing-capacity benchmark

Local review: http://localhost:3001/projects/800/workspace → Analysis → Shallow bearing resistance.

Project 800 / revision 115 is a separate copy of project 799 / revision 114. All 56 component bodies, four CAD footings, DXF identities and source calculations remain unchanged. All five existing soil-profile versions were copied as unapproved reference versions with original record IDs/hashes retained. No original analysis authorization was carried over to the new model revision. Original settlement, Winkler contact and OpenSees evidence remains preserved in its source project.

## Exact supported formulation

Prandtl undrained, total-stress, φ=0 bearing resistance of an ideal **infinite surface strip**. The supported geometry is a rough horizontal rigid strip of explicit width B on level ground, homogeneous infinite soil, Df=0, vertical concentric line load. It is not a finite rectangular or square footing approximation.

[FHWA GEC 6, Shallow Foundations (2002)](https://www.fhwa.dot.gov/engineering/geotech/pubs/010943.pdf#page=58), equations 5-1 through 5-5, gives the strip factors and gross/net distinction. Equation 5-4 gives Nc=2+π. Table 5-1 at printed page 53 / PDF page 60 rounds the φ=0 row to Nc=5.14, Nq=1, Nγ=0. The evidence file uses zero-based PDF page indices 57 and 59. USACE EM 1110-2-2502 (1989), equations 5-3a/b/c/d, independently corroborates these strip factors. These are mechanics references, not enabled design-code checks.

The implemented subset is:

q0 = γ Df = 0

qu_net = su Nc = su(π+2)

qu_gross = su Nc + q0 Nq + 0.5 γ B Nγ = qu_net

Resistance per unit length = qu_gross B.

Required inputs include explicitly sourced synthetic su, φ, unit weight, B, Df, reference elevation, line load, zero shear/moment/slope, soil/interface/loading idealizations, groundwater exclusion, declared resistance factor/method and applicability. Inputs are finite, bounded and server-validated. Missing sources, rectangular geometry, nonzero φ or embedment, eccentricity, horizontal/inclined loading, layered soil, unknown groundwater and requested groundwater corrections are rejected before authorization.

Groundwater is explicitly excluded from this synthetic idealization. That is not an observation that the actual site is dry. Unit weight is recorded rather than invented or derived; its terms vanish for this surface φ=0 subset. No su is inferred from E, Poisson ratio, unit weight or the prior synthetic profile.

## Ultimate versus allowable/design resistance

The declared synthetic resistance method is GLOBAL_FS_ON_NET_ULTIMATE:

qallow_net = qu_net / FS

qallow_gross = qallow_net + q0.

The factor is explicitly entered and sourced, with FS>1. This is a **strength-only allowable reference**, not an approved site allowable bearing pressure. Settlement/site suitability and other governing limits are not checked. No LRFD resistance, code factors, IS/US compliance or safety approval is implemented. The displayed applied/reference ratio is a mathematical comparison only and has no PASS/SAFE verdict.

## Independently worked benchmark

Prescribed SYNTHETIC_VERIFICATION inputs: su=50 kPa, φ=0°, γ=18 kN/m³, B=2 m, Df=0, vertical line load=150 kN/m, FS=3. No actual CAD footing demand is imported into this case.

- Nc=π+2=5.141592653589793; Nq=1; Nγ=0.
- qu_net=qu_gross=50×5.141592653589793=**257.079632679490 kPa**.
- Ultimate resistance=257.079632679490×2=**514.159265358979 kN/m**.
- Strength-only allowable reference=257.079632679490/3=**85.693210893163 kPa**, or **171.386421786326 kN/m**.
- Applied pressure=150/2=**75 kPa**; applied/reference ratio≈0.875215. This is not a safety conclusion.
- Using the published rounded table factor 5.14 gives 257 kPa; the 0.079632679490 kPa difference is rounding, not a different physical model.
- Independent units: su=.05 N/mm²; qu=.05(π+2)=.257079632679490 N/mm²=257.079632679490 kPa. Multiplying pressure kN/m² by width m yields kN/m, not total force on the illustrated segment.

Independent bearing-factor verification computes general Nq(φ)=exp(π tanφ) tan²(π/4+φ/2), then evaluates the centred zero-friction limit [Nq(h)−Nq(−h)]/[2 tan(h)] for h=.01/.001/.0001/.00001 radians. It converges to Nc without calling the exact Nc implementation. Negative h is a mathematical derivative sample, not a supported negative-friction design case. Nq(0) and Nγ(0) are independently checked. A high-precision Decimal worksheet separately verifies resistance and global-factor arithmetic.

Scaling checks: doubling su doubles ultimate/reference resistance; doubling B doubles resistance per metre while pressure resistance remains unchanged; changing applied load changes applied pressure, not capacity; doubling FS halves the allowable reference without changing ultimate resistance; changing γ leaves this Df=0/φ=0 result unchanged. Inputs, finite-difference convergence, Decimal values, rounding comparison and authorized saved result are in numerical-evidence.json.

This is validation of the stated classical calculation, not a numerical soil-collapse simulation or experimental site validation.

## UI and provenance

The new Analysis panel provides explicit inputs/sources, reviewable saved proposal, exact-proposal authorization, computed resistance, applied stress and expandable immutable evidence. It does not load old soil-profile values into bearing properties. The preserved profile is labelled REFERENCE ONLY.

The 3D view shows a finite 6 m illustration segment of the ideal infinite strip, applied-load arrow, theoretical ultimate-reference arrow and an explicitly illustrative failure schematic. Arrow lengths and mechanism geometry are schematic; they are not computed collapse deformation, stress or an actual foundation reaction. All resistance values remain per metre. Return to preserved CAD model restores the actual component view.

Proposals bind the current saved model, original drawing/model fingerprints, common solver/demand provenance, original profile record and copied reference-profile version/hash. New proposals, edited bearing inputs, changed reference profiles or geometry/source changes stale old results and invalidate old authorization. Unsaved model edits, previews and revision comparison block execution. Results carry their own content hash. Save/reload and exact reauthorization are verified.

Browser testing exposed duplicate deep provenance traversals and two initialization requests. The new panel now loads history/audit together. Shared solver evidence is validated once, while the original model ownership/latest revision and original drawing/review are independently checked and fingerprinted. No validation gate was removed; no persistent caching or solver method changed.

## Actual CAD blockers

The actual four CAD footings are finite rectangles and carry transported axial/shear/moment demands through an unverified physical connection path. This infinite-strip, concentric benchmark does not assess them. Applicable sourced strength/friction data, groundwater/site conditions, verified load transfer, a validated rectangular/eccentric method and geotechnical review remain missing or unsupported. Actual CAD capacity stays BLOCKED, and previous synthetic soil data is never promoted into real-project evidence.

No bearing recommendation, settlement limit, soil suitability, reinforcement/footing strength, anchor/connection capacity, IS/US compliance or engineering approval is provided. Engineering approval remains DISABLED.

## Local test and preservation evidence

- **574 selected backend regression tests passed**, including existing OpenSees, CAD, soil-contact, settlement, profile, model-revision and component regressions. Final **25 bearing/authorization tests passed** after the localized provenance performance fix.
- Browser workflow passed ten unsupported/missing-input cases, forged and obsolete authorization rejection, strength scaling, source-profile staleness, saved reload, responsive layout, rendered schematic and return to preserved CAD. No page errors in the passed run.
- TypeScript and targeted ESLint passed.
- **9,926 pre-existing database rows** compared: none changed or missing. All 56 component bodies and original/copy DXF bytes match. All five source soil-profile versions were copied with identical profile bodies. Paid inference count did not increase.
- No Git/GitHub operations, commits, deployment, installation or paid AI.

Artifacts: numerical-evidence.json, preservation-evidence.json, browser-evidence.json, backend-tests.txt, final-tests.txt, browser-tests.txt and screenshots/.

STOP for review. No additional engineering method or actual-foundation capacity calculation is enabled.

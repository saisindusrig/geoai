# Soil profile and verified elastic settlement — local review

Open http://localhost:3001/projects/799/workspace and select Analysis → Geotechnical profile.

Project 799 / revision 114 is a separate review copy of project 798 / revision 113. All 56 saved component bodies, four CAD footings, DXF source identities and original project records are preserved. The existing OpenSees reaction and demand-transfer evidence remains referenced; source transport record 464 is read without modification. Existing soil-contact calculations remain in their original project and are not added to the new elastic displacement.

## Soil-profile workflow

Profiles contain borehole identity and local ENU location, ground reference elevation, explicit source records, soil layers with top/bottom depths, groundwater observation/reference, applicability and limitations. Unknown groundwater remains UNKNOWN. Unknown basal depth is distinct from FINITE depth and an explicitly declared UNBOUNDED_IDEALIZATION. An infinite half-space cannot be labelled a measured depth.

Each unit weight (kN/m³), elastic modulus (MPa) and Poisson ratio (dimensionless) has its own source ID and classification: MEASURED, CORRELATED, ENGINEER_ASSUMED or SYNTHETIC. Profile-level REAL_PROJECT, UNVERIFIED and SYNTHETIC_VERIFICATION labels are separate. Synthetic properties cannot be reclassified into a real/unverified profile simply by changing the profile label. No property is inferred from drawing geometry, another property or an unsupported correlation. Source strings are provenance declarations, not proof of experimental validity.

The editor supports explicit layer/source addition, layer removal, property editing, local undo/redo and immutable versioned saving. Source references, unique identities, contiguous ordered layers, positive thickness, finite values, material bounds and groundwater evidence are validated server-side. Missing E and Poisson ratio prevent elastic calculation; missing unit weight/groundwater is reported but these values are not used by this first elastic method. The history-loading race found during browser testing was fixed: editing waits for initial profile history, and saved profiles reload in canonical form.

## Narrow validated calculation

This milestone computes centre surface displacement beneath a uniformly loaded **flexible rectangular patch** on a homogeneous, isotropic, linear-elastic infinite half-space. It does not compute rigid-footing settlement, plate contact pressure or a full deformation field. In the display, the synthetic patch is centred at the declared borehole ENU reference; it is not assigned to an actual CAD footing.

The Boussinesq surface point-load displacement kernel is Gzz(r)=(1−ν²)/(πEr). The rectangular centre formula below is independently derived by integrating this kernel, rather than attributed to FHWA as a published rectangular-footing formula. [FHWA-HRT-05-152, Chapter 2](https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/ltpp/05152/chapt2.cfm) provides background on elastic half-space point-load response and distinguishes uniform loading from the pressure distribution under a rigid plate.

Let a=B/2, b=L/2 and q=N/(BL). Integrating 1/r over the four quadrants gives:

I = 4[a asinh(b/a) + b asinh(a/b)]

s_center = q(1−ν²)I/(πE).

The integral I has units m; q and E have units Pa, so s is m. Applied stress integrates exactly to N. The numerical reference independently integrates the point-load kernel over polar area cells: 512/2048/8192 midpoint angular cells, each with eight radial Gauss points. It does not use the rectangular closed-form influence factor. It independently checks integrated area, applied force and centre displacement, recording mesh refinement and discrepancies. Accepted numerical tolerances are 3e−5 relative displacement and 5e−5 relative applied-force error.

Supported bounds are B,L=0.05–20 m, aspect ratio at most 10, positive N≤100 MN, isotropic elastic modulus/Poisson bounds and centre displacement/min(B,L)≤0.01. Load elevation must equal the explicitly declared surface reference. Multiple layers, finite or unknown depth, embedment and nonsynthetic mechanical input cases are rejected for this first benchmark. No layer averaging or apparent modulus is introduced.

## Independent hand benchmark

Explicit prescribed synthetic values, not site investigation data:

- B=L=2 m, N=200 kN, q=50 kPa, E=20 MPa, ν=0.3.
- a=b=1 m; asinh(1)=ln(1+√2); I=8 ln(1+√2)=7.050988696156344 m.
- s_center=50000×0.91×7.050988696156344/(π×20000000)=0.005106008656286539 m = **5.106008656286539 mm**.
- Independent high-precision Decimal calculation uses N, mm and MPa: q=.05 N/mm², E=20 N/mm², a=b=1000 mm and I=7050.988696156344 mm. It gives the same displacement.
- Halving N gives 2.553004328 mm and 25 kPa. Doubling E to 40 MPa gives 2.553004328 mm at unchanged 50 kPa.
- Swapping B/L leaves the centre result unchanged; additional 1×2, 1×4, 1×10 and scaled square cases pass independent integration.
- Unit weight and groundwater changes do not alter this calculation: gravity/effective stress, pore-pressure coupling and consolidation are outside its declared mechanics.

Full numerical inputs, hand calculation, per-mesh integrations, latest authorized result and evidence hashes are in numerical-evidence.json. The screenshot with 5.106009 mm records the 20 MPa benchmark; the final saved browser workflow also verifies the 40 MPa scaling case at 2.553004 mm.

## Separation from Winkler contact

Elastic-half-space displacement and independent Winkler spring-bed displacement represent different mechanical models. This service has no Winkler stiffness input or conversion. k is NOT DERIVED from E, and Winkler displacement is NOT USED OR ADDED. Existing spring-bed results remain separately preserved. The new result is centre displacement of a flexible surface patch, not a substituted rigid-footing or actual-site settlement result.

## Authorization, staleness and visualization

Each profile is saved as a new immutable version with a source hash and superseded-version ID. Settlement proposals bind the exact profile version/hash, load, model revision and original reaction/drawing evidence. An explicit exact-proposal authorization is required before calculating. New profiles or proposals stale earlier results; source/model changes invalidate the binding. Dirty CAD geometry, previews and revision comparisons block execution. Editing a profile or load clears the prior diagram and shows STALE. Computed results have their own content hash.

The 3D display shows the declared synthetic profile slice, flexible loaded footprint, groundwater reference and the actual calculated centre-displacement arrow at ×100 display scale. It does not invent a deformation field. An unbounded layer is displayed to a clearly labelled 6 m cutoff; that is visualization truncation, not a physical lower boundary. Unknown extents are not drawn as known geometry. Return to saved CAD model restores the preserved component view.

## Actual-project blockers and exclusions

Actual CAD settlement remains BLOCKED. There is no sourced site investigation/profile establishing applicable E, ν, unit weight, groundwater behavior or layer extent, and physical column/plate/footing transfer behavior is unverified. The existing eccentric rigid CAD footings do not satisfy the validated flexible, concentric, uniform surface-traction benchmark. Even entered evidence or engineer assumptions do not activate an unsupported real-footing calculation.

No soil suitability, allowable bearing capacity, allowable settlement, groundwater condition, construction recommendation or safety is invented. Rigid-footing settlement, layered/finite-depth elastic analysis, eccentric contact interaction, shear, consolidation, nonlinear soil FEA, soil capacity, reinforcement/concrete strength and IS/US compliance remain unsupported. Engineering approval is DISABLED.

## Local verification and preservation

- **549 backend regression tests passed**, including 38 new mechanics/profile authorization tests and existing OpenSees, load transfer, CAD, model revision and component regressions.
- Browser workflow passed undo/redo, sourced profile saving, rejection of synthetic promotion, forged/obsolete authorization, finite-layer blocking, modulus scaling, stale diagrams, reload, responsive layout, profile/groundwater display and return to saved CAD. No page errors in the passed run.
- TypeScript and targeted ESLint passed.
- Compared **9,909 pre-existing database rows**: none missing or changed. All 56 copied components and original/copy DXF bytes match. Paid inference call count did not increase.
- No Git/GitHub operations, commits, installation, deployment or paid AI.

Artifacts: backend-tests.txt, browser-tests.txt, browser-evidence.json, numerical-evidence.json, preservation-evidence.json and screenshots/.

STOP for review. No further engineering method or actual-site calculation is enabled.

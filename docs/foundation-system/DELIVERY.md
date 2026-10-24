# Integrated RC foundation module — local delivery

Implemented and validated a **bounded synthetic foundation workflow**. Full engineering coverage and approval are **not complete**. Unsupported checks remain disabled; no site safety conclusion is made.

- Normal website: http://localhost:3001/projects/804/workspace → Analysis → Integrated RC foundation workflow → Create separate foundation study. Original project 804 is unchanged.
- Ready isolated demonstration: http://localhost:13001/projects/812/workspace → Analysis. Uses port 18001 and `isolated/foundation.db`; its reviewed calculation is result 628, model revision 135. These IDs belong only to the isolated database.
- Downloaded calculation report: `browser-calculation-report.html` (also downloadable from the panel; browser Print can save a PDF). Includes inputs, action bases, geometry, source/implementation hashes, formulas, independent benchmark constants, soil results, RC checks, quantities, disabled methods and review status. It is explicitly **not a safety certificate**.
- Screenshots: `3d-foundation-1600.png`, `3d-foundation-1280.png`, `offline-copilot-1600.png`, `normal-website-3001.png`.
- Machine-readable completed-feature matrix: `feature-matrix.json`.

## Implemented scope and reuse

- Saved CAD column/footing identities and transitive project-804 demand provenance; original drawings checked by hash. Separate study copies retain owned source/review records so existing supervised CAD editing remains available.
- Existing force/moment transport, prescribed-pressure cantilever bending, nominal strain-equilibrium flexure, compression-only Winkler contact and FHWA surface undrained rectangular bearing services are reused.
- Optional exact owned/current transported OpenSees reaction mapping checks CAD identities, reference planes and dependencies. Nonzero shear, moments, torsion or uplift are rejected by this uniform-pressure RC profile. Existing project-797 reactions contain shear/moment and are not silently reduced to vertical load.
- Service column action plus declared footing weight drives gross soil checks. Independently declared factored column action drives net RC cuts. Uniform self-weight cancels its own uniform reaction in net RC bending/shear. No automatic load combinations or assumed cylinder-to-cube conversions.
- Two orthogonal straight bottom mats, separate effective depths, provided/required steel where supported, spacing, partial cover checks, straight-bar development, concrete and reinforcement quantities.
- ACI 318-14 bounded normalweight interior-square shear checks; tension-controlled flexure using the existing nominal solver. Minimum steel is enabled only for the verified Grade60 subset. Straight development is restricted to the documented uncoated bottom-bar subset.
- IS456:2000 published scan subset: Fe415/Fe500 design stress-block flexure, minimum deformed steel, uniform square-footing distribution, spacing, diameter, minimum footing cover, punching and straight deformed-bar development. This profile names the scan containing amendments 1 and 2; later amendments/adoption are not represented as verified.
- Six unsaved comparisons of square width, thickness and bar count. They change no geometry or authorization. Existing CAD preview → exact authorization → save revision controls govern model changes.
- Existing Cesium renderer shows geometry, two mats, loads/reactions, service pressure/displacement labels, cover/depth/spacing, one-way cuts and punching perimeter. Diagram arrows are illustrative; numerical values are labeled.
- Existing deterministic offline Engineering Copilot explains current saved evidence, missing inputs, limitations and supported alternatives. It calls no inference provider and cannot authorize design changes.
- Immutable proposal/result records, latest-proposal authorization, idempotent calculation save, ownership, implementation/dependency hashes, stale results and stale-labeled downloadable reports.

## Independent numerical evidence

Synthetic reference: 1.2m square, 0.3m column patch, 0.45m thickness, service column144kN, independent fixture factored action216kN, cover75mm, eight20mm bars each direction. Fixture multiplier1.5 is an explicit numerical example, **not an adopted load combination**.

- Service footing weight16.2kN; gross soil action160.2kN; pressure111.25kPa; Winkler displacement5.5625mm for independently declared20,000kN/m³ stiffness.
- Unfactored face bending12.15kN·m; factored face bending18.225kN·m. Independent pressure-cell integration and SI/N-mm checks agree.
- Effective depths365mm and345mm. One-way shear demands15.3kN and18.9kN. IS one-way resistance remains disabled.
- Punching demand153.59625kN; implemented IS square-patch resistance1112.625kN. This individual check is not a footing approval.
- IS straight development at full design stress requires970.982143mm versus375mm available: **EXCEEDS IMPLEMENTED CHECK**. The demonstration is not represented as adequate detailing.
- ACI published example independently recomputed in original US units: upperd25.5in, one-way demand231.15kip versus reduced resistance348.356507kip; punching850.795313kip versus957.980394kip. Published values are rounded. The example has an inconsistent intermediate flexure arithmetic line; implementation does not copy that line.
- Independent Decimal IS resistance, inverse steel-area equilibrium, bar-layer depths, quantity/force balance, invalid/nonfinite inputs, unsupported editions and nonzero reaction components are covered by tests.

## Validation and preservation

- Backend focused suite: **134 passed** (`backend-tests.log`).
- Reused structural/CAD/geotechnical suite: **191 passed**, including native OpenSees (`engineering-regression.log`).
- Frontend existing RC/demand/Copilot suite: **26 passed** (`frontend-tests.log`).
- Isolated full browser workflow passed; two viewport sizes, zero page errors, report download, alternatives, saved offline explanation, stale-edit overlay clearing and reload (`browser-results.json`, `browser-tests.log`).
- TypeScript and scoped ESLint passed (`frontend-checks.log`).
- Actual existing CAD preview → authorization → saved revision → stale result → recalculation and 73-entity DXF import passed on a separate isolated study (`cad-edit-import-results.json`). The 1.5m × 1.5m × 0.54m alternative retained the same component ID and recalculated net pressure96kPa.
- Native CAD kernel/parameter propagation verification passed against preserved prior metrics (`cad-kernel.json`).
- Normal localhost:3001 browser smoke passed with all modifying requests blocked; none were attempted (`normal-website.json`). Normal8001 health and new route registration verified.
- **264 original databases and schemas unchanged; 55,296 original storage files and 2,090 engineering-proof files SHA256 unchanged** (`preservation-manifests.json`). All10,239 pre-existing development DB rows unchanged (`preservation-result.json`). Existing verified backup/manifests reused; no restoration/deletion or full-project backup performed.
- No Git/GitHub, installation, deployment, paid inference or cleanup. Test working DB and small drawing references are isolated test inputs, not a new full-project backup. Development naturally creates modest new test/build artifacts; no further disk-space reduction was attempted.

## Remaining blockers

- Nonuniform/biaxial contact coupled to RC shear/flexure, eccentric/edge/corner supports, uplift, piles, openings, stepped/sloped footings, shear reinforcement and seismic detailing are outside this module's validated RC domain.
- Available IS34.2.4.1 scan wording is ambiguous; authoritative amendment verification is required to enable IS one-way shear resistance. Existing demand and independent ACI shear checks continue separately.
- ACI318-19/25 checks and ASCE7-16/22/IS875 automatic combinations are disabled. Selecting a context does not establish adopted jurisdiction or code compliance.
- Full ACI minimum steel outside Grade60, spacing/durability qualification, and development outside the narrow documented subset are disabled. No extrapolated requirements.
- Site investigation, groundwater/layered/continuum/consolidation settlement, settlement acceptance, certified materials, exposure/fire/cracking, actual steel-column/base-plate/anchors/dowels and complete load transfer/detailing are unresolved.
- No hooks, laps, chairs, curtailment, anchorage devices, procurement waste, excavations or complete construction bar schedule. Quantities cover the supported straight mats only.
- No engineering approval or structural-safety certification. Review failed and disabled checks before any engineering use.

Primary references: [ACI published318-14 footing example](https://www.concrete.org/portals/0/files/pdf/318-example-1_rf_r1.pdf), [BIS IS456:2000 published scan](https://law.resource.org/pub/in/bis/S03/is.456.2000.pdf). Existing services retain their FHWA/VDOT method references.

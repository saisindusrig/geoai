# GeoAI: first validated engineering-analysis workflow

Planning baseline: 11 October 2026. Milestone 2 is complete; its editor, saved projects and revisions remain intact. This document proposes the next bounded milestone. No solver integration, code-check engine, analysis UI or database migration has been implemented by this planning task.

## First example and its limits

Start with one vertical elastic steel column, a rigid base-plate idealization, explicit anchor geometry, a rigid reinforced-concrete-footing idealization and one prescribed vertical soil spring. This is a compression-only mechanics benchmark. Plate flexibility, reinforcement, bolt engagement, bearing capacity and real soil constitutive response are outside its verified scope. Anchors carry no modeled load in this particular idealization; that must never be reported as an anchorage check. Retain geometry for every physical component and separately document the simplifications used in its analytical representation.

Engineer-supplied benchmark inputs: column L = 3 m, A = 0.01 m², E = 200 GPa; prescribed total support stiffness k = 100 MN/m; one centered downward load P = 100 kN. These are synthetic verification inputs, not recommendations for the maintenance platform. Small deformation, uniform section, elastic response, no self-weight, no bending, no buckling and no uplift are assumed. Downward displacement and compressive stress are positive in this reference; adapters must explicitly map solver signs.

Exact references: column shortening PL/(EA) = 0.15 mm; spring settlement P/k = 1.00 mm; head movement = 1.15 mm; column stress P/A = 10 MPa compression; upward ground reaction = 100 kN; strain energy Pδ/2 = 57.5 J. Neither stress nor settlement establishes adequacy.

`reference_benchmark.py` independently compares the closed-form solution with a two-DOF stiffness equilibrium solution and repeats in N–mm units. `reference-evidence.json` records actual local reference results. This verifies the arithmetic and unit mapping, not an established FEA solver. Status: **REFERENCE VERIFIED / SOLVER NOT RUN / ENGINEER REVIEW REQUIRED**. No code-specific design method is currently supported.

Proposed OpenSees benchmark mesh: fixed ground node, a coincident foundation node linked by a vertical zeroLength elastic spring, and column nodes joined by axial elements. First use 1, 2 and 4 axial segments; constrain unused DOFs explicitly. Record nodal translations, element axial forces and support reactions. A beam-column extension later requires actual section inertias, orientation, restraints and stability assumptions. Every modeled anchor, contact and footing simplification must be visible in the analysis manifest.

Acceptance gate before any production result: pin executable version and checksum; save generated solver input, raw outputs and logs; fail on nonconvergence, mechanisms or missing output. For this exact linear benchmark require relative error ≤ 1e-6 for nonzero displacement, stress and reaction, force residual ≤ 0.1 N, consistent results across segment counts, and SI/N–mm equivalence. Use absolute tolerances for expected zeros. Add half/double-load checks. An independent engineer reviews the idealization, references and recorded comparison before enabling this narrowly defined analysis capability. These tolerances are benchmark software criteria, not universal engineering tolerances.

## Architecture: preserve the existing model and separate responsibilities

Existing immutable ModelRevision documents and placement metadata remain the geometry source. Existing EngineeringAnalysis stores terrain/geometric results; it must not be relabeled as structural approval. Current structural-layout approval metadata is not a signature approving FEA. Add analysis records alongside existing records in a future reviewed migration, with no rewriting of old revisions or conceptual component metadata.

The proposed dependency chain is:

**Model revision → engineer input revision → analysis idealization → mesh → solver run → normalized computed results → edition-specific checks → engineer review → drawings/quantities.**

- **Physical model:** stable component IDs, geometry in metres, assigned material/section IDs, explicit interfaces and connection relationships. Geometric touching is insufficient evidence of load transfer. Anchor group needs bolt grade, diameter, coordinates, embedment, edge distances and concrete attachment definition. Footing needs reinforcement/cover and concrete grade. Reject missing or ambiguous data rather than infer it from colors or generic box dimensions.
- **Engineering input revision:** immutable values with dimensions, source, author and review status. Store E, Poisson ratio, density, steel yield/ultimate strength, concrete strength and reinforcement properties distinctly. Loads have coordinate system, application region, sign, case, service/factored classification and provenance. Geotechnical inputs include report reference, groundwater, stratigraphy, bearing basis, settlement limits and stiffness calibration. Do not equate subgrade stiffness, elastic modulus and allowable bearing pressure.
- **Analysis model:** explicit physical-to-element and component-to-node mapping; local coordinate transform decoupled from geographic placement; declared rigid offsets, restraints, releases, contact laws and excluded parts. Canonical SI internally, with documented adapter conversion for all dimensions including moments, pressures, density and acceleration. Check interface topology, zero-length members, overlapping mesh, rigid-body modes, units and load-case completeness.
- **Solver adapter:** local isolated subprocess, typed capability declaration, pinned version, deterministic input artifacts, bounded CPU/time, cancellation and logs. A successful process exit alone is insufficient. OpenSees is the proposed first adapter for member/spring models; CalculiX is a later candidate for local plate/solid/contact models. Their documentation establishes available element families, not suitability or accuracy for every engineering problem.
- **Result store:** immutable run ID with geometry/input/mesh/solver hashes, cases, convergence and residuals, displacements, reactions, element forces, stress tensor locations and units. Record whether stress is integration-point, nodal-extrapolated or averaged. Do not invent solid stresses for line elements; report axial stress only when its section relation is justified. A changed dependency makes results STALE without deleting them.
- **Check engine:** consumes normalized demands and explicit design inputs; never hides code factors inside solver mechanics. Each result contains pack version, code edition/amendment, clause, formula, substitutions with units, demand/capacity, method, assumptions, unsupported conditions and benchmark ID. NOT_APPLICABLE, UNSUPPORTED, INPUT_REQUIRED and OUT_OF_SCOPE remain distinct from PASS/FAIL.
- **Review:** review/sign-off references exact model, input, run and check hashes, reviewer identity/role, decision, notes and timestamp. Geometry approval, successful numerical verification and engineering approval are separate states. A revision or code-pack change invalidates applicability of an old approval; preserve its historical record.
- **Viewport:** display only persisted computed fields with units, case, component mapping, scale, min/max and result provenance. Exaggerated deformation is labeled. Missing/stale/unverified results show that status; no demonstration colors presented as calculations. Revision comparison includes geometry, input, mesh, solver, code pack and review differences.

## India and United States: versioned code packs

Project selection must identify country, local jurisdiction, adopted building-code edition, discipline standard and edition, amendments, design method, units and load-combination basis. Changing country does not silently substitute material properties or load factors. An edition being published does not establish local adoption.

Proposed independent pack families: India steel IS 800, concrete IS 456, loading IS 875 and applicable seismic standard, foundations/geotechnical standards selected for the actual footing/pile/soil problem; US steel AISC 360, concrete and anchorage ACI 318, loading ASCE 7 and applicable jurisdictional/geotechnical requirements. BIS references inspected cite IS 800:2007 and IS 456:2000; these are candidate editions, not a verified exhaustive current edition/amendment catalog. AISC lists 360-22; ACI publishes 318-25 as well as earlier editions; ASCE documents 7-22. The project engineer must establish the adopted editions and obtain authorized clause text.

Registry identity example: country + standard + edition + amendment set + method + semantic pack version. Store licensed-source reference/checksum, clause coverage, dimensional input/output contract, compatibility constraints, formula implementation version, benchmark-suite checksum, reviewer and release status. Load-combination packs are separately versioned. AISC LRFD and ASD cannot share an unspecified safety factor; IS limit-state and working-stress routes require distinct coverage. Indian concrete anchorage must have an explicitly adopted applicable method: no silent ACI fallback or assertion that IS 456 alone supplies all modern anchor limit-state checks.

Pack lifecycle: PLANNED → SOURCE_REVIEWED → IMPLEMENTED → BENCHMARK_VERIFIED → ENGINEER_REVIEWED. Only implemented, independently verified methods appear as selectable calculation capabilities. Country/profile availability alone is not code compliance. Keep historical packs immutable and retain old analyses under their original editions.

## One benchmark gate per design method

There are currently **zero implemented code-design methods**. The following register defines the required independent benchmark before enabling each proposed first method; none is represented as already verified:

1. **Code-neutral axial elasticity and spring support:** the numerical reference above is verified locally. Established-solver validation remains pending. Benchmark ID MECH-AXIAL-SPRING-001.
2. **IS 800 limit-state axial compression:** a pinned-edition, independently worked column case, with section class, buckling curve, effective length, nondimensional slenderness and partial factor explicitly supplied. Check both curve branches/boundaries in addition to the primary worked example. Status PLANNED; clause and independent expected capacity not yet reviewed.
3. **AISC 360 LRFD axial compression:** one authorized edition-matched worked column example, documenting section slenderness, effective length and nominal strength before resistance-factor application. Status PLANNED. Must benchmark demands using a compatible LRFD loading basis.
4. **AISC 360 ASD axial compression:** a separately checked allowable-strength example and service-load basis. Sharing the nominal-strength mechanics with LRFD does not replace an ASD benchmark. Status PLANNED.
5. **IS reinforced-concrete footing design and ACI strength footing design:** separate edition-specific hand-worked flexure, one-way shear, punching, bearing and development checks, each enabled only after its own benchmark. A single flexure example does not validate the other checks. Status UNSUPPORTED.
6. **Steel-to-concrete anchorage/base plates:** each adopted Indian method and ACI anchorage method needs independent bolt tension/shear, concrete failure, interaction and group/edge-condition benchmarks. Plate bending/contact mechanics needs a separate mesh-convergence benchmark. Status UNSUPPORTED; no invented universal Indian anchor design method.
7. **Loads, soil and earthworks:** each enabled IS/ASCE combination method needs independently enumerated factors and envelopes; bearing/settlement methods need engineer-reviewed soil-specific worked references; earthwork volumes need analytic geometry and optimization needs an independently checked small balance/haul problem. Status UNSUPPORTED.

For each method retain source page/example or signed independent calculation, original inputs, exact expected outputs, dimensional checks, tolerance justification, boundary/negative cases, solver/pack version and reviewer status. Generated expected values from the same formula implementation are not independent verification. Published references must be edition-matched and appropriately licensed. This register intentionally prevents a claim of broad discipline support based on one benchmark.

## Staged expansion, with explicit stopping gates

**Next milestone, after review:** implement only local solver adapter + the axial/spring benchmark + input/result provenance and true computed visualization. No code compliance badges. Preserve undo/revisions and prove save/reload/stale-results behavior. Then separately implement and independently review the first IS compression and AISC LRFD/ASD compression checks.

**Connections and foundations:** introduce plate flexibility, anchor groups and compression-only interfaces; validate contact and load distribution before code capacities. Then footing flexure/shear/punching/reinforcement and calibrated soil support. Validate uplift, eccentricity and settlement separately; retain unsupported seismic, fatigue and nonlinear soil cases.

**Multi-storey frame FEA:** extend component graphs to storeys, diaphragms, releases and loads; validate cantilever/frame examples, equilibrium, mesh sensitivity and then second-order and modal benchmarks. Separate global analysis from local connection submodels; transfer forces with coordinate and equilibrium checks. Do not infer nonlinear/seismic capability from a linear benchmark.

**Geotechnical and earthworks:** expand springs to engineer-calibrated continuum models only with constitutive benchmarks and boundary/domain studies. Build survey-based cut/fill with explicit datum, uncertainty, shrink/swell, haul/access and environmental constraints; quantity validation precedes optimization.

**Drawings and quantities:** derive dimensioned views, schedules and measured quantities from the pinned physical-model revision, including modeled bolts/rebar only when actually defined. Separate measured quantity from estimated procurement/cost. Every issue references the exact model, analysis, checks and approvals; unsupported checks remain visible in exports.

No solver-brand or Abaqus-equivalent accuracy claim is justified by these proposals. Verification is scoped to each tested model class; engineering adequacy remains an explicit professional review decision.

## Primary references consulted

- [OpenSees elastic beam-column documentation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/elasticBeamColumn.html) — section/material inputs for member elements.
- [OpenSees zeroLength documentation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/zeroLength.html) — coincident-node spring interfaces.
- [CalculiX documented capabilities](https://www.dhondt.de/ov_calcu.htm) — candidate solid/contact capabilities, not validation evidence.
- [AISC 360 official standard catalog](https://www.aisc.org/aisc/publications/current-standards/aisc-360/) — candidate steel edition.
- [ACI 318 official portal](https://www.concrete.org/topicsinconcrete/318buildingcodeportal.aspx) — concrete edition resources.
- [ASCE 7-22 announcement](https://www.asce.org/publications-and-news/civil-engineering-source/article/2021/12/02/updated-asce-7-22-standard-now-available) — loading/combination scope.
- [BIS publication referencing IS 800 and IS 456](https://www.services.bis.gov.in/tmp/WCCED21027624_20022025_1.pdf) — edition references only; not a substitute for approved standard text.

All application functionality and project data remain untouched by this planning task. Milestone 2 review model: http://localhost:3001/projects/768/workspace.

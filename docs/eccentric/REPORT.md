# Validated eccentric structural joints — local review

Completed 12 October 2026. Review website: http://localhost:3001/projects/782/workspace. Open **Analysis**, use **Select saved analysis members**, then **Show centerlines, nodes and offsets** or the computed-result tabs and **Fit Analysis**. **Inspect left/right connection** gives a close view of each offset. Cyan lines are saved physical centerlines; magenta lines are declared rigid arms; yellow markers distinguish retained analytical nodes from beam elastic endpoints. Numerical verification does not confer engineering approval.

## Scope and original geometry audit

Original project 768, revision 59 contains 45 components. Its current platform is 6 m × 4 m despite historical component names containing “5x3”. All eight perimeter beam-to-column centerline ends were audited. Horizontal offsets are ±0.15 m, vertical offsets +0.10 m, resultant length √(0.15² + 0.10²) = 0.180277564 m. North/south beams align with the supported East–Up analytical plane. East/west beams remain unsupported; no automatic rotation or projection was applied. Full observations are in [audit.json](<D:/layout project/docs/eccentric/audit.json>).

Project 782 is a separate copy retaining all 45 components and their stable identities. The selected north frame comprises `industrial-platform-5x3:column-nw`, `industrial-platform-5x3:beam-north`, and `industrial-platform-5x3:column-ne`. Both columns have 3.2 m centerline length, column-axis spacing 5.7 m, and the actual beam centerline length is 6 m. Beam ends are 0.10 m above the retained column-head nodes, with left/right offsets [−0.15,+0.10] / [+0.15,+0.10] m. Other 42 components and their load-sharing effects are excluded.

The declaration models massless rigid arms from column heads to the actual beam ends. It retains the full 6 m elastic beam, including its end overhangs. This is a deliberately explicit synthetic verification idealization, not an automatic interpretation of clear span, bearing, bolts, welds, contact or connection capacity. Nothing moves the saved geometry or infers structural connectivity from touching surfaces.

## Mechanics, inputs and approval gates

OpenSees 3.8.0 uses `geomTransf Linear -jntOffset` in global analytical coordinates, with `elasticBeamColumn` elements. Coordinate mapping is saved local East → analytical X, saved local Up → analytical Y; rotation is positive counterclockwise. N–mm solver inputs convert length, area, inertia, modulus and moment consistently; results return SI with explicit display units. Method documentation: [OpenSees Linear Transformation](https://opensees.berkeley.edu/wiki/index.php/Linear_Transformation).

For rigid offset r = [rx,ry], physical endpoint displacements are ux,end = ux,node − ry θ and uy,end = uy,node + rx θ. Retained-node moment is Mend + rx Fy − ry Fx. An independent 6×6 Euler–Bernoulli stiffness implementation uses a rigid-arm displacement operator B and axis transformation T; transformed stiffness is (TB)ᵀ k (TB). Actual local solver forces are transformed back for nodal and global equilibrium. Computed endpoint translations, offset couples and retained moments appear in **Computed connection force and moment transfer**. Deformation displays transformed rigid-arm endpoints alongside actual elastic-member displacements; display amplification is explicitly ×50.

Each nonzero joint requires selecting rigid-offset behavior, reviewing its observed signed vector, naming the assumption source and checking a separate left/right analytical-idealization approval. Input validation rejects missing approval, inconsistent vectors, invalid dimensions, unsupported geometry and malformed fields. A proposal then requires exact-hash numerical-solve authorization. Cloud inference remains locked; offline fixtures can prepare proposals and explain actual saved results, but cannot approve safety or execute arbitrary scripts. Results bind to exact saved model revision, document digest and input record; geometry, material/load/idealization changes invalidate their currency. A new model revision requires renewed joint review.

## First independently verified benchmark

The first benchmark was verified before any copy-project solve. Synthetic cantilever: actual elastic length 3 m; E = 200 GPa; A = 0.01 m²; I = 8×10⁻⁶ m⁴; fixed base; retained-end loads Fx = +1 kN, Fy = −2 kN, M = 0. Eight real runs compare zero offset and [0.15,0.10] m offset using 1/2/4 elements in SI plus 2 elements in N–mm.

- Zero offset: tip uy = −11.250 mm, θ = −0.005625 rad; base reactions [−1,+2] kN and +6.000 kN·m.
- Nonzero offset: retained tip ux = −0.486000 mm, uy = −9.393750 mm, θ = −0.004875 rad; physical elastic tip ux = +0.001500 mm, uy = −10.125000 mm; base reactions [−1,+2] kN and +5.600 kN·m.
- Physical-end moment +400 N·m plus offset couple −400 N·m gives the explicitly prescribed zero retained-node end moment.

The zero/nonzero comparison keeps the physical elastic beam at 3 m and applies the load at its respective retained node. Thus the physical load application point changes from [3,0] m to [2.85,−0.10] m, explaining the reaction moment change. This is not a same-load-location comparison.

Independent formulas use Mphysical = ry Fx − rx Fy, θ = Fy L²/(2EI) + Mphysical L/(EI), uy,physical = Fy L³/(3EI) + Mphysical L²/(2EI), ux,physical = Fx L/(EA), followed by the rigid-arm displacement mapping. Reaction moment is −[(L−rx)Fy + ry Fx]. Every case matches closed form, independent stiffness, local joint balance and overall equilibrium. See [benchmark-evidence.json](<D:/layout project/docs/eccentric/benchmark-evidence.json>) for individual solver provenance, raw-output references and numerical comparisons.

## Saved-platform numerical evidence

Latest verified analysis **277**, saved copy revision **82**, run `42b4191f-1dd3-440b-a1e7-6640b589216f`; OpenSees 3.8.0, exit code 0, convergence code 0. Inputs are explicitly synthetic: E = 200 GPa; solid-box column A = 0.09 m², I = 0.000675 m⁴; solid-box beam A = 0.06 m², I = 0.0002 m⁴; both bases fixed; +20 kN total East load shared equally between column heads (+10 kN each). These properties match the declared saved solid boxes for verification, not an established steel section specification. No self-weight or other project loads are inferred.

- Left retained column head: ux = **0.529390534 mm**, uy = **0.000460026 mm**, θ = **−0.000204449331 rad**.
- Left physical beam end: ux = **0.549835468 mm**, uy = **0.031127426 mm**.
- Left base: Fx = **−10.000000 kN**, Fy = **−2.587646965 kN**, M = **+24.625206150 kN·m**. Right base has opposite vertical reaction and the same horizontal reaction/base moment.
- Left physical beam-end moment **−7.762940895 kN·m**, offset couple **+0.388147045 kN·m**, retained joint moment **−7.374793850 kN·m**. Moment transfer is explicitly shown, rather than treating an offset as decoration.
- Independent symmetric strain-energy condensation agrees with actual column-head results within **1.99×10⁻¹⁷ SI**; this machine-precision agreement applies to this simple elastic verification model, not real structural accuracy. Global residuals [Fx,Fy,M] = [6.98×10⁻¹⁰ N, 1.36×10⁻¹² N, −2.32×10⁻⁹ N·m]. Every retained/intermediate node also satisfies equilibrium.

The hand derivation independently condenses symmetric unknowns u (head translation), v (antisymmetric vertical translation), θ (common head rotation). With Bc = EcIc, Bb = EbIb, EA = EcAc, beam length L, column height H and horizontal offset a:

Kuu = 24Bc/H³; Kuθ = 12Bc/H²; Kvv = 2EA/H + 48Bb/L³; Kvθ = 48Bb a/L³ − 24Bb/L²; Kθθ = 8Bc/H + 48Bb a²/L³ − 48Bb a/L² + 12Bb/L.

Let eff = Kθθ − Kvθ²/Kvv. Then u = P/[Kuu − Kuθ²/eff], θ = −Kuθ u/eff, v = −Kvθ θ/Kvv. Left head is [u,−v,θ], beam end [u−hθ,−v−aθ,θ], left vertical reaction EA v/H, base moment 6Bc u/H² + 2Bc θ/H. Full calculation values and artifact-hash verification for all 13 completed copy-project runs, including retries, are in [platform-hand-evidence.json](<D:/layout project/docs/eccentric/platform-hand-evidence.json>); the reproducible local verification script is `.cache/eccentric/verify.py`.

## Tests and preservation

- **41 backend tests passed**, covering real zero/nonzero benchmark cases, saved eccentric frame, 1/2/4 discretizations, N–mm conversion, half loads, translated coordinate origins, invalid vectors/approval/geometry, exact authorization, input staleness and immutable evidence retrieval. Existing elastic and saved-frame regression tests passed.
- **Eccentric browser workflow passed** in Chromium: actual saved-member selection; offset preview; approval gates; authorized real solver; computed-transfer inspection; half-load N–mm/4-element run; reload; restored SI load; platform preview/apply; undo/redo staleness; save/new revision/reapproval; real current solve; offline result explanation; no page or Cesium error. Saved evidence is [browser-evidence.json](<D:/layout project/docs/eccentric/browser-evidence.json>). A direct column move was correctly rejected by pre-existing attachment constraints; geometry testing used the supported platform editor instead.
- **Existing analysis workspace browser regression passed**, including saved zero-offset results, diagram toggles, extrema, member picking, units and reload. TypeScript `tsc --noEmit` and targeted ESLint passed.
- Fixed a browser-discovered engineering-input refresh race: older in-flight history reads can no longer make a newly saved input/proposal spuriously stale. Compact history responses retain computed results and evidence pointers while full immutable manifests retain all benchmark suites and references.
- Preservation comparison checked **9,486 pre-existing rows across 62 tables**: zero changed or missing original rows. Original projects, revisions, results and existing 22-call inference ledger remain intact. **Zero new paid inference calls.** Copy revision 82 preserves all 45 component objects and origin exactly against original revision 59. See [preservation-evidence.json](<D:/layout project/docs/eccentric/preservation-evidence.json>) and [copy-preservation.json](<D:/layout project/docs/eccentric/copy-preservation.json>).
- Actual Tcl has two explicit `-jntOffset` transforms. All recorded artifact SHA-256 values were checked against bytes on disk, including solver input and output files. Full latest evidence is in `backend/storage/opensees-benchmark/42b4191f-1dd3-440b-a1e7-6640b589216f/manifest.json` and remains downloadable through the Analysis Evidence interface.

Reproduce locally from `backend`: `.venv/Scripts/python.exe -m pytest tests/test_eccentric_frame.py tests/test_physical_frame.py tests/test_elastic_frame.py -q`. From `frontend`, set `PLAYWRIGHT_BASE_URL=http://localhost:3001` and `PLAYWRIGHT_SKIP_WEBSERVER=true`, then run the existing Playwright CLI against `e2e/eccentric-frame.spec.ts`; this intentionally appends verification inputs/results and a revision only to copy project 782. No software installation is required.

## Limitations and stopping point

Supported scope is a horizontal East-aligned beam joining equal-height vertical columns in one East–Up plane, bounded symmetric offsets and explicitly fixed bases/rigid arms. Offset length is limited to min(0.5 m, 20% of the smaller frame span/height); nonzero-offset reference rotations above 0.05 rad or endpoint translations above 5% of the smaller span/height are rejected as outside this validated linear domain. These numerical guards are not capacity checks.

Out-of-plane, rotated, asymmetric/long-offset arrangements, releases, semi-rigid joints, arbitrary support/load patterns, distributed loads, shear deformation, self-weight, slab participation, bracing participation, foundation/soil interaction, buckling, geometric/nonlinear/dynamic analysis, weld/bolt/plate capacity and whole-building analysis remain unsupported. There are no IS/US code-compliance or structural-safety claims. Engineering approval remains disabled. Analytical-idealization consent and solver authorization do not approve a physical connection. No further development phase has started.

## Screenshots

![Physical centerlines and offset inspection](<D:/layout project/docs/eccentric/screenshots/left-connection.png>)
![Full copied platform with actual computed bending results](<D:/layout project/docs/eccentric/screenshots/final.png>)

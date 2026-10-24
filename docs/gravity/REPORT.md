# Verified gravity and distributed-load FEA — local review

Completed 12 October 2026. Website: http://localhost:3001/projects/783/workspace. Open **Analysis**, select a **Saved load case / result**, then use **Show applied loads**, the result tabs and **Fit Analysis**. Project **783** is a separate 45-component platform copy; latest saved model revision **84**, verified analysis **290**. Engineering approval remains disabled. All material and load values below are explicitly synthetic verification inputs.

## Implemented scope

The existing saved three-member East–Up frame supports separate named cases containing explicitly signed vertical column-head nodal loads, a vertical uniform load over the actual saved beam length, and the existing equal horizontal head loads. Self-weight requires explicit per-component density/source, declared section area, gravity magnitude/direction/source; the current gravity direction is saved local negative Up. Every selected member must have a complete density declaration for a self-weight case. No slab load, tributary area, density, gravity or material property is inferred.

Up to four cases share the exact saved geometry, sections, materials, fixed bases and declared centerline/rigid-offset joints. An optional explicitly factored linear combination is identified as **linear superposition**, not an IS/US code combination. Every case runs independently in OpenSees; the factored numerical sum is checked against another actual combined-load solve. Cases and combination have separate solver run identities and downloadable inputs, outputs, logs and manifests. Negative factors are bounded verification inputs, not automatic design-code combinations.

The viewer now has case-specific load arrows with actual N/kN and N/m/kN/m labels, load-value/self-weight evidence, computed force and deformation diagrams and member inspection. Arrow lengths are symbolic. Deformation remains explicitly amplified ×50; force diagrams use normalized display offsets. Changing a case clears the preceding plotted results before displaying the selected case. Beam inspection distinguishes retained column-head DOFs from physical beam-end displacements transformed through eccentric rigid arms.

Camera framing includes frame bases as well as load arrows, rather than framing only loads near the beam. The camera looks toward the selected north frame from its exposed side. Connection close-ups show only two local centerline segments, the relevant offset and two node labels; platform dimension labels are temporarily hidden during inspection and restored afterward. Connection assumptions are expandable, reducing panel clutter without changing model geometry.

## Solver mechanics and independent verification

Existing OpenSees **3.8.0** and linear Euler–Bernoulli `elasticBeamColumn` mechanics are retained. Explicit uniform loads use `eleLoad -type -beamUniform Wy Wx`, transformed from analytical global axes into each member’s directed local axes. In SI, q is N/m. The separate NumPy stiffness implementation uses the consistent local load vector:

`fe = [qxL/2, qyL/2, qyL²/12, qxL/2, qyL/2, −qyL²/12]`.

It assembles `F += (TB)ᵀ fe`, solves `Kff uf = Ff`, obtains reactions `R = Ku − F` and local end forces `k ulocal − fe`. B is the independently implemented rigid-arm displacement operator; T rotates from analytical global to local axes. Eccentric loads therefore transfer forces and moments at their declared endpoints, including `Mretained = Mend + rx Fy − ry Fx`. Saved geometry is not snapped or moved.

Member diagrams use actual solver end forces with the explicit distributed-load terms: `N(x) = −Ni − qx x`, `V(x) = Vi + qy x`, `M(x) = −Mi + Vi x + qy x²/2`. Translation includes the exact uniform-load particular solutions `qx x(L−x)/(2EA)` in the axial direction and `qy x²(L−x)²/(24EI)` in the transverse direction, in addition to nodal Hermite interpolation. Omitting those terms would incorrectly show straight shear/linear moment diagrams and incorrect interior beam deflection. Display extrema are explicitly based on stored solver-derived samples, not a guarantee of continuous extrema for every mixed-load arrangement.

N–mm solver conversion is explicit: coordinates/offsets ×1000; A ×10⁶; I ×10¹²; E ÷10⁶; force unchanged; moment ×1000; uniform N/m load ÷1000. Canonical engineering inputs, density kg/m³ and gravity m/s² remain SI. Returned displacements, reactions and forces convert back to SI before display or comparison. All actual nodal forces, local member forces, reactions, node-by-node balance and global equilibrium are independently checked.

## First beam benchmark — passed before saved-frame extension

A synthetic fixed-fixed beam uses L = 4 m, E = 200 GPa, A = 0.01 m², I = 8×10⁻⁶ m⁴, and qy = −2000 N/m. Actual 2- and 4-element SI solves, a 2-element N–mm solve and a half-load solve passed independent hand calculations at every stored sample.

- Vertical support reactions: **+4.000000 kN each**.
- Local fixed-end moments: **+2.666667 kN·m left / −2.666667 kN·m right**. Internal beam moments have the corresponding hogging/sagging signs.
- Midspan vertical displacement: **−0.833333 mm**.
- Reference formulas: `Ry = −wL/2`, `Mi = −wL²/12`, `Mj = +wL²/12`, `v(x) = w x²(L−x)²/(24EI)`; shear and moment follow the equations above. Full diagram/deflection comparison error was below 10⁻¹² in the respective SI values for the first run.

A one-element fully fixed beam has no free degrees of freedom and the installed OpenSees linear system rejected it. That condition is explicitly rejected before execution rather than silently changing the mesh. The fixed-fixed prerequisite uses 2/4 elements. A separate actual 1/2/4-element uniformly loaded cantilever test verifies the one-element distributed-load/particular-solution formulation. Saved portal cases support and pass 1/2/4-element refinement.

See [beam-benchmark.json](</D:/layout project/docs/gravity/beam-benchmark.json>) for real solver version, files, convergence, independent stiffness and closed-form evidence. Failed initial all-restrained exploratory runs remain retained in local solver storage; they are not represented as verified.

## Saved eccentric portal verification

The copy preserves original project 768/revision 59 exactly: 45 components, unchanged identities, geometry and origin. Analysis selects `industrial-platform-5x3:column-nw`, `industrial-platform-5x3:beam-north`, `industrial-platform-5x3:column-ne`. Other 42 components and their load-sharing effects are excluded.

Column centerline length H = 3.2 m, column-axis spacing = 5.7 m, actual beam elastic length L = 6 m. Left/right offsets remain [−0.15,+0.10] / [+0.15,+0.10] m. Massless rigid arms retain the full actual elastic beam length; physical connection capacity and load paths through the rest of the platform are not established.

Declared synthetic sections/materials: E = 200 GPa for all three; solid-box columns A = 0.09 m², I = 0.000675 m⁴; solid-box beam A = 0.06 m², I = 0.0002 m⁴. These match the saved boxes for numerical verification, not a certified steel profile. Bases are explicitly fixed.

Three independent cases are saved:

- **Horizontal:** +20 kN total East load shared equally at the column heads. Existing horizontal behavior is preserved.
- **Gravity:** −2 kN/m over the actual 6 m beam and −1 kN at each retained column head; no slab distribution.
- **Self weight:** density 7850 kg/m³ for each selected member, explicitly supplied g = 9.81 m/s² toward negative Up. Beam weight **4.620510 kN/m**, each column **6.930765 kN/m**, total selected-member weight **72.079956 kN**. Rigid arms have no assigned mass or weight.

Gravity case numerical results:

- Beam midspan vertical displacement: actual **−0.205005230503 mm**, independent hand value **−0.205005230503 mm**.
- Left retained head [ux,uy] = **[−0.002055138, −0.001244444] mm**, θ = **−0.000025933916 rad**. Physical left beam end [ux,uy] = **[+0.000538254, +0.002645643] mm**; rigid-arm rotation explains the difference.
- Left base [Fx,Fy,M] = **[+2.153016114 kN, +7.000000000 kN, −2.350738719 kN·m]**. Right base has opposite horizontal reaction/base moment and the same vertical reaction.
- Left physical beam-end moment **+5.654214459 kN·m**, offset couple **−1.115301611 kN·m**, retained joint moment **+4.538912847 kN·m**. Actual endpoint force/moment transfer and node equilibrium are checked independently.
- Global residual [Fx,Fy,M] = **[−9.09×10⁻¹³ N, +9.09×10⁻¹³ N, +3.64×10⁻¹² N·m]**.

Self-weight case: actual beam midspan displacement **−0.475175064397 mm**; each base’s vertical reaction **+36.039978 kN**; left offset-induced couple **−2.576631124 kN·m**. Independent hand calculations agree. The gravity direction, density, A, elastic length, mass per metre and weight per metre are retained per component in the evidence.

Independent portal hand verification uses symmetric strain-energy condensation, separately from the full 6×6 element stiffness assembly. With Bc = EcIc, Bb = EbIb, EAc = EcAc, EAb = EbAb, a = 0.15 m and h = 0.10 m:

`Kuu = 24Bc/H³ + 4EAb/L`, `Kuθ = 12Bc/H² − 4EAb h/L`, `Kθθ = 8Bc/H + 4EAb h²/L + 4Bb/L`, `Fθ = w(L²/6 − La)`, `Fv = wL + sum(Fy,heads) + wcH`.

Then `θ = Fθ/(Kθθ − Kuθ²/Kuu)`, `u = −Kuθ θ/Kuu`, `v = Fv/(2EAc/H)`. Left beam end is `[u−hθ,v−aθ,θ]`; midspan vertical translation is `v−aθ+Lθ/4+wL⁴/(384Bb)`. Left reaction is `Fx = −12Bc u/H³−6Bc θ/H²`, `Fy = −EAc v/H−wcH/2`, `M = 6Bc u/H²+2Bc θ/H`. These equations independently reproduce the actual gravity and self-weight results, including eccentric axial/bending coupling.

Detailed calculations and byte-level input/output hash verification for every completed copy-project run are in [platform-hand-evidence.json](</D:/layout project/docs/gravity/platform-hand-evidence.json>). Reproduce read-only verification with `backend/.venv/Scripts/python.exe .cache/gravity/verify.py` from the workspace root.

## Verified linear superposition and solver provenance

Saved **H + G + SW** uses three explicitly declared factors of 1.0. The three independent cases are numerically summed and compared with a fourth actual OpenSees combined-load solve. **575 comparisons passed**, covering nodal and sampled displacements, local end forces, axial/shear/moment diagrams, reactions and offset moments. Maximum displacement difference = **4.34×10⁻¹⁹ m**; maximum force/moment difference = **5.37×10⁻¹⁰ in N or N·m**. This numerical agreement validates this linear benchmark, not real-structure accuracy or adequacy.

Combined left retained head: ux = **0.522587505 mm**, uy = **−0.005220108 mm**, θ = **−0.000290297205 rad**. Combined reactions: left [−2.872967643 kN,+40.452331035 kN,+16.843661553 kN·m]; right [−17.127032357 kN,+45.627624965 kN,+32.406750747 kN·m]. Global equilibrium residuals are below **2.3×10⁻⁹** in the respective SI units.

Latest actual run IDs:

- Horizontal: `eeea527b-92f7-42c8-a1fa-97c2acc02085`.
- Gravity: `b32bbf15-b4d4-4181-a9d7-5c7e698ceb10`.
- Self weight: `378be042-0f67-4286-bcaf-6fa8e10f844a`.
- Combined solve: `5eeee328-1588-41f5-9441-c766d3a0d514`.

Every run uses OpenSees 3.8.0 with exit code 0 and convergence code 0. `model.tcl`, node/force/reaction outputs, stdout/stderr, executable SHA-256, input/output hashes and independent stiffness comparisons are preserved under `backend/storage/opensees-benchmark/<run-id>/`. [Full combined manifest](</D:/layout project/backend/storage/opensees-benchmark/5eeee328-1588-41f5-9441-c766d3a0d514/manifest.json>) includes case and prerequisite evidence. Analysis **Evidence** downloads follow the selected saved case; unknown case names and filenames are rejected.

## Tests and data preservation

- **60 backend tests passed**: actual uniform beam, 1/2/4 cantilever and eccentric portal cases, SI/N–mm, half-load factors, independent portal condensation, equilibrium and diagram/deflection checks, missing density/gravity/direction/source, invalid component/case references, duplicate/mixed/empty/nonfinite inputs, unsupported slab loading, section/joint rejection, exact authorization, staleness, case artifact access, compact immutable history and all previous elastic/eccentric/horizontal tests. The only warning is the existing Starlette/httpx deprecation warning; no software was installed.
- **Full gravity browser workflow passed**: saved member selection; explicit eccentric approvals; missing-density 422; named cases and density/gravity entry; exact-hash 409 rejection; actual authorized solves; case-specific values and diagrams; load arrows; half-factor N–mm/4-element run; reload; geometry preview/apply/undo/redo; new revision and renewed joint/solver authorization; offline selected-case explanation; 1280×820 responsiveness; no page/Cesium errors; Nebius locked with 403.
- **Existing horizontal workspace browser regression passed**, including current saved numeric values, diagram toggles, member picking, Evidence and reload. Its original model and earlier screenshot/evidence files were preserved; new regression captures are under `docs/gravity/legacy-workspace/`.
- **Read-only gravity review browser test passed**, including beam selection, actual physical-end displacements and saved bending forces, current case/verification screenshots and desktop responsiveness. TypeScript and targeted ESLint passed.
- Database snapshot comparison checked **9,543 pre-existing rows across 62 tables**: **zero changed or missing original rows**. The copy’s 45 complete component objects and origin remain exactly equal to source revision 59 after save/undo/reload. Existing projects, revisions, solver evidence and the 22-entry live-inference ledger remain intact. **Zero new paid inference calls.** No GitHub, commits, deployment, installations or additional paid services were used.

Evidence: [browser-evidence.json](</D:/layout project/docs/gravity/browser-evidence.json>), [preservation-evidence.json](</D:/layout project/docs/gravity/preservation-evidence.json>), [copy-preservation.json](</D:/layout project/docs/gravity/copy-preservation.json>). Backend reproduction: from `backend`, run `.venv/Scripts/python.exe -m pytest tests/test_gravity_frame.py tests/test_eccentric_frame.py tests/test_physical_frame.py tests/test_elastic_frame.py -q`. Browser tests are `frontend/e2e/gravity-frame.spec.ts`, `gravity-legacy.spec.ts` and `gravity-review.spec.ts`; set `PLAYWRIGHT_BASE_URL=http://localhost:3001` and `PLAYWRIGHT_SKIP_WEBSERVER=true`. The full gravity test appends verification inputs/results and a revision only to review copy 783; the other two tests are read-only.

## Limits and stopping point

Supported assembly geometry remains the selected horizontal East-aligned beam and equal-height vertical columns in one plane, fixed bases and explicitly approved centerline/short symmetric rigid-offset joints. Only the selected elastic members receive loads; the visible slab, braces, foundations, plates, stairs and other connections do not automatically participate.

No distributed point-load interpolation, variable/partial UDLs, arbitrary support patterns, releases, semi-rigid connections, arbitrary 3D loading, slabs/load distribution, foundation/soil interaction, shear deformation, second-order effects, buckling, nonlinear/dynamic/seismic analysis, physical connection capacity or design-code compliance is enabled. The existing bounded small-displacement guards include interior uniform-load deflection; these are domain checks, not safety criteria. Engineering approval remains **DISABLED**. Results are linked to exact revision/document/input records; changing geometry, material, load cases, gravity/density or factors requires renewed review and authorization. No additional phase has started.

## Local screenshots

![Current saved gravity case and actual load arrows](</D:/layout project/docs/gravity/screenshots/gravity-loads-final.png>)
![Saved computed bending moments and beam member inspection](</D:/layout project/docs/gravity/screenshots/review.png>)
![Verified factored linear superposition](</D:/layout project/docs/gravity/screenshots/superposition.png>)
![Reduced-clutter eccentric connection inspection](</D:/layout project/docs/gravity/screenshots/connection-inspection.png>)

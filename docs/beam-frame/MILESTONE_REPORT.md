# Validated elastic beam and portal frame — 12 October 2026

Implemented locally with the existing OpenSees 3.8.0 executable. No installation, GitHub operations, commits, deployment or new paid inference. This milestone stops at the two explicit verification models.

## Working website

- Cantilever: http://localhost:3001/projects/779/workspace
- Portal frame: http://localhost:3001/projects/780/workspace
- Open **Checks → Validated elastic beam/portal**. Saved inputs, authorized proposals, computed results, fixture explanations and input/output downloads are retained. Use the deformation, moment and shear buttons to display computed diagrams in Cesium.
- These are separate saved projects. Original platforms, AI evidence, OpenSees axial benchmark and revisions remain intact. Preservation compared **9,399 pre-existing rows across 62 tables**: none changed or missing.
- Local launcher: `backend/scripts/serve_beam_frame_local.py`, API 127.0.0.1:8001, frontend localhost:3001. Cloud budget is locked, keys stay in backend configuration, and other paid integrations remain disabled. The previous 22-request Nebius ledger is unchanged.

## Explicit models and independent numerical evidence

Both models use homogeneous linear elastic Euler-Bernoulli beam-column elements, a linear geometric transformation and three in-plane DOFs per node (East translation, Up translation, counterclockwise rotation). No self-weight, shear deformation or geometric stiffness is included. Materials/sections/loads are explicitly **synthetic verification values**, never actual project engineering inputs. The saved display boxes represent member centerlines, not physical engineering sections.

### Cantilever, revision 75, latest analysis 197

- Span L = 3 m; E = 200 GPa; A = 0.01 m²; Iz = 8×10⁻⁶ m⁴.
- Root translations and rotation fixed; free tip carries 1,000 N downward.
- OpenSees tip displacement **−5.6250000 mm**, tip rotation **−0.0028125 rad**.
- Support vertical reaction **1,000 N**; fixing moment **3,000 N·m**; horizontal reaction zero.
- Internal shear magnitude **1,000 N**; bending diagram magnitude decreases linearly from **3,000 N·m** at root to zero at tip.
- Independent closed forms: uy(L) = −PL³/(3EI), θ(L) = −PL²/(2EI), V = P, Mroot = PL. A separate SI stiffness assembly also checks every node, reaction and local element force.
- Fx/Fy/Mz equilibrium residuals: **0 N / 9.095×10⁻¹³ N / 4.547×10⁻¹³ N·m**.
- Solver run `79b044db-e994-49a8-b317-4e6d3e73ec3e`.

### Portal, revision 76, latest analysis 202

The beam prerequisite passes before any portal solve is permitted.

- Span 4 m, column height 3 m; all three members E = 200 GPa, A = 0.02 m², Iz = 8×10⁻⁵ m⁴.
- Rigid upper joints, both bases fixed in ux/uy/rz. Horizontal load **10 kN at each upper joint**, total 20 kN to the East. No imposed vertical or distributed load.
- Both upper joints: sway **2.1761172677 mm**, rotation **−0.0005132448451 rad**.
- Upper vertical displacements: left **+0.0045985103 mm**, right **−0.0045985103 mm**.
- Each base horizontal reaction **−10 kN**. Vertical reactions: left **−6.1313470797 kN**, right **+6.1313470797 kN**. Each fixing moment **+17.7373058407 kN·m**.
- Independent reference: separately assemble each 6×6 local EA/L–EI stiffness matrix, rotate to global coordinates, impose explicit restraints, solve Kff uf = Ff, recover R = Ku − F and local forces. Matrix and load-vector evidence is retained in the manifest. This is an independent implementation of the same linear theory, not an external published portal certification.
- Global equilibrium includes the vertical-reaction lever arm: 2(17.7373058407) + 4(6.1313470797) = **60 kN·m**, balancing 20 kN × 3 m.
- Fx/Fy/Mz residuals: **1.310×10⁻¹⁰ N / −5.457×10⁻¹² N / −3.929×10⁻¹⁰ N·m**.
- Maximum nodal absolute comparison error **1.605×10⁻¹⁷** in SI translations/rotations; maximum reaction/local-force comparison error **1.456×10⁻¹⁰** in SI forces/moments.
- Solver run `9ff9f1aa-f77c-4d6f-82b1-41c2c6b6569a`.

See `numerical-evidence.json` and saved manifest downloads for solver version, executable hash, convergence code, exact TCL input/output hashes, independent calculations and load/material provenance. The executable SHA-256 remains `5aa4e9c80c410c510ca62ac3b2f1d64a8e50679f0238e140b5bebcd6d5ddbe6d`.

## Units, convergence and diagrams

- 1/2/4 elements per member: core displacements, reactions and member force distributions agree within declared tolerances. The cubic displacement field is exact for these nodal-load Euler-Bernoulli cases; this does not establish convergence for arbitrary distributed loads or other element formulations.
- SI and N-mm runs convert lengths, area, inertia, E and moments consistently. All displayed/evidence results are converted back to metres, N, N·m and radians; translations are additionally displayed in mm.
- Half-load runs produce half displacement, rotation and forces/reactions.
- Deformed curves use cubic Hermite interpolation of **actual computed** nodal translations and rotations. The default 50× display scale is labeled. It is not an independently computed continuous shell/solid deformation field.
- Moment/shear paths use **actual computed local end forces**, with normalized visual offsets. Their geometric drawing offset is not a physical displacement. Local force convention is displayed: [Ni, Vi, Mi, Nj, Vj, Mj], internal N = −Ni, V = Vi, M(x) = −Mi + Vi x. There are no distributed loads in these supported cases.
- Stale inputs or geometry remove active result overlays and block fresh execution/explanation from old proposals. An early diagram request is retained until Cesium is ready; the reload rendering race found during browser testing was fixed.

## Restricted AI integration, without paid inference

- The frame proposal context includes actual saved member identities, geometry, sources, explicit inputs, joints/restraints and supported limitations. Saved endpoints are verified against the declared benchmark topology; rotated/nested/moved or extra members cannot silently become the analytical frame.
- The Nebius adapter supports a restricted native `prepare_frame_analysis` tool. Its only arguments are exact model revision, input-record identity and component identities. It cannot execute arbitrary code, supply engineering numbers or directly run OpenSees.
- Missing explicit input fields are returned unchanged. A separate user authorization of the exact hashed proposal is required before local solver execution. Only current verified solver evidence may be explained. Geometry, inputs and solver evidence are hashed and linked to revisions; old evidence remains in history and is marked stale.
- **No live Nebius frame inference was tested or claimed.** The provider selector visibly locks cloud use; development tests use labeled deterministic frame fixtures, plus offline replay of the existing real column/review/explanation fixtures. A future paid frame test requires a new budget approval.
- The fixture explanation is a transport/workflow test, not evidence that a live model has understood this frame. Actual engineering numbers remain solver-owned.

## Audit of the nine rejected live Nebius responses

No inference retried. `saved-ai-audit.json` records each rejection and its saved usage evidence.

- **Five** responses exhausted the output allowance: four initial 4,096-token requests and a later 16,384-token primary-model review.
- **One** response cited a nonexistent component and was correctly rejected.
- **Three** were schema/evidence/prose validation failures whose original final response and exact diagnostic cause were not retained. Their precise cause cannot be recovered honestly from the saved evidence. Usage and budget accounting are preserved.
- All **13 accepted saved responses** replayed successfully against the schemas, without network access. This verifies format compatibility, not semantic engineering correctness; the previously identified Flash brace-plane error remains an unverified AI factual error.
- JSON parsing now rejects duplicate keys and NaN/Infinity. Evidence/inventory identity types are strict. Existing exact-reference, missing-input, hash and unsupported-claim gates remain enabled.
- Future inference retains a bounded, redacted final-response excerpt and a response hash in the usage ledger, plus a redacted validation error. Reasoning text is not retained. Existing historical responses were not altered.

## Tests and limitations

- **96 backend tests passed**, including the existing axial benchmark/API and physical-column/AI suites, real beam/frame runs, units, mesh checks, load scaling, invalid parameters, cloud lock, exact authorization, input/geometry staleness and offline fixture replay.
- Browser workflow passed for beam then portal: missing-input gate, explicit input saving, disabled execution until authorization, cloud HTTP 403, actual solver values, deformation/moment/shear controls, fixture explanations and reload. A second browser test passed locked provider selection and removal of the diagram on an unsaved E change, followed by restored saved evidence on reload.
- TypeScript and targeted ESLint passed. Screenshots are in `screenshots/`.
- No original database record changed. New projects and evidence are append-only. The additional retained copy created during the prior milestone remains untouched.
- The supported models are **dedicated two-dimensional linear verification benchmarks**, not general analysis of the existing 45/135-component platform, arbitrary frames or a real building. Section stress recovery, joint releases, distributed loads, shear deformation, out-of-plane torsion, nonlinear/P-Delta response, buckling, foundations/soil, seismic/dynamics and IS/US code checks are unsupported.
- Numerical verification is not structural adequacy or engineering approval. Code checks and safety approval remain disabled. No further phase was started.

OpenSees implementation references: [elasticBeamColumn](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/elasticBeamColumn.html) and [Linear coordinate transformation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/geomTransf/Linear.html).

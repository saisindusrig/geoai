# Saved physical structural assembly FEA — local milestone

Completed only the selected three-member, linear elastic frame workflow. No GitHub operations, commits, deployment, installation or paid inference. Engineering approval and IS/US design checks remain disabled.

## Local review

Open http://localhost:3001/projects/781/workspace and **Checks → Saved structural assembly**. Choose **Select saved analysis members**, then **Preview selected physical graph**. The saved results are available immediately; deformation, bending moment, shear, axial force and reaction buttons show actual computed results at the physical coordinates. Shift-click selection in the viewport was tested. Sections, material evidence, loads, support assumptions and rigid joints are editable explicitly; draft changes invalidate the displayed evidence.

This separate review project contains real saved solid-box geometry, not the older benchmark display envelopes. The latest restored saved revision is **79**, analysis **234**, OpenSees run **84de8228-f6db-44e8-93f7-eb97cd1da997**. Original revision 77 and the deliberately invalid geometry edit in revision 78 remain in history. Restoring geometry created a new revision and required fresh inputs/proposal authorization before computing current results.

## Physical-to-analytical mapping

Stable IDs:

- `industrial-platform-5x3:physical-frame-column-left`: center [1, 2, 1.5] m, dimensions [0.3, 0.2, 3] m; analytical nodes 1 → 2.
- `industrial-platform-5x3:physical-frame-beam-top`: center [3, 2, 3] m, dimensions [4, 0.2, 0.3] m; nodes 2 → 3.
- `industrial-platform-5x3:physical-frame-column-right`: center [5, 2, 1.5] m, dimensions [0.3, 0.2, 3] m; nodes 4 → 3.

Saved metric local ENU coordinates map to analytical X = East − 1 m, Y = Up, at constant North = 2 m. Positive analytical rotation is about negative North. The 3D results apply the inverse mapping and existing project placement transform. Geometry supplies lengths and positions. Shared nodes exist only after explicitly declaring both corresponding column-top/beam-end rigid joints. Touching surfaces are never accepted as structural connection evidence.

Each selected member requires an explicit solid-rectangle section, material identification, elastic modulus and sources. A and in-plane Iz must match the saved geometry and orientation. Per-member elastic moduli can differ. Missing/duplicate component references, incorrect sections, unsupported joints/supports and nonplanar geometry are rejected server-side. Numerical values cannot be supplied through arbitrary AI-generated scripts.

The original platform (project 768, revision 59) was audited and preserved. Its north-beam centerline ends are at x ≈ ±3 m, z = 3.3 m, while the column heads are x ≈ ±2.85 m, z = 3.2 m: about 0.18028 m endpoint offsets. Those interfaces need explicitly validated offset/connection modeling, so they were not silently connected or shortened. See platform-geometry-audit.json.

## Explicit synthetic verification case

These are declared synthetic verification inputs, not approved project engineering values:

- Span 4 m, two columns 3 m high. All three solid rectangular sections: A = 0.06 m² and Iz = 0.00045 m⁴; E = 200 GPa.
- Both bases fixed in both translations and rotation; both top joints declared rigid. This does not verify connection or foundation capacity.
- Total +East nodal load 20,000 N, 10,000 N at each column head. No self weight or distributed loads.
- Real OpenSees 3.8.0, linear `elasticBeamColumn` elements, three in-plane DOFs per node, `geomTransf Linear`, convergence code 0. Executable SHA-256 `5aa4e9c80c410c510ca62ac3b2f1d64a8e50679f0238e140b5bebcd6d5ddbe6d`.
- Each top joint sway: **0.3873035684 mm**. Left/right vertical displacement: **+0.0015317411 / −0.0015317411 mm**. Both rotations: **−0.00009153571226 rad**.
- Both base horizontal reactions: **−10,000 N**. Left/right vertical reactions: **−6,126.964316 / +6,126.964316 N**. Each base moment: **17,746.071368 N·m**.
- Column shear magnitudes: 10,000 N. Column axial forces are opposite in sign, magnitude 6,126.964316 N. Beam transverse shear magnitude: 6,126.964316 N; beam axial force is zero within numerical precision. Local sign conventions are shown beside the force evidence.
- Global equilibrium residual Fx/Fy/M: **−8.004×10⁻¹¹ N / −2.728×10⁻¹² N / 2.183×10⁻¹⁰ N·m**. Largest joint-equilibrium residual: **7.331×10⁻¹⁰** in N/N·m.

## Independent verification

The solver is independently compared at every node and member end against a separately assembled SI Euler-Bernoulli stiffness solution (Kff uf = Ff, R = Ku − F). The full reference matrix/load vector, element forces, comparisons and joint/global equilibrium residuals are retained. Largest translation/rotation absolute difference: 2.711×10⁻¹⁹; largest member-force/moment difference: 6.505×10⁻¹⁰ in SI units.

A separate symmetry-based hand calculation does not use that matrix assembler or solver outputs. With top sway u, top rotations θ, and vertical displacements left = −v/right = v:

    a u + b θ = P
    c v + d θ = 0
    b u + d v + f θ = 0

    a = 24EI/H³; b = 12EI/H²
    c = 2EA/H + 48EI/L³; d = −24EI/L²
    f = 8EI/H + 12EI/L
    j = f − d²/c
    u = P / (a − b²/j); θ = −bu/j; v = −dθ/c

    Rx = −P/2; Ry,left = EAv/H
    Mbase = 6EIu/H² + 2EIθ/H
    2 Mbase − Ry,left L = PH = 60,000 N·m

Those equations independently reproduce the displacements and base reactions above. The evidence contains their coefficients and values. This validates this linear theory/case, not structural adequacy or general connection behavior.

Actual saved-geometry runs with 1/2/4 elements per member agree at the physical joints and reactions; N-mm conversion matches SI; half-load results halve. Browser tests change one column to E = 190 GPa and verify the asymmetric response independently. The exact cubic displacement interpolation for nodal-load Euler-Bernoulli elements is not a convergence guarantee for other element formulations or loads.

The selected implementation uses the documented [OpenSees elastic beam-column element](https://opensees.berkeley.edu/wiki/index.php/Elastic_Beam_Column_Element) and [linear coordinate transformation](https://opensees.berkeley.edu/wiki/index.php/Linear_Transformation). Deformation is labeled 50× amplification; force diagrams and reaction vectors are normalized display offsets, with actual N/N·m values shown. They are not stress contours or solid/shell analysis.

## Tests and preservation

- **111 backend tests passed**, including the prior axial, column, beam/frame and AI workflows. A framework deprecation warning remains; it did not affect test results.
- Full browser workflow passed: actual viewport multi-selection, physical graph preview, explicit per-member material/section, joint/support/load declaration, exact-hash authorization and tampered-hash rejection, actual OpenSees, five result views, unit conversion, 4-element mesh, load scaling, nonuniform material, immutable save/reload, undo/redo, stale results and restoring a new revision.
- A second browser test passed after final backend restart: saved geometry/result reload, fresh exact authorization, display mapping and downloaded solver-input byte-hash equality.
- TypeScript and targeted ESLint passed. Offline fixture explanation is labeled unverified AI text. This is not a live Nebius capability test.
- Original database preservation: **9,438 pre-existing rows across 62 tables, zero changed or missing**. Original models, prior benchmark results, revisions and AI evidence remain intact. New review-project data/evidence is additive.
- **Zero live inference requests**. Existing Nebius usage ledger remains 22 records; cloud proposals receive HTTP 403. Keys remain in existing backend environment configuration and are not copied into the frontend or artifacts.
- Source inputs, solver script, output files, stdout/stderr, executable version/hash, convergence status, input hashes, document hash, revision identity and member mapping remain downloadable in the Checks panel. Model/input changes require a new reviewed proposal and exact solver authorization.

New runs store both canonical text and actual file-byte SHA-256; exact raw newlines are preserved in assembly downloads. A Windows CRLF mismatch was corrected without editing older records or artifacts. Older retained runs may have a canonical-text `input_file_sha256`; their `artifact_sha256["model.tcl"]` remains the actual original file hash.

Evidence files: browser-evidence.json, numerical-evidence.json, preservation-evidence.json, platform-geometry-audit.json and screenshots/.

## Unsupported conditions

Only a selected three-member, unrotated XZ planar portal with equal-height vertical columns, a horizontal beam, positive solid-rectangle dimensions, explicit rigid centerline joints and fixed bases is supported. Only equal horizontal nodal loads at the two heads are supported. Unselected members and their interactions/load transfer are not analyzed.

Rejected or disabled: eccentric/noncoincident joints; rotated, scaled, inclined or out-of-plane members; unsupported sections; missing material/load/support sources; releases/unvalidated joint behavior; slabs, foundations, springs and soil; self weight/distributed/vertical load cases; whole-building analysis; geometric nonlinearity, buckling, seismic/dynamic response; connection/foundation design; IS/US code compliance; automatic design changes or structural safety approval.

STOP: this milestone is complete for local review. No further systems or phases have been started.

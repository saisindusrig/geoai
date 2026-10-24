# Saved physical column → local OpenSees

Completed locally, 11 October 2026. No GitHub operations, commits, deployment, paid AI or additional software installation.

## Review locally

- Original platform: http://localhost:3001/projects/768/workspace — unchanged revision 59. Open Checks and select a saved column. Engineering inputs remain empty until supplied explicitly.
- Working numerical verification: http://localhost:3001/projects/773/workspace — separate saved copy of project 768/revision 59. Open Checks and select column-ne. Latest computed result is model revision 68, input record 124, analysis record 125.
- Backend: http://127.0.0.1:8001. Both local services remain running.

## Implemented scope

One supported workflow converts a selected existing maintenance-platform column into an isolated linear elastic axial OpenSees model. Its identity, box dimensions, orientation and ENU endpoints come from the exact saved model revision. The original selected column is 3.2 m long, not the earlier 3 m benchmark. No replacement benchmark geometry is generated for it.

Geometry consistency checks require finite positive dimensions, explicit metre units/local ENU coordinates, unit scale, no nested transform and a vertical member. Saved yaw is recorded. Tilted columns are rejected. The complete saved document also passes the existing component-reference/connectivity validation before conversion.

The UI requires explicit material identification and source, elastic modulus, declared solid rectangular section dimensions and source, centered axial compression and source, prescribed linear spring stiffness and source, input purpose and acknowledgement of the isolated axial idealization. No material, load or support engineering value is prefilled from rendering materials. Section dimensions must match the saved envelope. Hollow/rolled sections are unsupported.

OpenSees receives a fixed reference node, coincident column-base node, elastic axial zero-length spring, 1/2/4 uniform axial truss elements and an explicit downward head load. The 1D solver axis maps to the saved column's vertical ENU axis. Outputs include actual nodal displacements, element axial forces, stress calculated from solver force divided by declared area, and support reaction. All are converted back to canonical SI before display. The SVG uses actual computed nodal displacement with a labelled ×100 deformation scale; it is not a stress contour or full-platform FEA.

Engineering inputs are immutable appended records using the existing engineering-analysis store; no database schema changes. Results retain model/component/input hashes, record IDs, actual executable hash, OpenSees version, input/output files, stdout/stderr and convergence evidence. Ownership and fixed artifact filenames are enforced. UI downloads include model.tcl, nodes.tsv, forces.tsv, summary.tsv, stdout.txt, stderr.txt and manifest.json.

Changed geometry/model revision, material, load, support or other engineering input makes prior results stale. Unsaved model/analysis drafts and previews block execution. A new model revision requires explicit reassociation of inputs before rerunning. Historical results remain available through the component analysis-history API and evidence files. Existing model revision comparison and undo/redo are preserved.

## Numerical evidence — explicit synthetic verification inputs

These inputs test the implementation. They are **not project design properties, engineer-approved loads or geotechnical data**. The input purpose is VERIFICATION_ONLY in the UI and persisted record.

Initial actual saved geometry: component `industrial-platform-5x3:column-ne`, model revision 67, length 3.2 m, declared solid section 0.3 × 0.3 m (A = 0.09 m²). Explicit test values E = 200 GPa, P = 100 kN, k = 100 MN/m, 2 elements, SI solver units.

- Column shortening: 0.0177777777777780 mm. Independent P L/(E A): 0.0177777777777778 mm.
- Support translation: 1.0000000000000102 mm. Independent P/k: 1 mm.
- Head displacement: 1.0177777777777882 mm. Independent P L/(E A) + P/k: 1.0177777777777778 mm.
- Compression stress: 1.1111111111111261 MPa. Independent P/A: 1.1111111111111111 MPa.
- Upward reaction: 100.00000000000102 kN. Independent equilibrium: 100 kN.
- Equilibrium residual: 1.0186340659856796e-9 N.
- Actual run: 5b99b5e7-6d61-4079-b06f-f0011cfb8a7d, analysis 119, OpenSees 3.8.0.

A separate two-DOF stiffness calculation checks K = [[EA/L+k, -EA/L], [-EA/L, EA/L]], with centered head compression. Analytical formulas and actual stiffness matrix/load vector are recorded independently of solver outputs. Acceptance requires matching references within 1e-6 relative tolerance and equilibrium within 0.1 N; these are numerical verification tolerances, not safety criteria.

Changing E to 190 GPa and P to 50 kN, then running 4 elements in N–mm produces 0.5093567251461595 mm head displacement, 0.5555555555555134 MPa stress and 49.9999999999961 kN reaction. Prior results become stale.

Editing the saved platform's deck height from 3.6 to 3.8 m makes this physical column 3.4 m long. After undo/redo, save, explicit new input association and rerun, revision 68 yields 0.5099415204678575 mm head displacement, 0.5555555555555862 MPa stress and 50.00000000000209 kN reaction. Equilibrium residual is 2.0881998352706432e-9 N. Actual final run: 36d04173-22cf-4cb4-aff4-180f2503fca9.

Full snapshots, independent references, provenance, mesh and historical statuses: [browser-evidence.json](browser-evidence.json). Raw final files: `backend/storage/opensees-benchmark/36d04173-22cf-4cb4-aff4-180f2503fca9/`.

## Local verification

- 29 new backend tests passed: saved identity/geometry/transform/units, invalid geometry, section mismatch, explicit required inputs, unsupported methods, small-displacement bound, actual 1/2/4 element runs, SI/N–mm conversion, half/double load, independent references, equilibrium, immutable input revisions, ownership, optimistic input conflicts and stale results.
- 34 existing OpenSees tests passed, including actual benchmark runs and solver/output failure handling. Each physical run also requires the existing six-case solver verification suite to pass.
- 53 frontend regression tests passed: parametric platform 8, attachments 21, editable-model utilities 3, engineering dock 3 and editor hook 18.
- TypeScript compilation and targeted ESLint passed. No production deployment/build was performed.
- Two real Chromium/local-server browser tests passed: full selected-column workflow and original-project benchmark/default-input preservation. The full test captured no page exceptions or Cesium error panel.
- Initial browser-test harness failures were corrected: disclosure-open state, numeric rounding and the editor's existing selection reset after model save. These were test assumptions, not numerical solver failures.
- Preservation audit compared all 9,242 original rows across 62 tables against the pre-work SQLite snapshot: zero changed or missing original rows. See [preservation-evidence.json](preservation-evidence.json). Original projects were not edited; geometry save tests used separate local copies.

Screenshots: [initial SI result](screenshots/column-si.png), [stale after geometry save](screenshots/column-stale.png), [final physical model and computed result](screenshots/column-final.png).

## Limits and engineer review

Engineering approval and IS/US code checks remain DISABLED. Numerical verification validates this axial model implementation; it does not establish structural adequacy or site suitability. Material/source declarations and the solid section require engineer review; the application cannot certify their truth.

Unsupported: bending, buckling, lateral loads, load combinations, self-weight, nonlinear response, surrounding frame redistribution, connection load transfer, base-plate/anchor design, actual foundations, reinforced concrete, soil constitutive analysis and hollow/rolled section design. The prescribed axial spring is not a foundation/soil design. Surrounding components remain physical geometry and are explicitly excluded from this analysis.

The supported total displacement is bounded to 1% of column length as a small-displacement model-validity restriction, not a structural safety check. Model geometry is local conceptual geometry, not survey verification. No additional analysis disciplines or phases were started.

Reference for the supported element: [official OpenSees Truss documentation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/Truss.html).

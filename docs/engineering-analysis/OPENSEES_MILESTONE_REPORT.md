# GeoAI OpenSees milestone — local review

Completed 11 October 2026. Review http://localhost:3001/projects/768/workspace → **Checks → OpenSees axial column benchmark**. The in-app browser is left on the computed-results view.

## Implemented and independently checked scope

Actual OpenSees 3.8.0 runs locally as an isolated subprocess. The official Berkeley Windows package was installed only after explicit user permission, under `.cache/opensees`. No PATH or machine-wide installation was required. The development API remains on 127.0.0.1:8001 with mock AI, cloud credentials and paid AI providers disabled; the website remains on localhost:3001.

The model has one fixed ground node, one coincident spring/column-base node, and 1, 2 or 4 truss segments along a one-dimensional coordinate representing local vertical z. A zeroLength element with an elastic force–displacement material connects ground to base. Elastic trusses use E = 200 GPa and A = 0.01 m² over L = 3 m. A centered downward nodal force is applied at the column head; the spring stiffness is 100 MN/m. Only the vertical DOF exists, so there are no unconstrained lateral/rotational DOFs in this idealization. The model uses a linear static solution, one load step and explicit restraints. Solver coordinates and nodal displacements are upward positive; compression axial force is negative. GeoAI displays shortening/settlement downward positive, compression stress positive, and the upward reaction positive.

The default solver input is SI (metres, newtons, pascals). N–mm input converts length, section area, E and spring stiffness consistently, while forces remain newtons. Output displacement is normalized back to metres, force to newtons and axial stress to pascals. Stress is calculated transparently from the actual computed truss axial force divided by the specified area; it is not an invented or nodal solid stress field.

At 100 kN, the review run linked to **project 768, model revision 59, analysis 101** returned:

- Column shortening: **0.150000 mm**, versus PL/(EA) = 0.15 mm.
- Spring settlement: **1.000000 mm**, versus P/k = 1 mm.
- Head displacement: **1.150000 mm**, versus the sum = 1.15 mm.
- Compression stress: **10.000000 MPa**, versus P/A = 10 MPa.
- Upward ground reaction: **100.000000 kN**, versus P = 100 kN.
- Equilibrium residual: **1.455 × 10⁻¹¹ N**.

All five independently defined comparisons must satisfy relative error ≤ 10⁻⁶. Equilibrium and every segment axial force must agree with applied force within 0.1 N. Mesh identities/positions, ground restraint, finite outputs, complete output counts, convergence code and process exit are also checked. These are software benchmark tolerances, not general engineering acceptance criteria.

Each UI run executes a six-case verification suite before enabling its selected result: SI with 1/2/4 elements, 50 kN and 200 kN with 2 elements, and an equivalent N–mm case. Expected displacement/stress/reaction scale by 0.5 and 2 respectively. The original closed-form reference was independently cross-checked using a separate two-DOF stiffness formulation; solver comparison does not use an OpenSees-produced expected answer.

## Evidence, provenance and persistence

Each actual subprocess run retains `model.tcl`, `nodes.tsv`, `forces.tsv`, `summary.tsv`, `stdout.txt`, `stderr.txt` and `manifest.json` in `backend/storage/opensees-benchmark/<run UUID>`. Output TSV files contain raw solver-unit coordinates/displacements and newton forces; the manifest identifies units and normalized results. Summary records the solver-reported version, convergence code and reaction. Every selected run includes the six verification-run manifests.

The executable path/checksum, input-file checksum, engineering-input checksum, timestamp and exact model-document checksum are persisted with the result. Existing EngineeringAnalysis records store these immutable payloads with the exact model-revision ID; there was no database migration or replacement of existing geometric checks. UI downloads are project-owned, authenticated through the existing API client and restricted to a fixed artifact filename list. No request can choose an executable, arbitrary Tcl or filesystem path. Execution has a timeout and a per-process concurrency lock.

Applicability is separate from historical results. Unsaved model edits, pending geometry previews, changed load/mesh/unit inputs, a superseding saved revision or a model-document hash mismatch mark results **STALE**. Saved revision changes also use the existing stale-analysis mechanism. Original output payloads and files remain available for review. Reload restores the last run's input snapshot; selector edits are drafts until a new run is submitted. An older-revision run request is rejected with HTTP 409. Invalid dimensions/options and executable-override payloads are rejected before execution. A failed solver or failed verification suite never displays as a verified computed result.

GeoAI displays actual nodal displacement, per-segment axial force, ground reaction, reference comparisons and provenance in Checks. Its displacement diagram uses computed node coordinates/displacements, labels units and declares ×100 deformation exaggeration. It is a schematic of the isolated benchmark, not a stress contour on the maintenance platform. Existing platform geometry is displayed alongside it unchanged.

## Tests actually executed

- **34 backend tests passed:** actual 1/2/4-element solver runs, load scaling, N–mm equivalence, equilibrium, raw artifact capture, invalid input, missing executable, actual Tcl command failure, actual timeout, actual zero-stiffness nonconvergence, an unrestrained mechanism, mocked process errors/timeouts, corrupted/missing/nonfinite outputs, unexpected node identities, wrong force/restraint, nonzero process exit, project ownership, immutable persistence, revision staleness, artifact access, concurrency lock and suite-gate rejection.
- **47 frontend regression tests passed:** platform regeneration, attached-component geometry and editor history.
- **Full new browser workflow passed on localhost:3001:** real solver execution, computed diagram/values, artifact download, selector staleness, N–mm + double-load run, reload, model preview/edit, undo/redo, save, server/client stale status, preservation of the previous revision and rejection of invalid/obsolete requests. Save tests used separate **project 769**; original project 768 geometry/revisions were not edited.
- **Existing platform browser regression passed:** selection, attached stair editing, protected references, whole-assembly deletion preview/cancel, save protection and camera framing. It did not save model edits to project 768.
- TypeScript and targeted ESLint passed. No claim is made that the entire historical application test suite was rerun for this milestone.
- Database snapshot comparison checked **9,217 original rows across 62 tables**, with **zero changed or missing original rows**. New analysis evidence and a separate test project/revisions were added. The snapshot is `.cache/opensees-milestone/dev-before.db`.

One important failure test demonstrates why convergence alone is insufficient: removing the ground restraint produced a numerical result with convergence code 0 but zero support reaction. Independent equilibrium/reference verification correctly rejected it. A separate zero-stiffness test produced a nonzero convergence code and exit code 2; both failures are recorded. These are deliberately invalid linear test models, not nonlinear analysis.

The additional platform regression was initially blocked by automatic approval review's usage limit. It was retried after the stated reset time, approval succeeded, and the browser regression passed. No approval check was bypassed.

## Limitations and stopping point

This verifies only the isolated elastic axial-column/prescribed-spring problem. The 3 m length and 0.01 m² section are explicit benchmark inputs; they are not inferred from the current 6 × 4 × 3.6 m platform or its conceptual box columns. Linking a benchmark to revision 59 establishes provenance, not verification of that platform's physical structural system.

There is no base-plate flexibility/contact, anchor engagement, RC footing reinforcement/strength, soil capacity/calibration, self-weight, bending, buckling, lateral response, second-order effects, dynamics or nonlinear analysis. The plate/footing are rigid idealizations and anchors inactive under this compression-only case. No unsupported check is turned into PASS.

**All design-code checks and engineering approval are disabled.** The preserved geometry-review action was relabeled **Record geometry review**, with an explicit statement that it cannot approve FEA, connections, foundations or engineering adequacy. Numerical benchmark verification is not professional engineering approval.

No IS/US code packs, foundation design, nonlinear systems or subsequent milestones were started. No GitHub operations, commits, deployment or paid AI calls were performed. This milestone stops for review.

## Review files

- `review-run-evidence.json`: persisted actual run for project 768/revision 59, including its six-case suite.
- `opensees-numerical-evidence.json`: first actual six-case solver/reference comparison.
- `browser-evidence.json`: successful new workflow, saved test revision and historical analysis applicability.
- `failure-evidence.json`: deliberately invalid solver cases and their raw input/output/error evidence.
- `database-preservation.json`: original-row preservation comparison.
- `screenshots/opensees-review.jpg`: preserved assembly beside the real computed results.
- `screenshots/opensees-provenance.jpg`: solver/model/input hashes and raw artifact download controls.
- `screenshots/opensees-stale.png`: saved-model revision change invalidating earlier results in the separate test project.

Official package source: [Berkeley OpenSees executable distribution](https://opensees.berkeley.edu/OpenSees/user/download.php). Solver element semantics: [OpenSees zeroLength documentation](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/zeroLength.html).

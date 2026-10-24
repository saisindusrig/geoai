# Real Nebius engineering project test — 12 October 2026

Local only. No GitHub operations, commits, deployments, software installation or paid service other than the explicitly authorized Nebius inference. Live testing has stopped.

## Local website and preserved data

- Saved platform test: http://localhost:3001/projects/775/workspace
- Large context test: http://localhost:3001/projects/776/workspace
- Original project 768 and every pre-existing database row preserved: 62 tables, 9,326 original rows compared byte-for-byte by primary key; zero changed or missing rows. See `preservation-evidence.json`.
- Initial platform copy: revision 72, 45 components: four beams, four columns, one slab, four foundations, four base plates, four connections, two braces and 22 stair parts (one stair assembly).
- Stress fixture: revision 73, 135 components in three independent geometric bays at east offsets 0/20/40 m. Internal component references were remapped. Additional bays are frozen geometric copies, not a new multi-bay parametric generator or connected building analytical model.
- Browser height edit changed deck height from 3.6 to 3.8 m and column length from 3.2 to 3.4 m. Existing parametric stairs regenerated two additional treads, giving revision 74 **47 components**. Undo/redo, save/reload and stale evidence were tested on this isolated copy.
- Setup also retained an extra separate 45-component copy, project 777; original projects were not modified or deleted.

## Implemented and tested

The Assistant has a bounded whole-model review action. It supplies every saved component's identity, category, geometry, transform and references, attachment assemblies, independent-bay metadata, exact saved revision/hash and any explicit engineering inputs. Returned inventories must match; cited component IDs must exist. Reviews are unverified and become stale after geometry or engineering-input changes.

Native Nebius function calling can prepare only `prepare_column_analysis` with the exact saved revision, component and input-record identity. It cannot run a solver, introduce engineering properties, execute arbitrary code or modify geometry. A separate explicit authorization sends the exact hashed proposal to the existing validated OpenSees backend. Actual results return to a subsequent inference for explanation. Numerical values come from solver evidence, not generated prose.

Live testing uses the existing backend credential; no key entered the frontend or report. `backend/scripts/serve_live_nebius_test.py` enables only the guarded Nebius workflow while disabling other cloud AI/storage integrations. The single-process backend serializes inference reservations against a persistent global ledger with a $10 maximum. Each reservation bounds input UTF-8 bytes plus protocol overhead and configured output tokens at published rates; uncertain usage retains the reservation. Failed responses with reported usage still count. Legacy completion paths cannot bypass this ledger. This controls estimates, not the provider's actual billing system.

## Live inference evidence

- **22 live inference requests**: 11 Flash and 11 primary. No mocks used for these requests.
- Provider-reported input: **201,002 tokens**. Output: **46,813 tokens**, including reported reasoning usage. Total: **247,815 tokens**.
- Total estimated cost: **$0.2928594 USD**. Flash $0.0238562; primary $0.2690032. Unknown-usage reservations at the end: $0. Actual provider billing is unknown; these figures are not receipts.
- **13 responses accepted; nine rejected** by incomplete-output/schema/evidence/claim validation. All failures remain accounted. Model revisions can mark old ledger rows stale, but their cost remains in the cap; response acceptance is counted from HTTP evidence rather than that staleness label.
- **Six native proposal tool calls**, all accepted with exact restricted arguments. Both models identified missing inputs without supplying values; neither executed a solver automatically.
- Initial 4,096-output-token requests exhausted their allowance before complete answers. After changing to bounded 16,384 output tokens and low reasoning effort, both models successfully reviewed the 45- and 135-component contexts. Later review attempts remained unreliable: Flash cited a nonexistent component; the final primary review exhausted its output allowance. No automatic retries or solver authorizations followed those failures.
- Whole-model reviews are archived on revision 72/73. The revision-72 reviews are correctly **STALE** after geometry/input changes. The current revision-74 column result and full primary explanation are retained; no successful current whole-model review is implied.

Published prices used: Flash $0.15 input / $0.50 output per million tokens; primary $1.40 / $4.40. [Nebius official GLM catalog and pricing](https://nebius.com/services/token-factory/models/glm-models-inference). The account model catalog was checked without inference before testing. [Z.ai documents GLM-5.3 reasoning effort](https://docs.z.ai/guides/llm/glm-5.3). Backend availability retains the 11 October pricing-check date; testing crossed into 12 October local time.

## Model comparison and factual review

For the paired successful reviews, Flash took about 13.4/15.0 seconds for 45/135 components; primary took 8.7/12.6 seconds. Both copied actual category totals and recognized one stair per bay, not one stair per tread. Both identified missing loads, materials, section designations, connection behavior, soil/anchorage data and unsupported global analysis. Both recognized the three independent bays.

**GLM-5.3 produced the better factual review in this small sample**: it correctly located braces on the east/west elevations, while Flash mislabeled them north/south in its 45-component narrative despite citing the correct column pairs. Neither constitutes engineering verification. Primary costs substantially more and also failed a later review. Flash remains the low-cost default; no broad capability or reliability claim follows from this small test. Suggestions remained qualitative and were never applied automatically.

The UI provides bounded review/proposal/explanation actions, not unrestricted autonomous whole-project management or a multi-tool planner that runs complete building analysis from free-form chat.

## Actual OpenSees and independent validation

Four physical-column solver runs were performed, two per geometry/input state, using OpenSees **3.8.0**. Every run passed the existing verification suite and independent comparisons.

Explicit **synthetic verification inputs**, never represented as real project design properties: solid rectangular 0.3 × 0.3 m section, A = 0.09 m², centered compression P = 100,000 N, prescribed linear axial spring k = 100,000,000 N/m. This spring is not inferred soil support. Linear axial-only idealization with two truss elements; no actual foundation/connection stiffness is analyzed.

Initial saved column L = 3.2 m, E = 200 GPa, revision 72:

- PL/(EA) = **0.0177777778 mm** shortening.
- P/k = **1.0000000000 mm** spring settlement.
- Sum = **1.0177777778 mm** head displacement.
- P/A = **1.1111111111 MPa** compression stress.
- Element force = **−100 kN**; upward reaction = **100 kN**.
- OpenSees equilibrium residual **1.018634 × 10⁻⁹ N**; maximum relative comparison error about **1.36 × 10⁻¹⁴**.

Changed saved column L = 3.4 m, explicitly changed E = 190 GPa, revision 74, input 164, latest analysis 171:

- PL/(EA) = **0.0198830409 mm** shortening.
- P/k = **1 mm** settlement; total **1.0198830409 mm**.
- Stress **1.1111111111 MPa**; reaction **100 kN**; elements each **−100 kN**.
- Equilibrium residual **4.074536 × 10⁻¹⁰ N**.
- Latest run ID `aa5edd0f-1e56-4dbc-804c-7405d697589f`. Exact input/output/provenance is available through Checks → physical column evidence. The primary explanation is bound to analysis 171 and evidence SHA-256 `884eb613d06c17150febe4b34771aa9ed8d19b323a3d9210dc100945927371ab`.

Original three-metre reference benchmark and its historical evidence remain preserved: 0.15 mm shortening, 1 mm support settlement, 1.15 mm total, 10 MPa and 100 kN reaction. Different values for the selected saved column follow from its actual different length/declared area, not a changed reference benchmark.

## Local verification

- **81 backend tests passed** across agent, physical column, OpenSees benchmark and API tests. These include 1/2/4 discretizations, load scaling, SI/N-mm conversion, equilibrium, unsupported geometry/errors, authorization/staleness and budget guards. Mock transport is used in regression tests; live evidence is recorded separately.
- TypeScript and targeted ESLint passed.
- Browser rendered all 135 initial stress components and all 45 initial platform components, framed independent bays and loaded real solver evidence. After the edit it rendered 47 components, saved/reloaded revision 74, and marked previous proposals/results stale. Numerical formatting and stair regeneration required correcting test expectations, not disabling validation.
- Tampered proposal hashes rejected with HTTP 409 before solver execution. Explicit-input and geometry changes preserve history while invalidating old evidence.
- Final browser evidence, screenshots, live request/response evidence, usage ledger and database-preservation evidence are in this directory. No further live requests run automatically.

## Unsupported and next realistic milestone (plan only)

Whole-building FEA, real foundation/soil analysis, connections/base plates/anchor capacities, bending/shear/torsion, buckling, nonlinear behavior, seismic/dynamic analysis and IS/US code compliance remain unsupported. Geometry/reference checks do not establish force-transfer stiffness, capacity or a complete engineering load path. AI text is unapproved; numerical verification applies only to the supported axial model. Structural safety approval and design-code checks remain disabled.

Before expanding to global FEA, define a versioned physical-to-analytical graph: node/member identities, offsets, releases, material/section records with sources, explicit engineer-supplied loads, combinations and support properties, stable mesh mapping and revision/input/result hashes. The smallest next numerical milestone should be one linear elastic beam or portal-frame benchmark with independently verified displacement, bending forces and equilibrium; only then combine members into a global model with validated joint connectivity and load transfer.

Keep solver computations separate from versioned country/jurisdiction/code-edition check modules. Develop independently benchmarked Indian IS and American AISC/ACI/ASCE checks after each relevant analytical method is validated. Foundation/soil and steel-to-concrete connections require geotechnical inputs and separate validated methods. No part of that expansion was implemented here.


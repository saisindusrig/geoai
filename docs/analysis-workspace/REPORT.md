# Engineering Analysis workspace — local review

Review URL: http://localhost:3001/projects/781/workspace. Choose **Analysis** in the right rail, then **Fit Analysis**. The existing port 3000 instance and environment file were preserved; the review frontend uses process-local API settings.

Implemented a dedicated Analysis inspector within the existing workspace. Opening it gives the model more space by temporarily hiding the adjacent Assistant pane without changing its saved visibility preference. Frame Model frames the physical assembly; Show/Hide Results controls the overlay; Fit Analysis centers the computed diagram. The completed proposal is collapsed, while active authorization proposals remain reviewable.

Results have Overview, Displacement, Axial Force, Shear, Bending Moment, Reactions and Evidence views. Signed extrema carry units and member names; full stable component IDs are available in inspection and tooltips. Displacement extrema refer to stored sampled translation magnitudes, not an asserted continuous maximum. Support reactions show support nodes and linked column identities. Clicking a physical member or a diagram with its component identity selects the existing saved component. Inspection displays endpoint translations, rotations and actual element forces. Deformation is amplified 50 times; force curves remain explicitly normalized display geometry. Straight local polylines now use ArcType.NONE so short analytical curves render correctly rather than being treated as globe arcs.

Evidence expands to coordinate mapping, equilibrium residuals, raw member end forces, solver logs and SHA-256 hashes. Existing artifact downloads are retained. Offline AI explanations use the existing restricted fixture path and saved solver evidence; their text is labelled unverified. Explicit material/section/load/support/joint inputs, exact-proposal authorization, revision checks, stale-result suppression and disabled engineering approval remain unchanged.

## Verification

- Two Chromium workflow tests passed: saved result mapping and signed extrema; all five diagram modes and hide/fit controls; actual viewport beam selection and computed-curve component picking; column inspection via linked support; stored revision reload; real solver-log retrieval; desktop 1600 px and narrower 1280/900 px without horizontal overflow; offline fixture explanation; changed load staleness; geometry undo/redo staleness and discard/reload.
- A final read-only capture rerun passed after the camera/legend refinements.
- Existing physical-frame backend regressions: 15 passed. TypeScript and targeted ESLint passed.
- All 9,484 pre-existing rows across 62 tables were checked against the SQLite backup: no changed or missing original rows. Model revision 79 and analysis 234 remain intact. Offline explanations append records; they do not replace existing evidence. No new geometry revision was saved in this UI-only review; the existing save implementation was retained and previously saved geometry/results were tested through reload.
- Live paid inference calls this milestone: zero. Existing inference ledger remains at 22 entries. No GitHub, Git operations, deployment, installation or solver-method edits.

## Existing numerical evidence shown by the UI

OpenSees 3.8.0; saved three-member frame, revision 79 / analysis 234. Column head ux 0.3873035683894 mm; sampled maximum translation 0.388797 mm on beam-top. Base Fx is -10 kN at each column; Fy is -6.126964316106/+6.126964316106 kN; base moments are 17.746071367788 kN·m. Global residuals are about -8.004e-11 N, -2.728e-12 N and 2.183e-10 N·m. The existing independent-reference and mesh/unit verification evidence is retained in the numerical evidence file and solver manifest. Values come from saved solver results, not new illustrative calculations.

## Limitations

This workspace exposes the currently supported three-member planar elastic frame. It does not add whole-building, nonlinear, buckling, slab, foundation, eccentric-joint, connection-capacity or IS/US design checks. Engineering adequacy and approval remain disabled. Sources remain synthetic verification assumptions. Display-scaled curves and offline AI prose are not design approval. Mobile layouts below 768 px were not included in this desktop-focused browser test.

Screenshots: screenshots/overview.png, member-moment.png, evidence.png, responsive-1280.png and responsive-900.png. Evidence: browser-evidence.json, numerical-evidence.json and preservation-evidence.json.

Stopped at this milestone for review.

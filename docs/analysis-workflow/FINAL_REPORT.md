# Guided Analysis workflow — visual review

The default Analysis interface now follows **SELECT → INPUTS → ANALYZE → RESULTS**. This milestone changes usability and presentation; it introduces no engineering calculation method.

Open the normal website at http://localhost:3001/projects/793/workspace and choose **Analysis**. A separate, fully exercised synthetic structural workflow is at http://localhost:13001/projects/830/workspace. Project 829 is the separate empty-model example. Both new projects exist only in the isolated review database.

## Default experience

SELECT presents Structural analysis, Slabs and floor systems, and Foundations and soil. Availability comes from saved model metadata, component categories and current evidence. Geometry candidates are explicitly described as requiring inspection, not as proven physical connections. A fresh model explains that saved geometry is required. Project 804 remains an RC/foundation reference; it is not misrepresented as an integrated foundation study. Its existing specialized calculations remain accessible in Advanced mode.

INPUTS displays the selected method's necessary fields. The planar workflow lets an engineer choose two columns and a beam directly in the panel, inspect saved geometry, enter elastic moduli in GPa, identify materials/sources, explicitly choose observed solid rectangular sections, declare restraints/joints, and supply loads with units and sources. Coincident rigid declarations and rigid-offset approvals retain the existing backend distinction. Sources, detailed mappings and specialized settings remain available without becoming the default page.

Existing named frame cases and superposition controls reuse the current editor. Saved slab workflows retain support mappings, exclusions and declarations, with pressure/source editing in the guide; establishing a new complex slab/support mapping remains an Advanced operation. Spatial and coupled demonstrations expose their prescribed reviewed inputs and assumptions without pretending to support arbitrary new geometry/material cases. Foundation studies expose saved actions, independent strengths, soil properties, reinforcement and detailing; synthetic example inputs are loaded only through an explicit labeled action. No soil property, material strength, applied load or physical connection is inferred.

ANALYZE provides readiness guidance, required warnings, review acknowledgement and a prominent exact-proposal action. Creating/replacing a review does not authorize a solver run. A separate unchecked authorization control is required before **Authorize and analyze** becomes available. The existing endpoints receive the exact proposal/input ID, hash and authorization flag. Ownership, revision, input/document hash, stale-result and applicability protections remain on the backend unchanged. The offline proposal provider remains `mock`; no paid inference is enabled. Progress describes the actual pending request without inventing a solver percentage. Errors have a read-only retry; failed/stale calculations require a new explicit review and are never automatically rerun.

RESULTS centers the existing 3D workspace. Compact cards switch loads/reactions, deformation, member actions, supported floor/soil checks and warnings. The guide reuses the current structural, floor, coupled-shell and foundation overlay builders. Component selection highlights source identities; supported floor isolation, static-case animation, magnification and load-case selection remain available. A single persistent Restore model control clears temporary isolation/overlays. Detailed evidence and downloads are secondary. Numerical verification is distinct from “Within implemented check,” “Exceeds implemented check,” “Not verified” and “Not supported.” No SAFE/APPROVED label is introduced.

The header and step navigation remain visible while the panel scrolls. They identify analysis type, selection, current result/revision and next action. Default input/result content uses the existing outer panel scroll; large nested numerical viewers are not part of the default experience. Native buttons/selects, visible focus styles, step focus and live request/error messages support keyboard use.

## Advanced capabilities and reopening

**Advanced mode** mounts the complete previous Analysis interface, including specialized CAD/source review, connection inputs, slab mapping, mesh/units, foundations, soil, alternatives, evidence/history and method-specific tools. The existing content is preserved rather than replaced by a reduced implementation. Existing assistant navigation can open the guide or mount the appropriate advanced destination.

Only browser view preferences are stored: analysis family, step, visual mode and selected load case, keyed by project. Reopening reads current saved evidence; it does not save engineering inputs, edit project/CAD data, authorize a proposal or rerun OpenSees. An unsaved model, preview/comparison or changed engineering input hides the saved overlays until resolved. The authorization checkbox is never persisted.

## Important pre-existing stale result

Project **823** already had pending review **691**, making older analysis **684** stale. The guide correctly refuses to present 684 as a current verified result. Neither the pending review nor the old result was authorized, updated or deleted during this milestone. The browser tests verify this state explicitly. Project **822**, current analysis **682**, supplies the current spatial-frame visual acceptance example. Project **828**, analysis **693**, supplies the bounded coupled-shell example. Unsupported diaphragm, lateral shell, two-storey shell and capacity methods remain disabled.

## Validation and evidence

The evidence bundle includes before/after screenshots at 1280 and 1600 px, a real Chromium recording of all four steps and explicit authorization, test logs, source hashes, downloads and preservation reports.

The full frontend suite contains 392 passing tests across 80 files. Ten tests added here cover workflow routing, empty models, current/stale result distinctions, explicit authorization, drafts, error retry, preference restoration and advanced access. Relevant existing backend suites cover 298 tests across the regression and guidance logs, including native OpenSees, frame/slab/foundation methods and authorization. TypeScript and scoped ESLint results are saved separately. Final browser totals and detailed assertions are in `test-results.json` and `browser-final.log`.

Browser acceptance covers projects 793, 794, 804, foundation demonstration 814, stale spatial project 823, current spatial project 822, coupled demonstration 828 and empty project 829 at both widths. It checks step navigation by keyboard, visual cards, restoring geometry, reopening results without writes, Advanced access and absence of horizontal page overflow. A separate test completes a first-time structural analysis in project 830 using explicit synthetic 200 GPa and 20 kN declarations, through the real existing backend/OpenSees workflow, without a technical accordion. Only allowlisted modifying requests to that isolated project are permitted. All original-project browser checks block modifying requests.

Initial testing caught a coincident-joint form declaration that the existing backend correctly rejected; the UI was corrected to respect that restriction. An initial spatial test expected a pre-existing stale result to be current; the acceptance test was corrected rather than altering the engineering status. A local Next.js rewrite callback referenced a module variable unavailable in its compiled callback. Its port lookup was placed inside the callback while preserving existing port validation and configuration options. No numerical or authorization service was changed to make a test pass. Initial failure logs remain retained.

## Preservation

Read-only row/schema fingerprints were taken before implementation. The original development database's **10,245 rows and schemas remain unchanged**. All **10,484 pre-existing isolated rows** remain unchanged. Only new review projects 829/830 and their explicitly authorized test records were appended. The final append counts are in `review-preservation.json`.

Existing preservation manifests confirm all **55,296 original storage files**, **2,090 original engineering proof files**, and **264 original database schemas**. The 263 other original databases match the older fingerprints. The development database's older 10,239-row baseline differs only by its six already-existing retained additions; the new milestone baseline confirms no changes to those additions. All **635 prior spatial solver files** remain unchanged. The existing backup is reused as a verification reference; no backup is deleted, relocated or recreated.

No Git/GitHub operation, installation, deployment, paid inference, cleanup or unrelated engineering feature is part of this milestone. This remains local development. Numerical verification and bounded checks do not constitute structural safety or engineering approval.

Stopped for visual review.

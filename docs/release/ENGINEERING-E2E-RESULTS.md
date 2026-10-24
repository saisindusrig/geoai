# Engineering integration results

A real local frontend production build at localhost:3002 talks to a real JWT-only FastAPI server at127.0.0.1:8022. Database/storage paths and guards are recorded in isolated-server.json. AI is deterministic template mode; credentials are cleared and external socket destinations blocked. Terrain/OSM adapters explicitly return unknown/assumed evidence. API responses are not intercepted in this connected journey; external browser assets are blocked. Commercial usage/rate-limit accounting is disabled only in this disposable harness, not application policy.

## Connected checks

- PASS: real JWT login through website
- PASS: create disposable project through website
- PASS: save synthetic location, boundary and alignment through actual API; reload workspace
- PASS: real non-billable generation job completes and persists design/BOQ/model
- PASS: actual site-analysis API persists computed metrics and explicit unknown terrain
- PASS: protected PDF CSV JSON and GLB bytes, MIME, filenames and CORS metadata
- PASS: missing invalid expired JWT and foreign project are rejected
- PASS: website downloads authenticated real report, BOQ and model; PDF preview uses Blob
- PASS: gizmo pointer and keyboard targets are nonoverlapping at three desktop widths
- PASS: expired session download follows existing login redirect policy
- PASS:component selection→Inspect→0.1m East edit→Apply→Undo→Redo→Save→Reload. Revision1→2; restore original position in revision3; original revision immutable.

Classification:

- Website login, neutral-project creation, typed-project API creation, saved boundary/alignment and reload:ISOLATED FULL-STACK VERIFIED. The name-only website creates an intentionally unclassified project; typed fixture creation uses the existing API, not a policy-changing PUT. These are separate disposable projects, explicitly recorded.
- Geospatial site analysis:ISOLATED FULL-STACK VERIFIED with actual area48188.1m² and unknown elevation; no terrain accuracy claim. Location/drawing input was submitted by API; pointer-driven map drawing/measurement NOT VERIFIED.
- Generation:ISOLATED FULL-STACK VERIFIED for one actual nonbillable balanced job→persisted completed scenario/model and6 BOQ rows. The job finished before the first status sample, so only completed was observed; intermediate preview/queue rendering and refresh-midjob timing are NOT VERIFIED by this journey. Existing polling/cancel/timeout tests cover separate mocked/unit cases. No second generation was submitted for a retry.
- Model editing, selection, inspector, undo/redo, save/reopen and history:ISOLATED FULL-STACK VERIFIED. See editor-results.json and screenshots/editor-saved-reload.png.
- BOQ/report/PDF/CSV/JSON and protected generated GLB artifact:ISOLATED FULL-STACK VERIFIED for deterministic outputs and ownership. CSV rows match the saved estimate; PDF parses/renders; GLB parses. Template output does not establish structural solver correctness.
- Formal approval-controlled GLB export:NOT VERIFIED for success; rejection ISOLATED FULL-STACK VERIFIED (409). No engineer approval was granted.
- Structural solver invocation, member force/stress diagrams and approval-controlled structural engineering workflow:NOT VERIFIED in this connected run. Existing frontend and scoped backend regressions pass; they are not substituted for a real engineering acceptance fixture.
- Production live workflow:NOT VERIFIED. No production credentials/resources used.

## Harness failures and corrections

Retained attempt logs identify an ambiguous New Project locator, invalid test assumption that neutral project type could be PUT, a formal GLB approval refusal initially treated as an unexpected failure, a missing numeric-input Tab commit, a startup-readiness race, and an incomplete disposable schema missing Stage1 lineage. These were harness/setup issues; no auth/approval/editor-input behavior was weakened. A new fixture database with the full registered schema/immutability guards enabled successful saves. A separate accessibility runner initially had a missing loop brace, corrected before its successful run. Do not count failed attempts or reruns as extra passing tests.

Frontend:441 passed across99 files (logs/unit-complete.log). TypeScript and ESLint passed (logs/types-complete.log, logs/lint-complete.log). Production build passed (logs/build-final.log). Browser/API journey:10 passed,0 failed (logs/fullstack-schema-ready.log); editor persistence journey:1 passed (logs/editor-schema-ready.log). These are runner checks, not11 separate Playwright test files. Axe:16 states,0 detected violations; zoom4 states; no automated failures. Backend:48passed,1skipped (logs/backend-complete.log), superseding the earlier36passed/1skipped scoped run. No rerun counts are added.

No original user project/database was changed. Disposable typed project2 and neutral project1 belong to seeded test account1001 in the explicitly isolated SQLite server. Geometry edits were a0.1m East test offset, restored in a new revision. No production credentials, paid AI/terrain, solver mathematics, design formulas, BOQ arithmetic, geometry generation algorithms or authorization checks were changed. No approvals were granted, push/deploy performed, or user database reset/migrated. Test schemas were created only in newly named fixture databases.


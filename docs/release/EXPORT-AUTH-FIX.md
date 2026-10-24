# Authenticated exports and previews

22 October2026, Asia/Calcutta. P1 transport defect corrected and verified against a real isolated JWT backend.

## Implementation

- frontend/lib/api.ts:fetchBinary reuses getAuthToken, fetchRead, ApiError parsing and the existing401 session policy. Only configured API-origin /api/ and /files/ resources receive credentials; redirects are rejected. No bearer in query parameters, logs, DOM links or analytics. HTTP401/403/404/500 remain distinct ApiError statuses; network errors are surfaced once without automatic replay or unauthenticated fallback.
- frontend/lib/download.ts:concurrent exports share a pending promise; response.blob preserves bytes; Content-Disposition ordinary and UTF-8 filenames are decoded and basename/control/device-name sanitized. Safe fallback filenames retain format. A temporary anchor is removed immediately; its Blob URL is revoked after1second. No Blob is stored in application state after download. Completion means browser handoff, not confirmation of the user's disk write.
- frontend/components/ui/download-button.tsx:local synchronous lock, disabled/busy feedback, error toast and explicit Retry action.
- ExportCard, report, cost, BOQ, ProfessionalModelEditor and both assistant export entrypoints use the shared transport. Modern assistant retains failed pending download actions for retry. Drawing-source DXF and foundation HTML download implementations were consolidated. Existing locally synthesized timeline/map/evidence exports remain local; JSON evidence fetched via api.get already carries bearer headers. Public landing/model assets remain public and receive no bearer.
- ProtectedPdfPreview fetches with bearer and abort signal, verifies PDF MIME/signature, displays a Blob URL and revokes it on close/unmount/path replacement. Error/retry is explicit. A late unmounted result cannot allocate an object URL.
- useProtectedFile resolves protected Cesium model/excavation assets to Blob URLs with abort/revoke and failure feedback; no unauthenticated retry. Rendering geometry/camera code is unchanged.
- backend/app/main.py exposes Content-Disposition and X-Request-ID through existing CORS middleware. Origins, bearer dependencies and ownership rules are unchanged.

All project exports inspected use get_current_user/get_owned_project. Local /files/ requires JWT and project ownership in JWT mode. Report model downloads now target the owned model export endpoint; the backend's structural-layout approval gate remains authoritative.

## Integrity and authorization evidence

Actual isolated login and browser download passed. PDF:5 pages parsed with pypdf; project name/disclaimer present; all pages rendered and visually inspected. CSV:6 rows match saved JSON quantity_estimate item codes, quantities, rates and amounts exactly. Generated GLB:21936bytes,GLTF2 header/length/JSON validated,37 meshes. SHA256/MIME/server filenames are in fullstack-results.json. PDF filename report_project_2.pdf; CSV boq_project_2.csv. The generated GLB artifact is **not** an approved formal export.

Missing/invalid/expired bearer→401; foreign project→404; unscoped protected file→403. Expired-session browser download clears the token and follows the existing /login?next policy. Unit tests cover500/network failure, explicit retry, concurrent callers,5MiB cleanup, UTF-8/path/device filenames, MIME and byte preservation, preview rejection/cleanup and protected model late-result cleanup. No test token value was written to evidence.

Formal /exports/model.glb on the generated structural revision→409, as required without engineer approval. UI announces the refusal and offers retry; no approval was added and no alternate file path is presented as a formal approved export. The test separately validates owned generated-file GLB bytes. A successful approval-controlled formal GLB export remains NOT VERIFIED.

Frontend:441 passed across99 files (logs/unit-complete.log). TypeScript and ESLint passed (logs/types-complete.log, logs/lint-complete.log). Production build passed (logs/build-final.log). Browser/API journey:10 passed,0 failed (logs/fullstack-schema-ready.log); editor persistence journey:1 passed (logs/editor-schema-ready.log). These are runner checks, not11 separate Playwright test files. Axe:16 states,0 detected violations; zoom4 states; no automated failures. Backend:48passed,1skipped (logs/backend-complete.log), superseding the earlier36passed/1skipped scoped run. No rerun counts are added.

No original user project/database was changed. Disposable typed project2 and neutral project1 belong to seeded test account1001 in the explicitly isolated SQLite server. Geometry edits were a0.1m East test offset, restored in a new revision. No production credentials, paid AI/terrain, solver mathematics, design formulas, BOQ arithmetic, geometry generation algorithms or authorization checks were changed. No approvals were granted, push/deploy performed, or user database reset/migrated. Test schemas were created only in newly named fixture databases.

Evidence:fullstack-results.json,download-integrity.json,logs/fullstack-schema-ready.log,logs/download-integrity.log,screenshots/authenticated-report.png,screenshots/exported-pdf-page1.png,screenshots/pdf-content-pages.png.

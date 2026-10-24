# Final production release decision

22 October2026, Asia/Calcutta. **NO-GO for unrestricted production launch.** The authenticated export transport defect and desktop gizmo target defect are corrected; connected preliminary workflows and repeated stability measurements now have substantially stronger evidence. Full approved engineering/export acceptance remains incomplete.

## Resolved

- P1 authenticated binary transport:headers,HTTP/session handling,filename/MIME/bytes,duplicate guard,loading/retry,Blob lifecycle,PDF/model previews and CORS filename visibility. Actual JWT browser/backend verification passed.
- P2 workspace hydration CLS:9-sample before/after matrix improved from0.180–0.271 to0.00076–0.00270. See protocol caveats.
- P2 camera gizmo target size/overlap:fixed grid,exact orientation events,keyboard/pointer/focus tests and zero focused axe violations.
- Full-stack evidence expanded to persisted geometry,template job,site analysis,BOQ/report,exports and real editor save/reload/undo/history.

## Outstanding release requirements

- **P0:none newly observed in sampled checks.**
- **P1 acceptance gap:**successful engineer-approved formal GLB export and structural solver/member-diagram workflow NOT VERIFIED. The backend correctly refuses an unapproved revision with409. User restrictions prohibit enabling approvals; no bypass, fake approval or generated artifact relabeling was used. Obtain an appropriately authorized nonproduction engineering fixture and validate this protected path before production GO.
- **P1 acceptance gap:**complete pointer-driven map location/drawing/measurement→generation→structural-analysis journey on representative terrain/hardware is NOT VERIFIED. Saved API geometry and editor persistence are verified separately.
- Production PostGIS/Redis/object storage,real provider/runtime credentials and long-running job restart/reconnection acceptance remain unverified here. The isolated SQLite/in-memory runtime is deliberately not production infrastructure.
- P2/P3 limitations:real assistive technology acceptance,long-session GPU/heap retention,field LCP/INP,very-large-file streaming,PDF display of unknown elevation as None–None rather than polished unknown copy. No numerical value was invented or coerced to zero.

The supported preliminary planning/editing/PDF/CSV subset has ISOLATED FULL-STACK VERIFIED evidence. This narrower result does not authorize a production deployment or imply solver correctness.

Frontend:441 passed across99 files (logs/unit-complete.log). TypeScript and ESLint passed (logs/types-complete.log, logs/lint-complete.log). Production build passed (logs/build-final.log). Browser/API journey:10 passed,0 failed (logs/fullstack-schema-ready.log); editor persistence journey:1 passed (logs/editor-schema-ready.log). These are runner checks, not11 separate Playwright test files. Axe:16 states,0 detected violations; zoom4 states; no automated failures. Backend:48passed,1skipped (logs/backend-complete.log), superseding the earlier36passed/1skipped scoped run. No rerun counts are added.

## Exact application/test paths changed this run

- backend/app/main.py (CORS response metadata only).
- frontend/lib/api.ts;frontend/lib/download.ts;frontend/lib/download.test.ts.
- frontend/components/ui/download-button.tsx.
- frontend/components/project-results/ExportCard.tsx,ExportCard.test.tsx,ProtectedPdfPreview.tsx,ProtectedPdfPreview.test.tsx.
- frontend/hooks/useProtectedFile.ts,useProtectedFile.test.tsx.
- frontend/app/projects/[id]/report/page.tsx,cost/page.tsx,estimate/page.tsx.
- frontend/components/ai/ModernAssistantPanel.tsx;frontend/components/workspace/AssistantPanel.tsx.
- frontend/components/model-editor/ProfessionalModelEditor.tsx,EngineeringStudyPanel.tsx,FoundationSystemPanel.tsx (export entrypoints only).
- frontend/components/map/CesiumView.tsx (protected resource resolution only);CameraGizmo.tsx,CameraGizmo.test.tsx.
- frontend/components/layout/DashboardShell.tsx (stable hydration header).

Harnesses:backend/scripts/release_test_server.py,release_regressions.py;frontend/scripts/release-fullstack.cjs,release-editor.cjs,release-editor-inspect.cjs,release-cls.cjs,release-accessibility.cjs,write-release-reports.cjs. Runtime artifacts/screenshots/logs are under docs/release. Disposable databases,storage and browser profiles are ignored. Local build targets the isolated JWT API; deployment builds must use the intended approved environment. Source .env/secrets unchanged. Existing extensive user changes were not reset or attributed to this run.

No original user project/database was changed. Disposable typed project2 and neutral project1 belong to seeded test account1001 in the explicitly isolated SQLite server. Geometry edits were a0.1m East test offset, restored in a new revision. No production credentials, paid AI/terrain, solver mathematics, design formulas, BOQ arithmetic, geometry generation algorithms or authorization checks were changed. No approvals were granted, push/deploy performed, or user database reset/migrated. Test schemas were created only in newly named fixture databases.

Reports:[EXPORT-AUTH-FIX.md](EXPORT-AUTH-FIX.md),[ENGINEERING-E2E-RESULTS.md](ENGINEERING-E2E-RESULTS.md),[WORKSPACE-PERFORMANCE.md](WORKSPACE-PERFORMANCE.md),[ACCESSIBILITY-REVIEW.md](ACCESSIBILITY-REVIEW.md).


## Test runtime cleanup

The disposable JWT backend and isolated frontend were shut down after evidence collection. Their fixture data is retained locally and ignored by Git. No original development server was intentionally stopped. Rebuild with the intended environment before starting a normal local or deployment runtime; the last test build points to the now-stopped isolated API.

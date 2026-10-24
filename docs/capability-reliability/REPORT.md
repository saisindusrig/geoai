# Milestone 2 — Capability and result reliability

Completed locally. No numerical methods, authorization endpoints, original engineering records or geometry were changed.

## Behavior
- Before: frontend component counts could decide method availability; current-result checks relied on revision/status; planar visualization could use a different available record than the selected result.
- After: the read-only backend capabilities endpoint delegates applicability to existing frame/slab/spatial/shell/foundation validators and freshness to existing history gates. It returns Supported, Missing inputs, Unsupported or Stale with reasons. Missing inputs can be completed; unsupported methods cannot start a calculation.
- Current results must match project, saved revision, registered method type, result ID, verified status, document hash and existing source/latest-review authorization freshness. The chosen load case must exist in that exact result. An unavailable explicit selection clears the visualization rather than substituting another result.
- Multiple current records can be explicitly selected. Historical/stale/failed records remain labeled evidence, with full records available through Advanced mode. Reopening restores result identity without a solver run.
- SELECT → INPUTS → ANALYZE → RESULTS and existing visualizations remain. Exact proposal review and explicit authorization remain mandatory. Numerical verification is not engineering approval.

## Changed implementation and tests
- backend/app/api/routes/analysis_capabilities.py — read-only capability/result identity adapter using existing services.
- backend/app/main.py — register the endpoint.
- backend/tests/test_analysis_capabilities.py — validator reuse, ownership/revision gates, no execution on capability reads, stale reviews, failed child cases, distinct saved result/case identities and unsupported fixtures.
- frontend/lib/analysis-workflow.ts and analysis-workflow.test.ts — backend capability contract and strict saved-result identity matching.
- frontend/components/model-editor/GuidedAnalysisWorkflow.tsx and GuidedAnalysisWorkflow.test.tsx — readiness integration, saved-result selection/reopening, history and authorization readiness.
- frontend/components/model-editor/GuidedAnalysisResults.tsx and GuidedAnalysisResults.test.tsx — exact-record visualization and missing-load-case clearing.
- docs/capability-reliability/ — scoped logs and reused read-only preservation scripts/manifests; no database backups.

## Verification
- 94 backend regressions passed across capability, physical frame, slab transfer, spatial frame, coupled floor and foundation API tests (backend-regression.log).
- The final expanded multiple-result assertion passed in all 8 focused capability tests (backend-targeted.log).
- 12 frontend tests passed across 3 focused files (frontend-targeted.log).
- Scoped ESLint and TypeScript checks passed (lint.log, typescript.log).
- No full-suite or browser matrix was rerun for this focused milestone. Backend test databases are isolated in memory; no demonstration projects were created.
- One existing Starlette/httpx deprecation warning remains; no dependency changes were made.

## Preservation
- Original database: 10,266 rows and all schemas exactly unchanged against the pre-milestone fingerprints (milestone-preservation.json).
- Existing isolated database: all 10,500 prior rows unchanged, no appended rows (review-preservation.json).
- Existing spatial solver evidence: 635 files unchanged; coupled solver evidence: 21 files verified against existing artifact manifests (review-preservation.json, coupled-evidence-preservation.json).
- No restoration, cleanup, Git operations, installation, paid inference or deployment.

## Unsupported and unresolved scope
Existing engineering restrictions remain: arbitrary shell meshes, unvalidated diaphragm/connection behavior and unsupported foundation checks are not enabled. Capability reads do not certify physical connections or safety. Historical evidence remains accessible but is excluded from current-result visualization. No new numerical or engineering approval capability is claimed.

Stopped after Milestone 2.

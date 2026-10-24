# Gate 2J — project inventory

24 October 2026, Asia/Calcutta. Read-only inventory of `D:\layout project`: **270,220 regular files, 15,767,940,549 logical bytes (14.69 GiB), 394 grouped paths**. See `inventory.json` for measured totals/bytes, exact groups and **14** build roots. **749 reparse entries were recorded but not followed**, `.git` was excluded, and this gate's new evidence was excluded from the existing-footprint scan. Therefore these are scoped regular-file totals, not allocated disk usage or an exhaustive sum of external link targets. There were no filesystem scan errors.

## Application, assets and dependencies

Required source includes `backend/app` (523 files including bytecode), `backend/tests` (163), `frontend/app` (68), `frontend/components` (263), `frontend/lib` (162), hooks/stores, both script trees and Alembic. Full exact groups are retained in the inventory, not inferred removable from file age. **1,576 source/public-asset fingerprints** are in `source-asset-fingerprints-before.json`.

`frontend/public` has **437 regular files, 106,142,477 bytes**: branding, fonts, static marketing/3D resources and Cesium dependencies stay retained. Generated catalogue and Cesium copies have real build/runtime consumers. `frontend/scripts/sync-asset-catalogue.js` reads `backend/app/core/asset-types.json`; `copy-cesium.js` supplies public runtime workers/widgets/assets. Preserve this cross-directory source relationship in any new build artifact.

`frontend/node_modules` contains **64,117 regular files, 1,124,672,520 bytes**; `backend/.venv` **23,513 files, 1,289,671,056 bytes**; `backend/.venv-civicspan` and `backend/.cad-proof-deps` are separately retained. `dependency-accounting.json` inventories 47 frontend declarations with installed metadata, 29 satisfied backend requirements, all 11 migration files/head 011, and ten historical build/test fixture imports. No package was installed, imported as a solver, removed or declared unnecessary.

The normal launchers depend on `.local-tooling/node-24.22.1-validation/runtime` and `scripts/verify-local-node.cjs`. The entire `.local-tooling/node-24.22.1-validation` group spans **80,595 regular files, 5,433,847,631 bytes**, mixing the required runtime, installed dependencies, retained tests and generated builds. Do not delete the group. A sanitized process snapshot records the running normal backend; it was not probed, stopped or restarted.

## Databases, synthetic data and original records

`databases.json` lists **161 existing database/sidecar files**: 73 under backend, 21 docs, 49 `.cache`, 18 isolated tooling. All remain protected, including synthetic fixtures. `database-file-fingerprints-before.json` records their byte hashes without publishing document contents or credentials.

The current `backend/dev.db` has **140 users and 282 projects**, with 125 saved model revisions, 1,089 audit rows and 1,951 usage events. `backend/assistant-history.db` contains three task records. The exact per-table counts and non-PII record IDs/classifications are in `data-record-inventory.json`. Name/domain markers identify **125 possible development/test users and 17 possible demo/synthetic projects**; markers are not definitive provenance and never justify deletion. The remaining 15 users/265 projects have unverified provenance and are retained too. No email addresses/password hashes/document bodies were published by the inventory.

`backend/storage` contains 73,140 regular files; `.cad-proof-output`, `live-results`, `.cache` and docs retain CAD and engineering results/solver evidence. Baseline manifests independently verify 55,296 original storage and 2,090 proof entries, alongside database schemas and solver artifact hashes. Directory regular-file totals differ in scope from historical manifest entries and skipped reparse paths; no original entry is dropped merely to reconcile counts.

## Authentication, history and security evidence

Retain `frontend/lib/firebase-auth.ts`, `frontend/app/login/LoginPageInner.tsx`, `components/auth/SessionBoundary.tsx`, API token/session transport and tests. Backend `app/core/firebase_auth.py`, `core/security.py`, `services/identity_links.py`, ownership dependencies and immutable evidence rules remain unchanged. Gate 2H/2I inert configuration/reference artifacts remain in docs; Firebase is not enabled, ADC remains blocked and no Analytics or account/link operation was added.

Preserve audit/usage rows, assistant history, original identity/authorization records, `.env`/credential files, security matrices, backup manifests and all archived evidence. Secret files were classified by names/metadata rather than reading their contents. `archives.json` inventories archive candidates; `.cleanup-backups` alone contains three regular files totaling 486,370,426 bytes. No Git traversal/operation, restore or cleanup was performed.

## Duplicate/obsolete-code findings

Static source analysis found **three identical-file groups and seven identical function-body groups**, exact paths/lines in `duplicate-review.json`. **Zero application files are confirmed unused.** Identical generated catalogue data, route error boundaries and package initializers have intentional roles. Similar engineering/ownership route helpers are not interchangeable solely because their function bodies match; current router registrations demonstrate active consumers. Dynamic/framework imports and engineering semantics still require targeted review before any refactor.

See [CLEANUP-REPORT.md](CLEANUP-REPORT.md) for the three cleanup categories, exact 125-file candidate scope and recovery procedures, and [FRESH-ENVIRONMENT.md](FRESH-ENVIRONMENT.md) for the new empty environment and its unresolved admission/isolation requirements.

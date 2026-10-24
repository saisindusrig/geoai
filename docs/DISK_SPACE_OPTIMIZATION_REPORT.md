# GeoAI entire-project disk optimization

15 October 2026. Local development only. The below-10-GB target was achieved without deleting an environment, installed application dependency, recovery backup, database, original model, drawing or engineering verification record.

## Measured result

- Before: **16,456,896,975 bytes = 16.456896975 GB** (15.327 GiB).
- After: **9,481,066,916 bytes = 9.481066916 GB** (8.830 GiB).
- Net reclaimed: **6,975,830,059 bytes = 6.975830059 GB**, approximately 42.4%.
- Target: below 10,000,000,000 bytes, achieved with the normal website restarted and its workspace route compiled.

These are complete recursive logical-file-size measurements, including hidden folders, `.git`, `.cache`, installed dependencies, historical experiments and `.cleanup-backups`. Directory junctions are recorded but their shared targets are counted once. Three junctions in historical CAD workspace copies point at the main dependencies/public directory; counting those again inflates directory totals. GB means decimal bytes/1,000,000,000; GiB means bytes/1,073,741,824. Filesystem allocation/compression can differ from logical sizes. The after figure is the recorded inventory snapshot, before small final report/summary writes.

A traversal that follows all three historical junctions would add roughly 2.188 GB of shared dependencies/public assets a second time (about 18.645 GB before and 11.670 GB after). Those duplicated path totals are not additional disk consumption. Junctions were retained for the historical source copies; no dependency was deleted to lower a misleading traversal total.

The primary removals total 7,012,098,846 bytes. The net before/after figure is smaller because the running application regenerated runtime output and this task retained inventories, per-file removal manifests and validation evidence. Temporary validation output is not counted as additional headline savings.

## What was removed, and why

1. **Three inactive Next.js build trees: 6,855 files / 5,963,648,721 bytes.**
   - `backend/.cad-proof-output/workspace-frontend/.next`
   - `backend/.cad-proof-output/workspace-production/.next`
   - `frontend/.next`
   These contained Next manifests, compiled server/static output and compiler caches. Process command lines proved the actual website used `frontend/.next-phase1`; neither archived workspace build was active. Their `package.json`/build markers were checked, every target resolved inside the workspace, and unexpected database/drawing/solver file extensions and junctions were rejected before deletion. The corresponding source copies, dependency junctions and public assets remain available for regeneration.
2. **Stopped frontend compiler cache: 3,370 files / 833,306,341 bytes.** Only `frontend/.next-phase1/dev/cache` was cleared, after the verified frontend process tree was stopped. The active server/static output was retained. `run-website.bat` then restarted the website successfully. This cache grew slightly between the initial measurement and the stop.
3. **Byte-proven duplicate wheel-download fragments: 686 files / 215,143,784 bytes.** Every partial/resume/tail fragment was matched to an exact byte range of a retained complete wheel. Both complete wheel ZIPs passed integrity checks. Installed OCP/VTK modules and their DLLs were retained. The native CAD kernel and worker smoke test subsequently passed.

Each removed file has its path, size, SHA-256 and reason in:

- `disk-optimization/removed-inactive.jsonl`
- `disk-optimization/removed-stopped-frontend-cache.jsonl`
- `disk-optimization/removed-wheel-fragments.jsonl`

Task-created acceptance builds, temporary database/fixture copies and scratch files were cleared after their servers stopped. Their separate manifest is `removed-validation-artifacts.jsonl`; the attested browser test source was archived in `replay-sources/`. No existing recovery backup was used as writable test storage or removed to produce the savings.

## Preventing cache regrowth

The only application configuration change is `experimental.turbopackFileSystemCacheForDev: false` in `frontend/next.config.ts`, supported by the installed Next 16.2.9 documentation and type definitions. This disables the large persistent development compiler cache; hot reload still runs with in-memory state. The remaining cache metadata was 102 bytes at the check.

The tradeoff is extra compilation work after a cold restart. The frontend reported ready in 469 ms; the first normal workspace HTTP request after restart took 20.485 seconds, including compilation. This task does not claim a startup speed improvement. Runtime output, new user data, future builds and new backups can still grow; below 10 GB is the verified current footprint, not a permanent storage quota.

## Full storage classification

`disk-optimization/classification.json` records before/after counts and bytes for major groups. `inventory-before.json` and `inventory-after.json` contain deeper group totals, including Git metadata. The categories are:

- **A — Essential source/configuration/tests:** backend application, routes/services/models, migrations, frontend application/components/hooks/state, scripts, required test fixtures and dependency/build configuration. Retained.
- **B — Essential data and immutable evidence:** `backend/storage`, original SQLite files, CAD sources, model revisions, OpenSees evidence/manifests, original verification reports and recovery snapshots. Retained. Historical proof files were checked against the existing preservation manifest.
- **C — Required active runtime dependencies:** `backend/.venv`, `frontend/node_modules`, the installed native CAD kernel in `.cad-proof-deps`, active Cesium/public assets and the OpenSees executable. Retained. Only duplicate installer fragments were removed.
- **D — Regenerable builds/caches:** the specific verified inactive `.next` trees and stopped persistent compiler cache described above. Removed. The active `.next-phase1` server/static output remains.
- **E — Historical test artifacts:** historical test databases, logs, native proof outputs, source snapshots and experiment folders. Retained where they contain numerical/provenance evidence or uncertain dependencies. Mixed folders were separated by classification and targeted removal, not wholesale deletion or evidence relocation.
- **F — Potential duplicate environment:** `.venv-civicspan` is not used by the running website, but is not an equivalent copy of `.venv`. It has 51 packages, 35 version differences and an additional `opentelemetry-api` package absent from the active environment. Retained; no claim that it is safe to delete.
- **G — Protected or uncertain:** existing recovery backups, mixed `.cache` snapshots and Git metadata. Retained. No Git command, GitHub operation or metadata modification was performed.

## CAD proof directory findings

The apparent multi-gigabyte proof folder mixed generated frontend builds, dependency junctions, retained historical application sources, CAD models, proof databases, manifests and verification reports. The two real generated build trees accounted for about 3.982 GB. Dependency junctions also made naive recursive totals look larger than unique storage use.

After removing only those build trees, `.cad-proof-output` occupies **204,743,630 bytes** of real files. Its original B-reps, meshes/models, solver/worker evidence, reports, manifests, experiment data, source copies and license/vendor files remain. No evidence folder was moved into a backup to manufacture a smaller project measurement.

## Largest remaining directories

- `.git`: **1,639,815,208 bytes / 1.640 GB**. Measured only; untouched.
- `.cleanup-backups`: **1,481,117,225 bytes / 1.481 GB**. Protected recovery/verification copies; untouched.
- `.cache`: **1,441,213,843 bytes / 1.441 GB**. Includes historical database snapshots, fixture manifests and the active OpenSees distribution; untouched.
- `backend/.venv`: **1,253,868,028 bytes / 1.254 GB**. Active Python runtime.
- `frontend/node_modules`: **1,041,376,049 bytes / 1.041 GB**. Required installed frontend dependencies.
- `backend/storage`: **688,665,262 bytes / 0.689 GB**. User/project/engineering storage.
- `backend/.cad-proof-deps`: **633,261,721 bytes / 0.633 GB**. Installed native CAD runtime plus retained complete offline wheels.
- `frontend/.next-phase1`: **319,971,460 bytes / 0.320 GB**. Active generated frontend output.
- `backend/.venv-civicspan`: **210,085,660 bytes / 0.210 GB**. Separate versioned environment, retained.
- `backend/.cad-proof-output`: **204,743,630 bytes / 0.205 GB**. Retained proof/source/history files.

The before/after byte totals for `.git`, `.cleanup-backups` and `.cache` are exactly identical.

## Verification

- **Normal startup:** `run-website.bat` restarted the frontend on 3001; its proxy health endpoint returned HTTP 200 and the existing backend on 8001 returned `ok`. The normal workspace HTML returned HTTP 200 after cold compilation. No second normal-port server was started.
- **Strict isolation:** mutating browser checks used ports **13001/18001**, a new task-only database copied from the existing verified SQLite snapshot, and small separate CAD/model fixture storage. The backend asserted its database path, and every browser test first checked a unique `/__disk_validation` session marker. Original-port health was never accepted as proof of test isolation. No additional full-project backup was created.
- **Browser:** Assistant resizing, component preview/apply/undo/redo/save/reload, and offline Assistant persistence passed on the first run. The saved CAD/footing results view initially exceeded its 30-second loading expectation; it passed a bounded repeat in 33.6 seconds. The isolated saved-results API independently returned HTTP 200 with 12 records. Screenshots and all initial/recheck logs are retained. No UI, authorization or numerical code was changed to force the check to pass.
- **CAD import/editing, revisions, Assistant and OpenSees API regressions:** **126 passed**, one existing FastAPI test-client deprecation warning. Tests used a second isolated seeded database and separate output storage.
- **Native CAD runtime:** `verify_cad_worker.py` passed from the backend working directory with the retained pinned OCP/VTK packages on the subprocess import path. This includes native solid metrics and before/after component compilation. Earlier attempts exposed sandbox temp restrictions and an incorrect child-process import path; their logs are retained. No CAD worker code or limits were changed.
- **TypeScript:** passed.
- **Preservation:** all **264 existing database files** match baseline row fingerprints and SQLite schema definitions. All **55,296 original storage files** and **2,090 original CAD proof paths** match their existing archived SHA-256 values. Zero changed or missing originals. See `preservation-before.json` and `preservation-after.json`.
- The temporary acceptance servers were stopped, and their generated build/database/fixture copies were removed. The original website remains available at **http://localhost:3001/projects/793/workspace** with backend health at **http://localhost:8001/api/health**.

## Local development versus production

Local development needs the source, installed frontend packages, active Python runtime, configured credentials, original database/storage, and any native CAD/OpenSees runtimes used by the chosen workflow. The normal launcher uses `.next-phase1` and regenerates runtime output. A persistent Turbopack disk cache, old experiment builds and partial package downloads are not required.

Production needs a newly generated frontend build and appropriate production dependencies, the backend runtime/migrations/configuration, persistent application data, and the CAD/OpenSees runtimes for enabled features. Removing an old build does not remove the ability to build again. A fresh production build is required before using `next start`; no production build or deployment was performed for this disk-only task. Development caches, Git metadata, historical experiment builds and test databases are not deployment runtime inputs; their retention here is a separate local history/recovery decision.

## Further opportunities and permission boundary

The requested target was reached without high-risk deletions. Further large reductions would involve protected or version-specific material, and were not performed:

1. Review the **1.481 GB `.cleanup-backups`** retention policy, particularly the 663 MB acceptance-storage copy versus the verified source/database archive. These may contain recovery or unique test evidence; no deletion/relocation is authorized by this report.
2. Review historical database snapshots within the **1.441 GB `.cache`**, while retaining the active OpenSees runtime, manifests and required fixture references. A snapshot is not disposable merely because it is old or duplicated in name.
3. Validate all version-specific CivicSpan workflows before considering the **210 MB alternate environment**. Package differences prevent treating it as a redundant copy.
4. The two complete CAD wheel archives occupy about **129 MB** and are not loaded during normal execution. They were retained to preserve exact-version offline reinstall/reproduction capability. Removing them trades away that local recovery convenience and should be an explicit decision.
5. Git metadata is **1.640 GB**, but optimizing or removing repository history is outside the current no-Git authorization. It was not modified or proposed as an automatic saving.

No credentials were printed, rotated, moved or copied into the report. No paid inference, installations, deployment, Git or GitHub operations were used. No engineering formula, CAD geometry, authorization rule or UI design was changed.

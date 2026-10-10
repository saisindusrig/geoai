# GeoAI Phase 3B2A — final Linux CI acceptance

Recorded 10 October 2026 (Asia/Calcutta). This report supersedes the earlier “Linux not run” statements in CAD_WORKER_DEPLOYMENT_3B2A.md.

## Published change and execution

Dedicated branch: `codex/cad-linux-acceptance`. Draft PR: https://github.com/saisindusrig/geoai/pull/1.
Tested implementation commit: `9046420d7d167be5ae442b4d785c3028bd81fdf2`.
Successful isolated Linux run: https://github.com/saisindusrig/geoai/actions/runs/37974990667.
Every job stage completed successfully. No image was pushed or deployed. The original main checkout, index and unrelated pending changes were preserved using an alternate Git index.

Evidence artifact: https://github.com/saisindusrig/geoai/actions/runs/37974990667/artifacts/11638740640
Downloaded ZIP SHA256: `0abbf6cae61e068829f2bbfce017946e5733e5739ac9bda4a7c21f39455edfce`, independently verified locally.
Ignored local evidence: backend/.cad-proof-output/linux-accepted.zip, linux-accepted/* and linux-run-37974990667.log.
These are synthetic test metrics and inventories; private CAD artifacts and credentials were not published.

## Container, kernel and geometry results

Both runtime and verification container builds passed. Base: Python 3.13.6 slim Debian Bookworm, Linux x86_64, glibc 2.36 (libc6 2.36-9+deb12u10).
Runtime image ID: `sha256:724a6d89e6685f2768c344424cf1af148c45f3b7dca7650d297064d071cc1312`. This is a locally built image identity, not a registry manifest digest.
OCP/proxy 8.0.1.1.0 and VTK 9.6.2 loaded and executed successfully, without DISPLAY, network or cloud credentials.
All 533 inventoried worker-closure native libraries passed ldd verification; zero unresolved dependencies.

Six valid single solids passed analytic dimensions, volume and topology checks: concrete beam, steel I beam, circular column, slab opening, plate hole and tapered member.
Analytic face counts were respectively 6, 14, 3, 10, 7 and 6.
B-rep round trip, valid topology, watertight/winding-consistent meshes, hashes, boolean openings and invalid geometry rejection passed.
SUPPORT_FRAME compiled all ten components. Regeneration from 5 m to 6 m changed primary-0 and primary-1; the other eight components remained unchanged.

Windows/Linux comparison passed for the recorded Windows fixture: bounds absolute tolerance 1e-6 m; volume relative tolerance 1e-7 or absolute 1e-9 m³; validity, component IDs, solid counts and analytic topology checked.
Meshed-volume tests retain 0.5% tolerance with existing 0.002 m / 0.2 rad meshing settings.
No cross-platform bitwise B-rep/mesh reproducibility claim is made.

## Resource controls and artifact security

Actual Linux tests passed for timeout, CPU exhaustion (1 s CPU budget), memory exhaustion (64 MiB test limit), cancellation before/after launch, crash/nonzero-exit handling, descendant termination after timeout/cancel/leader exit, two-slot concurrency rejection/recovery, scratch cleanup and invalid input/output rejection.
Crash tests inject a worker-process exit; they do not establish exhaustive recovery from every possible OCCT segmentation fault.
Atomic publication failures, interrupted local fsync/write cleanup, private paths, ownership and retrieval authorization, content-hash corruption detection, fail-closed configured S3 behavior and authorized local orphan dry-run passed.
No failed worker result was published. S3 failure behavior used mocks; no real cloud bucket was exercised. Remote bucket privacy/durability and remote orphan reconciliation remain unverified.

The worker remains a fixed data-only subprocess outside ordinary FastAPI handlers.
Defaults remain 30 s wall time, 20 s CPU, 1024 MiB address-space limit and process-local concurrency 2.
Linux bootstrap sets RLIMIT_AS/RLIMIT_CPU and disables cores; teardown kills the process group.
CI containers enforced 2 CPUs, 3 GiB memory and PID limit 96, dropped all capabilities and enabled no-new-privileges. Headless runtime additionally used a read-only filesystem and 128 MiB /tmp.
No limit was weakened. A future durable queue still needs fleet admission, leases and recovery reconciliation. The image CMD/health check is a bounded fixture smoke command, not an implemented queue service.

Installation/build/health commands and recovery behavior remain documented in CAD_WORKER_DEPLOYMENT_3B2A.md. The build context is now repository root with an explicit Dockerfile-specific allowlist.
Verified platforms: Windows x64 development and Linux x86_64 Debian/glibc. ARM64, musl and GPU deployment were not tested.

## Exact test results

Successful Linux run: **170 passed, 0 failed, 0 skipped, 2 warnings in 21.86 s** (JUnit 21.858 s).
Includes CAD proof/integration/deployment, BIM foundation, AI3D V1/Generic3DExecutor boundaries, Building, Building Patch and ModelRevision suites.
Warnings: existing Starlette/httpx deprecation and pytest cache write permission on /worker. They did not prevent execution or change test selection.
Workflow actions also reported their Node runtime migration warning.

Windows supplied/previously verified baseline: focused 170 passed; full backend **854 passed, 0 failed, 2 skipped**. The full backend suite was not re-run on Linux; only the isolated 170-test workflow is accepted here.

## Failure evidence and bounded fixes

Run 1: https://github.com/saisindusrig/geoai/actions/runs/37973732664 — builds and headless native smoke passed; focused tests 168 passed, 2 failed.
Failures: missing scripts.run_cad_proof exporter and missing /docs/contracts/bim-project.schema.json in the verification image.
Fix commit c8e3c0ab65bb31d551e1e376f4b8ffde5e04b97f copied those existing assets, used repository-root build context and an explicit context allowlist. Both affected tests also passed locally.
Original log retained as backend/.cad-proof-output/linux-run-37973732664.log; GitHub artifact 11636684027 retains first failure evidence.

Run 2: https://github.com/saisindusrig/geoai/actions/runs/37974301902 — builds, smoke, cross-platform comparison and 170 tests passed; standalone linkage inventory failed.
Three bundled-library checks could not resolve wheel-local hashed sibling dependencies: Shapely GEOS and pyproj nghttp2/SQLite/TIFF/curl.
Fix commit 9046420d7d167be5ae442b4d785c3028bd81fdf2 explicitly supplies only the native file's own .libs directory to standalone ldd, clears inherited LD_LIBRARY_PATH, and records searchPaths. All missing dependencies and nonzero ldd exits still fail acceptance.
Run 3 re-ran the complete workflow and passed all 533 checks. Original second-run log and ZIP remain under backend/.cad-proof-output; GitHub artifact 11637343866 preserves the failed inventory.
No tests were bypassed, skips added or resource limits relaxed.

## Dependency and licensing review

CAD_LINUX_RUNTIME_INVENTORY_3B2A.json records the actual Linux inventory: 22 packages, no missing active Python dependencies, 533 native-file hashes, available notice/license hashes and complete linkage output.
The evidence also includes pip freeze, dpkg versions and image inspection.
Direct pins remain OCP/proxy 8.0.1.1.0, VTK 9.6.2, Pydantic 2.13.4, Shapely 2.1.2 and pyproj 3.7.2.
Resolved relevant transitives include matplotlib 3.11.2, NumPy 2.5.3, pydantic-core 2.46.4, Pillow 12.3.0, contourpy 1.4.0, fonttools 4.66.1, kiwisolver 1.5.1 and certifi 2026.7.22; remaining versions are in the inventory.

**Redistribution acceptance remains false.** OCP and proxy metadata declare Apache-2.0; VTK declares BSD; OCCT carries LGPL-2.1 plus its exception. Metadata is not a complete bundled-component license review.
OCP/VTK and OCCT license/exception texts are included in the runtime. The proxy wheel has no discoverable package-specific notice; attribution/source provenance must be supplied.
FreeImage and codecs, VTK third-party components, GEOS, PROJ/curl/TIFF/SQLite, NumPy math libraries and Pillow/font packages need notice and source-provenance reconciliation against the exact installed binaries.
OCCT corresponding source, modifications/build instructions and applicable replacement/relinking obligations require review. The header exception does not waive library redistribution conditions.
Native wheel-file hashes are complete for the scanned closure. System-library binary hashes, a full system-package licensing/source manifest, base-image digest lock, fully pinned transitive wheel hashes and a reviewed redistribution/source bundle remain missing.
Upstream references and the deployment obligation plan are in backend/cad-notices/README.md and CAD_WORKER_DEPLOYMENT_3B2A.md. Passing CI establishes technical execution, not legal acceptance.

## Scope and remaining blockers

Published implementation: 39 existing CAD/BIM workflow, source, dependency, fixture, contract, notice and documentation paths. Final acceptance report and Linux inventory add two documentation paths.
Bounded acceptance fixes changed Dockerfile/context allowlist, workflow context, deployment build instructions and the inventory ldd environment; they included the existing proof exporter.
No API credentials, .env, databases, dependency caches or private artifacts were committed. No unrelated history was rewritten.

Native compatibility/resource acceptance blockers are closed for this Linux target.
Remaining release blockers: redistribution/source/notice review and package/image locking; durable queue/fleet admission/recovery; real configured test-cloud privacy/durability and remote orphan policy; approval/source/revision transaction wiring for a later experimental integration.
**Phase 3B2B experimental workspace integration can start as a separate, explicitly gated batch.** This is not permission for production CAD Build or redistribution.
Production CAD Build stays disabled. Qwen/ModelRouter, production Generic3DExecutor, Building generation, proposal/approval behavior, workspace layout, ModelRevision schema and safety gates were not changed.
No Nebius requests, new specialists or hierarchical BIM generation were made. Work stops at Phase 3B2A.


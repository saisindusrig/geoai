# GeoAI Phase 3B2A — production-compatible CAD worker verification

## 1. Linux container build

**Not executed, not accepted.** Local Docker, Podman and GitHub CLI are unavailable.
The isolated `.github/workflows/cad-worker-linux.yml` is prepared for manual dispatch
and relevant pull requests. It has read-only repository permissions, no secrets,
no cloud credentials, no image publication or deployment. It has not been pushed
or run from this workspace; there is no successful Linux run to cite.

The existing Dockerfile now has a minimal runtime and separate verification stage.
Base: `python:3.13.6-slim-bookworm` (Debian/glibc candidate). System packages:
libgl1, libxrender1, libxext6, libsm6, libgomp1. CI records actual libc and dpkg
versions; tag availability, native loading and linkage must pass rather than be
assumed. Lock image digest/system packages after acceptance. A Dockerfile-specific
ignore excludes credentials, databases, local native caches and generated files
from the build context. The image runs as non-root `cadworker`.

## 2. Native kernel loading

Windows native loading succeeds with Python 3.13.6, OCP/proxy 8.0.1.1.0 and VTK
9.6.2. Those pins remain unchanged. Pydantic 2.13.4, Shapely 2.1.2 and pyproj 3.7.2
also retain their original pins. Linux CI uses pip check, imports OCP and VTK,
records resolved Python/system packages, runs ldd on native libraries in the
worker's dependency closure (excluding unrelated API-only native packages)
and fails if any dependency is not found. Linux native loading is pending.

## 3. Geometry compilation

`scripts/verify_cad_worker.py` is a headless offline smoke test, without FastAPI,
database, AI or storage publication. It constructs the existing six precise
solids, validates topology/bounds/volume, loads VTK, compiles the 10-component frame
through the bounded worker and regenerates linked beams from 5 to 6 m. It verifies
the other eight results remain unchanged within one platform run. Existing native
tests verify B-rep validity, watertight/winding-consistent meshes, hash integrity,
invalid geometry rejection and source mapping. No new geometry primitive or asset
specialist was added.

## 4. Windows/Linux compatibility

The recorded Windows reference is `backend/tests/fixtures/cad-windows-3b2a.json`.
Linux CI compares component IDs, validity, one-solid counts, analytic face counts,
bounds with 1e-6 m absolute tolerance and volume with 1e-7 relative / 1e-9 m³
absolute tolerance. Native fixture tests allow 0.5% meshed-volume error at existing
0.002 m / 0.2 rad meshing tolerances. Mesh vertex counts and B-rep/mesh bytes are
not compared across OS. Content hashes verify local artifact integrity, not
cross-platform serializer reproducibility. Windows self-comparison passes;
Windows/Linux agreement awaits the Linux job.

## 5. Timeout, memory, CPU, process tree and concurrency

The worker remains a fixed data-only subprocess, separate from API handlers.
Linux limit setup moved from preexec_fn to a small trusted bootstrap that sets
RLIMIT_AS, RLIMIT_CPU and zero core limit, then execs the fixed server command.
This avoids unsafe threaded preexec execution. JSON cannot select that command.
Linux cleanup kills the process group even if the leader exited or crashed first.

Windows Job Objects enforce committed-memory and user CPU time limits, explicitly
terminate at the limit, and kill descendants. Teardown now waits for active job
processes to exit before scratch cleanup, fixing a cancellation/child-handle race.
CPU accounting is periodic; wall timeout remains the independent execution bound.
Scratch cleanup retries Windows delayed handle release for at most three seconds
and fails explicitly if cleanup still cannot complete; it never publishes results
in that case. Job teardown can add a further bounded three-second cleanup margin.
Defaults: 30 s wall, 20 s CPU and 1024 MiB per child. Accepted ranges: wall
0.05–120 s, CPU 1–60 s, memory 64–2048 MiB. Output budgets remain 32 MB, 250k
vertices/500k triangles, 250 components and 2 MB input.

A process-local bounded semaphore admits at most two jobs and rejects excess
admission with CONCURRENCY_LIMIT; slots release on success/failure. This is not a
distributed queue or a fleet-wide limit. Deploy one supervisor per container,
use cgroup CPU/memory/PID limits, and add durable admission/queue control before
production. Arbitrary untrusted executables remain unsupported; process groups
are resource isolation, not a hostile-code security sandbox.

Windows tests cover timeout, 64 MiB exhaustion, crashes, mid-flight cancellation,
CPU exhaustion, descendant termination after timeout/cancel/leader crash,
concurrency rejection/recovery and invalid input. Linux versions of those tests
are scheduled by the workflow, not claimed to pass locally.

## 6. Licensing and packaging

The checked-in `docs/CAD_WINDOWS_RUNTIME_INVENTORY_3B2A.json` captures installed
direct and relevant transitive Python package versions, declared dependency edges,
metadata licenses/project URLs, all discovered native library names/hashes and
available notice/license files. The inventory now recognizes versioned Linux
.so files and recursively follows active dependencies. It includes OCP, proxy,
VTK, Pydantic/core, Shapely, pyproj, annotated-types, typing extensions/inspection,
NumPy and certifi. Windows's intentionally minimal target lacks matplotlib;
this is recorded, not concealed. Linux pip installation resolves its full closure
and CI captures that inventory and pip freeze for review.

`backend/cad-notices` carries the installed OCP Apache license, VTK notice, and
OCCT LGPL-2.1/exception texts into the runtime image. Proxy release metadata now
confirms Apache-2.0, but package-specific attribution/source packaging is pending.
[Proxy release](https://pypi.org/project/cadquery-ocp-proxy/8.0.1.1.0/).
OCCT corresponding source/build provenance and applicable replacement/relinking
conditions must be addressed; the exception does not discard its LGPL conditions.
[OCCT license](https://github.com/Open-Cascade-SAS/OCCT/blob/V8_0_1/LICENSE_LGPL_21.txt).
VTK and its third-party components need their applicable notices retained.
[VTK notice](https://github.com/Kitware/VTK/blob/v9.6.2/Copyright.txt).
Bundled FreeImage/codecs, GEOS, PROJ and NumPy/native dependencies need exact-source
and notice reconciliation. [FreeImage licenses](https://freeimage.sourceforge.io/license.html).

**Redistribution review is unresolved.** License metadata and a passing build
alone do not demonstrate compliance. Exact bundled library source versions,
third-party notices, corresponding-source bundle and fully resolved Linux
transitive/image hashes are release blockers. No native binary is committed.

## 7. Artifact security/reliability

Existing ownership, manifest membership, SHA-256, private local paths and fail-closed
configured-S3 behavior remain intact. Files never receive public CAD URLs.
An interrupted local write/fsync now cleans up its staging file before exposing
the hash-named destination; tests inject disk failure and verify no incomplete
file remains. Publication still validates all outputs before catalog insertion.

`local_orphans` is an authorized, project-scoped, read-only inventory of hash-named
files absent from committed manifests. Missing/corrupt manifests abort rather
than falsely marking live artifacts orphaned. Run with a fresh committed DB
session while upload jobs are idle. Never delete from this scan automatically;
retention grace, active upload leases and crash recovery are prerequisites.
Remote scanning deliberately refuses operation until a tested S3 inventory exists.

Tests use temporary local paths and mocked storage only. The regression runner
disables default configured S3 clients and blocks live Nebius HTTP transports
while allowing fixture mocks. No dedicated cloud test resources were supplied;
remote S3/bucket-policy verification was not performed. Local tests do not certify
remote privacy or durability.

## 8. Installation, deployment and recovery

From an isolated Linux environment, install `backend/requirements-cad-worker.txt`.
Never add native execution to FastAPI requests. A future job runner invokes
`compile_batch` with data-only recipes, then returns fully checked candidates to
the existing approval/artifact transaction. Keep immutable revisions and commit
the artifact catalog only after complete validation.

Build and run from the repository root:

```sh
docker build --target runtime -f backend/Dockerfile.cad-worker -t geoai-cad-runtime .
docker build --target verification -f backend/Dockerfile.cad-worker -t geoai-cad-verify .
docker run --rm --network none --read-only --tmpfs /tmp:size=128m --cpus=2 --memory=3g --pids-limit=96 --cap-drop ALL --security-opt no-new-privileges geoai-cad-runtime
docker run --rm --network none --cpus=2 --memory=3g --pids-limit=96 --cap-drop ALL --security-opt no-new-privileges geoai-cad-verify
```

The runtime CMD/healthcheck compiles fixtures without DISPLAY or network; it is a
smoke/verification image, not a long-running queue service. CI saves health metrics,
JUnit, image identity, inventory, resolved packages and ldd evidence. Supported
verified platform: Windows x64 development. Linux x64 glibc is a pending candidate;
ARM64, musl and GPU deployment are not accepted in this batch.

On crash/cancel/timeout, terminate the task tree, clean scratch, release admission
and publish no candidate. Retry from immutable definitions; never reuse incomplete
artifacts. Local interrupted writes leave no exposed destination; storage/DB
rollback can leave valid unreferenced blobs, which require conservative orphan
review. Container death requires job lease/reconciliation in a future durable queue.

## 9. Regression evidence

Final results are recorded below. Earlier focused testing exposed the Windows
teardown race (2 failures); a subsequent full run still had 1 scratch-handle
failure, 853 passed and 2 skipped. Bounded cleanup retry addressed that remaining
race. Final CAD integration/resource/artifact checks passed **34 tests, 0 failed,
0 skipped, 1 existing warning** in 13.06 s. The requested combined focused suite
passed **170 tests, 0 failed, 0 skipped, 1 warning** in 33.41 s; the later cleanup
change was verified with the 34-test set and the final full suite. CPU termination
was separately verified. The earlier baseline/failing runs are not substituted
for a final passing suite. Linux results remain not-run.

Final full backend regression: **854 passed, 0 failed, 2 skipped, 3 warnings** in
280.12 s. It used the final cleanup fix, live-Nebius transport guard, disabled
default cloud clients and temporary regression storage. The skips require two
scenario fixtures for compare ownership and a dedicated PostgreSQL/PostGIS
database. Warnings are the existing Starlette/httpx deprecation and two Pydantic
schema composition warnings. Exact JUnit/log evidence is ignored under
`backend/.cad-proof-output/3b2a-accepted.*`; focused evidence is
`3b2a-focused-final.*`. Health self-comparison, Python entry-point parsing and
workflow YAML validation passed. All 702 original checkpoint files still match
their Git content hashes.

## 10. Files changed

Modified: backend/app/experimental/cad_worker.py, cad_artifacts.py;
backend/Dockerfile.cad-worker; backend/scripts/cad_worker_inventory.py.

Added: .github/workflows/cad-worker-linux.yml;
backend/app/experimental/cad_worker_bootstrap.py;
backend/tests/test_cad_worker_deployment.py;
backend/tests/fixtures/cad-windows-3b2a.json;
backend/scripts/verify_cad_worker.py, run_cad_regressions.py;
backend/Dockerfile.cad-worker.dockerignore;
backend/cad-notices/README.md and four license/notice texts;
docs/CAD_WINDOWS_RUNTIME_INVENTORY_3B2A.json;
docs/CAD_WORKER_DEPLOYMENT_3B2A.md.

## 11. Unresolved blockers

- Linux workflow has not run: no container, kernel, linkage, resource or cross-OS
  acceptance result exists yet. Publish the proposed code and inspect a real run.
- Native transitive/system/image hash lock and redistribution/source/notice review.
- Durable queue, fleet-wide concurrency, leases/recovery and remote orphan policy.
- Dedicated test S3 resources, private bucket-policy proof and remote durability.
- Approved BIM/CAD source binding and existing revision/lineage transaction wiring.

## 12. Readiness for Phase 3B2B

Prepared for review, **not cleared for production integration**. Run the isolated
Linux workflow and close kernel/resource/linkage failures first. Then the next
bounded batch can implement an explicitly gated workspace adapter, authorized
artifact retrieval, Cesium component selection/Inspect and save/reload/lineage
tests through the existing approved revision pipeline. Production CAD Build stays
disabled. No provider/router, AI3D V1, Generic3DExecutor, Building/Patch behavior,
workspace layout, ModelRevision schema or engineering gate was changed. Phase
3B2A stops here; no hierarchical generation or asset specialists were added.

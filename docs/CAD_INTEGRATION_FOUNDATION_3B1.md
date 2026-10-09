# GeoAI Phase 3B1 — CAD geometry integration foundation

## 1. Contract

`backend/app/experimental/cad_contract.py` defines strict, finite, bounded
`cad-geometry/1`, `cad-recipe/1` and `cad-artifacts/1` data contracts. Checked-in
schemas are in `docs/contracts/cad-geometry.schema.json` and
`docs/contracts/cad-artifacts.schema.json`. Definitions retain component/asset/
assembly identity, material, metre parameters, component and assembly placement,
dependency/connection membership, source provenance, and server revision binding.
Closed recipe vocabularies reject paths, code, unknown operations, bad sections,
out-of-face holes, non-finite values and dimensions outside 0.0001–500 m.
Duplicate IDs, dangling references, cycles, multiple writers and inconsistent
COPY values are rejected. Coordinates are bounded by the existing BIM contract.

`from_bim` validates BIM/1 and extracts supported section/parameter definitions.
The legacy primitive is excluded entirely: changing its BOX cannot change CAD
definitions or hashes. BIM/1 and AI3D/1 remain unchanged.

## 2. Authoritative source and disposable mesh

The immutable parametric definition is authoritative. A validated single-solid
B-rep is its compiled representation. A separately hashed mesh is disposable.
Compilation saves B-rep before tessellation, preserving that distinction. The
manifest carries source definition hashes, B-rep/mesh SHA-256 and lengths,
validity, bounds, dimensions and geometric volume. Units are metres; the frame is
`PROJECT_LOCAL_VISUAL_REFERENCE`, Z up, not a surveyed vertical datum. Component
then assembly transforms are baked into geometry; preview transforms are a
separate overlay. No terrain or engineering approval is inferred.

Engineering verification stays UNVERIFIED; engineering quantities and material
takeoffs stay UNAVAILABLE. Geometric volume is metadata, not a verified takeoff.
Compiler, recipe and mesh versions enter the source/cache fingerprint. Revision
identity/document hash and every definition/material/placement/relationship also
enter it. A different base revision or changed parameter invalidates the key.
This batch prepares cache identity; no persistent shared cache is enabled.

## 3. Worker implementation and isolation

`cad_worker.py` launches only the fixed `cad_worker_entry` module. It imports no
native library. The child accepts validated JSON (2 MB maximum), then checks all
three pinned native package versions before loading OCP and compiling recipes.
No authored filenames or executable Python are accepted. Server scratch paths
exist only in supervisor arguments. Credentials are excluded from the child's
environment; native thread counts are constrained.

Each job uses a new process and private temporary directory. Defaults: 30 s and
1024 MiB; caller limits are bounded to 0.05–120 s and 64–2048 MiB. Windows uses a
Job Object with process committed-memory limit and kill-on-close. Linux uses
RLIMIT_AS/core limits and a process group. Linux setup is implemented but untested.
Wall timeout, cancellation, crashes, bad manifests, byte/hash errors and mesh
index errors fail the whole candidate. Windows memory exhaustion was tested.
Batch budgets: 250 components, 250,000 vertices, 500,000 triangles, 32 MB artifacts.
The parent validates complete outputs before returning any publication candidate.

This is process/resource isolation, not an OS security sandbox. The Linux
`preexec_fn` launcher is intended for a standalone job runner, not a threaded API
server. Production needs queue/admission control and OS/container isolation.
No native job has been registered in a normal request handler.

## 4. Windows and Linux

Windows 11 / Python 3.13.6 native loading and compilation were verified using the
existing ignored `.cad-proof-deps` target, not the production environment. Pinned
native packages: OCP 8.0.1.1.0, proxy 8.0.1.1.0, VTK 9.6.2. Worker data dependencies
match installed Pydantic 2.13.4, Shapely 2.1.2 and pyproj 3.7.2.

Docker/Podman were not found. `wsl --list --quiet` returned Wsl/E_ACCESSDENIED.
Consequently Linux installation/loading, RLIMIT behavior and container acceptance
were **not verified**. `backend/Dockerfile.cad-worker` is a non-root glibc Debian
Bookworm candidate with headless native dependencies and a native-load smoke CMD.
Build on Linux, run the actual contract/worker tests, verify system libraries and
resource enforcement, then lock image/wheel/transitive dependency hashes. The
Dockerfile is not a deployment acceptance certificate.

## 5. Dependency and licensing inventory

`backend/scripts/cad_worker_inventory.py` inventories installed package versions,
declared dependencies, native DLL/PYD files and available license/notice files
with SHA-256. Current generated inventory is ignored at
`backend/.cad-proof-output/3b1-runtime-inventory.json`.

OCP includes its Apache-2.0 wrapper license in `cadquery_ocp/LICENSE`.
[OCP source/license](https://github.com/CadQuery/OCP).
OCCT uses LGPL-2.1 with its header exception; the exception does not discard the
library's licensing conditions. Package corresponding source, notices, license
texts and a compliant library replacement/relinking arrangement where required.
[OCCT license](https://github.com/Open-Cascade-SAS/OCCT/blob/V8_0_1/LICENSE_LGPL_21.txt),
[exception](https://github.com/Open-Cascade-SAS/OCCT/blob/V8_0_1/OCCT_LGPL_EXCEPTION.txt).
VTK has BSD-style redistribution conditions and third-party components.
[VTK notices](https://github.com/Kitware/VTK/blob/v9.6.2/Copyright.txt).

The wheel inventory includes bundled OCCT TK libraries and FreeImage. Complete
transitive licensing, proxy license provenance, OCCT corresponding source and
third-party notice packaging are still pending. Installed notice files alone do
not establish distribution acceptance. The minimal Windows evaluation used
`--no-deps`; VTK's declared matplotlib plotting dependency was not installed in
the isolated target. Container pip installation resolves that dependency normally;
this remains unverified here. No native binaries are added to Git.

## 6. Artifact ownership and storage

`cad_artifacts.py` reuses `get_owned_project`, immutable `ModelRevision` rows and
existing `GeneratedFile` catalog records. `owned_source` reads the owned revision
and hashes its stored document. Trusted design provenance comes from a separate
server lifecycle context; payload self-assertions are insufficient. Publication
checks that context, ownership, project/revision association and document hash.
The approval-to-BIM source binding is a future integration responsibility; this
experimental service is not an approval endpoint.

Storage reuses configured durable storage services without public download URLs.
Local artifacts live in a sibling of LOCAL_STORAGE_DIR, outside `/files`.
S3 artifacts use a private namespace in the configured bucket and never produce
presigned URLs. Configured S3 failure fails closed rather than silently changing
stores. Deployment must verify bucket policy blocks anonymous private-prefix
reads; remote S3 publication was not tested here.

All keys are server-derived project + SHA-256, never user paths. Retrieval checks
project ownership and catalog membership before reading a manifest or artifact.
Hashes are checked again on storage reads. Catalog references use an opaque
`cad-private:` URI; ModelRevision contains neither B-rep nor triangle arrays.

All outputs are validated before writes; the catalog row is inserted last and
flushed into the caller's existing transaction. Caller commits/rolls back with the
approval transaction. Storage/compile failure publishes no catalog entry. Staged,
unreferenced blobs can remain after partial storage failure or DB rollback; they
are not retrievable through this service. Committed-manifest-based orphan GC,
retention and remote transaction recovery are production follow-ups.

## 7. Parametric regeneration

The existing bounded COPY propagation changes primary-0 length 5 → 6 m and
primary-1 follows. Native worker recompilation produces 6 × 0.3 × 0.5 m bounds and
0.1608 m³ geometric volume for each primary I beam (previously 0.134 m³). Their
definition/artifact hashes change; the other eight component results stay equal.
Their parameters, placements and material are preserved. No support relocation
or slab resizing happens. Dependency failure remains atomic and produces no new
artifact catalog or ModelRevision.

## 8. Assembly consistency

`review_changes` reports changed component IDs, untouched members in affected
assemblies, explicit connections involving edited members and unavailable
clearance rules. The frame edit returns REVIEW_REQUIRED for unchanged columns,
secondary beams, slab and plate, plus unresolved clearances. Explicit SUPPORTED_BY
edges receive CONNECTION_REQUIRES_REVIEW. This is deliberately conservative:
it detects review obligations, not physical connectivity/clearance satisfaction.
There is no connection solver or structural adequacy claim.

## 9. Workspace compatibility

`cad_adapter.py` emits an isolated `cad-workspace-preview/1` document using the
existing `components` structure, categories, visibility/lock fields and transform
shape. Collision-safe UUID5 IDs derive from project/asset/component identity.
Semantic parameters, provenance, materials and immutable source references
support future Layers, picking and Inspect. Render/B-rep geometry stays behind
catalog/hash references. Re-adapting preserves transforms/visibility/locks for
the same CAD IDs and leaves unrelated components intact. JSON reload preserves
identity and references; hash/ID comparison can distinguish changed components.

Production editable-model validation still rejects this schema and geometry kind.
No actual Cesium/Layers/Inspect renderer or production lineage insertion has been
enabled. Existing component lineage table must retain server-generated object IDs
and source associations when the later approved CAD revision adapter is added.
Non-unit scaling needs an explicit parametric edit policy; preview overlay scale
is not a regenerated authoritative source. Existing generic/building/terrain/
placement/approval routing remains unchanged.

## 10. Verification

Full backend regression: **846 passed, 2 skipped, 3 warnings**, 256.46 s.
Final CAD integration tests: **26 passed, 1 warning**, 4.57 s. Final combined CAD,
BIM, generic/building and ModelRevision focused suite: **162 passed, 1 warning**,
25.94 s. Both JSON schemas were regenerated
and checked against current Pydantic schema output. All 702 files captured in the
pre-edit checkpoint still match their Git content hashes.

The first full run had 838 passed, 2 skipped and 5 failures: the test harness
rejected deterministic HTTPX MockTransport calls as though they were live Nebius
requests. The guard was corrected to reject actual network transports while
allowing mocks; the full rerun above passed. No production fix was needed. The
earlier Phase 3A environment-sensitive archived-pilot redaction failure also
passes in this run with normal environment values rather than blank credential
overrides. No unresolved test failures remain in the completed full run. Warnings
are the existing Starlette/httpx deprecation and two Pydantic composition schema
warnings. Test logs/JUnit are ignored at `.cad-proof-output/3b1-full-final.*`.
The two skips are the compare-ownership test requiring at least two scenarios,
and the PostgreSQL upgrade test requiring a dedicated PostgreSQL/PostGIS database.

Tests
exercise strict round trips, trust and ownership, invalid recipes, hashes,
Windows native solids/meshes, metre/frame metadata, 5 → 6 m dependencies,
connections/review flags, source cache invalidation, private storage fail-closed,
atomic publication failure, worker crash/timeout/cancellation/memory exhaustion,
stable IDs, source-preserving overlays and unrelated component preservation.
No Nebius network requests are authorized or needed.

## 11. Files added in this batch

- backend/app/experimental/cad_contract.py
- backend/app/experimental/cad_worker.py
- backend/app/experimental/cad_worker_entry.py
- backend/app/experimental/cad_artifacts.py
- backend/app/experimental/cad_adapter.py
- backend/tests/test_cad_integration.py
- backend/scripts/cad_worker_inventory.py
- backend/requirements-cad-worker.txt
- backend/Dockerfile.cad-worker
- docs/contracts/cad-geometry.schema.json
- docs/contracts/cad-artifacts.schema.json
- docs/CAD_INTEGRATION_FOUNDATION_3B1.md

No production files were edited in 3B1. Earlier user/phase changes remain intact.
Verified pre-edit recoverable checkpoint:
`refs/heads/codex/checkpoint-phase3b1-20261009-220302`, commit
`e886dd4e8f89caa767d472e2e6979f78698a7a35`. An alternate Git index captured tracked
and non-ignored untracked work; current main branch, real index and working status
were checked unchanged. Ignored credentials/native dependencies/output are not
part of that checkpoint.

## 12. Exact blockers to production integration

1. Linux/container build, native loading and timeout/memory/process-tree tests.
2. Complete pinned transitive dependencies, image digest and redistribution bundle.
3. Durable queued worker admission/concurrency control and isolated task runtime.
4. Private S3 bucket-policy verification, orphan GC and remote failure recovery.
5. Approved BIM/CAD source binding, stale-head lock and lifecycle transaction wiring.
6. Versioned editable document CAD kind, authorized artifact endpoint and Cesium
   mesh rendering/picking, Layers/Inspect and transform policy.
7. Persistent component lineage, save/reload, History and revision comparison tests.
8. Connection/clearance rules or explicit unresolved review handling at approval.
9. Verified engineering quantity rules; until then CAD quantity inclusion is false.

## 13. Phase 3B2 recommendation

First run Linux CI/packaging checks. Then add one explicitly gated approved-CAD
revision adapter to the existing proposal/ModelRevision transaction, authorized
mesh retrieval and Cesium component rendering. Exercise stale-head refusal,
atomic rollback, save/reload/lineage, transforms, revision comparison and unrelated
asset preservation end-to-end. Keep unresolved assembly issues visible and CAD
engineering quantities unavailable. Enable production Build only in a later
accepted batch. Phase 3B1 stops here; no BridgeSpecialist, reinforcement design,
workspace redesign, provider changes or production CAD switch is included.

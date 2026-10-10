# GeoAI Phase 3A — isolated CAD geometry proof

## Outcome

Open CASCADE via OCP successfully constructed and validated six solid examples
on Windows/Python 3.13. The same 10-component SUPPORT_FRAME was compiled under
BRIDGE and INDUSTRIAL_PLATFORM asset labels. A 5 m to 6 m beam-length edit rebuilt
the two explicitly linked primary beams and preserved the other eight outputs.
Production generation, routing, approval rules, persistence and workspace code
were not changed. No live AI requests were made.

Recommended next candidate: **OCCT via pinned OCP in a separate geometry worker**,
subject to Linux deployment, redistribution and production integration review.
This is a successful experimental proof, not production CAD kernel adoption.

## Kernel comparison

**Existing GeoAI engine.** Repository inspection shows a bounded box/cylinder
compiler, rectangular polygon extrusion, planar segmented sweep, segmented pipe,
straight planar offset and simple arrays. These remain suitable for fast conceptual
previews. They do not provide general B-rep topology, exact openings, analytic
curved surfaces, lofting or fillets. Their editable-document and lineage pathways
should remain the integration foundation.

**OCCT/OCP.** OCCT provides B-rep modeling, extrusion, sweep, loft, booleans,
intersections, fillets and chamfers. OCP supplies thin Python bindings. These
capabilities address the precise-source geometry requirement; support in the
kernel does not imply that all operations are implemented in GeoAI. Sources:
[OCCT modeling algorithms](https://dev.opencascade.org/doc/overview/html/occt_user_guides__modeling_algos.html),
[OCP project](https://github.com/CadQuery/OCP).

**CadQuery.** Higher-level Python authoring over OCCT, rather than a different
kernel. It could reduce wrapper code, but also adds an authoring API and dependency
surface. It was not installed: this batch uses server-owned bounded recipes and
direct OCP calls, never model-generated Python.
[CadQuery project](https://github.com/CadQuery/cadquery).

**pythonocc-core.** Another mature OCCT binding, with conda installation and
CAD data-exchange support. Its wrapper is LGPL-3.0, unlike OCP's Apache-2.0 wrapper.
It was evaluated from documentation, not installed.
[pythonocc-core installation and license](https://github.com/tpaviot/pythonocc-core).

**Manifold.** Apache-2.0 library for manifold triangle meshes and booleans.
Useful for mesh processing; its triangle-mesh representation does not meet this
proof's analytic B-rep source requirement. That is the reason for preferring OCCT
here, not a general reliability comparison.
[Manifold project](https://github.com/elalish/manifold).

**CGAL and Parasolid.** CGAL has robust mesh/intersection algorithms, but package
licensing varies; its polygon-mesh-processing package is GPL, with commercial
licensing alternatives. Parasolid is a commercially licensed solid/surface kernel
with an established CAD ecosystem. Neither was installed or benchmarked, and no
commercial licensing quote was requested.
[CGAL mesh processing](https://doc.cgal.org/latest/Polygon_mesh_processing/group__PkgPolygonMeshProcessingRef.html),
[Siemens Parasolid](https://www.siemens.com/en-us/products/plm-components/parasolid/).

## Installation, licensing and deployment

Verified actual wheel metadata: `cadquery-ocp==8.0.1.1.0` requires
`cadquery-ocp-proxy==8.0.1.1.0` and `vtk==9.6.2`. OCP's supported Python range is
3.11 through 3.14. The Windows cp313 wheel is 47,922,364 bytes; the required VTK
wheel is 81,307,827 bytes. OCP lists Linux glibc 2.28+ wheels for x86-64 and ARM64.
Thus a glibc-based Linux worker is a candidate; an Alpine/musl image cannot be
assumed compatible. Linux loading and container deployment were **not tested**.
[OCP release files](https://pypi.org/project/cadquery-ocp/),
[VTK release](https://pypi.org/project/vtk/9.6.2/).

Both native wheels were downloaded from official PyPI URLs, checked against their
published SHA-256, and installed with the proxy into `backend/.cad-proof-deps`.
Production `.venv` packages and `requirements.txt` were not modified. This minimal
headless proof used `--no-deps`; VTK's optional plotting path was not exercised.
A normal installation of `requirements-cad-proof.txt` resolves the full declared
dependency graph, including matplotlib. Minimal native-core loading is not proof
of every optional viewer/dependency path.

OCP's wrapper is Apache-2.0. OCCT is LGPL-2.1 with an additional header-use
exception; the exception does not remove library redistribution obligations.
Distribution planning must preserve notices/license texts and satisfy applicable
source, modification and relinking requirements. The wheel wrapper's Apache label
does not relicense bundled OCCT. The downloaded OCP metadata had no bundled
license-text directory, so production packaging needs an explicit notice/source
inventory. VTK has a BSD-style license with third-party notices to retain.
No binary redistributable or license-complete deployment image was produced.
[OCP license](https://github.com/CadQuery/OCP/blob/master/LICENSE),
[OCCT LGPL](https://github.com/Open-Cascade-SAS/OCCT/blob/master/LICENSE_LGPL_21.txt),
[OCCT 8.0.1 exception](https://github.com/Open-Cascade-SAS/OCCT/blob/V8_0_1/OCCT_LGPL_EXCEPTION.txt),
[VTK copyright](https://github.com/Kitware/VTK/blob/v9.6.2/Copyright.txt).

Native code, wheel size, library loading, ABI pinning and tolerance behavior are
material deployment costs. The experiment disables parallel meshing and boolean
execution and does not share shapes between threads. Recommended worker isolation,
memory/time quotas and versioned caches are architectural recommendations, not
tested claims of general OCCT thread safety or production performance.

## Implemented precise geometry

All lengths use metres. Coordinate dimensions are computational metres, not a
survey datum. Each example must contain one positive-volume solid accepted by
`BRepCheck_Analyzer`; dimension and analytic-volume expectations are tested.

- Concrete rectangular beam: 0.3 × 0.5 × 5 m; CAD volume 0.75 m³.
- Steel I-section beam: width 0.3 m, depth 0.5 m, web 0.02 m, flanges 0.03 m,
  length 5 m; CAD volume 0.134 m³. It is a concave profile prism, not a box.
- Circular column: radius 0.2 m, height 3 m; CAD volume 0.3769911184 m³.
- Slab: 5 × 3 × 0.2 m with a centered 0.8 × 0.6 m through-opening;
  CAD volume 2.904 m³, with point classification proving the opening is empty.
- Plate: 0.4 × 0.4 × 0.02 m with a centered radius 0.04 m through-hole;
  CAD volume 0.0030994690 m³, with point classification proving the hole is empty.
- Rectangular ruled loft: 0.4 × 0.4 m to 0.2 × 0.2 m over 5 m;
  CAD volume 0.4666666667 m³. Only this two-section rectangular taper is exposed.

The low-level module also extrudes valid simple planar polygons; a concave L-profile
is tested. Arbitrary custom profiles are not yet mapped through BIM V1 parameters.
Self-intersecting profiles, invalid I-sections, bad dimensions, excessive openings,
null shapes and non-solid topology are rejected. Fillets, chamfers, general curved
sweeps, intersection queries, general lofts and arbitrary booleans are kernel
capabilities only; they are not implemented in this bounded GeoAI adapter.

## Geometry, tolerance and render output

The test tolerance is 1e-7 m; dimensional comparisons allow 1e-6 m. This is a
numerical policy for small synthetic examples, not an achieved engineering accuracy
or survey precision claim. CAD uses floating-point tolerances, not exact arithmetic.

Meshing uses absolute linear deflection 0.002 m, angular deflection 0.2 rad and
serial execution. Triangle orientation respects reversed faces and node placement.
Tests weld the render mesh and verify watertightness, winding and mesh volume within
0.5% of analytic CAD volume. CAD volume and mesh-derived volume remain distinct.
No production quantity engine was changed.
[OCCT meshing](https://dev.opencascade.org/doc/overview/html/occt_user_guides__mesh.html).

Each solid has an exported B-rep file; a slab B-rep write/read round trip is tested.
B-rep has no implicit project metre/datum binding here: the adjacent JSON records
units explicitly. STEP is a documented OCCT interoperability path, not implemented
or round-trip-tested by this proof; a future export must explicitly convert units
and test labels and coordinate frames.
[OCCT STEP translator](https://dev.opencascade.org/doc/overview/html/occt_user_guides__step.html).

The frame produces **1,534 face-local vertices and 1,404 triangles**. The artifact
runner took about **0.40 s** for two frame builds, regeneration and six additional
solid constructions/meshes on this machine, excluding imports/downloads/file output.
This is one small warm measurement, not a latency SLA or stress benchmark.
Repeated solid/mesh outputs match within this pinned environment. Cross-version,
cross-platform bitwise determinism is unverified.

## BIM mapping and trusted source boundary

Flow: BIM Component parameters + CrossSection + GeometryDefinition reference
→ bounded `cad-proof/1` recipe → OCCT solid → validated metrics and derived mesh.

`bim-project/1` remains unchanged. Its geometry primitive language cannot express
holes, I-section prisms or lofts. Therefore the **isolated candidate** carries an
explicit CADMapping sidecar. Its `legacyPrimitivePolicy: NOT_EXECUTED` marks the
mandatory V1 BOX as a derived local envelope only. The envelope is recalculated
from the solid, including after regeneration; it is never passed to the generic
executor as a substitute for the precise shape. Phase 3B needs a reviewed versioned
geometry contract before production persistence, rather than silently reinterpreting
V1 geometry. The candidate's BIM definition **plus CAD mapping** are authoritative;
glTF and triangles are disposable display caches.

Outputs retain component/asset/assembly IDs, metre parameters, cross-section
references, material references, component and assembly frames, dependency IDs and
design/source provenance. Component and assembly transforms compose separately.
A horizontal beam maps profile width to y, depth to z and length to x. glTF applies
the explicit right-handed ENU-to-y-up rotation `(x,y,z) → (x,z,-y)`.

`TrustedSource` is caller-owned context outside the authored payload. A mismatch
in design ID, design version or source revision is rejected. This is not production
ownership/approval verification: no project ownership fields or database writes are
accepted, and the operator-only proof uses synthetic trusted context. A future API
must derive this context from the existing owned revision/proposal path, never AI.

## SUPPORT_FRAME, regeneration and reuse

One shared assembly has four circular columns, two primary I-beams, two rectangular
secondary beams, one slab with an opening and one holed connection plate. No
asset-specific generator or specialist was created. The bridge-support/platform
concept and industrial elevated-platform concept differ only in BIM asset label;
the same recipes produce identical geometry and IDs. This is a conceptual frame,
not a complete detailed bridge or engineered connection layout.

The primary-0 length changes from 5 to 6 m. Existing foundation COPY propagation
identifies primary-1 as dependent. Both solids, local envelopes, metrics, hashes
and meshes regenerate; their volumes become 0.1608 m³. The other eight outputs
remain equal and IDs remain stable. A detached candidate epoch increments; source
design provenance remains attached to its original design. No ModelRevision is
created. Validation runs before publication of the new candidate. An injected
failure after the first rebuilt solid proves failure atomicity.

Supports and slab remain at their original positions and dimensions. The result
has a visible overhang and remains structurally unverified. No load-based sizing,
support relocation, engineering certification or reinforcement inference occurs.
Optional diagonal bracing, stairs and engineered connection details are unsupported.

## Cesium and review compatibility

The offline review page uses the existing installed Three.js renderer copied only
into the ignored artifact directory. It displays real kernel tessellation, separate
component materials, orbit/zoom, per-component selection and inspection, and before/
after candidates. Browser review verified beam inspection at 6 × 0.3 × 0.5 m,
0.1608 m³, stable ID and dependency/provenance fields; canvas ray picking was
exercised. A screenshot is saved beside the artifacts.

`check_cad_cesium.mjs` verifies that the installed Cesium API accepts all ten
triangle geometries, computes finite normals, retains per-component GeometryInstance
IDs and maps a synthetic local ENU origin to its ECEF anchor. This is a headless API
proof. Cesium GPU rendering, production mesh picking and large-scene FPS were not
tested. The small mesh budget supports a feasibility conclusion, not an FPS claim.

Current `editable_model.SUPPORTED_KINDS` and the existing CesiumView branch only
support their established primitive paths, so production conversion to an editable
mesh would currently be rejected. No workspace UI or schema was changed. A future
adapter must attach semantic IDs/inspection/materials and source definition hashes
to mesh instances while preserving parametric source, approvals and lineage.
Transform/save/reload of CAD meshes needs explicit integration tests.

## Tests and compatibility

Final focused run from `backend`, with proof dependencies on PYTHONPATH and empty
process-local S3 credentials/bucket and Nebius key:

```
.venv/Scripts/python.exe -m pytest tests/test_cad_proof.py tests/test_bim_foundation.py tests/test_ai3d_v1.py tests/test_building_specialist_v1.py tests/test_building_patch_v1.py tests/test_model_revisions.py -q --basetemp=.test-cad-proof-focused-final
136 passed, 1 warning in 18.86s
```

Includes 23 CAD tests covering profiles, six solids, analytic dimensions/volumes,
empty boolean holes, invalid topology, watertight tessellation, winding, deterministic
meshes, transforms, unit/source rejection, cross-asset reuse, dependency regeneration,
identity preservation, early and mid-build atomic failures, B-rep round trip and
glTF semantic nodes/axis metadata. Building, Patch, generic executor, approvals,
lineage and revision regression tests remain passing.

Full backend run before native kernel installation:

```
.venv/Scripts/python.exe -m pytest -q --basetemp=.test-cad-proof-full
796 passed, 3 skipped, 1 failed, 3 warnings in 278.23s
```

The one failure was the saved pilot configuration/redaction comparison in
`test_full_pilot_rescore_audit_preserves_sources`: temporary S3 overrides changed
the redaction environment. Its exact isolated rerun with the normal environment
passed (1 passed in 0.29s); it explicitly forbids provider requests. This is not an
all-green single full-suite claim. One skip was the optional CAD module absent at
that time; the other skips were pre-existing. The final native/affected suite was
then run successfully; the entire suite was not repeated after the final additions.

Frontend `tsc --noEmit --incremental false` and `npm run lint` both passed.
Headless Cesium geometry compatibility passed for ten components. Production
browser workspace selection/save/reload and Linux container tests were not run.
Initial Windows sandbox temp/socket issues were resolved with workspace basetemp
and approved offline execution. The remaining warnings are existing FastAPI/httpx
deprecation and Pydantic schema warnings.

## Files in this batch

- `.gitignore`: exclude isolated dependency/output directories.
- `backend/requirements-cad-proof.txt`: optional pinned OCP dependency.
- `backend/app/experimental/__init__.py`: explicit experimental package.
- `backend/app/experimental/cad_geometry.py`: native solids, validation, meshing.
- `backend/app/experimental/bim_cad.py`: recipes, trusted context, candidate mapping/regeneration.
- `backend/app/experimental/cad_fixtures.py`: shared SUPPORT_FRAME fixture.
- `backend/app/experimental/cad_review.html`: local proof reviewer template.
- `backend/scripts/run_cad_proof.py`: JSON, B-rep, glTF and reviewer artifacts.
- `backend/scripts/check_cad_cesium.mjs`: headless Cesium input checks.
- `backend/tests/test_cad_proof.py`: native proof tests.
- `docs/CAD_KERNEL_PROOF_3A.md`: this report.

Generated, ignored files live under `backend/.cad-proof-output`: `results.json`,
`summary.json`, six `.brep` files, 5 m/6 m `.gltf` files, `review.html`, local vendor
modules/license, `cesium-summary.json`, and `support-frame-preview.png`.
Downloads, wheels and resumable-download helpers remain only in `.cad-proof-deps`.
Existing uncommitted work and the earlier BIM foundation were preserved.

## Reproduce and Phase 3B recommendation

Standard optional install: use a separate environment or a workspace target, then
install `requirements-cad-proof.txt` normally. The local proof used this PYTHONPATH:

```
$env:PYTHONPATH='D:\layout project\backend\.cad-proof-deps;D:\layout project\backend'
.\.venv\Scripts\python.exe scripts/run_cad_proof.py
node scripts/check_cad_cesium.mjs
.\.venv\Scripts\python.exe -m http.server 8768 --bind 127.0.0.1 --directory .cad-proof-output
```

Phase 3B should first review and version the geometry recipe contract, build a
pinned glibc Linux worker with a complete license/source inventory, test native
timeouts/memory/concurrency and cross-platform tolerance behavior, and define
parametric-source/B-rep/render-cache ownership. Then integrate a feature-gated
mesh adapter into existing proposals, approved atomic ModelRevision persistence
and object lineage, with stable picking/materials/transforms/save/reload tests.
Add supported component bindings and dependency rules incrementally. Keep fast
conceptual primitives available. Stop here before AI hierarchical authoring,
detailed bridge reinforcement, production generation changes or model routing changes.

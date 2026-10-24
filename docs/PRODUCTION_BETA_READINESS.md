# GeoAI production beta readiness

Review date: 22 October 2026 (Asia/Kolkata). Local development only.

## Release recommendation

**INTERNAL PREVIEW ONLY. Not approved for a limited production beta.**

The normal workspace can complete a fresh, explicitly synthetic project journey
using existing geometry generation, reviewed inputs, native OpenSees, visual
results, evidence explanation and report export. This establishes software
integration within a bounded method. It does not establish building safety,
engineering approval, real-site soil suitability or complete code compliance.

Critical dependency advisories, unverified production operations and deliberately
restricted engineering workflows remain launch blockers. No deployment,
installation, credential change, Git operation or paid inference was performed.

## Local website and data boundary

- Normal application: http://localhost:3001 . Acceptance application:
  http://localhost:3011 . Both serve the same production build and ordinary routes.
- Final fresh acceptance project: http://localhost:3001/projects/820/workspace .
  Final separate foundation review: http://localhost:3001/projects/821/workspace .
- Validation API: http://127.0.0.1:8011 . All three listeners bind to loopback.
- **These review servers use an isolated database**, not `backend/dev.db`.
  `.cache/production-beta/website/validation.db` began as a read-only SQLite
  backup so existing reference workflows could be tested without changing them.
  Newly created acceptance projects exist only in that copy.
- New uploaded drawing bytes, generated files and solver artifacts go to the
  validation storage directories. Existing drawing references were copied for
  source-integrity checks. No demonstration data is migrated into the normal DB.
- `run-website.bat` remains the ordinary offline launcher for the original local
  database on API 8001. Do not use it concurrently on occupied port 3001.
- The isolated setup is reproducible with
  `backend/scripts/serve_beta_validation.py`, `frontend/playwright.beta.config.ts`
  and `frontend/e2e/production-beta.spec.ts`. It requires installed dependencies
  and the already installed OpenSees executable; it installs nothing.

## Demonstrated complete journey

The real Chromium acceptance test creates a project through the dashboard,
supplies explicitly synthetic site coordinates through the ordinary project API,
refreshes its site profile, selects the explicit offline template action, reviews
and approves its persisted proposal, and generates nine conceptual components.
No source database rows are seeded into this fresh project.

It selects the generated deck in Layers, applies a geometry edit, exercises
undo/redo, saves a new revision and reloads it. It selects an actual generated
beam and two columns, previews their physical-to-analytical mapping, declares
sections, synthetic material/load sources, fixed bases and both rigid offsets,
then saves those inputs. Solver execution remains disabled until exact proposal
consent; a forged proposal hash returns HTTP 409.

The existing native OpenSees 3.8.0 produces numerically verified evidence. The
test explores displacement, axial force, shear, bending moment and reactions,
captures 1280px/1600px layouts, requests a bounded offline explanation, downloads
the saved frame evidence report, imports a DXF reference, and checks that an
unsaved load change hides results and disables current-report export. Reload
restores the unchanged saved result. This is a real native calculation using
synthetic verification inputs, not real structural design approval.

Separate browser acceptance creates a foundation study from its existing
synthetic reference, previews the calculation, requires exact consent, downloads
its report and asks the offline Copilot about saved evidence. Reference project
804 remains a deliberately fixed-scope prerequisite, not a general site workflow.

Artifacts and exact project/result identities are in
`production-beta/journey.json` and `production-beta/foundation-acceptance.json`.
Screenshots: `production-beta/results-1600.png`, `results-1280.png`,
`drawing-reference.png`, `stale-draft.png`, `foundation-1600.png` and
`foundation-1280.png`. The final short browser video is
`production-beta/walkthrough.webm`.
Playback was verified: 28.32 seconds, 1280×720, project 820/result 643. The
read-only recording also checks saved support/member inspection. Metadata is
in `production-beta/walkthrough-metadata.json`.

## Integrated feature matrix

- **Projects — normal flow verified.** Name-only creation opens the ordinary
  workspace. Ownership tests cover project, scenario and job isolation.
- **CAD/DXF — reference import integrated.** Any owned saved model can now import
  and review bounded local text DXF. Source classification, units, entity IDs,
  hashes and missing engineering inputs remain explicit. Real DXF linework does
  not automatically become a structural model. Reviewed synthetic CAD-to-box
  conversion retains its separate source-review and exact-authorization gates.
  IFC/DWG/PDF structural extraction remains unavailable. Experimental native CAD
  capability is gated and was not installed or enabled.
- **3D editor, Layers and Inspector — verified.** Existing selection, component
  edits, preview/apply, undo/redo, saved revisions and renderer are retained.
  Display materials do not supply engineering properties.
- **Planar OpenSees — normal flow verified.** Three selected solid rectangular
  members, an explicitly supported planar graph, reviewed short rigid offsets,
  fixed bases and supported declared loads can be analyzed after exact consent.
  The rest of the structure is excluded from that calculation.
- **Multi-storey spatial results — implemented, bounded research workflow.** The
  source implements six-DOF shared-node elastic 3D frames and one/two-storey
  synthetic reviews, with independent stiffness checks and visual force modes.
  Backend regression coverage ran. Its prior isolated demonstration database
  was not imported into the normal database; a new full multi-storey browser
  qualification was not part of this acceptance run.
- **Slab/floor load paths — load-only where supported.** Explicit one-way uniform
  load allocation is distinct from slab stiffness, shell stress or diaphragm
  action. Synthetic coupled-floor research is separately gated. Unsupported
  real-project coupling, connection capacities and automatic whole-building
  load transfer remain unavailable.
- **Soil/foundations — existing synthetic workflow verified.** Explicit source
  binding, service actions, prescribed Winkler stiffness, restricted bearing
  references and foundation detailing remain separated. No site investigation
  or real geotechnical acceptance was performed. Nonzero unsupported reaction
  moments/shear are rejected rather than silently discarded.
- **RC design — bounded calculations only.** Nominal section mechanics and the
  existing restricted foundation provision subsets are present. Current source
  names limited ACI 318-14 example and IS 456:2000 amendment-1/2 scan subsets;
  this review does not authenticate jurisdictional adoption or the latest code.
  Unsupported editions, complete detailing and missing checks remain disabled.
- **Engineering Copilot — deterministic saved-evidence explanation.** No model
  is called. It uses saved identities, source/input status, limitations and
  current revision context. The new explicit offline template action reuses the
  existing proposal workflow; it cannot approve or silently apply geometry.
- **Reports — structural evidence export connected.** A saved frame report now
  includes exact project/revision/input/result identities, algorithm version,
  solver/artifact provenance, limitations and disabled approval/code status.
  The server rejects stale or unverified current reports with HTTP 409 and
  enforces ownership. Existing foundation HTML and planning PDF/JSON/CSV exports
  remain distinct; the planning PDF is not represented as a structural certificate.
- **Saving/history — verified for new geometry.** New revisions preserve the
  previous documents. Stale draft evidence is hidden; backend tests also cover
  persisted input/revision changes, invalid source bytes and stale authorizations.

## Safe integration and reliability fixes

1. Added an explicit isolated solver-artifact root for planar, spatial and
   coupled-floor services. Drawing storage now honors configured local storage.
   Default evidence locations are retained for ordinary use.
2. Allowed DXF reference review beside any saved owned model, while leaving
   analytical conversion and strength-method applicability gates intact.
3. Connected exact saved frame evidence to downloadable reports, including
   server-side current-status and ownership checks.
4. Exposed the existing local template through an explicit Copilot action, with
   normal proposal review and approval. Ordinary explanations remain offline.
5. Stale site profiles are omitted from evidence-only chat context; current
   site/model identity checks remain enforced. Template creation still requires
   the existing current-site validation.
6. Production startup now fails before database initialization when JWT is off
   or the application secret is default/short. No credentials were changed.
7. Tightened file path containment using path ancestry, rejecting similarly
   prefixed sibling directories rather than trusting string prefixes.
8. Rejected malformed and nonfinite model sizes/transforms and malformed
   component objects without conversion exceptions or invalid saved geometry.
9. Removed build-time Google Fonts requests. Existing font variables and layout
   use installed system fonts, permitting an offline production build.
10. Added a numeric loopback API-port setting and separate beta build directory
    for isolation. Added reproducible browser/backend/preservation runners.
11. Historical evaluation replay attempts to validate its archived configuration
    rather than adopting today's catalogue. An already-redacted archive remains
    unusable and is rejected; its bytes were not repaired or replaced.

## Engineering reliability assessment

Actual supported input models are enforced by existing Pydantic/domain gates,
geometry/source hashes, input identities, exact proposal hashes, explicit
authorization and solver verification. Native subprocess timeouts/failures,
nonfinite data, units, mesh checks, load cases, superposition, source changes and
ownership have backend tests. Solver output includes executable/version/input
and artifact provenance. Model revisions and saved results remain separate.

Numerical verification means agreement within the implemented mathematical
model and reference checks. It does not validate the selected physical
idealization, material certificates, actual connectivity, site actions, soil,
construction detailing or engineering approval. The planar result report does
not automatically certify that a future source-code change is equivalent to a
previous algorithm version; release-specific method qualification remains needed.

## Security and operations audit

- **Authentication:** development intentionally supports a mock user and mock
  user header. This mode is confined to loopback here and is not suitable for
  shared/public beta access. JWT ownership/admin tests ran. Production now fails
  closed on missing JWT/default or short signing secret. Token revocation,
  password recovery, organizational access and a production identity lifecycle
  have not been qualified end to end.
- **Project isolation:** project/scenario/evidence/file routes use ownership
  checks. New report and drawing paths retain them. Tests include wrong-owner
  access. This is not a penetration test of every route/provider configuration.
- **Validation/uploads:** bounded DXF uploads require text DXF with explicit mm/m
  units, supported planar entities, finite coordinates and classification. Invalid,
  oversized and unsupported formats have tests. General model validation now
  rejects malformed/nonfinite data. WAF/upload malware scanning and all external
  parser resource-exhaustion cases are unverified.
- **Files/secrets:** local path containment was fixed. Production file access is
  ownership-gated; development local files are public to the development API.
  No credentials were displayed or modified. No secret-history scan or rotation
  was run because Git/credential changes were out of scope. S3 signing and
  production origin policies still need operational qualification.
- **Database/migrations:** tests use isolated SQLite and memory databases;
  migration tests run on isolated targets. Production requires PostgreSQL/PostGIS
  and a current Alembic schema. No original or production migrations were run.
  Production upgrade/rollback against a representative PostGIS backup is unverified.
- **Backup/restore:** the acceptance database was created using SQLite's online
  backup API from a read-only connection. This tests local copy availability,
  not a disaster-recovery procedure. Production encrypted backups, object-store
  consistency, retention, recovery time and a restore drill remain launch blockers.
- **Errors/logging:** existing structured request logs, request IDs and safe global
  client error handlers are present and regression-tested. No alert delivery,
  on-call response or external monitoring was enabled. The full status probe
  reports production dependencies unavailable/unverified; no readiness label was
  overridden.
- **Workers/resources:** local inline jobs are not durable across restarts.
  Redis/worker availability, queue recovery, concurrency quotas and peak solver
  memory need production tests. The existing process-wide solver lock is a local
  serialization mechanism, not a distributed execution guarantee.
- **Dependencies:** read-only `npm audit` returned **37 affected dependency
  entries: 5 critical, 22 high, 9 moderate, 1 low**. Counts include transitive and
  development tooling and do not imply 37 independently reachable exploits.
  Critical entries include Next, MapLibre, the TerraDraw wrapper, Vitest and
  Tinypool. See `production-beta/npm-audit.json` for exact installed ranges,
  advisories and proposed fixes. No audit fix/install was run. Python packages
  were exercised but a complete Python vulnerability scan was not installed/run.

## Performance measurements

`production-beta/performance.json` records ten sequential warm loopback requests
per endpoint, discarding a warm-up. These are local observations, not load-test
or internet latency guarantees:

- Health: median 12.83 ms, nearest-rank p95 27.82 ms.
- Project list: median 16.93 ms, p95 31.24 ms; 150,149 response bytes.
- Compact saved-frame history: median 110.71 ms, p95 226.30 ms;
  482,860 response bytes. History payload reduction/pagination remains useful.
- Saved engineering context: median 91.19 ms, p95 208.34 ms; 35,438 bytes.
- Production dashboard HTML: median 2.18 ms, p95 24.51 ms; 23,000 bytes.

At one idle/post-acceptance sample, the isolated Python interpreter had about
276 MiB working set and 1,246 MiB private committed memory; the two Node servers
had approximately 56 and 105 MiB working sets. See `api-memory.json` and
`owned-process-memory.json`. These are single samples; peak memory, long-session
leaks, multiple users and large-upload/large-model behavior remain unverified.
The initial socket-listing memory attempt returned invalid PID-0 data and is
not used as evidence.

## Validation results

Final results and remaining qualification gaps are recorded below and in the
machine-readable logs in `production-beta/`.

- Full frontend unit regression: 382 passed after limiting worker concurrency
  to two. An initial 5-second Cesium test timeout passed independently and on
  the bounded full rerun. Final unit results are in `frontend-tests.json`.
- Full backend regression: 1,819 passed, 1 failed, 2 skipped in 276.23 seconds.
  The failure is the historical Qwen/Kimi pilot replay: its archived configuration
  version is `[REDACTED]-eval/1`, not a valid `geoai-eval/1`. The archive is
  preserved and was not reconstructed by guessing. See `backend-release.log`.
- Focused validation after security/model changes: 124 passed, 1 skipped.
  Engineering/ownership/foundation/spatial/RC focused run: 79 passed, 1 skipped.
- **Final real Chromium acceptance: 3 passed in 51.5 seconds**, covering the
  complete fresh journey, foundation workflow and transport failure/retry.
  Exact results are in `browser-tests.json` and `journey-browser.log`.
- TypeScript, lint and offline webpack production build are checked; their
  logs are `typescript.log`, `lint.log` and `build.log`.
- The old website acceptance suite was attempted and failed on obsolete
  Assistant-tab selectors. The current interface uses a separate Copilot
  panel/settings and explicit component Apply/Save model. It was not misreported
  as passing, and all 92 legacy browser files were not fully requalified.
- Windows sandbox socket-pair initialization stalled async tests; an initial
  sandbox build also denied a worker mkdir. Authorized local validation ran
  with the required Windows process/socket access. No packages were installed.

## Data-preservation evidence

Before validation, `beta_data_preservation.py` hashed **73,476 existing files**,
totalling **3,542,902,926 bytes**: original databases, CAD/model files, storage,
published evidence and configuration files. The SHA-256 manifest is
`production-beta/data-before.json`. Dependencies/compiler output are excluded.

Verification found **73,472 byte-identical originals**. Four existing runtime
logs under `docs/coupled-floor/` received append-only output. Every original log
prefix still matches its original SHA-256; nothing was truncated or replaced.
`runtime-log-changes.json` records their before/after lengths and prefix checks.
All original database files, model/CAD files and calculation artifacts in the
manifest remain byte-identical. `data-after.json` intentionally reports the four
changed logs, so it is not a blanket all-files-unchanged assertion.
This includes 604 existing database files and 946 CAD/model files. See
`production-beta/data-preservation-summary.json` for category counts.

No original DB rows were edited, no original evidence was replaced, and no
test/demo records were copied back into the normal database. Changes to source
code are intentional integration fixes, separate from preserved engineering data.

## Ranked launch blockers

### Critical

1. Resolve the npm critical/high advisories through reviewed dependency updates,
   followed by full build, browser and engineering regressions. Installation and
   package changes require the user's approval and were not performed.
2. Establish and qualify production identity/configuration and durable production
   infrastructure: PostgreSQL/PostGIS, migrations, Redis/worker, private storage,
   backup/restore and monitoring. The local mock-auth/inline-job configuration
   cannot be exposed as a public beta.

### High

3. Qualify real engineering applicability with authenticated input/material/site
   evidence and jurisdiction-specific professional review. Synthetic verification
   cannot support safety or design approval claims.
4. Foundation and advanced CAD/spatial studies still contain intentionally narrow
   reference/metadata gates, including source project 804. A general arbitrary
   building-to-foundation engineering journey is not supported. Do not remove
   these gates merely to make the UI appear integrated.
5. Complete large-model/concurrent-user/solver-crash recovery testing and production
   resource limits. Current memory/latency observations are insufficient for a
   service capacity recommendation.
6. Complete Python dependency/adversarial upload/security qualification and a
   production backup restore drill.

### Medium

7. Replace/requalify obsolete legacy browser selectors and special-port fixtures;
   the full legacy browser matrix is not green.
8. Resolve the redacted historical evaluation archive through an explicitly
   reviewed archival correction/import procedure, or formally retire that replay.
   Preserve the original, label any derivative and never invent missing values.
9. Reduce large saved-history payloads and qualify method-version changes against
   saved calculation provenance. Current numerical validity is not automatically
   equivalent to validation against every future implementation.

## Before enabling live AI

Paid Nebius inference remains off. Live AI would require explicit user-approved
budget and provider enablement, server-only credential setup, exact model/endpoint
verification, privacy/retention review, bounded request/tool permissions,
timeouts/token ceilings, usage reconciliation and live tests on disposable data.
It also needs behavioral evaluation for evidence grounding, missing data,
unsupported code/soil claims, stale revisions and geometry-change proposals.
Offline text/template success does not prove live-model reasoning or safety.

Stop here for final review. No release, merge, deployment or live AI enablement
is authorized by this report.

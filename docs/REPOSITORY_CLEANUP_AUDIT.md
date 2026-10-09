# Repository Cleanup Audit

Audit started 2026-10-09. This report records the cleanup of the local GeoAI checkout. All sizes are byte counts from the current Windows worktree unless noted. Git internals are counted separately from worktree files. `.env` files were not opened or included in any content review.

## Safety checkpoint

- Branch: `main`
- HEAD: `581854cfab1f16bac24ee67dea37296c0629546e`
- Worktree was already dirty before cleanup: 67 status entries (40 modified tracked paths and 27 untracked paths). These include the accepted Core Assistant V1, Building Specialist V1, Building Patch V1, workspace acceptance implementation, and related tests/docs. They were preserved.
- No credentials were committed or read.
- User-provided baseline: backend 660 passed, 2 skipped; frontend/build/browser tests passing. A fresh baseline run is being recorded below.

## Initial size checkpoint

| Scope | Files | Bytes | Classification |
|---|---:|---:|---|
| Worktree files excluding `.git` | 89,810 | 3,545,800,264 | Mixed source, assets, dependencies, and ignored local data |
| `.git` files | 420 | 48,270,180 | Git metadata |
| Repository directory total | 90,230 | 3,594,070,444 | Worktree plus Git metadata |
| Git-tracked files | 626 | 87,388,236 | Source, docs, config, generated contracts, and required assets |
| Tracked source/docs/config subset | 599 | 4,328,135 | Extension-based source/docs/config estimate; excludes binary assets |
| Untracked non-ignored files | 27 | 147,184 | Current user changes; preserved |
| Ignored local files (derived) | 89,157 | 3,458,264,844 | Rebuild/test environments, outputs, local data, and ignored secrets |

The ignored byte total is derived from worktree total minus tracked and untracked bytes. It includes local environment files, whose contents were not inspected.

Top-level worktree file sizes:

| Directory | Files | Bytes |
|---|---:|---:|
| `frontend/` | 61,051 | 2,438,306,855 |
| `backend/` | 28,732 | 1,107,074,406 |
| `docs/` | 10 | 321,189 |
| repository root files | 15 | 94,365 |
| `.github/` | 2 | 3,449 |

## Disk usage and classification

The largest local files are dominated by the ignored Next/Turbopack cache, installed dependencies, and Python environments. The largest tracked binary assets include `frontend/public/models/dummy-arch-bridge.glb` (47,365,264 bytes) and `earth_16k.glb` (17,999,372 bytes); these are retained as catalogued product assets (A: SOURCE/ASSET — KEEP). Required generated API contracts such as `frontend/lib/generated/stage1.ts` and `docs/contracts/stage1.schema.json` are retained (B: REQUIRED GENERATED — KEEP).

| Path / family | Evidence and approximate size | Class | Action |
|---|---|---|---|
| `frontend/.next/` | Ignored Next build/dev output; largest files are 253 MB Turbopack cache segments | C: REGENERABLE | Remove after frontend checks |
| `frontend/node_modules/` | Matched `frontend/package-lock.json`; install tree about 1,041,373,449 bytes | C: REGENERABLE | Keep to preserve local verification environment |
| `backend/.venv/` | About 715 MB; Python environment | C: REGENERABLE | Keep to preserve local verification environment |
| `backend/.venv-civicspan/` | About 210 MB; separate CivicSpan requirements entry point exists | C: REGENERABLE | Keep; dependency purpose differs and it may be in use externally |
| `backend/.test-*` (49 dirs) | Ignored pytest scratch DB/output directories, each contains test DB copies | D: DEVELOPMENT ARTIFACT | Remove after full tests |
| `frontend/test-results/` | Ignored Playwright test output (about 96 KB) | D: DEVELOPMENT ARTIFACT | Remove after E2E checks |
| `*.log` under backend/frontend | Ignored local dev/test logs; no running Python/Node processes observed at audit time | D: DEVELOPMENT ARTIFACT | Remove after verification |
| `backend/.pytest_cache/`, Python bytecode caches | Standard pytest/interpreter caches | D: DEVELOPMENT ARTIFACT | Remove after verification |
| `backend/dev.db`, `backend/storage/` | Local development database and stored objects; database was recently modified | F: UNKNOWN / LOCAL DATA | Preserve |
| `backend/*pre-migration*.db`, `.test-stage1-regression.db` | Database snapshots with potentially useful state; no content-based proof they are disposable | F: UNKNOWN | Preserve |
| `.env`, `frontend/.env.local` | Ignored environment files, contents not read | F: SENSITIVE LOCAL CONFIG | Preserve and never include in cleanup output |

The top 50 file inventory was captured during the audit. It is dominated by the entries above, GIS native libraries in virtual environments, Cesium development bundles in `node_modules`/`.next`, and the two retained model assets.

## Backend and frontend dead-code review

One source deletion met the high-confidence standard. Backend routes are explicitly registered in `backend/app/main.py`; assistant execution also uses a dynamic `ADAPTERS` registry, SQLAlchemy models, Pydantic contracts, capability declarations, and proposal/revision calls. The repository had uncommitted V1 code across those files, so static zero-reference findings were treated as insufficient evidence.

Frontend routes are discovered by Next.js filesystem routing. The dashboard tests import `frontend/app/projects/new/page.tsx` directly and assert that legacy asset/template selection is absent. The dashboard is therefore actively protecting the current project creation flow. Dynamic Cesium loading, workspace tools, tests, generated types, and catalogue scripts remain in use or deployment/build configuration.

| Candidate | Reference evidence | Replacement | Risk | Decision |
|---|---|---|---|---|
| `frontend/app/projects/new/workspace.module.css` (legacy wizard styles) | 0 references outside the stylesheet; `/projects/new/page.tsx` redirects to `/dashboard?newProject=1`; dashboard tests import the redirect and protect the direct name-only flow | Dashboard `NewProjectDialog` | Low | Removed the confirmed unused 9,522-byte stylesheet |
| `frontend/app/projects/new/page.tsx` (`NewProjectPage`) | Two references in `dashboard/page.test.tsx` exercise the redirect; Next also discovers the route by path | Dashboard dialog handles project creation; the shim preserves `/projects/new` links | High | Keep redirect shim |
| `backend/app/api/routes/templates.py` (`router`, `public_router`) | Both routers are registered in `app/main.py`; admin/public template API behavior remains live | No complete replacement; the new-project dialog does not replace the template library | High | Keep both routes and asset catalogue |
| `backend/app/services/design/road_generator.py` (`generate`) | Eight direct references outside the module: import/dispatch in `services/ai/orchestrator.py` plus imports/calls in alignment and elevation tests | None; accepted Building execution does not replace legacy road design routes | High | Keep compatibility path |
| `backend/app/services/assistant/road_specialist.py` (`RoadAdapter.generate`) | Registered once by `specialists.py`; two Core Assistant V1 scenario cases failed the assertion that ROAD generation is unsupported; no dedicated Road specialist acceptance test exists | No accepted Road generation adapter; legacy design road route remains separate | High | Kept typed Road code for review, but removed `GENERATE` from its registered capabilities and removed the misleading `ROAD_CONCEPT_GENERATION` capability label |
| Other suspected unreferenced frontend components | Next route reachability, dynamic imports, and test-only imports are not all provable through text search | None proven | High | No other file-level candidate met the deletion threshold |

## Dependencies

No dependency was removed. `frontend/package.json` has matching `package-lock.json`; runtime packages include Cesium, MapLibre, Deck.gl, React Three Fiber/Three, Terraform/geometry packages, and workspace state/UI dependencies. `next.config.ts` uses the bundle analyzer. Backend `requirements.txt` includes PostGIS/geospatial, storage, worker, exports, AI, and observability libraries. The separate `requirements-civicspan.txt` supports `civicspan_app.py` and its own tests. A package not present in a direct source import can still be required by configuration, build scripts, optional providers, or deployment, so no dependency was safely removable in this pass.

## Docs and scripts

- Current/setup documentation: `README.md`, `LOCAL_SETUP.md`, `DEPLOYMENT.md`, `STORAGE_SETUP.md`, and `MANUAL_QA.md`.
- Historical/acceptance material retained: Core Assistant V1 and Building Specialist/Workspace/Patch V1 reports, plus Stage 1 architecture and contracts.
- No temporary docs were deleted. README is updated in this cleanup to describe the accepted GeoAI assistant/workspace and current project creation path.
- Operational scripts retained: production smoke, admin creation, migrations, provider check, deterministic seed/demo, asset catalogue sync, Cesium copy, generated contract export, and accepted V1 fixture generators. No one-off script was removed.

## Git hygiene

The root `.gitignore` already covered Next, Node dependencies, Python caches, local DB/storage, logs, frontend Playwright output, backend `.test-*`, coverage, and evaluation outputs. This cleanup makes the Python, coverage, SQLite, and Playwright cache patterns explicit. The frontend `.gitignore` separately covers `node_modules`, `.next`, build output, test coverage/results, env files, and TypeScript build info. Generated contracts, lockfiles, migrations, source assets, and accepted tests remain trackable.

## Verification and final disposition

The stated baseline test result was reproduced after the limited fixes below. Backend checks ran against an isolated SQLite database; local user databases and migration snapshots were retained.

### Changes made

- Removed the confirmed dead project wizard stylesheet. Kept `/projects/new` as its tested redirect into the dashboard's name-only dialog.
- Corrected the Stage 1 TypeScript exporter to preserve dictionary schemas and emit strict empty-object types; regenerated the required TypeScript and JSON Schema contracts.
- Kept the unaccepted Road specialist files for review, but removed their `GENERATE` capability claim because Core Assistant V1 tests require road generation to remain unsupported.
- Updated root and frontend README descriptions and expanded root `.gitignore` patterns for Python, coverage, SQLite, and Playwright artifacts.
- Removed `frontend/.next/` (1,329,430,059 bytes), generated `frontend/public/cesium/` (22,289,643 bytes), `frontend/.cache/`, Playwright results, TypeScript build info, Python test scratch directories, source-tree bytecode caches, pytest cache, and 93 backend/frontend local log files. Retained `node_modules`, both Python environments, `backend/storage/`, and every database file.

### Final size

| Scope | Before | After |
|---|---:|---:|
| Worktree files excluding `.git` | 3,545,800,264 bytes | 2,067,309,642 bytes |
| `.git` files | 48,270,180 bytes | 48,270,180 bytes |
| Repository directory total | 3,594,070,444 bytes | 2,115,579,822 bytes |
| Git-tracked file bytes present in worktree | 87,388,236 bytes | 87,386,200 bytes |
| Tracked source/docs/config subset | 4,328,135 bytes (599 files) | 4,326,008 bytes (598 files) |

Retained local dependencies account for 1,041,373,449 bytes (`frontend/node_modules`), 715,296,411 bytes (`backend/.venv`), and 210,085,660 bytes (`backend/.venv-civicspan`). The 4,492,184-byte `backend/storage/` directory and all local DB files remain. After cleanup the worktree contains 84,680 ignored files, mostly retained dependencies and environment contents. No dependencies were removed. The initial audit measured 3,545,800,264 worktree bytes; the final worktree is 2,067,309,642 bytes, a reduction of 1,478,490,622 bytes (about 41.7% of the initial worktree).

### Final verification

| Check | Result |
|---|---|
| Backend `pytest -q tests` | 660 passed, 2 skipped, 0 failed (3 non-failing warnings) |
| Backend `pytest -q civicspan_tests` | 5 passed, 0 failed (1 deprecation warning) |
| Frontend Vitest | 190 passed across 40 files |
| Dashboard-focused test after stylesheet removal | 15 passed |
| TypeScript `npx tsc --noEmit` | Passed |
| ESLint `npm run lint` | Passed with zero warnings |
| Production build `npm run build` | Passed; all 21 app routes compiled |
| Project creation browser flow | 3 passed in installed Chrome |
| Building workspace + Building patch browser acceptance | 2 passed in installed Chrome against isolated local API/SQLite |
| Stage 1 contract exporter `--check` | Passed; Pydantic emitted two non-failing discriminator schema warnings |
| `git diff --check` | Reports trailing whitespace/extra blank lines in already-dirty frontend files; left unchanged to preserve the user's existing edits |

The Building browser checks confirmed Cesium canvas availability, editor selection/save/reload/history/layer controls, and approved Building patch application with revision comparison. Backend tests cover Core Assistant safety, proposal approval/revision, terrain/provenance, Building generation, patches, and workspace behavior. The isolated E2E server and database were stopped/removed after verification.

### Final tree (approximately depth 3)

```text
.
├── .github/workflows/
├── backend/
│   ├── .venv/                      # retained local environment
│   ├── .venv-civicspan/            # retained local environment
│   ├── alembic/versions/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/  db/  domain/
│   │   ├── middleware/  workers/
│   │   └── services/{ai,assistant,calculations,design,exports,geospatial,site_profiles,survey}/
│   ├── civicspan_tests/
│   ├── evals/
│   ├── scripts/
│   ├── storage/                    # retained local data
│   └── tests/
├── docs/
│   └── contracts/
└── frontend/
    ├── app/{admin,dashboard,login,projects,settings}/
    ├── components/{auth,dashboard,landing,layout,map,model-editor,workspace}/
    ├── e2e/
    ├── hooks/
    ├── lib/{generated,map}/
    ├── node_modules/               # retained for verification
    ├── public/{models,textures,videos}/
    ├── scripts/
    └── stores/
```

### Review required

- Historical migration database snapshots and `backend/dev.db` — retained because they may contain useful local data.
- CivicSpan-specific duplicate dependencies and provider/runtime branches — require per-entry-point runtime validation before pruning.
- Possible old UI components and pre-V1 generation code — no source removed because routing, dynamic imports, tests, registry wiring, or proposal/revision calls make a simple absence of text references insufficient.
- Road specialist schema and generation implementation — retained but no longer declares generation support. It has no dedicated acceptance test; review whether it should remain as compatibility material or be removed in a future pass.
- The combined `pytest tests civicspan_tests` invocation has a duplicate test basename; run the two suites separately unless pytest import mode is deliberately changed in a later focused fix.

### Second pass recommendation

After the architecture milestone, perform a targeted dependency and route inventory with runtime/import graph tooling for each supported backend entry point, review the Road specialist disposition and retained migration snapshots, and assess unused dashboard components with their owners. Keep this pass narrow and tie each proposed source removal to a focused behavior test.

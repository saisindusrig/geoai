# Phase C Gate1C — controlled local Node runtime transition

**LOCAL TRANSITION GO for new launcher process trees. Normal system Node/global npm remain unchanged. Existing normal website/API instances were not restarted or migrated. Firebase remains disabled; public launch remains BLOCKED.**

## Verified runtime and rollback established

Read Gate1A/Gate1B results, both existing launchers and retained preservation evidence. Before editing, copied exact launcher bytes into `rollback/` and recorded their hashes/effective Node/PATH in `before.json`. Both originally selected system Node22.18.0 by inherited PATH. The retained portable archive again matches the checksum previously verified against the official signed manifest. Its node.exe, npm CLI, npm package metadata and Windows/POSIX npm shims match ZIP-entry hashes; Node reports24.22.1, x64, npm11.19.1 (`runtime-verification.json`). All six files were rechecked after validation. No download, installation, global npm update or system PATH change.

`ROLLBACK.md` contains the exact restore commands. `rollback-demonstration.json` demonstrates restoring the updated launcher copies to byte-identical original files in a separate fixture, selecting inherited Node22.18.0 again. No original database, package or historical record is part of rollback. The new helper can remain inert after restore; original launchers never reference it. Node22 rollback is an availability path with Firebase still disabled, not Firebase-engine/security qualification.

## Exact changes

- `run-website.bat`: retain SETLOCAL; explicitly select the retained project-local node.exe, prepend only its process PATH, run shared preflight, and invoke the matching portable npm CLI through that exact node.exe for predev/dev. Existing frontend/API ports3001/8001, frontend health check, backend-only delegation and predev behavior remain. Added `--check-runtime`, which starts no services.
- `start-copilot-review.ps1`: select the same explicit executable/PATH before starting anything, run shared preflight, and use it for Next. Restore the caller's PATH in finally on success, failure and reuse. Added `-CheckRuntime`, returning before mutex/API/log/service startup. Existing mutex, backend start/reuse, healthy frontend reuse, ports, API rewrite flags and server command remain.
- New `scripts/verify-local-node.cjs`: require Windows x64/exact24.22.1, canonical expected executable path, six signed-archive file hashes, exact PATH-selected child Node24 and verified portable npm11.19.1/shims. No network, application/Firebase import or credential-config reading. Reject missing, modified, incompatible or fallback runtime before services. No automatic install, version substitution or Node22 fallback.

No validation guard, IPC exception, fixture port, account identifier or test provider was added to these normal files. `launcher-changes.patch` is a plain difflib review artifact, generated without Git.

| Launcher | Before SHA256 | After SHA256 |
|---|---|---|
| `run-website.bat` | `d9c5cbbb0d74b805b2ce4a1af91f62fe61829826ca250bfed54856c865b2fd65` | `b85f42397d9855a411e8dd1e7988ea974f1ef113f29c48700f6d992178b89cf9` |
| `start-copilot-review.ps1` | `36acca56dba7eba129c166935c1f6afe438a4fbece56e68d2b83dcdfae66ee8b` | `4acd7258ff072929f9cf6f4b1eb94fdcf40d281fc90a233a8c3d44d4da1cf255` |

Helper SHA256: `0d7e713b5da122a31b8e31d4c8c0cca8f706e6b94129b9a0fd2030b5ee09875b`. Full machine-readable hashes: `launcher-hashes.json`. The first preflight test exposed Windows `where npm` listing the official extensionless shim before npm.cmd; preflight was corrected to accept only verified bundled shim candidates and additionally hash those shim files. No service started during those early rejected checks.

## Main, npm and worker evidence

Actual normal launchers both pass check-only mode (`batch-preflight.log`, `powershell-preflight.log`). `preflight-tests.json`: six actual negative launcher invocations reject missing runtime, Node22 and modified npm in isolated fixtures. `path-fallback-rejections.json` additionally rejects a PATH-selected system Node22 child and a foreign current-directory npm candidate; the foreign npm is never executed. PowerShell PATH restoration was exercised in the same caller, then a plain node command still selected22.18.0. Batch SETLOCAL plus parent PATH hash comparison confirm no persistent change.

The build used a copied transitioned PowerShell launcher, not a manually guessed PATH prefix. A test-only Next entry captured its selected main/child/npm/PATH and then invoked **unchanged package.json `npm run build`** in the existing faithful physical frontend copy. `launcher-build-runtime.json` records Node24 for main and PATH child and the matching explicit npm CLI. This capture entry is only under local test tooling; it is not part of the real frontend or production launcher.

All 79 admitted validation runtime records are exact Node24.22.1; 4 owned compiler-IPC records map to Node24 workers (`runtime-summary.json`, guard log). The validation-only guard retains Gate1B's narrow owned-loopback compiler IPC admission and extends it to generated dev entries/server parent. Neither policy is in normal launcher code. Existing system Node22 remains available for other processes; known Next/npm/PATH-selected helpers are pinned and checked rather than silently falling back.

## Standard build and focused verification

- `build.log`/`build-result.json`: **standard npm prebuild + default Next16.4.2 Turbopack production build PASS**, exit0, approximately 35.07 seconds including five-second monitoring. TypeScript and all17 static pages completed. Bounded at180 seconds, no timeout. No Webpack substitution, package/lockfile change or suppressed engine check. Gate1B's qualified output was retained under a distinct tooling directory before this fresh build.
- `engine-compatibility.json`: Firebase13.1.0/Next16.4.2/React19.2.4 unchanged; all installed Node engine requirements pass24.22.1. The noninstalled optional ia32 Sharp entry remains explicitly reported, not suppressed.
- **109 focused frontend tests /16 files PASS** (`tests.log`): auth/unavailable Firebase, assistant status/receipts, geometry/orientation/transforms, graphics lifecycle, primitive/beam preview safety, transactions, undo/redo and explicit Save boundaries. Eight additional negative runtime/fallback scenarios above passed.
- Standalone TypeScript, scoped frontend ESLint, scoped recommended Node ESLint on the new helper and `node --check` PASS (`typescript.log`, `lint.log`, `launcher-lint.log`, `launcher-syntax.log`). Backend/engineering code unchanged; no solver/backend suite.

## Local runtime/browser validation and existing instances

Normal ports3001 and8001 were already reachable before validation. They stayed reachable afterward (`normal-ports-before.json`, `ports-after.json`); no original-port HTTP requests, restarts, replacement listeners or backend initialization were used for acceptance. Existing healthy-instance reuse is deliberately preserved. **Changing launcher files does not migrate an already-running Node process; its runtime was not re-identified or changed here. New starts select24.22.1.**

To exercise actual startup safely, copied launchers under tooling used only test-local port/mutex remaps (3017/8003 and a separate mutex), plus the same verified runtime through local junctions. Normal files still contain3001/8001 and the original mutex. The physical app/dependencies/config remained the Gate1B faithful copy; only synthetic API/files were available. Test npm configuration/cache was isolated and empty, no credential files read. The synthetic API rejects all writes.

The copied PowerShell launcher started the **real Next development server**, not the build-capture entry. `launcher-dev.log`, `browser.json`, `functional.json`: PASS at1280×900,1600×900,390×900 for homepage/title/StruvoCivil branding, login/local-development identity, Firebase-unavailable behavior, disabled registration, dashboard/project navigation, runtime diagnostics page, desktop WebGL2 geometry, selection/camera completion receipts, graphics controls, conceptual column/beam renderer receipts/Apply gating/Cancel, and assistant-open scene with accurately disabled AI. Mobile keeps the existing Desktop Required workspace gate. The screenshot `after-assistant-1600.png` was visually reviewed. No renderer/engineering/source-coordinate change.

Preview validation responses and renderer-result overlays are explicitly synthetic/mocked; no browser Apply/Save, actual Firebase authentication, solver or paid AI request occurred. Exact saved-result authority/approval contracts are covered by the focused existing tests, not presented as a new live-service qualification. Diagnostics payloads are synthetic: no numerical probe. Final browser page errors, unexpected blocked application requests and downloads are zero.

Then the copied **batch frontend mode** separately ran the matching npm predev/dev lifecycle (`batch-dev.log`). Its unchanged dev script's nominal3001 was overridden only by a test-copy CLI port argument to3017. Homepage and actual same-origin health proxy returned200 with the isolated API marker (`batch-runtime-smoke.json`). The main viewport suite was on the copied PowerShell dev server; the default production binary was built successfully but not separately served for another browser run in this phase. Gate1B's production-browser evidence remains distinct.

Existing Three.Clock and Vitest environmentMatchGlobs deprecation messages were retained, not suppressed or fixed through unrelated upgrades. Guard logs record denied Next registry DNS/Playwright global-marker writes as attempts, not successful external changes. No application request reached original projects, Firebase or Nebius. Only isolated test servers were stopped; final3017/8003 are closed, normal3001/8001 remain reachable.

## Original-data preservation

`preservation.json`: exact current baseline rows/schemas match **10,283 development rows and three assistant-history rows**, including audit and accounting. Original frontend/geometry/assistant source hashes, dependency manifests/lockfile, backend requirements and all ten static fixture inputs remain unchanged. Only the two authorized normal launchers plus the new standalone preflight helper changed; before/after launcher hashes are above.

Fresh retained manifests verify **55,296 storage files,2,090 engineering proof files,66 live database schemas,198 archive-only fingerprints** and **21 solver artifacts** unchanged. The old manifest's14 pre-existing row additions predate this phase and are preserved/documented. Archives read in place; no extraction, restore, migration, deletion or historical-record update. Original runtime files remain archive-identical. No Git, new dependency, Firebase Admin, credential change, cloud/billing/deployment, paid inference or destructive cleanup.

## Decision and remaining limits

**GO: local launcher runtime transition for new process trees.** Use `run-website.bat --check-runtime` or `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-copilot-review.ps1 -CheckRuntime` for no-start diagnostics. Normal commands/ports/backend reuse stay available. Manual bare node/npm commands outside these launchers still use the system installation; no global terminal/runtime policy was changed.

Firebase remains disabled and unqualified for genuine sign-in/lifecycle/ownership acceptance; no Admin installation or activation was performed. GPU memory sign-off remains open (loaded approximately112–121MB, disposed31–38MB, residual DOM/listener growth, no confirmed unbounded Cesium leak); no memory refactor or new performance phase. Existing real-service security/recovery gates and **public launch remain BLOCKED**. Stop after Gate1C.

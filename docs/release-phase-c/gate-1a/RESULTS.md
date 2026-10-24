# Phase C Gate 1A — isolated Node.js 24.22.1 compatibility validation

23 October 2026 (Asia/Calcutta). **Compatibility disposition: BLOCKED for a deliberate transition of the normal default pipeline.** Installed-engine checks, focused tests, Webpack production build and isolated production-browser checks pass. The default Turbopack production-build attempt remains incomplete in the junction-based working copy, so no blanket compatibility GO or normal-runtime switch is recommended. This is not evidence that Node 24 itself is defective. **Public launch remains BLOCKED independently.**

## Verified portable runtime

Actual Windows OS and process architecture are both X64. Downloaded only `node-v24.22.1-win-x64.zip` from `https://nodejs.org/dist/v24.22.1/`; no installer was used. Its SHA-256 is:

`d2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5`

The ZIP matches the official **cryptographically verified clearsigned checksum manifest**, not merely an unsigned checksum retrieved beside it. `signature-verification.log` records GnuPG VALIDSIG for fingerprint `5BE8A3F6C8A5C01D106C0AD820B1A390B168D356`, independently pinned from the [official Node release-key repository](https://github.com/nodejs/release-keys). Public key material came from that repository. Existing GnuPG shipped with the installed Git distribution was used as a standalone verifier; **no Git command or repository operation** was run. All keyring/trust files are under the isolated tooling directory, not a global user keyring. Initial MSYS sandbox/path setup errors were resolved before the cryptographic verification attempt; no invalid signature or checksum was accepted. See `archive-verification.json`.

Retained archive: `.local-tooling/node-24.22.1-validation/downloads/node-v24.22.1-win-x64.zip`.

Extracted runtime: `.local-tooling/node-24.22.1-validation/runtime/node-v24.22.1-win-x64/node.exe`.

Explicit executable reports **v24.22.1**. Its bundled npm CLI reports **11.19.1** with isolated empty user/global npm configuration and isolated cache (`npm-version.log`). No global npm update, PATH change, installer, Windows setting or normal startup launcher change. Existing normal Node remains `C:/Program Files/nodejs/node.exe`, **v22.18.0**.

## Dependencies and engine result

Existing **Firebase 13.1.0, Next 16.4.2 and React 19.2.4** retained. No dependency installation, downgrade, lockfile rewrite or unrelated package update occurred. **Firebase Admin remains absent**; its installation was not resumed.

`engine-compatibility.json` evaluates 488 lock entries declaring Node engine ranges. All **installed** entries satisfy Node 24.22.1, including the Firebase packages that require >=24.12.0 and reject the existing Node 22 runtime. The raw cross-platform lock contains one nonmatching optional `@img/sharp-win32-ia32@0.35.5` entry declaring `^20.9.0`; it is **not installed**, targets ia32 and is not used on this x64 machine. It also does not match Node 22. Do not claim every cross-platform lock entry is compatible or suppress a warning. No engine requirement was overridden.

A guarded SDK module smoke test imports only `firebase/app` and `firebase/auth`, verifies version/export availability and `getApps().length === 0`. No `initializeApp`, authentication, credential or project call was made. Its own process recorded zero blocked network attempts (`firebase-module-smoke.json`). This is module-loading evidence, not genuine sign-in/lifecycle qualification.

## Isolation and focused verification

Working copy: `.local-tooling/node-24.22.1-validation/work/frontend`. Copied frontend source/public marketing assets, excluding .env*, .npmrc, database/private CAD formats, old build outputs and original node_modules. Dependencies were reused through **743 per-package junctions** with a separate cache root. No package-manager install was needed. Only ten explicitly imported static JSON test/typecheck fixtures were copied outside frontend to satisfy existing test imports; source paths/hashes are listed in `static-fixture-inputs.json`. They were not exposed by the API/public directory or imported into a database. No original project model was used for browser routing.

A validation-only Node preload guards writes outside working/output directories, refuses environment-file reads, clears service credential references process-locally, disables Firebase/inference/telemetry, and blocks network outside the isolated frontend/API ports. It records runtime paths for workers. Vitest temp files were redirected into the working directory. Synthetic API runs loopback only with dotenv credential loading disabled, skips normal application initialization/migrations and rejects every non-GET/HEAD method. Existing fixture source is read without seeding. Normal frontend/backend processes were not restarted.

Results:

- **64 frontend tests passed / 12 files** (`frontend-tests.log`): auth capability/return paths, unavailable Firebase, safe assistant rendering/disabled status, isolated routing, primitive controls, beam/sandbox geometry, framing and model URLs. Existing Vitest environmentMatchGlobs deprecation retained. First attempt was blocked by the stricter temp-directory guard; rerun after redirecting temp passed. This was a harness issue, not a product code fix (`frontend-tests-initial-harness.log`).
- **TypeScript passed** under Node 24 (`typescript.log`). It also passed under existing Node 22 with incremental output disabled (`typescript-node22-comparison.log`). Initial isolated-copy failure was missing static test fixture imports, resolved by adding only the declared hashed fixture inputs. No source types were weakened or errors ignored.
- **Scoped ESLint passed** for login/config tests/source and assistant markdown (`lint.log`). No lint suppression.
- **Default Turbopack production build not qualified.** Initial copy could not resolve packages across junctions (`build-initial-isolation.log`). Only the isolated Next config received the installed Next documentation's `experimental.turbopackAdditionalRoots` entry pointing to the existing dependency directory; the normal config is unchanged. That retry stayed at compile with no server files/progress and was interrupted after a bounded attempt of approximately 4–5 minutes (`build-turbopack-incomplete.log`). No unmodified normal-layout Node 24 build or Node 22 build comparison was attempted. Do not infer a Node-specific regression or claim a default build PASS.
- **Supported Webpack production build passed** with explicit `next build --webpack` (`build-webpack.log`): compiled in 24.9 seconds, completed TypeScript in 11.1 seconds, generated all 17 static pages and completed trace collection. This validates the tested alternative path, not a silent bundler change to the normal website. No application source/dependency fix was made to force it to pass.
- **Isolated built-site browser checks passed** at 1280×900, 1600×900 and 390×900 (`browser.json`, `browser.log`) under the portable runtime and installed Chrome. Homepage/branding, local login, unavailable Firebase, disabled production registration, project navigation, desktop 3D geometry/camera fit and assistant-open visibility all passed. Zero final page errors, unexpected requests, writes or downloads. The first run narrowly rejected production RSC prefetches for `/privacy` and `/projects/new`; only those two exact same-origin read-only prefetch paths were permitted in the isolated harness, then rerun passed (`browser-initial-prefetch.log`). No API allowlist was broadened.
- **Actual same-origin proxy verified** through port 3017 `/local-api/api/health`, `/api/auth/config` and `/api/projects/991600`. These requests traverse Next's rewrite and require the synthetic backend marker, rather than relying solely on intercepted browser requests. No request to normal API port 8001.
- **Cesium/static renderer checked:** Cesium.js, Widgets CSS and createBoxGeometry worker returned 200; the sandbox canvas became ready and synthetic beam/columns remained visible with the assistant open. Existing Cesium asset-copy and catalogue scripts ran only in the isolated copy. No solver/analysis run. Chrome uses software rendering; GPU/performance qualification is not claimed.

Guard evidence (`guard-events.jsonl`) includes denied ordinary tool temp/cache writes during early harness setup and denied npm-registry DNS attempts from Next's update-related behavior; those requests were not allowed out. The Playwright global browser-cache marker write was also refused without affecting the browser tests. These denials are not hidden or presented as zero attempted network/write activity. No Firebase/provider request occurred. Validation-only changes are identified in the working copy and logs; no unrelated website fixes were made.

Screenshots: [3D with assistant at 1600](after-assistant-1600.png), [3D with assistant at 1280](after-assistant-1280.png), [mobile login restriction](production-registration-disabled-390.png), [mobile Firebase unavailable](firebase-unavailable-390.png). Screenshots visually inspected. Temporary frontend 3017 and synthetic API 8003 servers stopped; normal ports/launchers left alone.

## Before/after preservation

`preservation.json` compares exact pre/post row hashes/schemas: **10,283 application rows and three assistant-history rows**, zero row/schema/accounting changes. Original dependency manifests, backend requirements and both normal launchers match pre-test hashes. Copied static fixture originals match their saved hashes. Fresh existing manifests verify **55,296 original storage files, 2,090 proof files, 66 live schemas, 198 archive-only database fingerprints and 21 solver artifacts** (`preservation-audit.json`, `solver-preservation.log`). The older baseline's 14 additions predate this test and are preserved, not Gate 1A writes. No CAD/model/result/source-hash, authorization, accounting or conversation change; no migration, deletion or backup rewrite.

Original .env/credential files were excluded/not read by the runtime harness, Firebase remains disabled and Nebius inference remains disabled. No Firebase Admin installation, real identity, cloud activation, billing, deployment, package installation, numerical execution or destructive cleanup.

## Future deliberate transition and rollback

Before a normal-runtime transition, complete the **default Turbopack path** in a faithful self-contained dependency layout or separately approve a deliberate Webpack build policy after its tradeoffs are reviewed. A failed/incomplete isolated-root build must not be silently treated as an environment-only waiver.

If later approved, update `run-website.bat` and `start-copilot-review.ps1` to deliberately select a project-scoped pinned runtime and matching npm CLI for all predev/dev/build invocations. Current launchers resolve `node`/`npm` through PATH and accept a >=20.9 minimum; they would still select Node 22 and do not enforce the new Firebase engine floor. Their diagnostics/minimum must reflect the approved tested runtime. Prefer explicit project-local executable paths or process-local PATH selection, not a system-wide PATH/global npm replacement. Recheck normal port 3001/8001 proxy and same renderer workflows after an authorized transition; do not copy this test API port or additional-root setting into production implicitly.

Rollback today requires **no normal-site change**: continue using the existing Node 22 installation/unchanged launchers. The portable runtime/test directory is inert unless explicitly invoked; retain it and logs for review, no cleanup needed. Any future launcher transition should preserve its current baseline and restore only approved launcher selection on rollback; do not downgrade dependencies or erase data. The existing Firebase package must remain disabled/unqualified under Node 22 until runtime policy is resolved.

**Final decision: BLOCKED for full/default-pipeline runtime-transition qualification; tested Node 24/Webpack subset passes.** No normal runtime switch, Admin SDK continuation or Firebase activation authorized by this result. Stop after Gate 1A; public launch remains BLOCKED under all previously documented real-service/security/recovery gates.

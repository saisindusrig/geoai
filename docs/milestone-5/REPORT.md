# Milestone 5 — Security-patched runtime and Firebase preparation

Completed 23 October 2026 (Asia/Kolkata), continuing work begun 22 October. **The tested normal local instance is running patched Next.js 16.4.2. Private beta, deployment and engineering approval remain BLOCKED.**

## Exact local baseline and result

| Package/tool | Before: declared / locked / installed | Final: declared / locked / installed |
|---|---|---|
| next | 16.2.9 / 16.2.9 / 16.2.9 | 16.4.2 / 16.4.2 / 16.4.2 |
| eslint-config-next | 16.2.9 / 16.2.9 / 16.2.9 | 16.4.2 / 16.4.2 / 16.4.2 |
| @next/bundle-analyzer | ^16.2.9 / 16.2.9 / 16.3.6 | 16.4.2 / 16.4.2 / 16.4.2 |
| React / React DOM | 19.2.4 | 19.2.4, unchanged |
| sharp, framework image dependency | locked/installed 0.34.5 | locked/installed 0.35.5 |
| Node / npm | 22.18.0 / 10.9.3 | unchanged |

The attached prompt's quoted declarations matched the local declarations, but not the installed analyzer. No remote repository was fetched or compared; local files remain authoritative. Before hashes, source/lock snapshots and metadata: dependency-before.json, before-package.json, before-package-lock.json, next-target-16.4.2.json. Exact lock changes: lockfile-changes.json.

## Security version selection and image behavior

16.3.6 was insufficient after checking newer vendor advisories. The October SVG and cache/Server Action fixes require at least 16.4.1; 16.4.2 was the latest available stable 16.x metadata reviewed. Existing Node/React satisfy its published peers/engine requirements.

| Reviewed advisory | Patched floor | Tested result |
|---|---|---|
| [Windows RCE](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36) | 16.3.3 | 16.4.2 outside reviewed affected range |
| [AVIF optimizer RCE](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4) | 16.3.3 | 16.4.2 + sharp 0.35.5; benign codec proof passed |
| [next/og ImageResponse](https://github.com/vercel/next.js/security/advisories/GHSA-vcvr-r3jv-pc5j) | 16.3.6 | Patched defensively; no application ImageResponse/next/og entry point found |
| [SVG optimizer / Linux](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw) | 16.4.1, corrected sharp dependency | Patched version/dependency; default SVG rejection verified; no Linux runtime qualification claimed |
| [Typed-array cache RCE](https://github.com/vercel/next.js/security/advisories/GHSA-673q-mjm6-r5xr) | 16.4.1 | Patched; no application use-cache function found |
| [Server Action DoS](https://github.com/vercel/next.js/security/advisories/GHSA-p3m5-59mp-jv5r) | 16.4.1 | Patched; no application Server Action entry point found |

The installed transform uses the patched sharp implementation. Generated benign AVIF decoded/optimized to WebP; PNG encoded to AVIF; default SVG optimization was rejected. Native versions observed: sharp 0.35.5, libvips 8.18.7, heif 1.23.5. Therefore existing AVIF/WebP output configuration was retained, not blindly disabled. No malicious exploit payload was executed. Evidence: image-codec-probe.cjs/json and next-security.test.ts.

This is a scoped reviewed-advisory result, not a claim that every transitive dependency or unknown vulnerability is fixed. MapLibre/TerraDraw, Vitest/Tinypool, other retained parser/build/HTTP-client reports and Python advisories remain separately deferred under the Milestone 4 exposure assessment. No blanket audit fix was run.

## Commands and installation scope

Read metadata with `npm view next@16 version --json` and version-specific `npm view` queries for Next and matching tooling. A dry run left package/lock hashes unchanged. The actual authorized install was:

```text
npm install next@16.4.2 eslint-config-next@16.4.2 @next/bundle-analyzer@16.4.2 --save-exact --ignore-scripts --no-audit --no-fund --json
```

Only those three root declarations changed. Lock changes are in their Next/tooling/image dependency closure, including SWC, sharp/native variants, helpers/PostCSS and resolver transitives; no unrelated root packages were requested. npm reconciled pre-existing installed-tree/lock drift: **26 added, 43 removed, 202 changed** installed entries. This should not be mistaken for three downloaded files. The exact install result and **224 observed public npm tarball URLs/cache states** are retained in install-result.json and package-fetches.json; lockfile-changes.json records the resolved package changes. No lifecycle install scripts, force/major audit fix, Firebase SDK, emulator or browser download was used.

## Proven compatibility change

The upgraded Next ESLint plugin flagged the existing API helper's relative `window.location.href` assignment. The helper remains outside React and preserves its intentional full navigation after clearing rejected authentication. It now constructs the same-origin login URL and calls location.assign. The focused test verifies token clearing and the exact encoded project return path. Ownership, authorization, mutation retry and numerical methods were unchanged.

Source changes: frontend/package.json, frontend/package-lock.json, frontend/lib/api.ts. Next build/type metadata and the existing deterministic Cesium/catalogue build tasks were refreshed; these are generated operational artifacts, not engineering data. Verification files added: frontend/lib/next-security.test.ts, frontend/lib/api-auth-redirect.test.ts, frontend/e2e/milestone-5.spec.ts. Architecture: ../firebase/FIREBASE_FUTURE_ARCHITECTURE.md. Other outputs/scripts are scoped to this folder. Historical builds/backups were not cleaned up.

## Verification, including failures

- Before upgrade: 17 focused frontend tests passed. One retained browser baseline failed on the existing “missing required error components” screen; backend diagnostics were healthy. Baseline log/screenshot retained. That failure is not labeled an upgrade regression or given an invented root cause.
- Updated dependencies: 79 retained frontend tests passed across 12 files (Cesium/asset transforms, guided source-bound results, auth, downloads, diagnostics, persistent Assistant). Two new version/peer guards passed. One new auth-navigation test passed; five overlapping transport/download checks also passed. **82 distinct frontend tests**, not inflated by reruns.
- **93 targeted backend tests passed**, including isolated JWT/ownership, DXF/source downloads and hash integrity, exact proposal/hash and idempotency, stale-result gates and diagnostics. No original database was used for modifying tests; no solver rebuild/new method.
- TypeScript and scoped upgraded-tooling ESLint passed. Two required local production builds passed: the final rebuild was necessary after the narrowly tested auth compatibility edit. Existing prebuild catalogue and Cesium asset-copy tasks ran; 197 catalogue types retained. Logs: build.log, build-final.log, typescript-final.log, lint-final.log.
- Initial updated browser launch failed because npm's lock reconciliation selected the locked Playwright tooling whose expected bundled browser was absent. No browser was downloaded: the final run uses already installed Chrome via PLAYWRIGHT_CHANNEL=chrome. Failure output is retained.
- **Final real-browser matrix: 4 passed in 27 seconds**, at 1280×900 and 1600×900. Dashboard; project 793 current frame 421 / revision 103; project 794 current slab 431 / revision 105; project 804 remains a restricted foundation reference with no falsely current integrated result; Cesium workers/3D; saved result modes; diagnostics; keyboard/manual recovery; no horizontal overflow.
- Negative browser results: invalid token 401, foreign-project read/download 404, unallowlisted artifact 404, stale result 417 report 409. Current report 421 downloaded as an attachment with the same saved SHA-256. All browser modifying requests were blocked and none was attempted. External browser requests were blocked; no Firebase product or paid-provider API calls occurred. Assistant behavior has retained unit coverage; no conversational inference/write was submitted in browser tests.
- Screenshots inspected: project-793-1600.png and project-794-1280.png. Additional screenshots include all three projects at both sizes, dashboard, diagnostics and unavailable/recovery states. Test output: browser-final.log, security-1280.json, security-1600.json, normal-models-1280.json and normal-models-1600.json.

## Actual running instance

The final successful production build is served on **127.0.0.1:3001**, with the existing offline backend on **127.0.0.1:8001** and same-origin /local-api proxy. Next startup identifies 16.4.2; the served HTML contains the exact final BUILD_ID, linking runtime to the tested patched build. Package declarations, lockfile and installed Next tooling agree. Runtime evidence: runtime-final.json and web-final.log. The normal launcher reused these healthy processes without spawning duplicates (launcher-reuse.log). Current database/schema and OpenSees 3.8.0 version-only diagnostics are healthy; production qualification remains blocked.

## Preservation and operational metadata

Existing strict manifests verify **10,266 original database rows/schemas** and **10,500 isolated rows**, unchanged with zero appends. **635 spatial artifacts**, **21 coupled artifacts**, **55,296 storage files** and **2,090 CAD/proof files** verify unchanged.

The legacy verifier initially failed because .cleanup-backup-path names former uncompressed backup paths. Existing RESTORE.txt explains that those snapshots were already retained in retained-backups-20261022.zip. The archive was read in place, never extracted, moved, rewritten or restored. A second legacy assumption—every historical test DB still existing at its old live path—was also unsuitable. The scoped archive-aware verifier distinguishes **66 live database schemas** from **198 archive-only historical test databases** whose saved row fingerprints were verified in transient memory against the original baseline. It does not claim a current live-schema comparison for absent paths. Across live/archive comparisons, 263 older database fingerprints match; the development DB's historical difference predates this milestone and the strict current-row baseline matches exactly. Failure logs and the reconciliation are retained.

No full-project backup or original database copy was made. Only scoped source/lock snapshots and manifests were recorded. Build/type caches changed legitimately; normal request logs may receive operational append output and are not claimed byte-identical. No existing log, geometry, calculation, model revision, solver evidence, conversation, usage or authorization record was repaired or deleted. Evidence: preservation-audit.json, preservation-files.json, preservation-manifests.json, milestone-preservation.json and review-preservation.json.

## Firebase preparation and remaining gates

[Firebase future architecture](../firebase/FIREBASE_FUTURE_ARCHITECTURE.md) contains the component diagram, App Hosting versus static Hosting boundary, backend-verified identity mapping, Cloud Run API/worker candidates, relational Cloud SQL recommendation, private immutable Storage, costs/Blaze/guardrails, India-region questions and staged authorization/rollback gates. It creates no live integration. Official public documentation was read; no Firebase project/service/billing API was invoked and no original data was sent to Google.

| Gate | Status |
|---|---|
| Reviewed Next security update in tested local runtime | Verified within stated scope |
| Shared private beta / production identity and headers | Blocked |
| Durable jobs/database/private storage and restore drill | Unverified / Blocked |
| Remaining dependency, resource-abuse and production monitoring qualification | Unverified / Blocked |
| Firebase billing, identity migration, staging hosting and data cutover | Not enabled; separate authorization required |
| Engineering code/safety approval and unsupported analyses | Blocked; existing restrictions unchanged |

No Git/repository GitHub operation, paid inference, additional agent, deployment, billing enablement, data migration or destructive cleanup. Stop after Milestone 5 for review.

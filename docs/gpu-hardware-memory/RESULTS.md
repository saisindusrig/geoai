# GPU hardware and memory verification

**Hardware rendering: verified in the tested Chrome environment. Functional regressions: PASS. Memory stability: NOT QUALIFIED. Public launch: remains BLOCKED.**

No application/renderer changes were made. This is verification, not another optimization phase. Only local test harnesses, reports and evidence were added; original source, dependency manifests, launchers and runtime selection match prior hashes.

## Actual acceleration

`hardware-status.json` records both fresh headless and windowed installed Chrome: WebGL2 available, GPU compositing/WebGL/OpenGL enabled, and a non-software ANGLE hardware-renderer candidate. The actual Cesium canvas independently confirms a recognizable hardware-vendor renderer and explicitly rejects SwiftShader, llvmpipe, basic/software rendering (`performance.json`, all three sizes). Together these qualify the tested browser's hardware-backed WebGL2 path. Raw renderer names, vendor/device IDs, driver versions and SystemInfo device records were inspected only transiently and are not persisted. No hardware fingerprint or telemetry was added to StruvoCivil.

Chrome selected its normal driver; no forced ANGLE/driver flag or unsupported driver was used. The harness removes Playwright's no-sandbox and unsafe-SwiftShader flags. No browser profile/settings, system GPU preference, Windows setting or normal startup launcher changed. This does not certify the owner's separate existing Chrome profile, every browser/driver, a discrete GPU preference, monitor refresh rate or OS GPU utilization. No OS utilization percentage or VRAM figure is claimed.

## Repeated current hardware measurements

`performance.cjs`, `performance.json`, `performance-summary.json`: portable Node24.22.1, unchanged isolated Webpack build, installed headless Chrome, 1280×900 CSS pixels, Auto quality, synthetic 10/100/400 components. Three bounded repetitions per size: 2 seconds idle and approximately 1.2 seconds each controlled orbit/pan/zoom, refitting before each motion. The orbit rotates about the local model area, using the existing camera transform pattern. These are instrumented offscreen Chrome render-throughput figures, not monitor FPS or direct human input-lag measurements.

| Components | Idle draw calls / 2s, range | Median orbit / pan / zoom render FPS | Orbit mean CPU submission, median ms | Orbit GPU elapsed, median ms |
|---|---|---|---|---|
| 10 | 30–120 | 168.9 / 170.5 / 172.9 | 0.265 | 1.209 |
| 100 | 210–210 | 168.7 / 169.7 / 168.9 | 0.587 | 1.448 |
| 400 | 810–810 | 167.7 / 169.4 / 169.4 | 1.606 | 4.575 |

CPU values bracket Cesium preRender→postRender and exclude other CPU activity. GPU values use `EXT_disjoint_timer_query_webgl2`, up to six available samples per measured interval, discarding disjoint results; orbit has 18 accepted samples per size. They measure the queried frame command interval, not total GPU utilization, and instrumentation adds overhead. Idle draw counts vary during initial settling (notably size 10); idle FPS is deliberately low under on-demand rendering and is not an interaction performance failure. Raw timing arrays/ranges and idle renderer TaskDuration are retained.

There is **no equivalent pre-optimization physical-GPU baseline**, so no before/after hardware speedup is calculated. Prior SwiftShader FPS is never used as a hardware baseline. `performance-initial-invalid-orbit.json` preserves a rejected initial run: its world-origin orbit let the model leave view and those orbit figures are excluded. The initial large run also hit an ambiguous Fit selection test selector, fixed by scoping the test to Viewport presentation; no product change was needed.

All three sizes verified drawing buffers: Performance 802×494, Balanced/Auto 1234×760, High 1542×950. Settings change pixel workload/effects, not geometry. Per-mode samples are bounded observations, not repeated statistical claims of quality-mode FPS improvement.

## Interaction and visual regression

`functional.json` and screenshots: real screen-pick selection; three frontend camera requests returned successful completion receipts in approximately 353–360 ms. Selection-to-render receipt samples were approximately 26–112 ms, including browser automation/IPC overhead; these are not pure device input latency. The early camera moveEnd field can be null because that event is not the operation's completion receipt; functional checks instead use the real existing completion callback.

A clearly labeled **synthetic renderer overlay, not engineering evidence**, rendered and cleared. Both conceptual column and endpoint beam previews appeared; real renderer receipts enabled Apply, Cancel removed the preview and active Apply control, and neither Apply nor Save was invoked in browser tests. Proposal validation responses were explicitly mocked for these synthetic UI tests. They do not prove live assistant/provider authorization or genuine backend result authority. Current saved-result identity and approval contracts were covered by focused existing tests; a complete real saved-engineering-result end-to-end acceptance was not repeated or claimed.

Hardware WEBGL_lose_context loss and actual reconstruction passed on the 400-component scene; `hardware-context-lost.png` and `hardware-400.png` document it. Assistant-open hardware screenshot shows the model and accurate disabled-AI status. Final functional runs have zero page errors, unexpected blocked app requests or downloads. The first functional run asserted availability before the async reply and was corrected to wait for the actual disabled status.

`tests.log`: **98 tests / 12 files passed**, including exact transforms/orientations, geometry, supervised primitives/beams, editor undo/redo and explicit Save boundaries, stale/protected/duplicate proposals, camera/mouse controls, assistant receipts and structural/foundation display. TypeScript and scoped ESLint passed. Backend/engineering code unchanged, so no backend/solver suite was run. Reused the prior successful isolated Webpack build after verifying unchanged sources; no new build or default Turbopack qualification is implied.

## Memory investigation — stability remains open

The earlier ~143MB versus ~307MB values were individual `performance.memory` snapshots with different allocation/GC history; they do not establish a twofold retained-heap regression. Current controlled Runtime heap measurements separate loaded and disposed states and use forced collection.

1. `memory.json`: six project-switch cycles plus final disposal, GPU/resource hooks, WeakRef scene/context tracking and debugger Entity/EntityCollection/Event enumeration. Loaded geometry contained 5,200 Cesium entities for 400 components; after each disposal, **zero entities and zero EntityCollections** remained. Cached pick-anchor entity references were therefore not persistently retained in those checks. Destroyed scenes and contexts appeared to accumulate; disposal heap 32.24→66.97MB.
2. `memory-control.json`: six cycles without WebGL timer/resource hooks, but with debugger object enumeration, showed similar growth. That ruled out those GPU hooks alone, not all measurement artifacts.
3. `retainer-path.json`: a selected destroyed scene disappeared after debugger object groups were released and a full snapshot collected it. `retainer-path-dom.json` similarly collected a selected detached canvas. A stable strong root was not demonstrated for either selected object; debugger enumeration influenced the evidence. Full snapshots were processed/discarded in memory, never written as heap dumps.
4. `memory-clean.json`: six cycles, **no render/WebGL hooks, WeakRef tracking or object enumeration**, actual UI wheel interaction, same two synthetic projects. Loaded heap **112.17–121.48MB**; disposal heap **31.16–38.04MB**. Disposal DOM nodes grew 1,633→4,983 and listener count 1,092→2,000 (warm-up included). Five live dashboard marketing preview canvases explain five live canvases after leaving the editor; zero Cesium canvases remain.
5. `memory-snapshot.json`: independent four-cycle clean control with full snapshot collection at every sampling point, discarding snapshot contents. Loaded heap **112.26–119.86MB**, disposal heap **31.12–37.03MB**, final DOM nodes 4,222/listeners 1,892. Thus ordinary GC variation and debugging explain part of the first apparent growth, but do **not** justify declaring full stability. A smaller residual upward trend persists even with fuller collection.

Read-only lifecycle review: CesiumView removes projected-pick and collection listeners, transform handlers, ghost/sandbox primitives; viewer teardown destroys the viewer and clears data-source ownership. Graphics binding disconnects ResizeObserver and removes resize/orientation/context listeners. Existing Three/R3F gallery disposal has delayed teardown. These code paths and tests are evidence, not proof that every native GPU resource is immediately reclaimed. Wrapper create/delete balances are diagnostic estimates, not a native GPU-memory measurement.

**Finding:** the old 2× snapshot difference is not reproduced as 2× retained geometry memory. Geometry/entity cleanup works in the checked cycles. However, post-navigation heap/DOM/listener growth remains reproducible over bounded cycles; its precise strong retainer and long-run slope are unresolved. Do not call this a proven unbounded Cesium leak, or claim a memory-stability PASS. Further focused retention/longer-soak investigation is required before memory sign-off. No speculative application fix, framework upgrade, cache purge or renderer rewrite was made.

## Isolation and original-data preservation

Synthetic fixture API 8003 rejects all writes; copied frontend 3017 uses the previously isolated Webpack output. Browser routes reject external app requests, unexpected exports/downloads and non-GET requests, except the exact mocked preview-validation endpoint used by the functional harness. That endpoint never reaches the API. No solver, real Firebase, cloud, paid Nebius request or engineering/accounting write was made. Runtime guard disables inference/auth activation, excludes credentials and blocks external Node network/DNS and output outside local test directories. Retained guard logs include denied Playwright global-cache marker writes, not successful changes.

`preservation.json`: exact Milestone12 schemas and row hashes match **10,283 development rows and 3 assistant-history rows**; prior application source hashes, manifests/lockfile, backend requirements, normal launchers and ten original static fixtures unchanged. Fresh `preservation-files.json`/`preservation-audit.json`: **55,296 storage files, 2,090 proof files, 66 live database schemas, 198 archive-only fingerprints**, zero changed/missing original files. The older backup's 14 pre-existing row additions are documented and preserved. `coupled-evidence-preservation.json`: **21 solver artifacts unchanged**, without numerical execution. No archive extraction, restore, migration, deletion, Git, dependencies, cloud configuration or deployment.

## Manual owner verification and remaining limits

For a normal user session, open `chrome://gpu` and inspect Graphics Feature Status: WebGL/WebGL2 should report hardware acceleration. Privately inspect the active renderer in that page; SwiftShader/software/basic-render paths are not a hardware pass. Do not publish the full GPU/device/driver report. Open the guarded synthetic workspace, use Chrome Task Manager/Windows Task Manager to observe the browser GPU process/3D engine during camera movement, and repeat the same scene/settings; do not force flags or drivers. If a different session uses software, check `chrome://settings/system` graphics-acceleration setting and normal supported Windows driver configuration manually; no settings were changed here.

Longer natural-GC soak, exact residual DOM/listener ownership, real VRAM/OS utilization, normal-profile/browser/driver coverage and production-scale CAD remain unqualified. No equivalent physical before baseline exists. Firebase/inference stay disabled, normal Node22/launchers stay unchanged, and default Turbopack remains outside this qualification. Stop after verification. **Public launch remains BLOCKED; memory sign-off is also withheld.**

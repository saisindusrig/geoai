# GPU performance phase — local implementation and verification

Local implementation PASS. Physical-GPU performance qualification remains OPEN. Public launch remains BLOCKED by existing security/cloud gates. No normal Node/runtime transition, deployment or service activation.

## Rendering audit

The actual `/projects/[id]/workspace` uses Cesium 1.142.0, with stable WebGL2 and browser-managed GPU/driver selection. Three 0.184.0 constructs CPU-side component meshes and transforms before Cesium upload. Geometry positions use existing Earth-fixed/ENU transforms; no precision, geometry, identifiers or source hashes changed. Native Cesium frustum culling remains enabled. Existing flat terrain, source material styles, component primitives, edge entities, picking, clipping and saved engineering overlays remain authoritative. The separate SandboxGrid uses React Three Fiber 9.6.1; it and legacy `/model` are unchanged. WebGPU remains future work.

The reproducible bottleneck was forced continuous scene rendering (`requestRenderMode=false`), also imposed by SunStudyControls. Every rendered frame scanned all edge and anchor entities for pick anchors. Work increases with component count; per-component draw submissions remain. No GPU timer query, physical driver profile or evidence justified a risky instancing/LOD/geometry change. No batching, simplification or new graphics dependencies were added.

## Source changes

- `frontend/lib/workspace-graphics.ts`: presentation-only controller; on-demand rendering, bounded drawing buffer, resize/orientation observers, context loss/recreation and listener cleanup.
- `frontend/components/map/CesiumView.tsx`: use controller only in the editor; Auto/High/Balanced/Performance UI, cached component-anchor candidates invalidated by entity collection changes, clear loss/recovery/retry states and missing-WebGL guidance. Existing viewer lifecycle recreates GPU resources after restoration; editor draft stays in its existing owner. Recovery refits the camera rather than guaranteeing the previous camera pose.
- `frontend/components/map/SunStudyControls.tsx`: stop overriding the editor controller's resolution/render mode. Existing explicit sun/shadow controls and one-second sun-readout redraw remain, explaining approximately one idle frame per second.
- `frontend/lib/workspace-graphics.test.tsx`: bounded settings, resize, loss, restoration, no updates while lost, and disposed subscription tests.

Auto bounds the buffer by viewport pixel area (1.4M target, scale 0.65–1). Balanced uses scale 1, Performance 0.65, High 1.25 plus FXAA/shadows. Browser-recommended resolution avoids multiplying by devicePixelRatio. These are transparent display choices, not measured GPU-capability detection or an FPS-adaptive controller. No hardware fingerprint, persistent preference, telemetry or API write. Explicit sun-study settings can still change shadows. Controls were placed below the camera gizmo after screenshot review detected overlap.

## Synthetic before/after benchmark

Installed Chrome with `--use-angle=swiftshader`, portable Node 24.22.1, isolated Webpack production build, 1280×900, identical synthetic component counts/category distribution. Each case fits the camera, waits three seconds, measures three idle seconds and approximately two seconds of deterministic orbit. Original models are never used or modified. Before and after are sequential single-run samples; no statistical significance or physical-GPU conclusion.

| Components | Idle rendered frames | Idle draw calls | Fewer idle calls | Orbit FPS before → after |
|---|---|---|---|---|
| 10 | 68 → 3 | 1,020 → 45 | 95.6% | 35.5 → 33.5 |
| 100 | 63 → 3 | 6,615 → 315 | 95.2% | 31.9 → 34.8 |
| 400 | 47 → 3 | 19,035 → 1,215 | 93.6% | 30.6 → 32.9 |

See `before-benchmark.json`, `after-benchmark.json`, `comparison.json` and executable `benchmark.cjs`. Triangle values count submitted triangle-mode instances across frames/passes, not unique mesh triangles. CPU submission times are preRender→postRender wall times, not GPU execution times. Ready times include explicit fit/settling and are not pure parsing times. No reliable load-time or orbit-FPS improvement is claimed. Heap snapshots vary with allocations and GC: the final large after sample is about 307MB versus 143MB before; these snapshots do not establish a leak or a memory improvement. Physical GPU memory, long-run leak/soak and hardware/browser matrix remain unqualified.

Performance mode measured an 802×494 drawing buffer versus Auto's 1234×760 in the same viewport (~58% fewer pixels), without changing components. This reduces pixel workload; it does not prove an equivalent FPS improvement.

## Focused verification

- 69 tests in 12 files passed (`tests.log`): transforms, geometry, beam proposals, framing, structural/foundation display, assistant receipts/UI, supervised approval controls and login.
- 13 further mouse-control/desktop-gate tests passed (`interaction-tests.log`). Total 82. Apply/Save, cancellation, undo/redo and freshness safety are covered by existing focused mocked/unit boundaries; no new save or original-model mutation was used as proof.
- TypeScript and scoped ESLint passed; explicit portable Node24 `next build --webpack` passed. Final cosmetic placement was rebuilt and rechecked. Default Turbopack and normal Node22 remain unqualified, unchanged.
- `browser.json`: homepage, local login, Firebase unavailable, disabled registration, dashboard, diagnostics, workspace and disabled assistant at 1280×900, 1600×900, 390×900. Desktop 3D remains visible with assistant open. Mobile correctly retains existing Desktop Required gate rather than claiming mobile editing.
- `after-benchmark.json`: actual component screen-pick selection, enabled Fit selection, camera focus, resize, quality buffer change, real WEBGL_lose_context loss message and successful reconstruction. Browser page errors and unexpected requests/downloads/writes: zero in final checks. Quality/loss event details and screenshots retained.
- High-DPI browser check (`hidpi/browser.json` and log) passed at 1600 CSS pixels and devicePixelRatio 2: actual canvas width 1548 equals CSS width 1548, no automatic 2× multiplier.
- Diagnostics payload is explicitly synthetic; no numerical engine probe or solver execution. Assistant inference and Firebase remain disabled. Backend unchanged, so backend suite not repeated. No real engineering result recalculation or inference acceptance occurred.

## Isolation and preservation

All API access is read-only to existing isolated beam fixtures on 8003 with required marker; no writes accepted. Frontend on 3017 uses copied sources/public assets and installed dependencies via junctions. Browser rejects external origins, exports, unexpected paths and all writes. Node guard restricts runtime, network and output locations; it excludes credentials and blocks external DNS. `guard-events.jsonl` retains denied Next registry lookup / Playwright global cache-marker attempts and early harness setup denials; these were not granted network/global-write access. Earlier mobile timeout was a test assumption about the existing desktop gate and was corrected; no product gate was bypassed. Earlier idle mode conflict and failed recovery check are preserved in logs/debug evidence, followed by successful final verification.

`preservation.json`: exact current Milestone12 baseline matches for 10,283 development DB rows and 3 assistant-history rows, including schema/accounting. `preservation-files.json`: all 55,296 original storage and 2,090 proof files unchanged. Fresh archive comparison verifies 66 live schemas and 198 retained archive-only fingerprints; retained backup read in place, never extracted/restored. The old backup's 14 pre-existing additions are documented in `milestone-preservation.json`, not changes from this phase. `coupled-evidence-preservation.json` verifies 21 solver artifacts. `runtime-preservation.json` confirms original package/lockfile, backend requirements, startup launchers and all ten original static fixture inputs match retained pre-test hashes. No migration, original fixture overwrite, CAD/result/authorization/history/accounting mutation, new dependency or launcher change. Source checksums are in `changed-source-hashes.json`.

## Remaining limitations and stop

Physical-GPU qualification, GPU timings/memory, repeated statistical runs, long-lived memory soak, more drivers/browsers and production-scale CAD are still required before claiming universal GPU performance. Browser/OS chooses physical acceleration; this code cannot force a working driver. High mode may cost more. Per-component draw calls and continuous explicit animations remain; no unverified instancing or LOD shortcut. Existing engineering overlays/preview approval contracts remain; this phase does not independently recertify every result method or perform real Save writes. Legacy `/model` Cesium issue remains documented, outside scope.

No paid inference, Firebase/cloud activation, installs, Git operations, agents, solver execution, deployment or destructive cleanup. Stop after this phase; launch remains BLOCKED.

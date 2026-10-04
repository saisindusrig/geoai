# Advanced engineering workspace: implementation status

The complete supplied specification is **not yet accepted**. This implementation establishes terrain/evidence safety, adds owned engineering persistence and APIs, and connects sun/camera controls. The remaining product features below must be completed before calling the upgrade finished.

## Implemented and verified

- Unavailable terrain samples remain `null`; a neutral ellipsoid is visibly labelled **TERRAIN UNAVAILABLE**. Terrain initializes independently of the buildings layer.
- Rendering never automatically samples terrain to relocate a model. Saved revision placements supply the root anchor; otherwise the document origin remains a visual, unplaced anchor.
- Owned APIs store and inspect explicit placements, ground samples, independent checkpoint runs, residuals, analyses, preferences, cameras, audits, and spatial export manifests.
- Terrain activation preserves coordinates, keeps absolute placements valid, marks ground-relative placements for review, and invalidates dependent samples/analyses. Returning to an older version also requires review.
- Saving a new model revision preserves its accepted root anchor and marks analyses of superseded geometry stale; result payloads remain intact. An origin edit marks the inherited placement for review.
- Readiness requires resolved spatial metadata and independent validation. Imagery resolution cannot promote accuracy. Missing, failed, excluded and adjustment-only checkpoints remain visible in validation results.
- Horizontal RMSE uses both east and north residuals; vertical residuals compare same-reference XYZ observations. Datum separation is not treated as vertical error.
- Terrain versions are appended rather than overwritten by the version-creation API. Unresolved datum/unit conversions block activation.
- Authoritative sampling and chainage calculations use PostGIS. SQLite returns explicit unsupported/unknown results and still opens existing projects.
- Late OSM building loads are discarded after cancellation; missing read credentials and failed providers have visible states.
- Legacy imports reject missing CRS rather than assuming one. Raw LAS/LAZ is reference-only. Legacy cut/fill has no invented uncertainty band or default design elevation.
- Sun study uses the installed Cesium astronomical model and UTC clock, editable IANA timezone, date/time, playback speed, seasonal date shortcuts, azimuth/elevation and daylight readout. DST gaps and ambiguous local times are rejected.
- Shadow quality is Off/Balanced/High. Design models, editable entities and sandbox primitives cast/receive shadows. Shadow completeness is explicitly partial because trees and occluder coverage are not verified.
- Scene preset/quality controls and sun preferences persist for saved project models. Quality changes keep vertical exaggeration at 1×.
- Named camera records preserve world position, orientation and projection. Camera shortcuts and saved-view controls are available in the Scene / Sun study panel.
- Grid drag cancellation restores geometry and orbit controls on Escape, blur, pointer cancellation, lost capture, tool changes and unmount. Text inputs ignore the Escape transform shortcut.
- Sandbox editing, undo, autosave, grid/map switching and JSON backups remain functional and make no sandbox project API requests.
- Overlapping camera flights cannot report an early-ready scene; a browser regression checks the camera reaches the actual project location and visual inspection confirms the placed component over satellite imagery.

## Configuration and deployment

Set `CESIUM_ION_READ_TOKEN` in the backend environment to a restricted browser read token, with only required asset access and allowed application origins. Runtime configuration exposes this key only. `CESIUM_ION_WRITE_TOKEN` and the legacy `CESIUM_ION_TOKEN` are never returned to the browser. Existing installations that only configured the legacy key must explicitly configure the read key.

Public imagery can work without ion. This does not enable elevation terrain or OSM 3D buildings and does not establish engineering accuracy.

Production engineering operations require PostgreSQL with PostGIS and the `postgis_raster` extension. Run `alembic upgrade head` to apply migration `006`. Its spatial raster table is `engineering_terrain_rasters`; coverage checks use `ST_Covers`, ground sampling uses `ST_Value`, and profile stations use projected PostGIS geometry. SQLite migrations create evidence tables without pretending to implement these spatial operations.

The versioned raster table has no connected production GeoTIFF processing/import path yet. An ion terrain reference alone cannot supply authoritative server-side ground samples; those stay unknown until matching survey raster data is processed and loaded. Non-ellipsoidal/unit conversions also require a verified transformation pipeline; they are currently blocked, not guessed.

## Remaining acceptance work

- Complete and test the authoritative GeoTIFF import/processing pipeline, datum/unit transformations, coverage-aware world/survey fusion and terrain-version immutability at the database boundary.
- Connect seam QA and terrain-difference calculations to accepted datasets, map heatmaps and verified coverage-area statistics.
- Complete constraint imports/versioning, support checks, cross sections, conflict detection, analysis dependency invalidation on constraint edits, and linked profile/viewport UI. Current analysis math and profile API are foundations; all these workflows are not implemented.
- Complete the searchable grouped layer manager, survey/checkpoint inspection UI, guided import wizard, discrete project-readiness summary and backend-fed engineering dock.
- Migrate legacy 2D drawing tools to Cesium before removing the existing MapLibre drawing path. The workspace is not yet exclusively Cesium for all tools.
- Complete geographic move/rotate/scale gizmos, pivot/axis modes, typed active transforms, clipping/section tools and visual model revision comparison.
- Expand scene presets to control all technical overlays, survey residuals and clipping; current presets primarily configure lighting. Adaptive LOD currently covers globe/resolution, not every context/analysis layer.
- Complete sunlight persistence for all workspace states, verified occluder completeness, exact astronomical solstice/equinox instants rather than seasonal date shortcuts, and all camera target/projection round trips.
- Enforce checkpoint provenance against the exact terrain version and resolved datum, include missing observations from all required independent checkpoints, and prevent self-reported evidence from authorizing engineering readiness without server verification.
- Complete audit coverage for anchor unlocks, datum/constraint changes, checkpoint exclusions, revision restores and analysis exports; current operations record audits but the full required event set is not connected.
- Resolve project deletion/retention explicitly. A proposed automatic cascade deleting engineering evidence and audits was rejected by automatic approval review and was not applied. Projects with retained engineering records now return an explicit conflict instead of deleting evidence or failing with a database foreign-key error. Reading a workspace does not create a preferences record; only user edits autosave preferences.
- Run PostGIS integration tests with real survey rasters and browser acceptance checks with configured read-only ion assets. This machine currently has SQLite, no configured ion read token and no accepted survey dataset, so engineering-grade accuracy and realistic terrain/building shadows cannot be validated here.

## Verification

Full backend suite: 160 passed, 1 skipped; after the final revision-anchor change, all 12 focused revision/engineering API tests passed. Full frontend unit suite: 79 passed. TypeScript and lint passed. Three isolated Chrome browser checks cover sandbox editing/persistence/backups, drag undo/cancellation, terrain unavailability, timezone/UTC conversion, sun playback, scene quality, actual camera framing and shadow controls. In-app browser automation could not start because of the Windows sandbox ACL error; repository Playwright tests used an isolated browser profile.

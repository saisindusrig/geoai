# Repository disk audit — 2026-10-04

> Follow-up — 2026-10-04: At the user's request, the old `.netlify` directories, `netlify.toml`, and `render.yaml` were subsequently removed. Old Git history and hosting configuration were backed up under `.git-history-backup/2026-10-04/` (ignored by Git). The project now uses a fresh initial `main` commit for `saisindusrig/geoai`; an archived local branch preserves the old commits and the linked worktree remains intact. The measurements and preservation statements below describe the earlier disk-audit snapshot.

Initial file-content size: 5,661.749 MB (5,661,749,154 bytes); 93,745 files; no enumeration errors.
Sizes are logical file bytes, not NTFS allocated clusters. Parent directory totals overlap; do not add rows. Root excluded from directory ranking. Existing user changes are preserved.

## 30 largest directories

| PATH | SIZE | CATEGORY |
|---|---:|---|
| frontend | 4,680.510 MB (4,680,510,127 bytes) | SOURCE / REQUIRED |
| frontend/.next | 3,428.359 MB (3,428,358,654 bytes) | BUILD OUTPUT |
| frontend/.next/dev | 3,390.670 MB (3,390,670,065 bytes) | BUILD OUTPUT |
| frontend/.next/dev/cache | 3,019.229 MB (3,019,228,788 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94 | 3,019.229 MB (3,019,228,684 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack | 3,019.229 MB (3,019,228,684 bytes) | CACHE / TEMPORARY |
| frontend/node_modules | 1,041.373 MB (1,041,372,578 bytes) | DEPENDENCY |
| backend | 932.815 MB (932,815,267 bytes) | SOURCE / REQUIRED |
| backend/.venv | 715.296 MB (715,296,411 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages | 710.966 MB (710,965,553 bytes) | DEPENDENCY |
| backend/.venv/Lib | 710.966 MB (710,965,553 bytes) | DEPENDENCY |
| frontend/.next/dev/static | 212.487 MB (212,487,308 bytes) | BUILD OUTPUT |
| frontend/.next/dev/static/chunks | 211.901 MB (211,900,928 bytes) | BUILD OUTPUT |
| backend/.venv-civicspan | 210.086 MB (210,085,660 bytes) | DEPENDENCY |
| backend/.venv-civicspan/Lib/site-packages | 206.632 MB (206,631,932 bytes) | DEPENDENCY |
| backend/.venv-civicspan/Lib | 206.632 MB (206,631,932 bytes) | DEPENDENCY |
| frontend/.next/dev/server | 155.484 MB (155,484,043 bytes) | BUILD OUTPUT |
| frontend/node_modules/next | 155.223 MB (155,223,289 bytes) | DEPENDENCY |
| frontend/node_modules/next/dist | 154.985 MB (154,985,063 bytes) | DEPENDENCY |
| frontend/.next/dev/server/chunks/ssr | 154.474 MB (154,474,216 bytes) | BUILD OUTPUT |
| frontend/.next/dev/server/chunks | 154.474 MB (154,474,216 bytes) | BUILD OUTPUT |
| frontend/node_modules/@next | 136.974 MB (136,973,825 bytes) | DEPENDENCY |
| frontend/node_modules/@next/swc-win32-x64-msvc | 136.859 MB (136,859,141 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages/scipy | 115.250 MB (115,250,088 bytes) | DEPENDENCY |
| frontend/node_modules/next/dist/compiled | 108.242 MB (108,241,746 bytes) | DEPENDENCY |
| frontend/public | 105.316 MB (105,315,926 bytes) | PROJECT DATA |
| frontend/.netlify | 98.738 MB (98,737,652 bytes) | UNKNOWN — REVIEW REQUIRED |
| frontend/node_modules/cesium | 79.386 MB (79,386,396 bytes) | DEPENDENCY |
| frontend/public/models | 74.027 MB (74,027,156 bytes) | PROJECT DATA |
| frontend/node_modules/cesium/Build | 69.963 MB (69,962,962 bytes) | DEPENDENCY |

## 30 largest files

| PATH | SIZE | CATEGORY |
|---|---:|---|
| frontend/.next/dev/cache/turbopack/f37fad94/00004645.sst | 262.754 MB (262,754,394 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005396.sst | 259.846 MB (259,846,341 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00004554.sst | 259.352 MB (259,351,984 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00004649.sst | 258.222 MB (258,221,931 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00000566.sst | 258.172 MB (258,171,731 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00000508.sst | 256.783 MB (256,782,788 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00000413.sst | 254.867 MB (254,867,387 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00004555.sst | 188.238 MB (188,237,770 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00004650.sst | 171.655 MB (171,655,326 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00004646.sst | 171.375 MB (171,375,357 bytes) | CACHE / TEMPORARY |
| frontend/node_modules/@next/swc-win32-x64-msvc/next-swc.win32-x64-msvc.node | 136.859 MB (136,858,624 bytes) | DEPENDENCY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005399.sst | 123.528 MB (123,528,443 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005395.sst | 72.745 MB (72,744,976 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005401.sst | 62.923 MB (62,922,819 bytes) | CACHE / TEMPORARY |
| frontend/public/models/dummy-arch-bridge.glb | 47.365 MB (47,365,264 bytes) | PROJECT DATA |
| frontend/.next/dev/cache/turbopack/f37fad94/00005530.sst | 35.102 MB (35,101,783 bytes) | CACHE / TEMPORARY |
| backend/.venv/Lib/site-packages/rasterio.libs/gdal-360e5d11b6a02621294737b98153f3c0.dll | 23.064 MB (23,064,064 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages/pyogrio.libs/gdal-9fa6a5301668010b1474299a888c26da.dll | 21.924 MB (21,924,352 bytes) | DEPENDENCY |
| backend/.venv-civicspan/Lib/site-packages/numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll | 20.589 MB (20,589,056 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-63c857e738469261263c764a36be9436.dll | 20.415 MB (20,415,488 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages/scipy.libs/libscipy_openblas-64eda39e79589aedb16f58e5547eb599.dll | 20.261 MB (20,260,864 bytes) | DEPENDENCY |
| frontend/node_modules/@img/sharp-win32-x64/lib/libvips-42.dll | 19.113 MB (19,112,960 bytes) | DEPENDENCY |
| backend/.venv/Lib/site-packages/fiona.libs/gdal-3105cd430966b2574784cc5837b520a5.dll | 19.099 MB (19,098,624 bytes) | DEPENDENCY |
| frontend/public/models/earth_16k.glb | 17.999 MB (17,999,372 bytes) | PROJECT DATA |
| frontend/.netlify/static/models/earth_16k.glb | 17.999 MB (17,999,372 bytes) | BUILD OUTPUT |
| frontend/node_modules/cesium/Build/CesiumUnminified/Cesium.js | 15.820 MB (15,819,856 bytes) | DEPENDENCY |
| .git/objects/a6/779affbc65524e54f13e19b5d66832002c2336 | 15.626 MB (15,626,153 bytes) | SOURCE / REQUIRED |
| frontend/.next/dev/cache/turbopack/f37fad94/00005495.sst | 15.419 MB (15,418,726 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005535.sst | 14.702 MB (14,701,964 bytes) | CACHE / TEMPORARY |
| frontend/.next/dev/cache/turbopack/f37fad94/00005441.sst | 14.651 MB (14,651,439 bytes) | CACHE / TEMPORARY |

## Cleanup plan (recorded before deletion)

| PATH | SIZE | CATEGORY | SAFE TO DELETE? | REGENERATABLE? | HOW TO RECREATE | RECOMMENDATION |
|---|---:|---|---|---|---|---|
| frontend/.next | 3,428.359 MB (3,428,358,654 bytes) | BUILD OUTPUT | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | npm run dev / npm run build from frontend | Delete |
| frontend/test-results | 3.752 MB (3,751,556 bytes) | TEST OUTPUT | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | npm run test:e2e from frontend | Delete |
| backend/.pytest_cache | 0.016 MB (15,800 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/tests/__pycache__ | 0.895 MB (894,558 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/api/routes/__pycache__ | 0.359 MB (359,448 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/design/__pycache__ | 0.262 MB (261,907 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/ai/__pycache__ | 0.221 MB (221,165 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/__pycache__ | 0.146 MB (145,759 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/survey/__pycache__ | 0.135 MB (135,012 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/db/__pycache__ | 0.092 MB (92,190 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/alembic/versions/__pycache__ | 0.072 MB (71,643 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/core/__pycache__ | 0.061 MB (61,257 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/exports/__pycache__ | 0.053 MB (53,463 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/geospatial/__pycache__ | 0.051 MB (51,088 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/civicspan_tests/__pycache__ | 0.041 MB (41,035 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/scripts/__pycache__ | 0.024 MB (24,168 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/services/calculations/__pycache__ | 0.024 MB (24,138 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/__pycache__ | 0.011 MB (11,255 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/middleware/__pycache__ | 0.011 MB (11,015 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/__pycache__ | 0.007 MB (6,648 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/workers/__pycache__ | 0.006 MB (5,844 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/alembic/__pycache__ | 0.004 MB (4,284 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| backend/app/api/__pycache__ | 0.000 MB (286 bytes) | CACHE / TEMPORARY | Yes, once relevant processes stop and tracked-file/reparse checks pass | Yes | Python imports / python -m pytest from backend | Delete |
| frontend/node_modules | 1,041.373 MB (1,041,372,578 bytes) | DEPENDENCY | No in this task | Yes | npm ci (package.json and package-lock.json exist) | Preserve: reinstalling restores essentially the same size |
| backend/.venv | 715.296 MB (715,296,411 bytes) | DEPENDENCY | No in this task | Uncertain / not applicable | python -m venv .venv; pip install -r requirements.txt | Preserve: unpinned versions and native geospatial wheels make exact reconstruction uncertain |
| backend/.venv-civicspan | 210.086 MB (210,085,660 bytes) | DEPENDENCY | No in this task | Uncertain / not applicable | python -m venv .venv-civicspan; pip install -r requirements-civicspan.txt | Preserve: installed extras and exact versions not fully captured |
| frontend/.netlify | 98.738 MB (98,737,652 bytes) | UNKNOWN — REVIEW REQUIRED | No in this task | Uncertain / not applicable | Netlify build, but plugin/state provenance not fully established | Preserve for manual review |
| .netlify | 0.001 MB (1,253 bytes) | UNKNOWN — REVIEW REQUIRED | No in this task | Uncertain / not applicable | Linked site state/configuration | Preserve |
| frontend/public | 105.316 MB (105,315,926 bytes) | PROJECT DATA | No in this task | Uncertain / not applicable | Not guaranteed | Preserve all models, textures, videos and runtime assets |
| backend/storage | 3.319 MB (3,319,032 bytes) | PROJECT DATA | No in this task | Uncertain / not applicable | Not guaranteed | Preserve surveys, terrain, uploads and generated exports |
| .git | 47.797 MB (47,797,015 bytes) | SOURCE / REQUIRED | No in this task | Uncertain / not applicable | Not applicable | Preserve all history; read-only audit only |
| backend/dev.db | 0.754 MB (753,664 bytes) | DATABASE | No | No | Restore from verified backup only | Preserve |
| backend/planning.db | 0.000 MB (0 bytes) | DATABASE | No | No | Restore from verified backup only | Preserve |

## Dataset and special-file inventory

All matching project files below are preserved, including generated exports. Dependency/build copies excluded.

| PATH | SIZE | CATEGORY |
|---|---:|---|
| frontend/public/models/dummy-arch-bridge.glb | 47.365 MB (47,365,264 bytes) | PROJECT DATA |
| frontend/public/models/earth_16k.glb | 17.999 MB (17,999,372 bytes) | PROJECT DATA |
| frontend/public/models/road_street.glb | 3.593 MB (3,592,988 bytes) | PROJECT DATA |
| frontend/public/models/simple_satellite_low_poly_free.glb | 3.049 MB (3,049,428 bytes) | PROJECT DATA |
| frontend/public/models/fluffy_cloud.glb | 2.020 MB (2,020,104 bytes) | PROJECT DATA |
| backend/dev.db | 0.754 MB (753,664 bytes) | DATABASE |
| backend/storage/projects/2/scenario_4/model.glb | 0.075 MB (74,716 bytes) | PROJECT DATA |
| backend/storage/projects/2/scenario_16/model.glb | 0.075 MB (74,716 bytes) | PROJECT DATA |
| backend/storage/projects/2/scenario_17/model.glb | 0.075 MB (74,716 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_5/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_3/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_9/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_2/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_8/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_7/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_6/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_5/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_1/model.glb | 0.067 MB (67,220 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_90/preview.glb | 0.058 MB (57,912 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_89/preview.glb | 0.058 MB (57,912 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_89/model.glb | 0.057 MB (56,640 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_90/model.glb | 0.057 MB (56,640 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_4/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_5/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_7/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_8/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_2/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_3/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_4/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/9/scenario_20/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_1/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_6/model.glb | 0.035 MB (35,284 bytes) | PROJECT DATA |
| backend/storage/projects/127/scenario_102/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/277/scenario_219/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/114/scenario_92/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/100/scenario_79/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/264/scenario_209/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/250/scenario_199/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/179/scenario_142/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/251/scenario_199/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/192/scenario_152/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/209/scenario_167/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/22/scenario_19/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/223/scenario_179/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/236/scenario_189/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/237/scenario_189/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/166/scenario_132/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/290/scenario_229/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/153/scenario_122/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/48/scenario_39/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/9/scenario_9/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/140/scenario_112/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/74/scenario_59/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_9/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/61/scenario_49/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/8/scenario_9/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_9/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/35/scenario_29/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/87/scenario_69/preview.glb | 0.030 MB (30,304 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_19/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/206/scenario_163/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_166/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_12/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_11/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/205/scenario_162/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_14/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/207/scenario_164/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_10/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/290/scenario_229/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_15/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/208/scenario_165/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_178/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_13/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_18/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_91/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_9/model.glb | 0.030 MB (29,768 bytes) | PROJECT DATA |
| backend/storage/projects/222/scenario_177/preview.glb | 0.026 MB (26,400 bytes) | PROJECT DATA |
| backend/storage/projects/222/scenario_177/model.glb | 0.026 MB (25,624 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_9/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_5/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_3/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_5/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_6/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_8/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/7/scenario_7/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_2/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_1/excavation.glb | 0.022 MB (21,632 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_90/excavation.glb | 0.018 MB (18,472 bytes) | PROJECT DATA |
| backend/storage/projects/113/scenario_89/excavation.glb | 0.018 MB (18,472 bytes) | PROJECT DATA |
| backend/storage/projects/3/scenario_5/model.glb | 0.013 MB (12,672 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_1/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_5/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/9/scenario_20/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_4/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_4/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_2/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_3/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_6/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_7/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_8/excavation.glb | 0.011 MB (10,764 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_15/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/206/scenario_163/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/6/scenario_18/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/208/scenario_165/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_14/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/205/scenario_162/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_178/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/207/scenario_164/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_13/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_11/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_91/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_9/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/1/scenario_12/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_19/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_10/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/290/scenario_229/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/5/scenario_166/excavation.glb | 0.009 MB (9,184 bytes) | PROJECT DATA |
| backend/storage/projects/222/scenario_177/excavation.glb | 0.008 MB (7,932 bytes) | PROJECT DATA |
| backend/storage/projects/4/scenario_6/model.glb | 0.005 MB (5,260 bytes) | PROJECT DATA |
| backend/storage/projects/101/scenario_201/revision_2/model.glb | 0.004 MB (3,888 bytes) | PROJECT DATA |
| backend/storage/projects/101/scenario_201/revision_1/model.glb | 0.004 MB (3,888 bytes) | PROJECT DATA |
| backend/storage/projects/2/scenario_16/excavation.glb | 0.001 MB (1,316 bytes) | PROJECT DATA |
| backend/storage/projects/2/scenario_17/excavation.glb | 0.001 MB (1,316 bytes) | PROJECT DATA |
| backend/planning.db | 0.000 MB (0 bytes) | DATABASE |

## Git audit

```text
count: 1327
size: 42.02 MiB
in-pack: 818
packs: 1
size-pack: 656.35 KiB
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```

All-object scan includes reachable and unreachable loose/packed objects. Largest blob sizes below are uncompressed; they are not additive to working-tree sizes. No history rewrite, prune, GC, or object deletion.

| BLOB | UNCOMPRESSED SIZE | PATH / STATUS |
|---|---:|---|
| 13e0edf30eec892307ec727d1a50eb71057c1736 | 47.365 MB (47,365,264 bytes) | frontend/public/models/dummy-arch-bridge.glb |
| a6779affbc65524e54f13e19b5d66832002c2336 | 17.999 MB (17,999,372 bytes) | frontend/public/models/earth_16k.glb |
| 62d55275ee7d28b3623eb1efd1ab83b1e3bf2115 | 3.593 MB (3,592,988 bytes) | frontend/public/models/road_street.glb |
| 7c7dc935afa82fd2e4db6ad91ce9c94f7d8c1195 | 3.049 MB (3,049,428 bytes) | frontend/public/models/simple_satellite_low_poly_free.glb |
| bb5c850b4885ebefd25f885cc7b455f73f5cf553 | 2.494 MB (2,494,086 bytes) | frontend/public/textures/coast_sand_rocks_02/textures/coast_sand_rocks_02_nor_gl_1k.exr |
| 9da599826ddeb567b2a92de5c2776982740217c3 | 2.306 MB (2,305,562 bytes) | frontend/public/textures/coast_sand_rocks_02/textures/coast_sand_rocks_02_disp_1k.png |
| f36daf462c517d7619f0501bdf31c2ef5ade330d | 2.201 MB (2,201,020 bytes) | frontend/public/videos/hero-mall-loop.mp4 |
| cd0b2ebc7d484b250318585bf4e281eea2f83c60 | 2.020 MB (2,020,104 bytes) | frontend/public/models/fluffy_cloud.glb |
| b28d37cb26e38a28fb7e8e7483e73721f6299ca0 | 0.926 MB (925,874 bytes) | frontend/public/textures/coast_sand_rocks_02/textures/coast_sand_rocks_02_rough_1k.exr |
| 1555f855db4c7492240478d60de25e1e275841b9 | 0.839 MB (839,184 bytes) | frontend/public/textures/coast_sand_rocks_02/textures/coast_sand_rocks_02_diff_1k.jpg |
| 56a5970217157cf28be7e7d1b6128b0e8f5f8d39 | 0.419 MB (419,454 bytes) | frontend/package-lock.json |
| 0bac08ecf982efe7fed0ad927af9c241c0293eec | 0.415 MB (415,456 bytes) | frontend/package-lock.json |
| 769995d220f5fc941f4f55cd878e998d6fc5f392 | 0.379 MB (378,812 bytes) | frontend/package-lock.json |
| 1b6b5f75d1ca0c91a15e6297494bd03bfdb64598 | 0.273 MB (272,975 bytes) | frontend/package-lock.json |
| d020c5b44b317449616eb7b52e8418f5e231ad87 | 0.230 MB (230,087 bytes) | frontend/public/textures/coast_sand_rocks_02/coast_sand_rocks_02_1k.blend |

Git occupies only 47.797 MB and is not responsible for multi-gigabyte usage. Large model/media blobs are future review candidates only; required assets must stay available. Unmapped objects require manual provenance review.

## Verification

- TypeScript: `tsc --noEmit --incremental false` passed after `next typegen`.
- Lint: `npm run lint` passed.
- Frontend unit tests: 31 files, 142 tests passed.
- Backend tests: 188 passed, 1 skipped; CivicSpan tests: 5 passed. One dependency deprecation warning in each suite. Suites run separately because both contain a module named test_civicspan.py. A temporary source copy was used, with no original .env, databases, or storage. Initialized the temporary database because some tests bypass the lifespan fixture.
- Frontend restarted on port 3000; GET / returned HTTP 200. Existing backend on port 8001: GET /openapi.json returned HTTP 200.
- Dependencies were not removed, so no reinstall was needed.
- E2E browser suite and production build were not run; frontend unit tests and development startup were verified.
- Preservation hashes: 1,777 files checked; none missing; only the authorized .gitignore change differs. Includes original databases, assets, data and configuration. Dependency and Git internals excluded from hash comparison.
- Scoped ignore rules added for secondary Python environment, lint/tool caches, build output and coverage. Model/source paths checked to remain unignored.
- Existing user source changes and deleted files were left untouched.


## Final measurement

- Original: 5.662 GB (5.273 GiB; 5,661,749,154 bytes)
- After cleanup and startup: 2.400 GB (2.235 GiB; 2,400,146,424 bytes)
- Net recovered: 3.262 GB (3.038 GiB; 3,261,602,730 bytes) (57.6%).
- Final scan: 89,013 files; no errors; no reparse directories skipped.
- Measurement uses logical file bytes, not NTFS allocated clusters. The development server remains running, so cache size can grow again. Report edits after the snapshot add a few KB.

## Largest remaining directories

| PATH | SIZE (MB) | CATEGORY |
|---|---:|---|
| frontend | 1,421.371 | SOURCE / REQUIRED |
| frontend/node_modules | 1,041.373 | DEPENDENCY |
| backend | 930.323 | SOURCE / REQUIRED |
| backend/.venv | 715.296 | DEPENDENCY |
| backend/.venv/Lib/site-packages | 710.966 | DEPENDENCY |
| backend/.venv/Lib | 710.966 | DEPENDENCY |
| backend/.venv-civicspan | 210.086 | DEPENDENCY |
| backend/.venv-civicspan/Lib/site-packages | 206.632 | DEPENDENCY |
| backend/.venv-civicspan/Lib | 206.632 | DEPENDENCY |
| frontend/.next | 172.971 | BUILD OUTPUT |
| frontend/.next/dev | 172.955 | BUILD OUTPUT |
| frontend/node_modules/next | 155.223 | DEPENDENCY |
| frontend/node_modules/next/dist | 154.985 | DEPENDENCY |
| frontend/.next/dev/cache | 137.081 | BUILD OUTPUT |
| frontend/.next/dev/cache/turbopack/f37fad94 | 137.081 | BUILD OUTPUT |

## Deleted directories

- `frontend/.next`
- `frontend/test-results`
- `backend/.pytest_cache`
- `backend/tests/__pycache__`
- `backend/app/api/routes/__pycache__`
- `backend/app/services/design/__pycache__`
- `backend/app/services/ai/__pycache__`
- `backend/app/services/__pycache__`
- `backend/app/services/survey/__pycache__`
- `backend/app/db/__pycache__`
- `backend/alembic/versions/__pycache__`
- `backend/app/core/__pycache__`
- `backend/app/services/exports/__pycache__`
- `backend/app/services/geospatial/__pycache__`
- `backend/civicspan_tests/__pycache__`
- `backend/scripts/__pycache__`
- `backend/app/services/calculations/__pycache__`
- `backend/app/__pycache__`
- `backend/app/middleware/__pycache__`
- `backend/__pycache__`
- `backend/app/workers/__pycache__`
- `backend/alembic/__pycache__`
- `backend/app/api/__pycache__`

The `.next` directory was regenerated by type generation and the startup smoke check. Deleted 23 classified directories; no dependency environment or dataset was deleted.

## Deliberately preserved and manual review

- All source, migrations, manifests, lockfiles, configuration and pre-existing work.
- Both SQLite databases, all backend/storage uploads and exports, GeoJSON/DXF/survey/terrain content, and every model, texture, video and required Cesium runtime asset.
- Frontend node_modules, both backend environments and all Git history.
- frontend/.netlify (98.738 MB) and root .netlify remain: examine generated deployment payload separately from state/configuration before future cleanup.
- Python requirements use version ranges and the CivicSpan environment contains packages beyond its minimal manifest; retain environments until exact reconstruction is documented.
- Historical model blobs listed above may be considered for future LFS/history planning, but .git is small and no rewrite is warranted for this cleanup.
- No first-party top-level dist/build/coverage/playwright-report/.turbo/.cache/.mypy_cache/.ruff_cache/htmlcov cleanup targets were found in the initial inventory. Names occurring inside dependencies remain dependencies.

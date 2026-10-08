# Stage 1 foundation (Steps 1–3)

This batch freezes common contracts, blocks direct AI reply mutations, and installs additive database storage. The later site retrieval, persistent conversation behavior, tool orchestration, proposal/build services and specialist generators are outside this batch.

## Reused application state

`Project` remains the owner of the boundary. Terrain dataset versions, active terrain configuration, `GroundSample`, the existing readiness function, `ModelRevision`, `ModelPlacement`, Engineering Dock checks and generation jobs remain authoritative. Site profile tables hold references/snapshots only. Cesium and the workspace layout are unchanged. The existing approved `BuildingPlan` workflow remains the current building feature; the new general proposal tables have no writer yet.

The Assistant has two rendered components. `AssistantPanel` and `ModernAssistantPanel` now treat all provider-suggested geometry commands as a proposal request. The backend `/ai/chat` and `/ai/chat/stream` responses strip executable model commands too, so an older client cannot apply an AI reply directly. Existing read-only site analysis, layer and download actions remain available. The explicit manual editor, parameter form, and manual regenerate control remain separate. `submit_proposal_command` is a fail-closed service seam until the proposal service is built.

## Contracts

Pydantic source: `backend/app/domain/stage1.py`. Regenerate and verify `frontend/lib/generated/stage1.ts` and `docs/contracts/stage1.schema.json` with `cd backend && python scripts/export_stage1_contracts.py [--check]`. Types cover typed known/unknown facts, CRS and vertical datum, five site selection forms, source-specific evidence, missing information, capability registry, generic multi-asset civil intent, dependency manifests, validation, approval and proposal-only commands.

The registry has independent DISCUSS, PLAN, PROPOSE, GENERATE, VALIDATE_GEOMETRY and ANALYZE capability levels. Unknown civil asset names are retained and discussable. The foundation intentionally advertises no executable proposal or generator: current building generation exists through its older explicitly approved workflow. Capability promotion requires implementing and testing the corresponding service. Civil intent accepts multiple distinct asset requests; it does not depend on a building schema.

Unknown elevation is `null` with a reason. Public map/assumed facts cannot become validated engineering input through a label. Survey source alone remains unverified without validation evidence. Image resolution is never a measurement-accuracy method.

## Persistence and deployment

Migrations 008 and 009 add 28 project-scoped Stage 1 tables and explicit placement elevation state. New immutable histories have SQL update/delete guards on PostgreSQL and SQLite. Mutable lifecycle status uses separate rows. New nested references have project-scoped foreign keys; SQLite has guard triggers even if a legacy connection lacks `PRAGMA foreign_keys=ON`. `site_selection_versions.canonical_geometry` is PostGIS `geometry(Geometry,4326)` with a GiST index and spatial checks in production; SQLite stores bounded JSON snapshots for demo use. SQLite does not provide PostGIS spatial query or engineering readiness parity.

**Before upgrading an existing installation, take a consistent database backup and confirm recovery.** The local `backend/dev.db` was backed up as an ignored `backend/stage1-pre-migration-*.db` file before upgrading to revision 009. Both new migration downgrades deliberately raise an error because dropping histories or forcing `NULL` elevations to zero would discard information. Restore a verified pre-upgrade backup if rollback is required. The backups should be retained according to the project's storage policy and never committed.

`anchor_elevation` is now nullable and has `elevation_resolution` plus `elevation_provenance_json`:

- A matching accepted valid/stale ground sample with matching coordinates, elevation and vertical reference is `RESOLVED`, including a genuine 0 m value. An explicitly accepted placement with matching audit proof and vertical reference is also `RESOLVED` as a recorded value; this does not grant survey readiness.
- A `NULL` stays `UNKNOWN`. A 0 m value becomes `NULL` only when the saved revision explicitly says `elevation_known=false`, the placement is marked legacy and no vertical reference or contradictory evidence exists. The old numeric value is preserved in audit provenance.
- Other old values, including ambiguous zero and nonzero values, are `LEGACY_UNRESOLVED`. Their numeric display transform stays stored; the placement API returns `elevation: null` for engineering use and an explicitly named `legacy_display_elevation` for preserving its visual placement. Model geometry, heading, offset, transform and revision are untouched. The frontend rejects null for engineering calculations and does not replace it with zero.
- Newly accepted placements write `RESOLVED` plus source provenance.

New foundation tables are installed by Alembic. An application startup cannot silently create them on an unversioned database. Existing legacy tables still use their startup compatibility behavior. A caller must validate nested references with the project-scoped ownership service before later Stage 1 write APIs are added.

## Validation and remaining work

Focused tests cover contracts, unknowns, CRS, five selection variants, evidence, arbitrary/multiple assets, capability denial, AI reply safety, existing manual regeneration, isolated 007→009 migrations, legacy elevation classifications, transforms, nested ownership, immutable histories and PostgreSQL DDL compilation. PostgreSQL migration execution requires an empty disposable database provided through `STAGE1_TEST_POSTGRES_URL`; generated DDL compilation does not count as a live PostGIS test.

The existing local demo database has historical foreign-key violations in `usage_events` and `audit_logs`; the upgrade adds none in Stage 1 tables. Repairing those older records is separate data maintenance and is not silently part of this migration. Next work begins at Stage 1 Step 4, site profile retrieval and derivation, followed by conversation and memory services, proposal lifecycle, controlled tools, Nebius orchestration and the building vertical slice.

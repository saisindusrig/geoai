# Phase 4A — Offline parametric BIM assembly authoring

## Acceptance boundary

This phase implements deterministic, structured-data authoring and offline native proofs. There is no live model client, assistant tool registration, orchestration queue, new asset executor, automatic approval, production CAD switch, or workspace change. Geometry validity is separate from engineering adequacy. Every demonstrated candidate remains engineering `UNVERIFIED` with unresolved support and clearance conditions and finalization blocked.

## 1. Existing supported CAD/BIM capabilities

The audit covered `bim-project/1`, `cad-geometry/1`, the CAD mapping and worker, BIM parameter propagation, CAD workspace revision services, ModelRouter/Assistant, proposal lifecycle, capability registry and frozen site context. The existing worker executes profile extrusion (rectangular and I sections), circular columns, rectangular openings, circular holes and rectangular lofts. Its artifact validation checks native results, B-rep validity, mesh integrity and content hashes.

The authoring allowlist exposes only these component/recipe pairs:

- BEAM and GIRDER: profile extrusion or rectangular loft.
- COLUMN and PIER: circular column, profile extrusion or rectangular loft.
- SLAB and DECK: rectangular opening or rectangular profile extrusion.
- BRACING: profile extrusion; placement supports planar heading, not arbitrary three-dimensional inclination.
- PLATE: circular hole or rectangular profile extrusion.
- BEARING: rectangular profile extrusion as a geometric representation only.

Other names in the broader BIM vocabulary do not grant executable capabilities. The machine-readable capability descriptor includes exact recipe parameter names, supported profiles, dimensional rules and budgets. COPY is the only exposed parameter dependency; unresolved dependencies are rejected. Geometry uses metres and local ENU placement; heading uses degrees. Existing legacy BOX descriptors are marked `NOT_EXECUTED`; the authoring pipeline derives and compiles native recipes, without using boxes as replacement geometry.

## 2. AI BIM authoring contract

`backend/app/domain/bim_authoring.py` defines strict, extra-field-forbidding contracts: `bim-authoring-intent/1`, `bim-assembly-plan/1`, `bim-assembly-expansion/1`, `bim-assembly-relationships/1` and combined `bim-authoring/1`. The checked-in JSON Schema is `docs/contracts/bim-authoring.schema.json`.

They reuse existing materials, sections, parameters, placement, constraints, dependencies and native recipes. They represent requested systems, multiple semantic assets, parent assemblies, component groups and roles, explicit component identities, assumptions, typed unknowns, requested selection/object references, connection intent and clearance intent. Model data cannot supply authoritative project/source/approval/provenance/geometry-validation fields or Python, JavaScript or CAD scripts.

## 3. Hierarchical authoring architecture

`stage_packet()` creates deterministic bounded packets with exact output JSON Schema and capability data. UNDERSTAND consumes request text; PLAN consumes validated intent; EXPAND consumes one planned assembly and shared definitions; RELATE consumes validated component reference summaries. Strict validation follows each stage. Preparation validates the complete bundle, composes parent translations/headings into existing BIM assembly placement, validates the existing BIM foundation and derives the existing CAD contract. Review is a separate result.

Bounds: eight requested systems/assets, sixteen assemblies, eight components per assembly, sixty-four components globally, 250 KB complete authoring input, 24 KB stage packets and a conservative weighted compilation budget of 128. Existing worker limits remain 30 seconds wall time, 20 CPU seconds, 1024 MiB memory and two local process slots. The offline proof invokes this separate subprocess worker explicitly; preparation/proposal creation never invokes it.

## 4. Component and assembly vocabulary

Assets retain the user's semantic type, including unregistered types. Assembly IDs, parent IDs, roles and planned groups organize supported components without granting an asset-specific executor. Shared materials, profiles and recipe mappings are reused across bridge and platform fixtures. Semantic bearing blocks and planar bracing members carry no bearing mechanics, joint design or structural analysis claims.

## 5. Validator implementation

`backend/app/experimental/bim_authoring.py` checks strict schema, hashes linking stages, duplicate IDs across semantic namespaces, group counts/roles/types, hierarchy membership/cycles, material and section references, parameter units/dimensions, exact recipe allowlists, requested references against frozen context, server selection policy, constraint applicability, dependency references/cycles and COPY value agreement. It checks total/component/stage/compilation budgets.

Structural members require explicit supported-by intent reaching a declared unknown foundation; other exposed members require connection intent. Support cycles, dangling/self references and omitted support are rejected. Every component requires unresolved clearance coverage. Authored resolved status cannot bypass these conditions. Terrain, soil, loads, foundations, clearances, code compliance, vertical datum and engineering approval remain unknown. AREA-based conceptual bridges additionally retain unknown crossing conditions.

## 6–8. Supported demonstrations

The explicit native proof compiled all four supported cases using the existing OCCT worker:

- Conceptual bridge: one asset, thirteen components, five assemblies; four circular piers, four bearing representations, two I girders, two rectangular diaphragms and a deck with an opening.
- Industrial platform: one asset, twelve components, three assemblies; four columns, two primary beams, two secondary beams, opening slab, drilled plate and two planar bracing members.
- Mixed project: two independently identified assets, twenty-five components and eight assemblies. Shared materials/sections are reused; the platform root is translated twenty metres from the bridge root.
- Unregistered observation structure: twelve components assembled from the same platform definitions and mappings, without adding a specialist or capability registration.

Each native component returned valid single-solid geometry. B-rep/mesh artifact hashes and byte counts were verified before artifact bytes were discarded. Synthetic fixture metrics are saved locally at `backend/.cad-proof-output/4a-authoring-demonstrations.json`; this is ignored verification evidence, not published CAD. Dependency tests verify 5 m to 6 m COPY regeneration and unchanged definition preservation. Hierarchy tests verify rotated/transformed child placement.

## 9. Unsupported-feature behavior

Reinforcement-cage requests return an explicit unsupported-feature diagnostic and no partial native build. Invalid dimensions, material references, dependency cycles and omitted support return rejected reviews. Invalid mappings, unsupported components, omitted clearances and hostile authoritative/script fields are also tested. Diagnostic responses do not echo arbitrary executable input.

## 10. Proposal review integration

`proposal_summary()` provides requested structure, assets, hierarchical assemblies/groups, component dimensions/materials/recipes, assumptions, missing facts, unresolved connections/clearances, geometry status and engineering status. Geometry status remains `CONTRACT_VALID_NATIVE_NOT_RUN` for normal offline proposals; only actual server-side native results can produce `NATIVE_GEOMETRY_VERIFIED` in diagnostic review.

`create_offline_proposal()` is a trusted internal function, not a new route or assistant tool. It uses ordinary `ProposalService` and CUSTOM asset review data, plus a private, hash-bound authoring/BIM/mapping/review snapshot. CUSTOM review does not grant production generation. No approval, native worker call or ModelRevision creation occurs here. Existing CAD finalization still rejects unresolved connections. If private snapshot persistence fails, the call fails; an ordinary review proposal may already exist, but this does not grant an executable authoring artifact or CAD approval.

## 11. Source/provenance safety

Owned context is frozen from the existing clean user message, current model revision, current site profile and selection. Object references must belong to the frozen selection and match current geometry hashes. Server-owned project/source/evidence identity is attached after model data validation. Candidate hashes bind authored data, derived geometry, source, selection/object/evidence references and the capability descriptor.

Snapshots use the existing private store and `cad-private:` content references, with hash verification and idempotency checks. Orphan detection now recognizes authoring snapshots. Ownership checks reject other users. Native proof revalidates candidates to reject mutated data before invoking the worker. No public artifact URL, cloud resource or production data was used.

## 12. Tests and files changed

Verification completed on Windows on 2026-10-10:

- Full backend: **908 passed, 2 skipped, 0 failed**, 255.67 seconds; three existing dependency/schema warnings. Skips: ownership comparison needs two seeded scenarios; dedicated PostgreSQL/PostGIS database is not configured.
- Focused authoring/CAD/BIM/AI3D/Building/Patch/ModelRevision regression: **224 passed, 0 failed**, 38.96 seconds; one dependency warning. This includes 44 new authoring tests.
- Frontend: **197 passed, 0 failed**, 41 test files.
- TypeScript `npx tsc --noEmit`: passed. ESLint with zero-warning threshold: passed.
- Native demonstration CLI: all four supported cases compiled; unsupported feature and four invalid cases rejected. Checked-in authoring JSON Schema matches the current Pydantic schema exactly.

Logs and JUnit evidence are under ignored `backend/.cad-proof-output/4a-*`. Backend regressions used isolated local storage and SQLite; the runner blocks real Nebius HTTP transports and disables configured cloud storage. No new browser test or production build was needed because Phase 4A changes no frontend code or UI wire contract.

The initial authoring test run had one fixture setup error (`site_db` was not imported); importing the existing fixture fixed it. No assertion or resource limit was weakened. Original local failure evidence is preserved in `.cad-proof-output/4a-authoring-first-failure.log`.

Phase 4A adds:

- `backend/app/domain/bim_authoring.py`
- `backend/app/experimental/bim_authoring.py`
- `backend/app/experimental/bim_authoring_fixtures.py`
- `backend/tests/test_bim_authoring.py`
- `backend/scripts/verify_bim_authoring.py`
- `docs/contracts/bim-authoring.schema.json`
- This report.

Phase 4A modifies only the authoring-snapshot recognition in `backend/app/experimental/cad_artifacts.py`. Pre-existing dirty work is preserved. Qwen PRIMARY, ModelRouter, AI3DDesign, Generic3DExecutor, Building/Patch, ModelRevision schema and frontend source are unchanged by this phase.

Reproduce the offline demonstrations with the pinned native dependencies available on PYTHONPATH:

```powershell
cd backend
$env:PYTHONPATH=(Join-Path $PWD '.cad-proof-deps')+';'+$PWD
.venv/Scripts/python.exe scripts/verify_bim_authoring.py --native-proof --export-schema
```

## 13. Remaining limitations

The packets and fixtures are deterministic offline boundaries, not a live orchestrator or evidence that a model reliably authors these schemas. No browser flow is added. Connection and clearance intent has no engineering resolver. Foundation sizing, loads, soil/terrain assessment, code compliance, reinforcement, joint mechanics, arbitrary 3D placement and unsupported recipe types remain outside this foundation. Native geometry proofs do not resolve site or engineering unknowns. Existing deployment licensing/redistribution and fleet recovery limitations remain unchanged. This phase's new authoring proofs were executed on Windows; the earlier Linux worker acceptance is not a new Linux run of Phase 4A.

## 14. Exact next step for live Qwen

In a separately authorized batch, add a default-off assistant adapter that freezes the existing owned source context and calls the existing, unchanged PRIMARY routing path with these bounded stage packets. Parse each response strictly into its stage contract, validate immediately, expand one assembly at a time and stop with explicit diagnostics on unsupported or invalid output. Bind the assembled candidate to the current source and feed the existing proposal review/private snapshot path. Native execution must remain a separate approved experimental action with renewed ownership/source/approval checks and unresolved engineering conditions enforced. First verify the adapter with recorded/mocked model responses; live Nebius acceptance requires separate authorization. Do not route an AI response directly to CAD Build.

Phase 4A stops at the offline foundation.

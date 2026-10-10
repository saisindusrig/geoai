# Phase 4B — Checkpointed Qwen BIM authoring, offline acceptance

## 1. Adapter architecture

`backend/app/experimental/bim_orchestration.py` connects the Phase 4A data contracts to the existing provider seam. It is accessible only through explicit human application commands under `/api/projects/{project_id}/experimental-cad/bim-authoring/runs`. Start saves a run without invoking a provider. GET reads progress. POST `/{run_id}/advance` advances one model stage, or saves the final review after all model stages are complete.

Authorization requires project ownership, the existing experimental CAD gate/user/project allowlists, plus `GEOAI_EXPERIMENTAL_BIM_AUTHORING=true`, `GEOAI_BIM_AUTHORING_USER_IDS` and `GEOAI_BIM_AUTHORING_PROJECT_IDS`. Missing/malformed configuration denies access. The new switch is off by default. Nothing is registered as a production executor or chat tool. No automatic approval, native geometry compilation or ModelRevision mutation occurs.

## 2. ModelRouter integration

Each model stage invokes existing `ModelRouter.route()` with DESIGN_REQUEST, PROPOSAL_ONLY, COMPLEX and engineering-sensitive metadata. This selects existing PRIMARY configuration, disables tool calling, preserves the router's 3,500 output-token cap and existing completion timeout (at most 120 seconds), and calls existing `NebiusProvider.complete()`. The provider and Qwen configuration are unchanged. Acceptance uses recorded fixture responses or a mocked `assistant_json` through the real provider seam; no Nebius transport was invokead.

## 3. Stage execution and checkpoints

UNDERSTAND → PLAN → EXPAND for each individual assembly → RELATE/VALIDATE → REVIEW. Phase 4A `stage_packet()` supplies the exact schema and supported capability descriptor. RELATE performs complete BIM/CAD validation before its output becomes a valid checkpoint. REVIEW revalidates and persists the proposal without another model request.

Runs reuse `GeneratedFile` and private content-addressed storage; no new conversation system or ModelRevision schema is introduced. A private snapshot holds frozen context, valid stage outputs and their hashes, and the final review. The catalog stores ownership/message/request identity, status, attempt counters and snapshot hash. Valid outputs are retained in subsequent snapshots. Reading verifies private bytes against their content hash. Failed outputs and provider error text are not persisted.

Each action commits a RUNNING claim and consumes an attempt before calling the provider. Duplicate active actions are rejected. Successful stages are never re-requested during retry. There are at most two attempts per model stage, and at most 38 model calls per run. Cancellation preserves prior valid checkpoints. An interrupted process has an unknown in-flight request outcome; after 150 seconds, an explicit `recover_interrupted=true` action can consume the remaining attempt. A successful response lost before checkpoint persistence may therefore be requested again; this is not exactly-once provider execution.

There is no durable worker, scheduler, unattended retry, lease renewer or background FastAPI task. Responses expose `durableWorkerAvailable=false` and `EXPLICIT_SINGLE_CHECKPOINT_ACTION`. The caller must advance the run explicitly. Recovery means resuming committed local checkpoints, not durable job execution. Superseded private run snapshots may appear as orphan candidates; existing inventory is conservative and does not delete them automatically.

## 4. Structured-output validation

Every response is parsed as a bounded JSON object and validated with its exact strict stage schema. Plan/intent hashes, assembly identity, group membership, component identity, supported mappings, material/section references, metre parameters and recipe dimensions are checked at the earliest available stage. Expansion checks cross-stage duplicate IDs and accumulated compile cost. Full reference/dependency/support/clearance validation is required before RELATE succeeds.

Stage output is bounded to 50 KB, frozen context to 16 KB, and the complete stage packet with trusted context to 40 KB. Phase 4A's eight-components-per-assembly, sixteen-assembly, sixty-four-component and weighted compilation bounds remain unchanged. Authoritative project/source/provenance/validation/approval fields remain forbidden in model data.

## 5. Capability handling

Only the existing BEAM, GIRDER, COLUMN, PIER, SLAB, DECK, BRACING, PLATE and BEARING mappings are exposed. The descriptor includes precise operations, profile parameter keys, dimension rules and placement limitations. A BEARING is a geometric representation, and BRACING has planar heading only. Reinforcement, tendon design, complex foundations, arbitrary 3D inclination and engineering analysis are not executable capabilities. Unregistered semantic assets can compose the same supported components without a new specialist.

## 6. Failure and repair

Malformed JSON, strict-schema failures, existing provider INVALID_RESPONSE, truncation, timeout and transient unavailability permit one subsequent stage-specific retry. This follows the existing assistant's two-attempt repair policy, but moves the second attempt to a separate explicit action. The repair packet includes a safe diagnostic code, never the invalid response or provider's raw error text.

Semantic failures (unsupported feature/mapping, invalid recipe dimensions, references/dependencies, source mismatch or missing required intent) stop the run. No server repair changes dimensions or invents engineering facts. Explicit instructions also prohibit the model's schema repair from fabricating inputs. Exhausted attempts stop. Storage failures preserve preceding checkpoints and grant no executable artifact. Diagnostics distinguish malformed JSON, output truncation, provider timeout, invalid dimensions, stale source/site/requirements and unsupported features.

## 7. Proposal-review integration

The existing Phase 4A `create_offline_proposal()` path saves through ordinary `ProposalService`, stores the private hash-bound authoring/BIM/mapping/review snapshot and attaches an ASSISTANT message with a normal PROPOSAL part to the original conversation. The conversation sequence is advanced so subsequent ordinary messages remain functional. No UI source change is required: existing Assistant and proposal-review components consume the existing message/proposal contract.

Geometry remains `CONTRACT_VALID_NATIVE_NOT_RUN`. All demonstrated proposals require review, remain engineering `UNVERIFIED` and have `finalizationBlocked=true`. Required support and clearance intent is preserved. Existing experimental CAD finalization policy is unchanged; these unresolved authoring proposals do not become approved native CAD builds.

## 8. Offline scenarios

- A: bridge, thirteen components and five expansions, saved proposal; eight model requests.
- B: platform, twelve components and three expansions, saved proposal; six model requests.
- C: mixed project, twenty-five components and eight expansions, saved proposal; eleven model requests.
- D: unregistered composition, twelve components and three expansions, saved proposal; six model requests.
- E: reinforcement request rejected during UNDERSTAND; no partial proposal or approval.
- F: malformed/schema-invalid/truncated responses consume at most two stage attempts; preceding checkpoints are retained. Provider timeout is also bounded and diagnosed.
- G: changed source revision, changed source document/site profile or changed accepted requirements rejected before provider execution. Changes during provider latency also prevent checkpoint publication.
- H: invalid component relationship rejected during RELATE validation; no saved proposal or approval. Invalid dimensions and mapping are rejected during EXPAND.

All successful acceptance runs explicitly prohibit native compiler calls and assert unchanged ModelRevision documents, no new ModelRevision and no approval records.

## 9. Authorization and provenance

The server freezes the owned clean user message, request, current revision and document hash, current site profile/selection version and payload, selected objects/evidence, relevant accepted requirement versions, explicit engineering unknowns and current capability descriptor. Relevant accepted memory uses the same global/selected-asset/proposal-asset scope as conversation capture. Changes to that accepted set invalidate the run. The complete frozen hash is compared before every model action and again after provider latency.

Strict schemas reject model-supplied project/source authority. Final preparation attaches existing server-owned provenance and rechecks the source at proposal persistence. Candidate/private snapshot hashes bind the result to the authoritative context. Run access requires the original authorized actor and project owner. Private checkpoint bytes are integrity-checked; corrupt storage fails closed. No public native artifact URL or cloud test resource is used.

## 10. Files changed in Phase 4B

- Added `backend/app/experimental/bim_orchestration.py`.
- Added `backend/tests/test_bim_orchestration.py`.
- Added this report.
- Modified `backend/app/api/routes/cad_experimental.py` to add the explicit start/read/advance commands and safe conflict diagnostics.
- Modified `backend/app/experimental/cad_artifacts.py` to recognize current private authoring-run snapshots in orphan inventory.

Pre-existing checkout changes are preserved. No frontend source, model configuration, ModelRouter, provider implementation, production executor, specialist, approval policy or ModelRevision schema was changed.

## 11. Verification

Final verification on Windows, 2026-10-10:

- Full backend: **936 passed, 2 skipped, 0 failed**, 276.17 seconds, three existing dependency/schema warnings. Skips: ownership comparison requires two seeded scenarios; dedicated PostgreSQL/PostGIS database is not configured.
- Seeded focused authoring/CAD/BIM/provider routing/AI3D/Building/Patch/ModelRevision suite: **249 passed, 0 failed**, 53.62 seconds, one dependency warning.
- Dedicated new authoring suite: **28 passed, 0 failed**, 9.73 seconds.
- Frontend: **197 passed, 0 failed**, 41 files, 73.76 seconds with one test worker and file parallelism disabled. Existing five-second timeout was retained.
- TypeScript and zero-warning lint: passed. Production Next build: passed; compilation 22.4 seconds, TypeScript 17.2 seconds and all fifteen static pages generated.

Original local logs are preserved under ignored `backend/.cad-proof-output/4b-*`; JUnit results are `4b-full.xml`, `4b-focused-seeded.xml` and `4b-unit.xml`. The offline backend runner blocks actual Nebius HTTP transports and disables configured cloud storage. No cloud resource or native artifact publication was used for authoring acceptance.

Initial validation found an incorrect test-fixture import and an overly specific stale-context assertion, both corrected without changing a safety gate. The first broad focused run recorded **242 passed, 5 failed**: those two test issues and three existing API tests whose in-memory SQLite harness lacked tables. The final harness uses fresh seeded file-backed SQLite. The first frontend run recorded **196 passed, 1 failed**: an unchanged scene-profiling test exceeded its five-second timeout during concurrent testing. Final verification reduces test parallelism without increasing that timeout. The restricted Next build stalled and was stopped using its verified process IDs before retrying with native subprocess access; user development servers were preserved. No application behavior was changed to bypass these verification failures.

## 12. Remaining blockers

Mocked acceptance is not evidence of live Qwen schema reliability, token sufficiency or useful semantic design. No durable background worker exists. In-flight remote completion outcomes cannot be recovered exactly once. Full native execution remains a separately approved experimental workflow, and unresolved connections/clearances have no engineering resolver. Existing licensing/redistribution and deployment recovery limitations remain. Phase 4B makes no engineering adequacy or compliance claim.

## 13. Live request count and maximum budget

For a small platform with three assemblies: six model requests normally, at most twelve with one retry at each stage, plus start/six stage advances/one review advance as explicit application actions. Maximum generated output is 21,000 tokens normally or 42,000 tokens with all retries. Each stage input is at most 40 KB; UTF-8 bytes provide a conservative 40,000-token input upper bound (the actual Qwen tokenizer count must be measured), plus message framing. The conservative twelve-request content bound is 480,000 input tokens plus 42,000 output tokens; it is a safety upper bound, not an expected bill or tokenizer measurement.

Each invocation uses the unchanged router timeout, at most 120 seconds; twelve invocations therefore allow at most 1,440 seconds of provider time across separate actions. A largest accepted sixteen-assembly run permits nineteen normal or thirty-eight maximum requests and 133,000 maximum output tokens. No monetary estimate is asserted without current provider pricing and measured input usage.

## 14. Next live Qwen acceptance step

Authorize a separate small live acceptance batch and explicitly configure isolated owned test project/user allowlists and both experimental switches. Keep production Build disabled. Use one current saved site/profile/revision and a three-assembly supported platform request. Start the run, advance one checkpoint at a time with the existing NebiusProvider, record route/usage/finish diagnostics without credentials or raw provider failure text, and verify a saved proposal with unresolved engineering intent and zero CAD/approval/ModelRevision mutation. Stop on semantic failure or the twelve-call ceiling; do not enlarge token/configuration limits automatically. Live native generation requires another explicitly approved experimental step after proposal and engineering-policy review.

STOP after Phase 4B. No live Nebius request was made in this batch.

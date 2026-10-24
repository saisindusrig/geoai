# Release security expansion and Phase A — pending source screenshots

**Shared/public launch remains BLOCKED. No launch or cloud activation performed.**

The two screenshots are not attached to this request or available in the searched attachment/workspace inventory. Their exact 1–40 wording and numbering cannot be reconstructed from topic summaries. No fabricated numbered matrix is supplied. Please attach both screenshots. Phase A was subsequently supplied by the user and incorporated below. Existing Milestone 12 evidence remains the starting point, not a new security certification.

## Safely completed

- Read-only inventory: `file-inventory.json` lists 51,576 scanned database, CAD/model and engineering-evidence files; `database-inventory.json` inventories 133 local database files and table counts. This covers the enumerated formats and solver-evidence directories, not every possible engineering format. Archived-only databases are retained under the existing preservation manifests rather than extracted.
- `synthetic-record-candidates.json` reports candidate internal user/project IDs with heuristic markers only, without exporting emails, credentials or project text. Names are not proof of synthetic provenance. Unclassified records are protected; no deletion list or automatic purge was created.
- Exact live database hashes/schemas match Milestone 12 entry: 10,283 application rows and three assistant-history rows. No accounting or conversation changes. See `preservation.json`.
- Existing preservation manifests freshly verified 55,296 original storage files, 2,090 proof files, 66 live schemas, 198 archived-only database fingerprints and 21 coupled solver artifacts. Historical 14-row additions in older baselines predate this work.
- Confirmed clean-data defect fixed: `backend/app/api/routes/projects.py:get_demo_project` previously called a development seeder without checking production mode. It now returns 404 in production/prod before invoking the seeder or committing. Development demo behavior is preserved. Synthetic regression tests: `backend/tests/test_release_clean_boundary.py`.
- `test_foundation_production_safety.py` readiness aggregation tests now mock supplemental storage/rate-backend probes instead of accidentally invoking real services. Initial run had seven failures because production storage correctly failed closed; `phase-a-tests.log` retains the failures. This is test isolation repair, not disabling storage safeguards. Final results are in `phase-a-final-tests.log`.
- Existing release-security and mocked Firebase tests: 76 passed (`focused-tests.log`). No inference or solver execution. Earlier Milestone 12 frontend/TypeScript/lint/browser evidence is retained; it is not represented as a fresh Phase A browser run.

## Clean production environment specification

No production infrastructure has been created. Prepare a NEW PostgreSQL/PostGIS database and NEW private object-storage namespace under separately approved staging/production identities. Never point these environments at `backend/dev.db`, `planning.db`, assistant-history.db, docs fixtures, release test databases, original storage, CAD proof output, archives or solver-evidence folders. Do not restore any development backup into production.

Start with zero user, project, model, evidence, conversation, usage and audit application records, except explicitly approved schema metadata/bootstrap administrative records. Bootstrap must use a separately reviewed identity/account-link approval transaction, not copying user IDs or bypassing ownership. Never rewrite historical local IDs or accounting. New production AI reservations require a qualified shared ledger, not a copied development ledger. Keep existing histories intact locally.

Only reviewed Alembic migrations may create/upgrade the new schema. Production `init_db` already checks schema/PostGIS and returns without create_all or startup demo seeding. The production demo endpoint is now also blocked. Explicitly inspect migrations/default data before execution; no migration was run here. Marketing bridge/demo assets may remain public display content but must not seed real user projects. Exclude fixtures, local DBs, CAD/solver artifacts, screenshots, .env/keys and archived backups from a future deployment package by an independently verified allowlist. No Git history inspection or operations were performed.

Release acceptance: query the NEW isolated environment for zero development/test IDs and zero imported ledger/history rows; verify private bucket listing is denied, signed access expires, cross-user file access fails, and all generated objects belong to the correct new project. Hash before/after artifacts and preserve the old environment untouched. An empty specification is not proof of an empty configured service.

## Exact Firebase prerequisites and account lifecycle

Reuse `backend/app/core/firebase_auth.py` and `backend/app/services/identity_links.py`. Official backend `firebase-admin` and frontend Firebase JS SDK must be separately approved and installed if absent; none was installed. Configure a real Firebase project, enable only reviewed sign-in providers, authorize the chosen staging domain and approved callback URLs, supply restricted server credentials through a secret store, and set exact FIREBASE_PROJECT_ID with AUTH_REQUIRE_JWT and the adapter flag. Never expose Admin credentials in NEXT_PUBLIC variables or browser bundles. Current adapter requires a credentials file; workload identity/ADC would require a separately reviewed adapter change, not an undocumented assumption.

Verify genuine ID tokens with the official SDK, correct issuer/audience/subject/time/signature and check_revoked=True. Revocation checking incurs an additional account-service network request per verification; certificate refresh also needs connectivity. Fail closed on errors, disabled/revoked accounts and unlinked identities. No email-only linking, automatic user merge or browser-supplied ID selection. Approve/provision the separate identity-link schema and an audited dual-identity ownership process; no public linking endpoint currently exists.

Real-service acceptance must include sign-in/out, persistence choices, expiry/refresh, password reset/email verification where enabled, disabled/deleted accounts, revocation, account recovery, admin removal, tenant/project mismatch, cross-user API/download/result/history denial and rollback without local-identity fallback. Session-cookie authentication is not implemented by token mocks: if added, require secure HttpOnly/SameSite cookies, CSRF defense and independent session lifecycle tests. Current local JWT password login is not genuine Firebase lifecycle qualification.

## Production guards and outstanding gaps

Existing code: `core/production.py` rejects development JWT bypass/default secrets/disabled limiter/unsafe CORS; `db/session.py` forbids production SQLite/fallback; `services/storage.py` rejects missing/unreachable production object storage; `services/rate_limit.py` refuses production memory fallback per request. Storage configuration does not prove private IAM. Shared Redis availability is currently rejected at request time, not an unconditional early startup requirement; retain this Phase A gap rather than claiming the requested startup invariant is complete. Explicit trusted-proxy configuration is also unqualified.

Nebius inference remains disabled. Local site_store accounting is not a qualified distributed budget. No offline fallback, paid retries, model escalation or enabling of live AI. Tool allowlists, frontend confirmation, source/revision hashes and manual Apply/Save remain. Numerical jobs are independent; uncertain attempts require renewed authorization and must not auto-retry. No numerical methods changed.

PostgreSQL/Cloud Storage staging prerequisites: approved isolated services/identities and cost boundary, restricted network/IAM, migration privileges separate from runtime, actual PostgreSQL driver/PostGIS/version qualification, private bucket with owner-authorized access. Existing storage is S3-compatible, not proof of native GCS support. Native GCS adaptation cannot be claimed complete.

Migration/restore procedure (not executed): create only a new synthetic staging database; record schema version; apply reviewed migrations explicitly; generate two synthetic users and owned projects; save revision/source hashes and authorized immutable evidence using approved test fixtures; capture backup and object manifests; restore to a second new isolated target; compare row counts/ownership/hashes/revisions/evidence and verify cross-user denial. Inject bounded connection/storage/worker failures, preserve uncertain-job status, require new numerical authorization, test duplicate saves and object/database reconciliation. Measure restore time/data-loss window. Never run this against originals or reuse an actual engineering authorization to rerun a solver.

## Pending 40-control deliverable

For EACH original screenshot control, the final matrix will retain its exact number/text and include: Implemented / Partial / Missing / Not applicable; exact function/config and line reference; test/evidence path and scope; remaining vulnerability or live qualification; launch-blocking decision with reason. Not applicable requires an evidenced absence of the feature, especially payments/cookies; no checkbox is called secure solely because a flag or mock exists. Server-side AI pricing exists separately from any customer billing workflow, so they must not be conflated.

No credentials were rotated, Git history purged, production accounts changed, or records deleted. No fresh dependency scan, live Firebase/cloud recovery, browser run or deployment qualification is claimed. Milestone 12 high-risk blockers remain: live identity/lifecycle, distributed isolation, restore/private storage, durable jobs, shared AI budgets, production TLS/CSP/proxies, parser/resource/dependency and monitoring qualification. Stop for review; next input required is both screenshots, then separate approval for any real service prerequisites.

## Screenshot transcription received — follow-up supersedes pending-source note

The user subsequently supplied `D:/STRUVOCIVIL_40_SECURITY_CONTROLS_CODEX.md`. The exact A01–A20/B01–B20 matrix is now delivered in [40-CONTROL-MATRIX.md](40-CONTROL-MATRIX.md), with [follow-up results](FOLLOW-UP-RESULTS.md). The earlier missing-screenshot note above is historical; no further screenshot upload is required for the supplied transcription. Launch remains BLOCKED.

## Phase B — affected controls updated

Local remediation and focused evidence are recorded in [Phase B RESULTS](../release-phase-b/RESULTS.md). The same 40-control artifacts now include changes to 12 affected rows only; original screenshot wording and the other 28 control assessments are preserved. Launch remains BLOCKED pending genuine staging qualification.

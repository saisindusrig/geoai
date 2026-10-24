# Screenshot-accurate 40-control follow-up — 23 October 2026

**Decision: BLOCKED for shared beta/public launch. Stop for human review.**

Delivered [40-CONTROL-MATRIX.md](40-CONTROL-MATRIX.md) and [machine-readable companion](40-CONTROL-MATRIX.json). The source document supplied by the user resolves the earlier missing numbering: A01–A20 and B01–B20 preserve each screenshot's original 1–20 sequence. Original wording is retained, including B20's `[end of screenshot text cropped]` annotation. This is a user-supplied transcription, not an independent pixel/OCR verification.

## Assessment

40 controls: **24 Partial, 7 Missing, 3 Unverified, 6 Not applicable; zero Implemented claims.** These are whole-control release assessments: individual local protections have passed tests, but their required production scope is not demonstrated. Every row records applicability, status, code/config, test/evidence, limitations, severity, launch effect and smallest safe next step. Conditional blockers explicitly describe when they apply.

The six N/A assessments are bounded to current reviewed architecture: public database key (A03), session cookies (A09/B19), cookie CSRF tokens (B02), customer payment webhooks/prices (B07/B08). The explicit bearer-token design still needs XSS/persistence/lifecycle qualification; it is not an assertion that all CSRF or session risks vanish. The 500-file source-pattern review found no active customer payment/webhook, application cookie session, password-reset or CAPTCHA integration in backend/app and frontend app/lib; pattern absence is not an exhaustive proof about infrastructure. See control-source-review.json. Nebius cost tables/reservations are assessed separately in B08/B10, not presented as customer billing.

Important risks are explicit: legacy registration returns a duplicate-email 409 (B05); legacy PBKDF2 work factor needs qualification (A10); Firebase reset/session revocation lifecycle is absent/unqualified (B03/B04/B12); bot and progressive account-aware abuse controls are missing (A12/B17); full script CSP, HTTPS, HSTS and trusted proxy policy remain unqualified (A18/A19/B01); uploads/native parsers lack complete ingress/work bounds (A16/B06/B11). No broad registration rewrite, arbitrary lockout, cookie retrofit, RLS policy or hashing migration was introduced under this follow-up.

No Git operations, secret-history purge or rotation occurred. A02 remains Unverified and blocking until approved human exposure review; lack of a scan is not proof of leaked credentials. Production database role grants/encryption cannot be verified from flags (A05/B20). Server-owned authorization remains required regardless of optional RLS.

## Focused changes and verification

No new application vulnerability fix was justified in this follow-up. The Phase A production demo-seeder rejection and its tests are retained, not repeated or recounted as a new fix. Existing 76 + 18 focused backend passes remain evidence with their original scope and logs. Milestone 12 frontend/TypeScript/lint/browser checks are reused; no new frontend or browser-run claim is made because application/frontend behavior was not changed here.

Four new non-destructive matrix integrity tests passed (`matrix-tests.log`): exact source wording/numbering/hash, forty unique complete rows with allowed statuses, preserved cropped annotation/BLOCKED disposition, and exactly forty Markdown control rows. `build_40_matrix.py` regenerates the artifacts without application startup/network. Code/source-pattern review is recorded separately; these tests verify document integrity, not security effectiveness.

## Preservation and clean production

Fresh read-only row/schema comparison in `preservation.json` matches the Milestone 12 entry: **10,283 application rows and three assistant-history rows**, unchanged. Fresh original file/archive-manifest comparison is recorded in `follow-up-file-preservation.log` and `preservation-audit.json`; original solver comparison in `follow-up-solver-preservation.log` verifies 21 artifacts. Phase A inventory remains 133 live local database files and 51,576 files within its enumerated CAD/model/database/evidence formats; archived-only database fingerprints are not extracted or counted as new live databases. Candidate synthetic IDs are heuristics, never deletion approval.

Production remains a specification, not a provisioned service: NEW isolated database, private storage and shared ledger with no copied development users/projects/history/accounting; explicit approved migrations; no dev bypass or demonstration seeding; marketing geometry separate from user projects. Preserve all historical development records and original IDs. See the existing RESULTS.md clean-production/Firebase/staging/restore procedures; they are not duplicated as a second architecture.

## Remaining release blockers and next approvals

1. Approve prerequisites for genuine Firebase SDK/project/provider configuration and audited identity linking, then qualify real sign-in, refresh, recovery, revocation/disabled accounts and multi-user isolation. No SDK installation, credentials/account change or Firebase activation done here.
2. Approve isolated PostgreSQL/PostGIS/private storage staging, separate runtime/migration/worker/backup least privilege, restore/hash/revision/evidence recovery and storage/IAM denial tests. Existing S3 compatibility does not prove native GCS operation.
3. Qualify durable jobs and atomic evidence publication plus shared transactional AI reservations/reconciliation. Keep inference disabled; uncertain numerical work needs renewed authorization, never automatic rerun.
4. Qualify TLS/HSTS/CSP/CORS/proxy deployment, ingress/parser limits, enumeration/account-abuse policy, fresh dependencies and monitoring/incident response. No localhost or mocked test can certify these.
5. Conduct approved secrets/exposure review with no public disclosure; any needed rotation/history action requires separate authorization.

Engineering suitability and numerical-method approval remain independent of software security. No solver execution, model/CAD/revision edits, account/usage writes, downloads, deployment, cloud billing, paid inference, migrations, cleanup or further milestone was performed. No GO issued.

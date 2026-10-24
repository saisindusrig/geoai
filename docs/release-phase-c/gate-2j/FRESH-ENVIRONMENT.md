# Gate 2J — fresh environment design, not provisioned

Use a completely new source artifact and data namespace. **Do not empty the existing website's databases or reinterpret cleanup as a production-data migration.** `fresh-environment-plan.json` is inert, with every initial application data count zero and runtime admission BLOCKED. The proposed root `D:\StruvoCivil-Staging\gate2j-proposed` was not created; its final location and permissions need approval.

## Source and dependency boundary

Prepare a reviewed source/assets artifact outside the development checkout, preserving StruvoCivil branding/homepage, Google/Email login UI, 3D renderer/editor/previews/approval rules, engineering methods and ownership/security checks. Copy **approved application source and public marketing assets only**, not databases, `.env`, secret files, developer profiles, test evidence, original CAD, solver records, conversations or ledgers. Build/runtime accounts must not inherit read access to the original checkout or backups. Do not run the existing normal launchers for this new environment; leave them unchanged.

Keep Next 16.4.2/React 19.2.4, Firebase browser 13.1.0/Admin 7.7.0 and the verified Node 24.22.1 contract. A future isolated toolchain/artifact delivery needs approval; pointing the new runtime back into `.local-tooling` inside the protected checkout would defeat its no-read boundary. No package installation/copy or launcher change happened here.

`dependency-accounting.json` records **47 frontend declarations, all with installed metadata**, **29 backend requirements, all installed and satisfying their declarations**, eleven Alembic revision files and static head **011**. Installed metadata is not a new runtime/engine/security qualification. Retain `backend/app`, migrations, canonical `asset-types.json`, frontend source/stores/hooks, public fonts/brand/3D assets, scripts and licensing/CAD notices. The prebuild catalogue synchronizer reads backend canonical data and writes `frontend/lib/asset-types.generated.json`; retain this dependency. The Cesium copy script needs the installed Cesium package and public workers/widgets/assets. Do not delete public assets as if they were compiler caches.

There are **ten existing build/test imports of historical engineering fixtures**, individually fingerprinted in `dependency-accounting.json`. They are test dependencies, not live user data. A fresh build boundary must replace/decouple those tests using separately reviewed synthetic fixtures or preserve them solely in a segregated historical test workspace; **do not copy historical engineering records into the fresh runtime**. This is a build-isolation blocker, not permission to modify numerical methods or delete tests.

## Empty schemas and data

Initial state: zero users, projects, UID links, revisions, saved results, CAD/drawings, assistant conversations, usage/accounting and audit rows. Install required schemas/indexes/foreign keys/immutable evidence guards with an approved migration role on a **new PostgreSQL/PostGIS database** only. Verify current migration head and migration-from-empty behavior before runtime start. Do not invoke `init_db()` in development mode to obtain tables: its dev path can create defaults/accounts/demo data.

The identity-link table lives in separate metadata and is **not installed by the current Alembic chain**. `identity_links.py` requires users, approval audits and links through the same database session. An approved explicit schema migration/link bootstrap remains necessary; do not attach an empty link DB to historical users. Leave all tables empty until a later approved bootstrap creates a new internal approver and authorized synthetic/staging identities with audit-bound UID links. Do not preload dev ID 1 or merge by email.

Use new private storage, assistant-history and usage/audit namespaces with no original data mounts or shared volumes. New Redis/rate-limit/job namespaces must not inherit local demo state. Existing `docker-compose.yml` uses named volumes `pgdata`, `redisdata`, `miniodata` and development settings; do not reuse that deployment unchanged. Exact endpoints, private credentials, resources, naming, ACLs and backup destinations remain unapproved.

Cloud Run's filesystem is not the proposed durable database/store. No cloud resource, database, container, volume or user was created. Private PostgreSQL/storage/shared limiter, backup/recovery and real service durability still require separate qualification; no mocked test establishes them.

## Fail-closed startup and no original reads

The proposed environment must run production semantics with enforced JWT/Firebase authorization and **no legacy login branch**, valid schemas, new private data paths and non-default secrets. While Firebase remains disabled/ADC blocked, staging runtime admission stays **BLOCKED**, not open under legacy auth. A static login/homepage build may remain disconnected; authenticated workspace access waits for approved identities and backend qualification. Both login methods and in-memory per-tab sessions remain in the retained code.

Existing controls provide useful boundaries: `db/session.py` rejects production SQLite and unavailable PostgreSQL; `init_db.py`'s production path checks PostGIS/current schema and returns before seeding; `/api/projects/demo` rejects production use. However, `security.py` still accepts legacy JWT when Firebase is disabled, and current production checks do not by themselves require the proposed Firebase-only staging mode. A separately reviewed startup admission/configuration policy is needed; **do not claim the current disabled application already meets that new runtime contract**. No auth behavior was changed here.

Required future admission checks: canonical approved new paths/DB identity, no overlap with originals, no reparse/junction/volume aliases, no original-data ACL grants, no root/back-end dotenv inheritance, no editable installation/PYTHONPATH into the old checkout, no development localhost database endpoint fallback, no shared existing compose volumes, and only an approved backend identity source. Reject before app imports/DB initialization; current app settings and engine initialization can otherwise run during import. Restrict mounts/filesystem permissions and network egress independently of application strings.

Eight offline tests in `test_isolation_plan.py` reject original paths, traversal, lookalike prefixes, relative/UNC/other-drive paths, reparse/inherited-access declarations, seeding, data copying and fallback. These validate the **plan's lexical admission contract only**. No new filesystem ACL, database role, network policy or running environment exists to prove actual access denial. Live no-read/least-privilege/backup tests remain BLOCKED until their isolated setup is explicitly approved.

## Approval sequence and recovery

1. Approve the exact new source/data/tooling root, source manifest and build/test-data boundary. Do not modify or migrate the original checkout/data. Verify no inherited mounts/permissions.
2. Separately approve new local or cloud resources/roles, explicit schema-from-empty migration and private backup/restore test using newly synthetic data only. Cloud/billing remains a separate gate; this plan grants none.
3. Review and implement no-seed/Firebase-only startup admission plus schema/link bootstrap under a separate scope; preserve existing development behavior. Run source/ownership/session regressions and prove denied access to the original data with the new restricted principal.
4. Independently approve current official Firebase configuration/identity use and bounded F01–F07. Gate 2I verified the owner-supplied app identifiers offline; it did not enable SDKs, backend ADC or accounts. Keep Nebius disabled and engineering jobs unauthorized throughout setup.
5. On failure, stop only the new environment's ingress/processes, preserve its evidence and reject restart until reviewed. Do not flip a reachable service into legacy authentication, restore over historical databases, discard ledgers or delete the original development data. New backups/rollback target the new environment only.

A fresh environment can be empty without losing existing work because the existing checkout and all its data remain separate, untouched and recoverable. **Nothing is provisioned or launched by Gate 2J.**

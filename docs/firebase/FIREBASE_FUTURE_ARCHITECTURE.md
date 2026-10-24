# StruvoCivil — Firebase future architecture

Design preparation only, reviewed 22–23 October 2026 (Asia/Kolkata). Firebase + Google Cloud is the planned platform. No project, billing account, credentials, SDK integration, deployment or data migration is created by this document. Shared private beta and engineering approval remain **Blocked**.

## Component boundary

```text
Browser / Cesium
   | sign-in -> Firebase Authentication [future]
   | HTTPS, verified identity context
   v
Firebase App Hosting: Next.js SSR / UI / controlled API routing [candidate]
   | explicit user ID token over HTTPS; no client-supplied internal user ID
   v
Cloud Run: existing FastAPI ownership / capability / proposal gates [candidate]
   |-- Cloud SQL PostgreSQL: users, project ownership, revisions, authorization,
   |                        job state, audit and immutable result identities
   |-- durable queue -> isolated OpenSees worker service / Cloud Run Job
   |                     -> checksummed immutable outputs and completion record
   `-- private Cloud Storage: CAD, drawings, solver evidence, reports

Optional later: bounded Firestore collaboration/presence projections.
                No authoritative solver/authorization writes from browser.
```

These are candidates to validate, not deployed resources or engineering-method changes. Firebase Hosting does not execute the Python/OpenSees service.

## Frontend hosting

Prefer evaluating Firebase App Hosting for this dynamic Next.js app. Google documents Next support and its managed Cloud Build/Cloud Run delivery path ([App Hosting](https://firebase.google.com/docs/app-hosting)). Compatibility with **StruvoCivil's selected Next 16.4.2**, adapter, Cesium workers/assets, SSR, protected routes, streaming, runtime secrets and API proxy must be tested before approval. Built-in framework support is not proof that this particular release/build works on that adapter.

App Hosting requires Blaze billing; enabling it is a separate user decision. Conventional Firebase Hosting is only an alternative if a future independently assessed frontend is genuinely static-exportable. StruvoCivil currently has dynamic project routes and API routing; do not silently remove SSR, auth, proxy or engineering features to force a static export. Compare options using the [official product comparison](https://firebase.google.com/docs/app-hosting/product-comparison). The current loopback rewrite must eventually become a fixed allowlisted HTTPS backend destination, with no user-controlled proxy target.

## Identity and existing ownership

Candidate: Firebase Authentication for sign-in, verified by the Python backend. Verify Firebase ID tokens server-side with a qualified Admin SDK integration, not client-decoded claims. Validate signature/key ID, issuer, project audience, expiration, issued/authentication times and nonempty subject. Ordinary token verification does not automatically check revocation; define and test revocation/disabled-user handling, cache bounds and key-fetch failure behavior ([verification requirements](https://firebase.google.com/docs/auth/admin/verify-id-tokens)).

Map verified `(issuer, uid)` to a unique stable internal user through an audited association table. Never accept an internal user ID, email match or project claim supplied by the browser as ownership authority. Existing per-project/model/result/download checks remain decisive. Custom roles/claims must be server-managed, least-privilege and refreshed/revoked through a documented policy; they do not replace ownership queries.

Do not replace legacy JWT/login yet. First test a feature-flagged identity adapter with isolated users, wrong issuer/audience/signature, expiry/revocation, cross-project rejection, deliberate account linking and rollback. Do not automatically merge accounts by email or renumber historical owner IDs. Compare memory/session-cookie approaches and CSRF/XSS protections before selecting token persistence; existing localStorage behavior is not automatically qualified for beta. Never log ID/access/refresh tokens or ship service-account keys to the browser.

## Python/OpenSees and job execution

Keep independently verified FastAPI methods and OpenSees outside the frontend runtime. Assess separate Cloud Run API and restricted worker containers, with Cloud Run Jobs as a run-to-completion option ([job execution](https://cloud.google.com/run/docs/execute/jobs)). Select a durable queue only after testing delivery, cancellation and failure semantics; Cloud Tasks or Pub/Sub are candidates, not configured integrations.

The future API must verify current owner, saved revision/source hashes, exact proposal authorization, supported method and load case before creating a job. Commit durable job identity atomically; use an idempotency key bound to authorized context. At-least-once delivery must never imply a second authorization or silently duplicate a solve. A worker revalidates the immutable authorized snapshot, executes only fixed supported commands, applies CPU/memory/time/concurrency limits and records terminal state. Read/status/manual Retry remains separate from mutation authorization.

Workers use isolated scratch directories; ephemeral container disks are not evidence storage. Publish checksummed outputs and manifests to private durable storage before atomically marking results accessible. Preserve failure evidence, source IDs, method/version/solver/executable provenance, signs and units. Qualify crash recovery, job retries, distributed locks, partial uploads and quotas before staging.

The existing Windows executable cannot simply be copied into a Linux container. Select a supported native binary/container and independently revalidate its exact numerical benchmarks, units, equilibrium, forces, displacements, mesh and hash/provenance behavior. No new FEA method or automatic physical connection assumption follows from moving runtimes.

## Relational records and immutable files

**First database candidate: Cloud SQL PostgreSQL**, because existing SQLAlchemy transactions, revision relationships and authorization chains are relational ([Cloud SQL overview](https://cloud.google.com/sql/docs/postgres/introduction)). Plan schema/migration compatibility, connection pooling/private access, backups, restore, precision, JSON ordering/hashes and transaction isolation on disposable data first. Preserve internal IDs and audit chains; define portable row comparisons before claiming equivalence across database engines.

Do not replace or combine the 264 baseline SQLite databases automatically. They include historical/test/evidence databases with different purposes. Inventory their ownership and retention requirements individually; migration of any original requires explicit authorization. Firestore is only a later candidate for bounded presence/collaboration projections. It is not assumed to be the principal engineering transactional store, and security rules do not substitute for backend authorization or solver validation.

Assess private Cloud Storage for original drawings, CAD files and immutable solver/report artifacts. Keep server-side tenant/owner checks, fixed object identities, checksums and artifact allowlists. Consider versioning and reviewed retention policies ([Object Versioning](https://cloud.google.com/storage/docs/object-versioning)); versioning alone is not a complete immutable backup/recovery policy. Eventual signed downloads need short expiry, exact object generation, minimal scope, authorization before issue and auditable access; URLs must not grant listing or cross-tenant prefixes. No public bucket or client authority to overwrite evidence. Test application ownership independently of infrastructure IAM.

## Cost and readiness

| Surface | Cost concern / guardrail to qualify | Current readiness |
|---|---|---|
| App Hosting | Blaze required; SSR/requests, cached and uncached egress, builds and retained images | Unverified; enablement Blocked |
| Firebase Authentication | Provider/usage-dependent charges and quotas; protect signup/sign-in abuse | Unverified; no live configuration |
| Cloud Run API/workers | CPU, memory, requests, idle/minimum instances, job duration, retry/concurrency bounds | Unverified; no containers deployed |
| Cloud SQL | Persistent instance/storage/backups and network cost, including idle capacity | Unverified; no database provisioned |
| Private Storage | Original + retained versions, operations, retrieval/egress and lifecycle | Unverified; no objects migrated |
| Build/operations | Cloud Build, Artifact Registry, logs, secrets, monitoring, queue and egress costs | Unverified; no resources created |

[App Hosting costs](https://firebase.google.com/docs/app-hosting/costs) describe the Blaze requirement and underlying billed services. No fixed monthly estimate is defensible without workload, region, retention, solver duration and traffic measurements. Budget alerts alone do **not** necessarily cap spending. Separately qualify supported spend caps, quotas, maximum instances, job limits and failure-safe responses; some controls trade availability for cost protection ([Cloud Billing budgets](https://cloud.google.com/billing/docs/how-to/budgets)). Never enable billing or assume every service has a hard cap as part of a local test.

No-charge strategy now: existing local offline website, synthetic in-memory fixtures, local storage, blocked external browser traffic and recorded contract tests. Future emulator or mock-adapter work requires its own dependency/identity scope; no emulators or SDKs are installed here. Original data stays local. Cloud staging and any live identity/key fetching require separate approval. Paid AI is not required; keep provider budgets disabled.

## Region and governance questions

Evaluate India-user latency, availability of each selected service/region, cross-region transfer, backup locations, residency and retention obligations before choosing regions. Do not assume that an App Hosting frontend region, CDN location, Auth processing location, SQL region and object storage location have identical residency guarantees. Define project access, deletion/retention conflicts, incident response, disaster recovery and applicable legal requirements with the responsible reviewers. No India region or compliance certification is selected automatically.

## Migration gates and rollback

1. **Security patch and local proof** â€” qualify patched dependencies/runtime and preserved originals. Rollback only to a reviewed secure version; an old vulnerable build is not an approved fallback.
2. **Isolated identity proof** â€” authorize synthetic identities/adapter tests; prove ownership and linking. Feature flag off restores existing local login without rewriting historical users.
3. **Durable database/storage restore drill** â€” authorize isolated representative copies, reconcile every record/object checksum and test recovery. Keep originals authoritative until an explicit cutover; never overwrite them during a rehearsal.
4. **Worker/job qualification** â€” approve exact container/solver versions and queue policy; independently validate numerics and duplicate/crash behavior. Route no original job automatically; rollback disables new submissions while retaining evidence.
5. **Staging hosting** â€” separately authorize project/billing/region/secrets, validate adapter/build/headers/proxy/cost controls using synthetic data. Roll back traffic/configuration without mutating source evidence.
6. **Limited private beta** â€” require all independent security, operations, recovery and scope gates, named reviewer approval and monitored limits. Maintain a tested rollback and explicit data cutover decision.

Each gate requires a separate reviewed decision. Application readiness never confers engineering safety/code approval, and unsupported engineering workflows remain disabled.


## Public domain preparation
Intended origin: `https://struvocivil.com`. DNS, TLS, Firebase authorized domains and callbacks remain unconfigured and unverified. Validate these separately before production use. Local API destinations stay unchanged.

Milestone 9.1 public identity: **StruvoCivil** — **Model. Analyze. Design.** The assistant is **StruvoCivil Assistant**. This documentation update does not configure Firebase or production authentication.


## Milestone 10 foundation (23 October 2026)

The disabled backend adapter and frontend mode-discovery boundary are now implemented; see [Milestone 10](../milestone-10/RESULTS.md). Neither `firebase-admin` nor the official browser `firebase` package is installed. No Firebase resources, credentials or live sign-in are configured. The identity-link schema is a separate metadata blueprint, not part of automatic database initialization; no original schema was migrated. Live sign-in and account linking remain blocked pending separate approval and qualification.


## Milestone 11 durability assessment

Local atomic publication, conservative recovery decisions and strict synthetic browser routing are prepared. Cloud persistence, durable job dispatch, shared multi-instance assistant accounting and cloud recovery remain unqualified. See [Milestone 11 report](../milestone-11/RESULTS.md) for scope, evidence, compatibility blockers and preservation comparison. No service, billing, deployment or original migration was activated.

# Release Phase C — preflight and authorization gate

23 October 2026 (Asia/Calcutta). **STOPPED AT SDK INSTALLATION APPROVAL GATE. Launch remains BLOCKED.** This is a prerequisite report, not completed Firebase qualification. No SDK installation, real credentials, Firebase account/API use, cloud changes, provider activation, billing, deployment or engineering calculation occurred.

## Reviewed and locally established

Read Phase B RESULTS/STAGING-QUALIFICATION, Milestone 10 adapter report, current backend `core/firebase_auth.py`, audited `services/identity_links.py`, frontend `lib/firebase-auth.ts`, and current 40-control matrix. The existing frontend deliberately reports Firebase unavailable. No replacement authentication service, mock production identity or fake sign-in control was added.

Local runtime inspection: Python **3.13.6**, Node **22.18.0**. Official backend `firebase_admin` module is absent; browser `firebase` package is absent and undeclared. Both must be installed before a real SDK integration can compile and be exercised. No package files or lockfiles were changed. Runtime/dependency compatibility still requires approved resolver/build testing; current versions alone do not prove compatibility.

Official release notes checked on this date list these exact candidate pins:

- Python **firebase-admin==7.7.0**, released 23 September 2026. [Official Admin Python releases](https://firebase.google.com/support/release-notes/admin/python).
- Browser **firebase@13.1.0**, released 21 October 2026. [Official JavaScript releases](https://firebase.google.com/support/release-notes/js).

Use only `firebase/app` and `firebase/auth` modules for this integration. The broader SDK must not introduce Firebase AI use; Nebius remains the only application AI provider and inference stays disabled. Exact pins are proposed for approval, not installed or production-qualified selections. Do not automatically upgrade unrelated application packages if resolution conflicts occur; report the conflict.

## Gate 1 — separate approval needed now

Approve or decline **local-only installation** of those two official SDK versions in the existing backend virtual environment and frontend project, with scoped dependency/lockfile updates, dependency-resolution review and focused build/tests. Firebase remains disabled; no credentials, real-service access, cloud resources or billing are included in this approval.

No installation commands were executed. Because the user explicitly requires stopping at any authorization gate, no further runtime integration edits or new mocked acceptance claims were made after identifying this prerequisite. Phase B test/TypeScript/lint/browser evidence is retained, not rerun as Phase C evidence when no product code changed.

## Subsequent gates — not included in Gate 1

**Project/provider/domain approval.** No Firebase project or approved provider/domain identity was supplied or inspected through an authenticated console. A human must designate a dedicated non-production Firebase project or separately approve creating one. Record its non-secret project ID, app ID and exact auth domain in the approved environment specification; do not assume `struvocivil.com` or an existing project may be changed. Proposed minimal provider is Email/Password for synthetic password/reset cases; it is NOT approved or enabled. Google, phone/SMS and other providers remain out of scope unless separately approved. Confirm password policy, email-enumeration protection, quotas and allowed user actions on the actual project. Firebase recommends verifying enumeration protection rather than inferring it from client messages. [Official password-auth guidance](https://firebase.google.com/docs/auth/web/password-auth).

Use an explicitly approved restricted HTTPS staging origin plus only separately approved local test origins. Verify authorized domains, auth handler/redirect URLs and reset continuation URL allowlists; no open redirects, wildcard production origins or implicit localhost authorization. Provider/domain configuration changes require approval. No DNS, certificate, Firebase Hosting or other deployment is authorized. Auth callbacks and recovery mail must not target real production users.

**Credential-use approval.** Current backend adapter accepts a service-account credential file and checks its project identity. Proposed delivery is a restricted read-only secret-mounted file or local protected file outside the repository, supplied by the operator through a secret-delivery channel and referenced by environment configuration. Backend only; never NEXT_PUBLIC, browser storage, logs, screenshots or chat. No keys or credential contents are requested here. Short-lived workload identity/ADC would require a reviewed adapter change; do not claim the existing certificate-file path supports it automatically. Define least privilege for token/account verification; revocation/disable test operations should use a separate authorized operator identity. [Official Admin setup](https://firebase.google.com/docs/admin/setup).

**Synthetic account/linking/data approval.** Approve creation of new Firebase test users and NEW isolated local/staging database, history/ledger and storage paths. No import of old IDs, passwords, CAD/results, conversations, accounting or authorization records. Identity-link schema/provisioning must be explicitly reviewed and authorized; the resolver cannot create accounts or merge by email. Approve the administrative bootstrap/audit transaction and eventual rollback/retention plan before any linking writes. A real Firebase user is not automatically an authorized StruvoCivil user.

**Live acceptance approval.** Approve bounded F01–F07 operations: genuine sign-in/token checks, token revocation, disable/re-enable/delete only designated synthetic accounts, reset/change/recovery mail to designated test inboxes, logout/persistence tests and cross-user denial. These actions alter a real Firebase service or use real credentials and are NOT implicitly authorized by installation approval. Record allowed test identities/operations, operator, traffic limits and cost boundary. Billing is not authorized; inspect the selected product/provider prerequisites and stop if billing or service upgrades are required. No claim of zero real-service cost is made.

## Genuine frontend work to implement after Gate 1

Reuse the current feature flag and existing login UI, not a second editor/auth app. Use the modular official SDK for sign-in, `onIdTokenChanged`/current-token retrieval, explicit persistence policy, `signOut` and supported password recovery. Candidate restricted-session policy is SDK in-memory persistence, subject to approval/usability testing; do not silently default to durable local persistence. [Official persistence guidance](https://firebase.google.com/docs/auth/web/auth-state-persistence).

Firebase tokens must be obtained from the SDK per current session, not copied into the legacy localStorage token store or decoded into an internal user ID. Existing API transport needs an explicitly selected Firebase token source and fail-closed mode handling. Logout must clear UI/session state and sensitive cached owner data. Client logout alone must not be described as revoking a stolen token. Retain the official backend SDK check_revoked=True boundary; revocation checking makes an additional account-service network request, with certificate refresh also requiring connectivity. [Official session management](https://firebase.google.com/docs/auth/admin/manage-sessions).

No cookie sessions are currently implemented. If chosen later, Secure/HttpOnly/SameSite and CSRF controls require separate design and real HTTPS tests. Recovery/reset expiry, single-use and enumeration behavior must be observed through the actual official flow, not homemade reset tokens or mocks.

## Critical account-abuse qualification detail

Phase B account/IP quotas protect FastAPI `/api/auth/login`, which is disabled in Firebase mode. Browser SDK sign-in/reset calls go directly to Firebase: the FastAPI limits **do not automatically cover those requests**. Do not mark A11/B17/B12 complete on that basis. Qualify Firebase-side enumeration/abuse controls, sign-in/reset quotas and restrictions on the selected real project. A UI-only throttle would not be server protection. Any additional enforcement mechanism or service upgrade needs its own approval. No arbitrary permanent lockout is proposed.

## F01–F07 disposition and evidence

All seven real-service cases are **NOT RUN — blocked by approvals/prerequisites**. Existing Milestone 10/Phase B mocked tests remain clearly labeled synthetic.

- F01: genuine SDK sign-in and official backend signature/project/time verification for linked users; reject wrong/unlinked identities.
- F02: old tokens refused after approved revocation/disable/delete; service errors fail closed.
- F03: browser logout clears session and data; independently qualify global revocation if required.
- F04: synthetic reset/change link expires, cannot replay and is correctly scoped; prove enumeration/abuse behavior and old-session handling.
- F05: recovery and identity changes never email-merge or transfer ownership; audit linking/revocation.
- F06: two new users cannot cross-read/write/download projects/CAD/results/history or forge admin identity.
- F07: refresh, expiry, persistence, tabs, reload and logout behavior meet the explicitly chosen session policy.

Reuse Phase B's detailed staging test plan. Genuine Firebase tests may begin against a newly isolated local test backend only if that scope and service credential use are approved. That would still NOT qualify production PostgreSQL/private storage/TLS/cloud durability; those are separate real infrastructure gates. No development identity bypass or old-user database may be used to make an integration appear successful.

## Preservation and matrix

Fresh read-only row/schema comparison (`preservation.json`) exactly matches the Milestone 12 entry: **10,283 application rows and three assistant-history rows**, zero row/schema changes; usage/history/audit records unchanged. Original engineering files were not opened for writes; reuse Phase B's verified 55,296 storage files, 2,090 proof files, 21 solver artifacts and archive/schema manifests. No full backup, migration, deletion or original-data seeding.

No application code or security-control outcome changed, so the current 40-control matrix remains unchanged. Relevant identity/session/abuse entries retain their Partial/Missing/Unverified assessments; no mock or version lookup is used to improve them. Frontend/backend regression, TypeScript, lint and browser checks were not represented as freshly run Phase C tests. They become required after authorized integration changes.

**Next decision: Gate 1 local SDK installation only.** Any project/provider/domain configuration, credential use, account provisioning, live acceptance, resources or billing remains separately gated. Launch stays BLOCKED, Nebius stays disabled, and this run stops for human review.

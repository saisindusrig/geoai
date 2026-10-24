# StruvoCivil — Milestone 10: Firebase Authentication Foundation

Completed locally on 23 October 2026. **Foundation implemented; actual Firebase sign-in and shared-user deployment remain BLOCKED.** Stopped after Milestone 10.

## Delivered implementation

`backend/app/core/firebase_auth.py` is a disabled-by-default official Admin SDK adapter. `FIREBASE_AUTH_ENABLED=false` preserves existing FastAPI JWT/local development behavior. Enabling it requires `AUTH_REQUIRE_JWT=true`, an explicit Firebase project ID, the installed official `firebase-admin` package and a configured service-account credential file matching that project. The adapter rejects emulator mode, missing prerequisites and unsupported tenant identities. No SDK was installed, no credentials configured and no live verification attempted.

Only `firebase_admin.auth.verify_id_token` establishes token trust. Signature/key verification remains entirely with the official SDK. The configured project is passed explicitly; issuer, audience, nonempty matching subject/UID, finite expiration/issued/authentication times and lifetime ordering are checked after SDK verification. There is no client-claim decoder, homemade signature verifier or offline identity fallback.

Every verification requires `check_revoked=True`, with zero clock skew and no application positive-verification cache. Invalid/expired/revoked/disabled tokens return 401. Certificate/account service failures, missing SDK/credentials or misconfiguration fail closed with 503. Unknown/unlinked identities return 403. Firebase mode never accepts legacy JWT, mock-header identity, password registration/login or the development token shortcut as fallback. Disabling the adapter restores the preexisting enforced-JWT/local modes; it does not rewrite users or ownership.

Revocation/disabled-account checks require an extra Firebase Authentication network round trip per verification. Certificate refreshes may also need network access. This increases latency, network traffic and quota/operational cost; no monetary price or free allowance is assumed. These requests were not made during development. Official references: [ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens), [revocation checks and extra round trip](https://firebase.google.com/docs/auth/admin/manage-sessions), [Python SDK reference](https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth).

## Auditable identity-link boundary

`backend/app/services/identity_links.py` defines a separate schema blueprint, deliberately excluded from normal Base metadata/startup initialization. Original databases were not migrated and contain no `auth_identity_links` table. Missing schema returns unavailable; login cannot create it.

The resolver maps exact verified issuer/subject to an existing internal user. It requires an ACTIVE unique association, existing target user, existing administrative approver and a matching existing audit approval. The approval binds link ID, issuer, SHA-256 of subject, internal user ID and approver. Browser-supplied user IDs, emails, roles and project claims cannot select or elevate the account. No user creation, email merging, renumbering or ownership transfer occurs.

No public linking/write endpoint was added. A separately reviewed administrative provisioning/linking process must verify control of both identities, establish authority, transact the link and approval together, enforce uniqueness, provide revocation and audit retention, and handle approver changes. Current resolution also rejects links whose approver no longer has an admin role. This is a prepared read boundary, not a completed account-linking product workflow.

Resolved internal IDs flow through the same existing project/CAD/file/result/engineering authorization and assistant-history dependencies. Existing audit records are never rewritten. No successful-login audit write was added to the request dependency; link approvals and existing sensitive-operation auditing remain authoritative.

## Frontend preparation and local compatibility

`GET /api/auth/config` returns only sanitized mode/prerequisite flags, the enabled project identity and whether legacy password login is permitted. It performs no Firebase network request and exposes no credential path or key.

`frontend/lib/firebase-auth.ts` validates this response at runtime and supplies the small sign-in preparation boundary. The existing login page retains StruvoCivil styling and password login in local/legacy mode. It explicitly labels local development identity as **not Firebase authentication**. Firebase mode hides password registration/login and shows an unavailable explanation; no fake Google/Firebase button is offered even when backend prerequisites appear present. Missing/malformed configuration fails closed with manual Retry. The existing backend remains the authorization authority regardless of frontend flags.

The official browser `firebase` package is absent. No browser sign-in, token persistence, refresh, logout or session integration is claimed implemented. Existing legacy localStorage bearer handling remains unchanged and unqualified for a shared-user release. A later approved integration must select and test a session policy, synchronize frontend enforcement with backend mode, avoid persisting Firebase refresh tokens in the legacy store, and qualify XSS/CSRF, revocation, expiry, logout and recovery behavior.

The normal local API initially served older code. It was refreshed with `serve_local_foundation.py`, a loopback-only local launcher that skips startup initialization/seeding/migrations against the already initialized database. It keeps Firebase disabled, uses Nebius only, disables paid inference/offline AI fallback and clears provider credentials process-locally. Normal proxy health, auth configuration and an owned project read returned 200 (`normal-proxy-check.json`). No environment credentials or persistent provider settings were edited. The refreshed local API and existing frontend remain running; temporary synthetic review API was stopped.

## Audit sources and security scope

Reviewed existing FastAPI JWT verification, local mock identity, login/register/token/me routes, user/admin dependencies, project ownership, authenticated file containment/download audit, saved-result/engineering authorization and owner-scoped assistant history. Reviewed the existing Firebase future architecture and Milestone 4 findings in `docs/private-beta-security/REPORT.md`, plus Milestone 5's patched-runtime report.

Milestone 4's development-token bypass fix remains intact, including stronger rejection in Firebase mode. Existing ownership checks are reused. Proxy trust, localStorage/XSS exposure, session lifecycle, headers, recovery and shared-production infrastructure still require qualification. Milestone 5 records the later runtime dependency patch; M10 does not claim the old dependency finding is still unpatched or that broader deployment security is now qualified.

## Focused verification

- **42 backend tests passed**, one existing Starlette deprecation warning. All Firebase SDK outputs are synthetic/mocked; databases are in-memory and files/history temporary. Cases cover linked identity, official SDK arguments, explicit project and issuer, malformed/forged/expired/revoked/disabled rejection, invalid claims/time/tenant, wrong service-account project, missing SDK/credentials/enforcement, emulator refusal, verifier outage, unknown identity/email non-linking, browser ID/role rejection, absent link schema, missing target/approver/audit, inactive link, shortcut rejection and safe disabled rollback.
- Existing gates are exercised under the resolved Firebase identity: cross-project reads, revisions, file/download ownership and audit, exact saved-result/load-case/stale rejection, forged engineering authorization rejection and owner-scoped assistant-history isolation. No solver execution is used as a test.
- **34 frontend tests passed** across login, preparation boundary, safe redirects, rejected bearer handling, existing assistant history/tools and availability. Final seven login/boundary tests were rerun after lint fixes and passed. Provider behavior remains mocked.
- TypeScript and scoped ESLint passed with zero warnings. No broad engineering suite, package installation or production build was needed.
- Fresh Chrome checks passed at **1280×900**, **1600×900** and **390×900**. Local login labels/forms, mocked Firebase-unavailable state, no fake login controls, branding, dashboard/project navigation, main 3D scene and assistant availability were checked. Final run recorded no JavaScript errors, unexpected writes, downloads or horizontal overflow. Screenshots were visually inspected. See `browser.json`, `browser.log`, `after-login-*`, `firebase-unavailable-*` and `after-assistant-*`.
- Browser verification used the retained isolated M9 project API, mocked unavailable-Firebase configuration and blocked external requests/application writes. Final harness routes both API and file reads to isolated storage. The legacy `/model` Cesium issue remains documented and untouched; the working `/workspace` renderer was checked instead.

**Mocks are not proof of genuine Firebase sign-in or cryptographic verification.** The installed SDK path cannot be live-qualified while the SDK/project credentials are absent.

## Preservation and disclosed verification side effect

All **10,282 request-entry application rows and original schemas remain unchanged**, with no removed or modified original rows. All **three original assistant-history/accounting rows remain exactly unchanged**. No identity-link schema was created in original databases. CAD, revisions, geometry, calculations, result/source hashes, authorizations, conversations and historical audit evidence were preserved.

The first browser harness routed one GLB asset to the normal API rather than isolated storage. This appended **one `file.download` usage event**, ID 2490, project 5, `excavation.glb`. This was not paid inference. It is retained, not deleted. Therefore the application database is **not exactly unchanged in total row count**: 10,283 rows now exist versus 10,282 on entry. See `added-row-evidence.json`, `row-comparison-diagnostic.json` and `preservation.json`. The routing defect was corrected and the final browser run added no further original accounting rows.

Reused manifests verified **55,296 original storage files**, **2,090 engineering proof files**, **66 live database schemas**, **198 archived-only database fingerprints** and **21 coupled solver artifact files**. Original hashes remain unchanged. The older 10,269-row baseline retains its earlier 13 synthetic additions plus the one disclosed M10 usage event; no destructive cleanup or restoration was performed. See `preservation-manifests.json`, `preservation-audit.json`, `preservation-files.log`, `coupled-evidence-preservation.json`.

## Readiness and remaining approved steps

**Ready:** disabled adapter foundation, sanitized mode discovery, audited association read boundary, isolated contract/ownership tests and preserved local workflow within the limits above.

**Blocked:** actual Firebase sign-in, shared private beta, cloud activation and deployment. Missing prerequisites are recorded in `prerequisites.json`: official Python Admin SDK, official browser SDK, configured project identity/credentials and provisioned/audited account links. No live SDK verification is claimed.

Next steps require separate approval: install/pin/review official SDKs; select authorized Firebase project/provider configuration and secure least-privilege credentials; implement approved link provisioning and review process; choose browser session/refresh/logout policy; validate issuer/audience/signature/revocation and service failures against a genuine isolated project; qualify abuse controls, HTTPS/CORS/proxy/headers and recovery; approve any cloud/billing/domain changes separately. Do not enable flags merely to bypass missing prerequisites.

No Firebase project creation, billing activation, deployment, production credentials, original-data migration, Git operations, parallel agents, destructive cleanup, paid AI or unnecessary installation occurred. No Milestone 11 work was started.

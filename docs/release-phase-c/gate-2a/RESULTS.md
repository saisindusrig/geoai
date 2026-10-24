# Phase C Gate 2A — prepared frontend/session integration

24 October 2026. **Local implementation verified. Genuine Firebase authentication and public launch remain BLOCKED. Stop after Gate 2A.**

Reviewed Milestone 10, Phase B security findings, Gate 1C/1D and the approved 40-control matrix. Reused the existing login, API transport, project store, backend Admin adapter and audited identity-link resolver. No backend authorization, database schema, SDK version, launcher or engineering method changed.

## Implementation

- `frontend/lib/firebase-auth.ts`: lazy official modular `firebase@13.1.0` integration. Initialization requires enabled/ready backend Firebase mode plus an explicit enabled frontend configuration, approved password provider, matching project and validated domain/app identity. Missing/malformed/unavailable configuration does not initialize an SDK app. `initializeAuth` explicitly selects `inMemoryPersistence`; sign-in, token retrieval/forced refresh, token-state observation, sign-out and gated recovery use official SDK APIs. SDK errors are not exposed verbatim. No token decoder, browser-claim authorization or refresh-token copy to the legacy localStorage key.
- `frontend/lib/api.ts`: existing JSON, optional reads, uploads, binary files and chat streams now obtain SDK ID tokens asynchronously in Firebase mode. Destinations remain restricted to the configured API origin and `/api/` or `/files/` prefix; redirects are refused, cookies omitted and response caching disabled. Caller headers cannot override the authoritative bearer. Rejected sessions are invalidated without automatic refresh/replay or legacy/development fallback. A late rejection from account A cannot sign out account B. Session abort signals and generation checks reject stale header/body/stream completion.
- `frontend/components/auth/SessionBoundary.tsx` and root layout: discover backend mode before mounting account views. On identity changes, reset the existing project store, clear transient toast state, remount private project/assistant views, and remove account-specific bookmark/result/scenario view caches. Original offline sandbox drafts and general preferences remain intact. Local/demo workspaces are withheld in Firebase mode. Historical backend conversations and saved editor data are never deleted.
- Existing `LoginPageInner`, `UserMenu`, `useAuthUser` and `RequireAuth`: reuse current styling and navigation, expose sign-in only when the gates permit it, route logout through the SDK, read the authenticated internal profile from the backend, and prevent mock-user/demo fallback in Firebase mode. Production registration remains disabled. Password recovery has no working UI unless its additional explicit policy flag and all sign-in prerequisites pass.
- `frontend/lib/site-assistant.ts`: streams share the same asynchronous bearer boundary and reject events from a previous session. Inference, assistant tools, approvals and saved history are unchanged.

## Confirmed race correction

The focused `hooks/useProjectData.session.test.tsx` reproduced a delayed `Promise.all` project load restoring account A's project into the global store after switching to B. `confirmed-aggregate-session-race.log` retains the failure (actual project 123, expected 456). `useProjectData.ts` now captures its mount's identity generation and checks it before accepting aggregate loads or scenario/mesh state. The same regression passes after the correction. Geometry, transforms, source hashes, revisions and calculation behavior are unchanged.

Sign-in completion after explicit logout and late token events following failed SDK logout are also rejected. Token refresh for the same identity does not remount the editor or discard its current draft.

## Focused verification

- **62 frontend tests / 14 files passed** (`frontend-tests.log`): disabled/unavailable/malformed configuration; obsolete async preparation; memory persistence; SDK token retrieval/refresh/expiry; generic sign-in errors; recovery gates and generic outcomes; logout/account switching; cache clearing and draft preservation; stale response bodies, late 401 and aggregate project loads; no legacy bearer fallback; protected file bytes/MIME and destination limits; no transport retries; existing local login, registration restrictions and assistant SSE handling.
- **62 backend tests passed** (`backend-tests.log`, `offline-verification.json`), reusing isolated Firebase and Phase B security fixtures. Includes mocked revocation, disabled/unknown users, project/file/result ownership, assistant isolation and preserved local authentication. Official Admin 7.7.0 imports; zero real SDK apps initialized and zero forbidden network/credential attempts. This is not live signature/service verification.
- **TypeScript passed**, **scoped ESLint passed** for all changed source/test files. `frontend-checks.json` records the final standard **Turbopack production build passed in 24.78 seconds**, using the approved portable Node 24.22.1 with inherited worker PATH. No Webpack substitution or dependency upgrade.
- Fresh isolated Chrome checks at **1280×900, 1600×900 and 390×900** cover homepage branding, local login, production-registration rejection, Firebase-unavailable UI, dashboard/project navigation, diagnostics, visible 3D geometry and disabled assistant. Actual same-origin proxy GETs for health/config/synthetic project and Cesium assets pass. Final `browser.json` records no page errors, writes, downloads or external requests. Desktop scene/assistant and mobile unavailable-login screenshots were visually inspected.

Build/browser validation uses the retained isolated frontend copy and synthetic read-only API on 3017/8003. The isolated output directory and owned-worker IPC policy are validation-only. Initial bounded sandbox/IPC build timeouts, a missing local-review proxy flag, a startup-readiness race and early test-harness/assertion mismatches are retained in separate logs. The corrected harness uses the existing local-review proxy flag and waits for services. No normal Next configuration, security exception, launcher, port, or service restart was introduced.

Existing Vitest configuration/assertion-rewrite and Starlette/httpx deprecation warnings remain. The mocked 401 navigation test also reports jsdom's unsupported full-document navigation; its assertions pass. No dependencies were installed to suppress warnings.

## Preservation

Read-only before/after/final comparison with Milestone 12 verifies exact schemas and row fingerprints for **10,283 application rows and 3 assistant-history rows**, including existing ownership, audits, conversations and accounting. Reused archive checks verify **55,296 storage files, 2,090 engineering proof files, 66 live database schemas and 198 archive-only fingerprints**. All 21 retained coupled solver artifacts remain unchanged; no solver was run.

The older archive's 10,269-row snapshot predates the 14 additions already documented before Milestone 12; these are not Gate 2A writes. Frontend/backend dependency manifests, lockfile, Node launchers, backend auth adapter and configuration retain their before hashes. Four graphics source files and ten original engineering fixture inputs remain unchanged. No original data was imported into staging, migrated or deleted. SDKs remain browser 13.1.0 / Admin 7.7.0.

## Remaining gates

See `STAGING-PREREQUISITES.md` for exact flag names, configuration boundaries and approvals. Email/password is the only prepared provider. In-memory persistence remains a candidate awaiting final session-policy approval. SDK logout is local session clearing, not global revocation; recovery expiry, account lifecycle, provider abuse controls, HTTPS and real-service ownership acceptance remain unqualified.

The 40-control matrix's deployed-security statuses are not upgraded based on mocks. In particular, B03/B12 remain genuine recovery/session blockers. No credentials, Firebase project activation, real Firebase user, live sign-in, paid inference, cloud billing/deployment, original-data migration, Git operation or additional agent was used. **Stop here; public launch remains BLOCKED.**

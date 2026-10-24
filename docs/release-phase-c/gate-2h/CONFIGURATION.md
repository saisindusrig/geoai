# Gate 2H — registered Web app configuration preparation

24 October 2026, Asia/Calcutta. **Offline preparation only. Real authentication and public launch remain BLOCKED.**

The owner reports the registered Web app **StruvoCivil Staging** in `struvocivil-918c9`, Google and Email/Password enabled, and previously reviewed signup/deletion/enumeration/password controls. This phase neither reads its live settings nor verifies those assertions. No app ID, browser API key, project number or service credential was obtained, guessed or copied from screenshots.

## Template and exact mapping

Use [frontend.staging.env.template](frontend.staging.env.template) as a review artifact, **not an active environment file or shell script**. It lives under documentation and is not automatically loaded by Next.js. Do not copy it over the root/frontend/backend normal development or production environment files.

The four consumed Web SDK settings map to existing variables:

- Official `projectId` → `NEXT_PUBLIC_FIREBASE_PROJECT_ID`: pinned to `struvocivil-918c9`.
- Official `authDomain` → `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`: pinned to `struvocivil-918c9.firebaseapp.com`, with no protocol, slash, port or suffix. This is the expected standard domain, not a live configuration read. Stop if the registered app reports a different value; do not substitute a custom domain automatically.
- Official `apiKey` → `NEXT_PUBLIC_FIREBASE_API_KEY`: `<OFFICIAL_WEB_API_KEY>` remains an invalid placeholder.
- Official `appId` → `NEXT_PUBLIC_FIREBASE_APP_ID`: `<OFFICIAL_WEB_APP_ID>` remains an invalid placeholder. The app display name is not an app ID. A Web app ID has the expected `1:<positive project number>:web:<hex identifier>` shape; the actual number/identifier must come from the reviewed registered app, not from a fabricated sample.

The global `NEXT_PUBLIC_FIREBASE_AUTH_ENABLED=false` remains off, independently of the prepared Google/password flags. Both provider flags are `true` in this **inert template only**, preserving the dual-provider candidate while authorizing no connection. Recovery remains false and needs separate mail/policy approval. No existing environment file changed.

No measurement ID, Analytics import/initialization, Storage, Messaging or Realtime Database configuration is added. The Auth-only integration uses its existing `firebase/app` + `firebase/auth` imports and SDK 13.1.0. The Firebase setup snippet's optional Analytics line is not an instruction to initialize another product. [Official configuration options](https://firebase.google.com/docs/web/learn-more#config-object).

`NEXT_PUBLIC_` settings are browser-visible and inlined at build time. Only approved public Web app configuration belongs there; never service-account JSON, Admin private keys, OAuth client secrets, passwords or refresh tokens. A future configuration change needs a deliberate isolated rebuild/full reload; changing runtime environment alone does not reliably change an already-built browser bundle. [Next.js environment behavior](https://nextjs.org/docs/app/guides/environment-variables#bundling-environment-variables-for-the-browser).

## Validation and trust limits

`frontend/lib/firebase-auth.ts:firebaseConfigurationIssues()` performs local format/identity checks. Existing `firebaseSignInAllowed()` now reuses it, preserving backend/browser enable/readiness/provider gates. The backend's explicit project must match the browser project; the authentication domain must match that exact expected project. App ID syntax is bounded; obvious placeholder API keys and malformed values are rejected before SDK import/initialization. No generic ADC or local-login fallback is introduced.

The Gate 2H template tests supply **exactly `struvocivil-918c9` as the expected project**. The shared website validator retains its existing generic backend-bound project behavior for other separately configured environments; it does not hardcode a global project override. A different expected project cannot silently validate this staging template. No backend identity policy was relaxed.

Passing local checks does **not** prove that a well-formed app ID/API key belongs to the registered Web app or project. Neither does it establish domain authorization, key restrictions, actual provider settings, signup denial, service availability or signature verification. Those require later approved official configuration review and real acceptance. Current placeholders intentionally fail format checks even if someone flips the frontend flag.

Existing per-tab `inMemoryPersistence`, `User.getIdToken()` transport, Google user-click popup, mandatory backend `/api/auth/me`, revoked/disabled checks and audited issuer/UID-to-internal-user ownership remain unchanged. No email/name/photo-based access, auto-provisioning, provider linking or account merge is added. Normal reload/tab/logout limitations and the unimplemented administrator-approved linking workflow remain documented in [Gate 2F account-linking](../gate-2f/ACCOUNT-LINKING.md).

## Remaining approvals — not granted by Web app registration

1. Approve a named operator to review/use only the registered app's public configuration for this exact project/app and approved test origin. Deliver values to a new isolated staging configuration through the approved local mechanism, not screenshots copied automatically or credential contents in chat. Do not register another app. This phase does not read or populate those values.
2. Review exact authorized domains, API restrictions, CORS/proxy routing and isolated data targets. Require new synthetic users, audit-bound internal UID links, private fixture files and empty staging history/accounting; never development-data copies or implicit fallback/seeding.
3. Resolve the separately approved backend keyless implementation and identity source. Current ADC remains blocked with `ADC_IDENTITY_NOT_QUALIFIED`; certificate remains the default and Firebase remains disabled. No Cloud Run, billing/Blaze, key creation, credentials or service configuration is authorized here.
4. Only after those prerequisites, separately approve enabling both frontend/backend gates in the isolated environment and a bounded named-subject F01–F07 network/session/ownership test scope. Real user creation, provider linking, mail or recovery mutations need their own explicit approval. Registration alone authorizes none of these operations.

Do not flip a reachable staging backend into legacy mode as rollback: stop/isolate ingress first and retain enforced authentication. Keep the existing [acceptance and rollback plan](../gate-2b/ACCEPTANCE-AND-ROLLBACK.md). All live F01–F07 cases remain NOT RUN. No cloud or public launch follows this gate.

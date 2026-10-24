# Gate 2A — configuration and approval boundary

Everything remains disabled. Do not paste credentials into chat or commit them. No following step is authorized by completion of Gate 2A.

## Required separately approved configuration

Backend: `FIREBASE_AUTH_ENABLED=true`, `AUTH_REQUIRE_JWT=true`, an exact approved `FIREBASE_PROJECT_ID`, and securely delivered `FIREBASE_AUTH_CREDENTIALS_FILE` whose official service-account project matches it. The installed official Admin SDK remains the sole verifier, including mandatory per-request revocation/disabled-account checking. Approve the resulting certificate/account-service network traffic and qualify its availability, latency and quota costs.

Frontend build configuration, all absent/false by default:

| Setting | Requirement |
| --- | --- |
| `NEXT_PUBLIC_FIREBASE_AUTH_ENABLED` | Explicit `true` only after activation approval and matching enabled/ready backend |
| `NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED` | Explicit `true` only for an approved email/password provider |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Exact match to backend project identity |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Approved public browser SDK configuration; never an Admin/Nebius secret |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Currently restricted to the exact project's `project-id.firebaseapp.com` domain |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Approved web-app identity in the official `1:number:web:hex` form |
| `NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED` | Keep false until the separate recovery/provider/domain policy is approved |

These public settings are compiled into the frontend. Configuration changes require a deliberate rebuild and full reload; no runtime auto-activation or credential discovery is implemented. No settings file or real values were created in Gate 2A. Existing same-origin API configuration/proxy and Node 24 launchers remain unchanged.

## Approvals before genuine acceptance

1. Approve the restricted staging Firebase project/web app, enabled provider, exact authorized staging origin and any intended localhost test domain. Cloud creation/activation, credentials and billing still require their own explicit authorization.
2. Approve secure credential delivery outside chat, least-privilege service access, clean isolated staging database/storage, explicit identity-link schema migration, and audited links between newly synthetic Firebase subjects and internal staging users. Do not link by email, accept a browser internal ID, copy development users or transfer ownership.
3. Approve the candidate **in-memory, per-tab** session policy or specify a separately reviewed replacement. No refresh tokens are copied to localStorage. SDK logout clears the local session; it does not establish global server-side revocation. Cookie/SSR authentication and durable/cross-tab persistence are not implemented.
4. Approve recovery behavior: provider, authorized action domains/URLs, expiry, enumeration protection, abuse/rate limits, session invalidation and audit policy. The frontend uses only the official SDK recovery call and a generic outcome; it supplies no local reset token or success guarantee.
5. Explicitly authorize F01–F07 real-service acceptance with new synthetic users/data: sign-in and backend signature verification, audited linking, refresh/logout, reset expiry/recovery, revocation/disabled accounts, cross-user file/result/history denial, outages and safe disabling. Mocks are not evidence these services work.

Direct Firebase browser sign-in/recovery do not pass through FastAPI's legacy login endpoint. Phase B's legacy account/IP limits therefore do not automatically qualify Firebase provider abuse controls. Real provider enumeration, throttling and recovery controls remain release blockers (including B03/B12 and distributed qualification under A11/B17). No permanent account lockout was added.

No Google/OAuth, MFA, account-provisioning UI, account-link approval UI, custom auth domains, tenants, persistent sessions or real recovery qualification is claimed. Nebius stays disabled; engineering execution is outside authentication acceptance. Public launch remains BLOCKED.

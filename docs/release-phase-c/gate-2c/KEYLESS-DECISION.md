# Gate 2C — keyless identity-selection gate

24 October 2026. Dedicated target supplied by the owner: `struvocivil-918c9`. Its isolation, IAM, billing and Firebase configuration have **not** been inspected. No authority to use its credentials or services is inferred.

## Decision: stop before an operational ADC implementation

The installed official Firebase Admin SDK 7.7.0 implements `credentials.ApplicationDefault._load_credential()` by calling `google.auth.default(scopes=...)`. Its constructor alone does not select or establish a service identity. Google's documented discovery sequence includes an environment-selected file, a cached local ADC login, and a runtime metadata identity. Selecting a project or checking a returned project ID does not establish which principal is used. Inspecting credential type only after discovery is too late to promise that no developer credential was accessed. [ADC discovery](https://docs.cloud.google.com/docs/authentication/application-default-credentials), [Admin initialization](https://firebase.google.com/docs/admin/setup).

No approved workload credential source, service-account principal, issuer/audience trust policy or isolated credential-delivery environment was supplied. Therefore secure local ADC identity selection cannot currently be guaranteed. In accordance with the requested stop condition, no ADC discovery/loading, credential inspection, Google login, impersonation or real verification was attempted. No local Google profile, well-known credential location or environment-file secret was inspected.

## Implemented preparation only

- `FIREBASE_AUTH_CREDENTIAL_MODE` defaults to `certificate`; existing certificate initialization, named app, project check and official token verification remain in use for that mode.
- Explicit `adc` selection requires exactly `struvocivil-918c9`, then always fails readiness with `ADC_IDENTITY_NOT_QUALIFIED` / HTTP 503. A different project returns `ADC_PROJECT_NOT_APPROVED`. Unknown/case-mismatched modes are rejected, never normalized into certificate mode.
- Readiness rejects ADC before touching the certificate-file path. `_sdk_verify` independently rejects it before SDK import or cached-app reuse. Setting the mode cannot borrow an existing certificate app or activate ambient ADC. There is no enable-through flag or principal-name assertion that bypasses this gate.
- `FIREBASE_AUTH_ENABLED` remains false by default. No environment files or running services changed. In an explicitly enabled Firebase mode, the existing security dependency rejects requests rather than falling back to a legacy JWT or development identity.
- Existing `check_revoked=True`, zero clock skew, signed-token SDK boundary, exact issuer/audience/lifetime checks and audited UID-to-internal-user resolution are unchanged. Revocation/disabled-account checking entails a backend account lookup and network dependency per verification; outages remain fail-closed. Offline tests do not establish real availability, latency, quota or service cost. [Session checks](https://firebase.google.com/docs/auth/admin/manage-sessions).

**This is a guarded mode selector, not a working keyless adapter or genuine Firebase qualification.** Do not set `adc` expecting sign-in to work. No SDK substitute, homemade token verifier, key download or refresh-token handling was introduced.

## Required solution and next approvals

Choose and approve one identity architecture before further implementation:

1. **Local/external workload:** a reviewed Workload Identity Federation provider with exact issuer, audience, subject/attribute restrictions and one dedicated verifier service account in the staging project. Approve the actual external workload identity delivery mechanism and credential-configuration custody. Future loading must explicitly select and validate this source before any SDK credential loading, reject user ADC and private-key files, and never search a developer profile. The non-secret federation configuration is distinct from a service-account private key; its source endpoints and trust rules still require review.
2. **Managed workload:** a separately approved isolated runtime with a dedicated attached service account, a verifiable identity-selection mechanism and no developer credential mounts/environment overrides. No cloud runtime creation or deployment is authorized here. A spoofable environment marker or matching project string is insufficient.

For either architecture, supply the **principal identifier and trust-policy decisions through an approved non-secret review**, never tokens, private keys or credential contents in chat. The current code does not implement either source. A subsequent reviewed implementation must bind app caching to the selected mode/project/source identity and fail before initialization on disagreement, then undergo isolated offline tests followed by separately authorized real-service acceptance.

The verifier's proposed custom role remains `firebaseauth.users.get`, subject to actual project/IAM qualification. It needs no user creation/update/deletion, recovery mail, configuration changes, storage administration or engineering authority. A federation-to-service-account flow additionally needs a narrowly scoped trust/impersonation grant (for example `roles/iam.workloadIdentityUser` to the approved federated subject on that one account); this is separate from Auth lookup permission, and nothing was granted. Do not grant pool-wide access, Owner, Editor or blanket Token Creator as a shortcut. [Auth permissions](https://docs.cloud.google.com/identity-platform/docs/access-control), [WIF least privilege](https://docs.cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation), [WIF setup](https://docs.cloud.google.com/iam/docs/workload-identity-federation).

Approve source/principal/trust and an isolated bootstrap/linking procedure first. Any service configuration, credential use, test users, mail, real network verification, resource creation or costs require their own explicit scope. No service-account JSON key is part of the proposed solution. Public launch and F01–F07 remain blocked.

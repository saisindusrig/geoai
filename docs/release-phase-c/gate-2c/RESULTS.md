# Phase C Gate 2C — secure keyless Firebase preparation

24 October 2026, Asia/Calcutta. **Stopped at the requested identity-selection gate. Operational ADC integration and genuine authentication are BLOCKED. Public launch remains BLOCKED.**

## Changes and decision

Reviewed the existing adapter/configuration, installed official Admin SDK 7.7.0 credential implementation, audited identity resolver, Gate 1D installation evidence and Gate 2A/2B security/prerequisite reports. No project Console, Google login, service credential, ADC profile or environment-file secret was accessed.

The SDK's `ApplicationDefault` eventually calls `google.auth.default()`. Ambient discovery can load a developer's cached user credential; an explicit project ID cannot pin the principal. No approved workload credential source or dedicated verifier principal is defined. Secure local identity selection therefore cannot be guaranteed with the supplied prerequisites. The requested stop condition applies; an operational ADC loader was **not implemented or qualified**. The decision and narrowly scoped future solutions are in [KEYLESS-DECISION.md](KEYLESS-DECISION.md), with official documentation supporting the discovery/trust requirements.

The only application changes are:

- `backend/app/core/config.py`: add `FIREBASE_AUTH_CREDENTIAL_MODE="certificate"`, preserving the existing default and disabled feature flag.
- `backend/app/core/firebase_auth.py`: reject unknown modes; reserve explicit `adc` for exactly `struvocivil-918c9`, then reject it with `ADC_IDENTITY_NOT_QUALIFIED` / HTTP 503 until a reviewed source exists. Readiness rejects before credential-file access; the SDK boundary separately rejects before imports or app reuse. Certificate initialization and mandatory official `check_revoked=True` behavior are retained.

No switch can activate ADC in this implementation. No default-credential discovery, custom Google credentials wrapper, JSON key generation, token decoder, silent certificate fallback, development fallback or account provisioning was added. Existing UID/issuer/audit linking and ownership dependencies were not changed. No application environment or running service was modified/restarted.

## Offline verification

[backend-tests.log](backend-tests.log) and [offline-verification.json](offline-verification.json): **71 passed, 2 existing warnings, 11.20 seconds**. Run with `backend/.venv/Scripts/python.exe docs/release-phase-c/gate-2c/verify_offline.py`.

- Existing 62 synthetic tests: official-SDK-shaped mock verification, linked identity, wrong issuer/project/credential project, expired/forged/malformed tokens, revoked/disabled accounts, missing credentials/SDK, verifier outage, unknown links, cross-user projects/files/saved results/history, audited link integrity, local login, registration, account-aware limits and admin isolation.
- Nine new cases in `backend/tests/test_firebase_keyless_gate.py`: approved/wrong ADC project; five unsupported mode values; disabled mode without inspection; cached certificate-app rejection and no local-identity fallback after ADC selection. ADC requests return unavailable before any verifier call; they are not represented as passing live authentication/revocation tests.
- Harness clears inherited environment, bypasses dotenv, uses temporary/in-memory synthetic storage, blocks real SDK initialization/credential discovery, blocks original backend database access and blocks application network connections. Only Windows stdlib asyncio's internal wakeup socketpair is allowed. **Zero real SDK apps initialized; zero forbidden network/credential attempts.**
- An initial fixture-registration error is retained in `initial-fixture-registration-error.log`; it was corrected in test imports only. Existing warnings are AnyIO assertion rewriting and Starlette/httpx deprecation; no dependencies were changed to suppress them.
- [scope-verification.json](scope-verification.json): Python AST syntax and scoped whitespace checks passed for changed Python/tests and evidence scripts; all 106 installed distributions still match Gate 1D, including Admin 7.7.0. No configured backend lint runner was found; this is not presented as Ruff/Flake8 execution.

No frontend or launcher change: TypeScript, frontend lint/build and browser suites were not rerun. Prior Gate 2A browser/session evidence remains prior mocked/local evidence, not fresh Gate 2C genuine authentication proof. No normal service restart was required.

## Preservation

- `preservation-before.json` and `preservation-after.json`: exact read-only schemas/row fingerprints match the Milestone 12 baseline: **10,283 application rows; 3 assistant-history rows**, including historical accounting/audits.
- `preservation-audit.json`: fresh verification against retained manifests found **55,296 original storage files and 2,090 proof files unchanged**, 66 live schemas and 198 archive-only database fingerprints verified. Historical archives were read in place, without extraction, restore or backup writes. The older archive's 10,269 application rows plus its 14 documented pre-Milestone-12 additions remain the unchanged current baseline; no rows were added in Gate 2C.
- `coupled-evidence-preservation.json`: all **21** referenced coupled solver artifacts match their hashes; no solver ran.
- `scope-verification.json` and `input-hashes-after.json`: only the two listed backend application inputs changed among the prior 30 tracked inputs. Other **28** match, including all 18 Gate 2A frontend sources, ownership/link code, dependencies, Node launchers/helper and both approved 40-control matrix files. Four GPU source hashes also match.

## Remaining requirements and next actions

[KEYLESS-DECISION.md](KEYLESS-DECISION.md) specifies the missing named principal, pinned workload credential source, issuer/audience/subject restrictions, least-privilege IAM and separate credential-use approval. Workload Identity Federation or an isolated managed identity is a proposed architecture, not a configured service. No service-account private key is proposed.

[NEXT-CONSOLE-ACTIONS.md](NEXT-CONSOLE-ACTIONS.md) records later approved operator actions for the exact project: isolation/Web-app review, email/password only, explicit test domains, service-side signup restriction, enumeration protection, recovery/session policy, fresh internal users/link database/private storage and separately authorized F01–F07. Provider/tier support, genuine revocation/outage behavior, audited bootstrap tooling, recovery completeness and costs remain unqualified. Existing 40-control outcomes were not upgraded.

No Firebase activation, credentials, impersonation, user creation, recovery mail, live F01–F07, paid inference, numerical execution, cloud resources, billing, deployment, Git, package changes or destructive cleanup occurred. **Stop after Gate 2C; review the identity architecture before any further implementation or activation.**

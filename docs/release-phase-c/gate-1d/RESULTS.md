# Phase C Gate 1D — Firebase Admin SDK installation

24 October 2026. **GO for the authorized local SDK installation only. Firebase authentication and public launch remain BLOCKED. Stop at Gate 1D.**

## Installation and scope

Reviewed Gate 1, 1A, 1B and 1C evidence and the existing disabled adapter. Used the existing `backend/.venv/Scripts/python.exe`: Python 3.13.6, Windows AMD64. Firebase Admin was absent. `pip check` passed before and after installation.

Installed exactly **firebase-admin 7.7.0**, plus 20 newly required transitive packages. No previously installed distribution was removed or changed. `resolution-review.json` lists every planned version and prior installation status; `package-comparison.json` records the actual additions and verifies all existing versions remained unchanged. The resolver found compatible Python 3.13 wheels without a conflicting upgrade.

The initial sandboxed PyPI request failed DNS resolution; the explicitly authorized registry request succeeded. Reviewed the dry-run before mutation, then installed only its resolved wheels with `--no-deps --require-hashes`. `approved-resolved-wheels.txt`, `resolution.json`, `install.json` and their logs retain the exact public registry URLs, versions and SHA-256 evidence. This is dependency compatibility evidence, not a dependency vulnerability audit.

The only application dependency-manifest change is the exact `firebase-admin==7.7.0` line in `backend/requirements.txt`. Before SHA-256: `ebf0a05e337874751ff3ab1eb2d335d32c9e2299ba8f4ed6c07492a7e03280d1`; after: `f90e1b936c5001d31b8759fd726c157be095cc75a2235c55304f349a3c8637ae`. Original bytes are retained in `requirements-before.txt`. No adapter, environment configuration, frontend package, lockfile or launcher changes.

## Local verification

`verify_offline.py` imports the installed official `firebase_admin`, `auth` and `credentials` modules and verifies package/module version 7.7.0. Configuration is synthetic: inherited environment cleared, dotenv loading disabled, temporary storage and in-memory databases only. SDK initialization, credential loading, application network calls and original backend database access are blocked. The sole socket exception permits the Windows standard library's private asyncio wakeup socketpair call site.

- Default `FIREBASE_AUTH_ENABLED=false`: unavailable, no verifier fallback.
- Enabled synthetic configuration without a project: `PROJECT_REQUIRED`, HTTP 503.
- Configured synthetic project without credentials: `CREDENTIALS_MISSING`, HTTP 503.
- **62 focused tests passed** in 8.44 seconds: `backend/tests/test_firebase_auth.py` and `backend/tests/test_release_phase_b.py`.
- Coverage includes mocked linked identities, issuer/audience/lifetime rejection, revoked/disabled identities, verifier outage, mandatory revocation options, unlinked identities, audited association, project/file/result ownership, assistant isolation, local password authentication and registration, account-aware abuse limits, and admin isolation.
- Zero Firebase apps initialized; zero forbidden network/credential attempts. All identity outcomes are synthetic/mocked, **not genuine Firebase acceptance**.
- Two warnings: already imported AnyIO pytest assertion rewriting; existing Starlette/httpx deprecation. No package changes were made to suppress these.

Initial harness failures are retained: an absent synthetic home directory, an overbroad socket guard blocking asyncio IPC, and an interrupted sandboxed run. After correcting only the harness, a broader exploratory run passed 64 tests but failed 8 legacy ownership tests that assume a populated global application database or live infrastructure diagnostics. Its log is `legacy-suite-isolation-failure.log`; these tests are not claimed as passing. The final 62-test run uses the existing isolated ownership/authentication fixtures and does not open the development database to satisfy those assumptions.

The Node launcher check independently passed: Node 24.22.1, npm 11.19.1, main and PATH child selection verified. Both launchers and their helper retain Gate 1C hashes. Existing website/backend processes were not restarted. No frontend code changed, so TypeScript, frontend build and browser suites were not repeated; Gate 1C frontend qualification remains the prior evidence, not a new Gate 1D browser result.

## Preservation

`preservation-before.json`, `preservation-after.json` and `preservation-final.json` match the Milestone 12 schema and exact row fingerprints: **10,283 application rows and 3 assistant-history rows**, including existing ownership, audit and accounting records. No original database migration or account creation.

Reused retained manifests without extracting/restoring backups: **55,296 storage files, 2,090 engineering proof files, 66 live database schemas and 198 archive-only database fingerprints** verified. All 21 retained coupled solver artifacts match; no solver was executed. Four graphics source hashes and ten original engineering fixture inputs also match. See `preservation-audit.json`, `preservation-files.json`, `coupled-evidence-preservation.json` and `source-preservation.json`.

The older archive's 10,269-row application snapshot predates the 14 documented additions already present at Milestone 12 (1 user, 1 project, 5 audit and 7 usage rows). These are not Gate 1D writes; the current 10,283-row baseline matches before and after this task.

## Remaining authorization gates

No Firebase project configuration, credentials, credential discovery, real users, cloud APIs, Firebase verification services, billing, deployment, paid inference or Git operations were used. Nebius inference was not enabled.

Genuine authentication still requires separately approved restricted staging project identity, allowed sign-in providers and authorized domains, secure credential delivery outside chat, audited identity linking, and isolated synthetic accounts/data. Then explicitly authorize real-service F01–F07 acceptance, including signature verification, refresh/logout/recovery, reset expiry, disabled/revoked accounts, cross-user denial and revocation-check availability/network costs. SDK installation and mocked tests do not qualify these controls. Infrastructure, recovery and distributed-budget launch gates remain separate.

# Phase C Gate 2H — Firebase Web app configuration

24 October 2026, Asia/Calcutta. **GO for offline preparation only. Firebase remains disabled by default; real authentication and public launch remain BLOCKED. Stop after Gate 2H.**

## Delivered

- [frontend.staging.env.template](frontend.staging.env.template): an inert documentation template for the owner-reported registered **StruvoCivil Staging** Web app. Exact expected project `struvocivil-918c9` and standard authentication domain are pinned; API key and app ID remain explicit invalid placeholders. Both Google/password provider flags are prepared, global connection flag remains false and recovery remains false. It is not a normal `.env` file and is not loaded automatically.
- [CONFIGURATION.md](CONFIGURATION.md): exact official-field mapping, build-time/public-variable handling, validation limits and separate future configuration/connection approvals. No settings were copied from screenshots or read from the real project.
- `frontend/lib/firebase-auth.ts`: extracted a pure `firebaseConfigurationIssues()` validator and reused it in existing sign-in gating. It checks the backend-bound expected project, exact domain, bounded Web app ID syntax and API key format/obvious placeholders before SDK import/initialization. No replacement auth service or additional feature flag was introduced.
- `frontend/lib/firebase-staging-config.test.ts`: 13 focused cases exercising the actual template, exact staging identity, invalid domains/project/app IDs/API placeholders, disabled connection, provider gates and zero SDK/network initialization. Existing login, UID authorization and session tests were retained.

Offline shape validation cannot prove that a syntactically valid app ID/API key belongs to the registered app. Official configuration review and separately authorized live acceptance are still required. The shared runtime remains bound to its backend-configured project; the staging-template checks explicitly require `struvocivil-918c9` rather than silently replacing other environments' identity.

## Verification

- **80 frontend tests passed**, 11 focused files: configuration, Google/password login, popup error paths, backend-denied identities, disabled/default behavior, token transport, logout/account switching, stale responses, project/cache and assistant isolation. `frontend-tests.log`.
- **71 backend tests passed**, using synthetic databases and mock verifier outputs: issuer/project/token rejection, revocation/disabled-account contracts, audit-bound identity linking, unknown accounts, cross-user project/file/result/history denial, local authentication and blocked ADC. **Zero real SDK apps initialized and zero forbidden network/credential attempts.** `backend-tests.log`, `offline-verification.json`.
- **TypeScript, scoped ESLint and default Turbopack build passed** in the retained isolated copy with checksum-verified portable Node 24.22.1. Build: 27.83 seconds. No Webpack substitution, package change, normal launcher change or normal service restart. `frontend-checks.json` and respective logs.
- Source scan found no Firebase Analytics import/initialization in the application paths checked. No measurement ID or Analytics configuration was added.

Existing Vitest/jsdom and Python test warnings remain; no package was upgraded to suppress them. A preservation source scan initially encountered an existing non-UTF-8 file; the scanner was changed to inspect bytes, without altering that file. No application test/build failure remained. UI markup is unchanged; Gate 2F browser/screenshots remain prior evidence, not newly rerun Gate 2H browser or live-sign-in evidence.

## Preservation

`preservation-before.json` and `preservation-after.json` are identical: exact baseline schemas/row fingerprints match **10,283 application rows and 3 assistant-history rows**, including original accounting/audits. Backend Firebase/UID/ownership code, dependencies and all normal Node launcher hashes remain unchanged.

Fresh read-only manifest verification found **55,296 original storage files and 2,090 proof files unchanged**, 66 live database schemas and 198 archived-only fingerprints verified, and **21 coupled solver artifacts** unchanged. Archives were read in place without extraction/restore. The older archive's 10,269 application rows plus 14 documented pre-Milestone-12 additions remain the current unchanged baseline; no records were added here. See `preservation-audit.json` and `coupled-evidence-preservation.json`.

`status.json` / `input-hashes-after.json` verify that only `frontend/lib/firebase-auth.ts` changed among the 30 prior tracked inputs; the other **29** match. The new template, new configuration test and this evidence packet are the additional files. The other five Gate 2F frontend sources, all four GPU source hashes, frontend package/lockfile, 106 installed Python distributions and approved security-matrix files are unchanged. No existing environment file was read or edited for configuration, and no original data was opened for writes.

## Remaining approvals

The registered app and provider/security settings remain **owner-reported**, not live-verified. Next approve a named operator's review/use of this existing app's official public configuration and exact test origin, populating only a new isolated staging configuration while leaving connection flags off. Do not submit Admin keys/OAuth secrets in chat or register another app.

After that, the separately reviewed backend keyless implementation, clean staging data/audited UID links and a bounded synthetic-subject live acceptance scope must be approved before either connection gate is enabled. Current backend ADC remains blocked; no Cloud Run, ADC, Blaze, billing, credentials, user creation/linking, live authentication, mail, paid inference, solver, deployment, Git or destructive cleanup occurred. F01–F07 remain NOT RUN. **Stop at Gate 2H; no automatic live connection or launch.**

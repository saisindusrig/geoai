# Phase C Gate 1 — installation halted on Node compatibility gate

23 October 2026 (Asia/Calcutta). **Gate 1 is partially completed and STOPPED. Launch remains BLOCKED.** No runtime upgrade, SDK substitution, Firebase configuration, credential access, real authentication or cloud operation is authorized or performed.

## Exact result

- `firebase@13.1.0` is installed in the existing frontend, pinned exactly in package.json and package-lock.json. npm added 76 packages. Comparison with the saved pre-install lock proves **zero existing locked package version changes**. Scripts/audit/funding calls were disabled with `--ignore-scripts --no-audit --no-fund`; package-registry traffic only. No application imports or sign-in functionality were added.
- **Compatibility blocker:** ten resolved Firebase lock entries, including core app/auth dependencies, declare **Node >=24.12.0**. The existing runtime is **Node 22.18.0 / npm 10.9.3**. npm emits EBADENGINE warnings but permits installation; its exit code is not proof of compatibility. See `npm-plan.log`, `npm-install.log` and `installation-status.json` for exact versions/engine declarations.
- The warning was already present during lock-only resolution and was missed before npm installation began. Installation finished before the conflict was reviewed. No attempt was made to suppress engine requirements, upgrade Node, downgrade Firebase, remove packages or repair unrelated dependencies. The SDK remains unused and unqualified; the existing frontend source is unchanged.
- `firebase-admin==7.7.0` **was not installed**. The Python resolver was running a dry-run and was stopped once the broader compatibility gate was identified. Installed Python packages are exactly identical before/after (`python-resolution-status.json`); backend requirements were not changed. The incomplete resolver output is not an approved backend lock or successful compatibility finding. Existing Python is 3.13.6.

## Scoped changes and evidence

Authorized changes completed: frontend/package.json adds only the exact Firebase dependency; frontend/package-lock.json adds its resolved graph. No unrelated existing package versions changed. Required Firebase SDK transitives include modules outside Authentication (including AI-related packaging); they were not imported, initialized or enabled. Nebius remains the only application AI provider and paid inference is unchanged/disabled. Installing packaging is not activating those services.

Pre-install evidence: frontend-package-before.json, frontend-lock-before.json, backend-requirements-before.txt, python-packages-before.json and database-before.json. Post-install resolution/versions: npm-resolution-review.json, installation-status.json and python-packages-after.json. These are scoped manifests/metadata, not full-project backups. Original package baselines retained; no Git operations.

`pip-check-before.log` and `pip-check-after.log` both report no broken Python requirements. This confirms the unchanged Python environment, not Firebase Admin compatibility. Installed browser SDK version was read from package metadata without importing or initializing Firebase. No service-account files, .env files or Firebase configuration were opened. No Firebase API, account, credential, DNS, billing, deployment or inference operation occurred.

**Focused backend/frontend runtime tests, TypeScript, lint and build were not run after the stop gate.** Do not reuse prior passing Phase B tests as post-install proof. Package presence, a successful npm exit and historical browser screenshots do not qualify a runtime the package declares unsupported. Those checks are pending an approved compatibility resolution.

## Preservation

`preservation.json` compares exact pre/post database row hashes and schemas: **10,283 application rows and three assistant-history rows unchanged**, no row/schema/accounting changes. No original database startup, migrations, account writes or usage events were invoked. Fresh existing engineering/archive manifests are checked in `file-preservation.log`, `preservation-audit.json` and `solver-preservation.log` (55,296 original storage files, 2,090 proof files, 66 live schemas, 198 archived-only fingerprints and 21 coupled solver artifacts). The older baseline's 14 prior additions are historical and retained, not this installation's writes. No CAD/model/result/source-hash or authorization record was modified.

The auth adapter and local configuration files were left untouched; FIREBASE_AUTH_ENABLED was not enabled and no SDK initialized. Original historical reports, assistant ledger and audit records remain intact. Security-matrix statuses are unchanged; no cloud/authentication control is marked implemented because of package installation.

## Required next decision

Approve a narrowly scoped **runtime compatibility resolution plan** before proceeding: either a separately reviewed Node upgrade meeting the declared minimum, with compatibility/rollback verification for the whole existing frontend, or a separately approved alternative Firebase SDK version whose declared support includes the existing runtime. No version substitution is assumed. This report does not recommend blindly changing the system-wide Node installation.

After that decision and compatibility checks, resume the still-approved exact Admin SDK installation if applicable, review its full transitive plan and run focused checks. Any conflicts requiring unrelated package changes must again stop for approval. Project/provider/domain configuration, credential delivery/use, synthetic account/link provisioning, live F01–F07, cloud resources, billing and deployment remain under separate future gates. No automatic continuation beyond Gate 1.

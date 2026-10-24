# Gate 2I — disabled staging configuration review

24 October 2026, Asia/Calcutta. **Offline validation PASS. Independent match to official saved Web app configuration NOT VERIFIED: reference missing. Real authentication and public launch remain BLOCKED. Stop after Gate 2I.**

## Supplied material and provenance

The requested `docs/release-phase-c/gate-2i/` directory was initially absent. The subsequently supplied `D:\StruvoCivil_Gate2I_Disabled_Staging_Config.zip` contains exactly three small files: `README.md`, `VALIDATION.json`, and `frontend.staging.env.review`. Only those fixed documentation paths were imported, without overwriting existing files; archive traversal, arbitrary extraction and executable processing were not used. `archive-inventory.json` records original SHA-256 hashes and the ZIP digest.

The supplied README explicitly identifies the values as a screenshot transcription **not independently checked against the saved official settings**. Its instructions were treated as reference material, not authorization to open the Console, enable flags or modify environment files. The supplied `VALIDATION.json` was preserved byte-identically as a prior self-reported claim, not adopted as this review's evidence.

Neither the original screenshot nor an independent official Web app configuration export is included. The project/app display name is an owner assertion, not proof of app ID ownership. A local path to that independent source was requested while offline work continued; none was available at completion. No Console/account login, public config endpoint or live Firebase API was used to fill this gap.

## What was verified offline

**Eight tests passed** in `offline-tests.log`, using `offline-review.test.ts`, the unchanged existing `firebaseConfigurationIssues()` / `firebaseSignInAllowed()` / `prepareFirebase()` code, and checksum-verified portable Node 24.22.1. SDK initialization is mocked and external networking is blocked. `offline-test-result.json` records the validator source hash and successful test exit.

- Exactly eight allowlisted variable assignments; no duplicate/extra keys, shell interpolation or private-key/refresh-token/client-secret assignment markers.
- Exact owner-approved project ID: `struvocivil-918c9`.
- Exact expected standard authentication domain: `struvocivil-918c9.firebaseapp.com`, without scheme/port/path or attacker suffix.
- Prepared API key and Web app ID pass the **existing local format checks**. Their actual project/app ownership, registry association and key restrictions are not established by syntax. `identifier-validation.json` stores fingerprints and outcomes without repeating raw values in this report or tool output.
- `NEXT_PUBLIC_FIREBASE_AUTH_ENABLED=false` and `NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED=false` are explicit; Google and Email/Password are prepared without enabling the connection.
- The review artifact's SHA-256 matches the supplied packet's validation record. This establishes consistency of the packet, not independent official provenance.
- Even a mocked ready backend cannot cause this disabled configuration to initialize Firebase or call the network: **zero initializeApp/initializeAuth/fetch calls** in the test.

An initial inspection hit a terminal output-encoding error; it was corrected by printing sanitized JSON, without altering the packet. The only test warning is the existing Vitest environmentMatchGlobs deprecation. No application code fix, TypeScript/build/lint/browser rerun or genuine Firebase acceptance is claimed for this documentation-only review.

## Isolation and preservation

The received values remain only in the documentation review artifact. No runtime, launcher, normal development/production `.env` file, backend adapter or feature flag was changed. Test code lives in the evidence folder and is copied only into the retained isolated test workspace. Its environment is sanitized; no review values are loaded into a real Firebase SDK. No Analytics, account creation/linking, Google OAuth token handling or new authentication path was introduced.

`preservation-before.json`, `preservation-after.json`, and `preservation-comparison.json` verify identical original schemas/row fingerprints: **10,283 application rows and 3 assistant-history rows**, including accounting/audit history. All **30 prior tracked application inputs**, the Gate 2H validator/tests, dependencies and normal launchers remain byte-identical. The three supplied packet files also retain their original hashes.

Reuse Gate 2H's verified original-data manifests for **55,296 storage files, 2,090 proof files, 66 live schemas, 198 archive-only fingerprints and 21 solver artifacts**. They were not rescanned here; this phase wrote only documentation/test evidence and never opened CAD/solver originals for writes. No migration, cleanup, deployment, Git, SDK installation, service activation, billing, paid inference or solver execution occurred.

## Remaining Gate 2I qualification

Provide a separately sourced official configuration export or the source registration screenshot for **StruvoCivil Staging** in `struvocivil-918c9`, identified by its origin/date. Compare the exact `projectId`, `authDomain`, `appId` and public browser `apiKey` byte-for-byte offline; do not send Admin private keys, OAuth secrets, tokens or passwords. A screenshot can establish transcription consistency, but it does not prove the settings are still current without an authorized current review.

Until that evidence is supplied, **do not describe the identifiers as matched to the official saved app**. No values were guessed, repaired or substituted. Keep the configuration in this inert location with flags false; existing backend ADC and real F01–F07 remain blocked. Any future official configuration access, connection, account action or activation requires its separately defined authorization. **Stop after Gate 2I; no automatic continuation.**

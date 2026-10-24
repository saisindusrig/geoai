# Gate 2I — disabled staging configuration review

24 October 2026, Asia/Calcutta. **Gate 2I offline validation COMPLETE: all four identifiers exactly match the owner-supplied Firebase Console reference. Real authentication and public launch remain BLOCKED. Stop after Gate 2I.**

## Supplied material and provenance

The requested `docs/release-phase-c/gate-2i/` directory was initially absent. The subsequently supplied `D:\StruvoCivil_Gate2I_Disabled_Staging_Config.zip` contains exactly three small files: `README.md`, `VALIDATION.json`, and `frontend.staging.env.review`. Only those fixed documentation paths were imported, without overwriting existing files; archive traversal, arbitrary extraction and executable processing were not used. `archive-inventory.json` records original SHA-256 hashes and the ZIP digest.

The supplied README explicitly identifies the values as a screenshot transcription **not independently checked against the saved official settings**. Its instructions were treated as reference material, not authorization to open the Console, enable flags or modify environment files. The supplied `VALIDATION.json` was preserved byte-identically as a prior self-reported claim, not adopted as this review's evidence.

After the initial review, the owner supplied all four values directly in this conversation and explicitly identified them as copied from Firebase Console for StruvoCivil Staging. That is the accepted reference for completing this offline comparison. All four were compared byte-for-byte with the unchanged review artifact and matched. `owner-console-reference.json` records the source, field fingerprints and match outcomes without duplicating raw identifiers. No Console/account login, public config endpoint or live Firebase API was used. This is a comparison to an owner-supplied Console reference, not an independent live-service inspection.

The initial reference-missing assessment and test results are retained as `REVIEW-RESULTS-before-owner-reference.md`, `offline-tests-before-owner-reference.log` and `offline-test-result-before-owner-reference.json`. They are historical, superseded by this completed offline review. The supplied packet's original README/VALIDATION remain byte-identical rather than rewriting their provenance.

## What was verified offline

**Twelve tests passed** in `offline-tests.log`, using `offline-review.test.ts`, the unchanged existing `firebaseConfigurationIssues()` / `firebaseSignInAllowed()` / `prepareFirebase()` code, and checksum-verified portable Node 24.22.1. Four added tests verify exact field fingerprints against the accepted owner reference. SDK initialization is mocked and external networking is blocked. `offline-test-result.json` records the validator source hash and successful test exit.

- Exactly eight allowlisted variable assignments; no duplicate/extra keys, shell interpolation or private-key/refresh-token/client-secret assignment markers.
- Exact owner-approved project ID: `struvocivil-918c9`.
- Exact expected standard authentication domain: `struvocivil-918c9.firebaseapp.com`, without scheme/port/path or attacker suffix.
- Prepared API key and Web app ID pass the **existing local format checks** and exactly match the owner-supplied Console values, as do project ID and auth domain. Actual service availability, provider behavior and key restrictions were not tested. `identifier-validation.json` stores fingerprints and outcomes without repeating raw values in this report or tool output.
- `NEXT_PUBLIC_FIREBASE_AUTH_ENABLED=false` and `NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED=false` are explicit; Google and Email/Password are prepared without enabling the connection.
- The review artifact's SHA-256 matches the supplied packet's validation record. This establishes consistency of the packet, not independent official provenance.
- Even a mocked ready backend cannot cause this disabled configuration to initialize Firebase or call the network: **zero initializeApp/initializeAuth/fetch calls** in the test.

An initial inspection hit a terminal output-encoding error; it was corrected by printing sanitized JSON, without altering the packet. The only test warning is the existing Vitest environmentMatchGlobs deprecation. No application code fix, TypeScript/build/lint/browser rerun or genuine Firebase acceptance is claimed for this documentation-only review.

## Isolation and preservation

The received values remain only in the documentation review artifact. No runtime, launcher, normal development/production `.env` file, backend adapter or feature flag was changed. Test code lives in the evidence folder and is copied only into the retained isolated test workspace. Its environment is sanitized; no review values are loaded into a real Firebase SDK. No Analytics, account creation/linking, Google OAuth token handling or new authentication path was introduced.

`preservation-owner-reference-before.json`, `preservation-owner-reference-after.json`, and `preservation-comparison.json` verify identical original schemas/row fingerprints: **10,283 application rows and 3 assistant-history rows**, including accounting/audit history. All **30 prior tracked application inputs**, the Gate 2H validator/tests, dependencies and normal launchers remain byte-identical. The three supplied packet files also retain their original hashes. Earlier preservation evidence remains retained.

Reuse Gate 2H's verified original-data manifests for **55,296 storage files, 2,090 proof files, 66 live schemas, 198 archive-only fingerprints and 21 solver artifacts**. They were not rescanned here; this phase wrote only documentation/test evidence and never opened CAD/solver originals for writes. No migration, cleanup, deployment, Git, SDK installation, service activation, billing, paid inference or solver execution occurred.

## Completed scope and remaining live gates

The owner's explicit Console reference resolves the missing-reference blocker for Gate 2I. The prepared values were not edited: exact `projectId`, `authDomain`, `appId` and public browser `apiKey` comparisons all passed. **No further reference is required for this authorized offline scope.**

Keep the configuration in this inert location with Firebase/recovery flags false and both providers prepared. No values were guessed, repaired or substituted; no Analytics was initialized. Existing backend ADC and real F01–F07 remain blocked. Matching identifiers is not evidence of successful authentication, account authorization, signup prevention, revocation or provider availability. Any future connection, account action, backend identity change or activation requires separate authorization. No production settings or billing changed. **Stop after Gate 2I; no automatic continuation.**

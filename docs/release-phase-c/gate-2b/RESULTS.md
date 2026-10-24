# Phase C Gate 2B — staging approval preparation

24 October 2026, Asia/Calcutta. **Approval packet complete; activation and F01–F07 remain BLOCKED / NOT RUN. Public launch remains BLOCKED.**

## Delivered

1. `STAGING-CONFIGURATION.md`: dedicated-project eligibility, one reviewed web app, email/password only, exact proposed loopback origin/auth-domain distinction, service-side signup denial, existing feature flags, proposed in-memory policy, new data/identity-link architecture and no-seed startup prerequisites.
2. `IAM-CREDENTIALS-AND-COSTS.md`: least-privilege role candidates, separation of cloud/internal authority, current certificate-file limitation, credential custody, network families, authentication versus other Google Cloud costs, operator traffic limits and budget-alert limitations.
3. `ACCEPTANCE-AND-ROLLBACK.md`: existing F01–F07 numbering retained; each case specifies genuine operations, synthetic subjects, expected behavior, failures, extra approvals and sanitized evidence. Rollback closes isolated ingress before disabling Firebase and never reopens development/legacy access.
4. `APPROVAL-CHECKLIST.md`: ten independent, unchecked human decisions. No project, provider, identity, credential, cost or test operation is implicitly approved.
5. `approval-plan.json` and `verification.json`: machine-readable pending decisions, blocked test cases and focused document/preservation checks.

## Material decisions and blockers

- **Existing project versus new:** unresolved. No project inventory or owner attestation was supplied or accessed. Reuse is conditional on dedicated non-production isolation; otherwise a new project is required under separate approval. No project ID, real domain, operator or credential was guessed.
- **Public signup:** hiding the application's signup form does not restrict direct Firebase registration. Require supported service-side end-user signup restriction and a genuine denial test. Provider/domain/API-key configuration alone is not that protection. Selected-tier support and any upgrade/cost requirement remain unknown.
- **Identity-link storage:** existing resolver requires links, internal users and audit approvals in the same new staging database/session. No cross-database development-user references, email merges, automatic account creation or new resolver is proposed. Reviewed bootstrap/link/schema tooling remains a prerequisite.
- **Credential delivery:** current adapter requires an approved certificate file; it does not support keyless ADC/WIF. A key-prohibiting policy blocks activation until a separately reviewed integration exists. No broad runtime Auth Admin role is proposed.
- **Session/rollback:** reload loses in-memory sign-in; tabs are independent. Client logout is not global revocation. Turning off backend Firebase on a reachable staging API would expose its legacy JWT branch; rollback therefore isolates/stops staging first and leaves enforced auth on.
- **Acceptance completeness:** F05's full recovery/account-change/reauthentication/link-operation workflow is not implemented. F01's genuinely signed wrong-project subcase needs a separately authorized isolated issuer source; a one-project test cannot silently claim it. Real expiry, recovery messages, provider abuse behavior, deleted-user status, outage handling and global revocation still need explicit scope and real evidence.
- **Costs/infrastructure:** no candidate project's tier or billing status is verified. Prefer eligible unbilled Spark and stop on required upgrades or charges. Local authentication qualification cannot qualify cloud storage, PostgreSQL durability, production HTTPS, distributed AI budgets or a public release. No budget-alert-as-hard-cap claim.

Public official documentation was checked for IAM, registration restrictions, persistence, enumeration, limits and costs; links are placed beside claims in the packet. No console, authenticated project inventory or authentication endpoint was used. Findings distinguish current source behavior from unverified project/service configuration.

## Verification and preservation

This is a documentation-only approval phase. Application authentication, geometry, engine, SDK packages, environment files, launchers and the approved 40-control matrix were not modified. No frontend/backend/build/browser suite was rerun or presented as fresh Gate 2B live evidence. Gate 2A's tests remain prior local/mock evidence.

Focused checks validate all ten pending approvals, exactly F01–F07 with required fields and NOT_RUN status, valid internal document references, unchanged application/dependency/matrix input hashes, and exact read-only schema/row matches with the Milestone 12 baseline: **10,283 application rows and 3 assistant-history rows**. Preservation scripts open databases read-only and do not load application settings or credentials.

Reuse Gate 2A's original-file manifests: 55,296 storage files, 2,090 proof files, 66 live schemas, 198 archived-only fingerprints and 21 solver artifacts. No new file scan, backup extraction, migration, original-data access for writes or cleanup was required for these documents. Relevant 40-control entries retain their existing Partial/Missing/Unverified outcomes; B03, B04, B12 and live A06/A07/A11/B05/B17/B20 qualification remain open.

No service account/credential configuration, project/user creation, email, live verification, billing, deployment, DNS change, Git, package installation, engineering calculation or paid Nebius inference occurred. **Next step is human review of the checklist only. Stop at Gate 2B.**

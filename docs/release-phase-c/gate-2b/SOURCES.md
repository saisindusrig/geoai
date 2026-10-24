# Gate 2B — reviewed sources and provenance

Public official documentation reviewed 24 October 2026. No console login, project inventory, credentials or authentication API use. Published schemas/pricing describe possible services, not the configuration, permissions or bill of an uninspected project. Recheck selected-project availability and current terms before separately approved execution.

- [Identity Platform users and self-service restrictions](https://docs.cloud.google.com/identity-platform/docs/concepts-manage-users): project-wide shared user database and restricting end-user account creation/deletion.
- [Project Config API](https://docs.cloud.google.com/identity-platform/docs/reference/rest/v2/Config): authorized-domain semantics, product subtypes and client signup/deletion flags. The schema does not establish entitlement on the proposed candidate.
- [Auth API IAM mapping](https://docs.cloud.google.com/identity-platform/docs/access-control): account lookup versus mutation/configuration permissions.
- [Firebase management permissions](https://firebase.google.com/docs/projects/iam/permissions): app/project inspection and app registration permissions; additional setup privileges require review.
- [Authentication role definitions](https://docs.cloud.google.com/iam/docs/roles-permissions/firebaseauth): predefined Viewer/Admin scopes and sensitive permissions to exclude from runtime.
- [Service-account key custody](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys): avoid unmanaged long-lived keys and protect any approved key-delivery boundary.
- [Email enumeration protection](https://docs.cloud.google.com/identity-platform/docs/admin/email-enumeration-protection): service behavior differs from generic UI handling; inspect the actual project setting.
- [Web persistence](https://firebase.google.com/docs/auth/web/auth-state-persistence): memory-only reload and independent-tab behavior.
- [Session revocation](https://firebase.google.com/docs/auth/admin/manage-sessions): distinguish logout/token expiry/revocation and extra account-service lookups.
- [Firebase pricing](https://firebase.google.com/pricing), [Identity Platform pricing](https://cloud.google.com/identity-platform/pricing), [Authentication quotas](https://firebase.google.com/docs/auth/limits): product/plan differences and real mail/API constraints, not spending authorization.
- [Firebase budget alerts](https://firebase.google.com/docs/projects/billing/budget-alerts): notifications are not a verified hard cap for all services.

Local evidence: Gate 2A RESULTS/STAGING-PREREQUISITES and preserved verification outputs; Milestone 10 audited identity association report; Phase B RESULTS/STAGING-QUALIFICATION F01–F07; Phase C PREFLIGHT-AND-APPROVALS; current 40-control matrix; backend `firebase_auth.py`, `security.py`, `identity_links.py`, DB startup/selection and frontend Firebase/session implementation. Installed official Admin source was inspected as text only for verification/revocation behavior; no SDK initialized.

Superseded Milestone 10 statements that browser SDK/session integration were absent are historical. Gate 1D and Gate 2A establish installed SDKs and locally verified integration; neither establishes genuine sign-in or a configured Firebase project.

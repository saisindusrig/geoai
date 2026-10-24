"""Create documentation metadata only. No settings, credentials, SDK or cloud imports."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
approvals = [
    ('G2B-01', 'Project and product'), ('G2B-02', 'Provider and service configuration'),
    ('G2B-03', 'Origin and domain'), ('G2B-04', 'IAM and credentials'),
    ('G2B-05', 'Clean data, bootstrap and linking'), ('G2B-06', 'Session policy'),
    ('G2B-07', 'Sensitive acceptance operations'), ('G2B-08', 'Live acceptance execution'),
    ('G2B-09', 'Costs and availability'), ('G2B-10', 'Rollback, retention and restart'),
]
cases = [
    dict(id='F01', name='Sign-in and verified identity', identities=['A', 'B', 'U'],
         operation='Official SDK sign-in; backend token/project/lifetime verification; direct signup-denial negative; conditional genuine wrong-project token.',
         expected='Linked exact internal identities; 401 invalid/expired, 403 unlinked, 503 unavailable; no signup or fallback.',
         failure='Wrong identity or token accepted, automatic linking, service signup, or fallback.',
         additional_approval='Live sign-in and subject provisioning; helper issuer needs independent approval; natural expiry window.',
         approval_ids=['G2B-01', 'G2B-02', 'G2B-03', 'G2B-04', 'G2B-05', 'G2B-06', 'G2B-08', 'G2B-09'],
         unresolved='Valid wrong-project issuer unavailable; no second project implicitly authorized.'),
    dict(id='F02', name='Revocation, disable/delete and outages', identities=['A', 'B', 'D'],
         operation='Retain pre-action token in memory; revoke, disable/re-enable, independently approved D deletion; isolated service/certificate failures.',
         expected='No protected access with old tokens; revoked/disabled 401; service unavailable 503; deleted status observed without assuming 401.',
         failure='Old token authorizes, skipped revocation, outage fallback or unrelated account affected.',
         additional_approval='Exact subject/actions, deletion separately opt-in, scoped network faults and operator permissions.',
         approval_ids=['G2B-04', 'G2B-05', 'G2B-07', 'G2B-08', 'G2B-09', 'G2B-10'],
         unresolved='Live revocation/outage/deleted-subject status unqualified.'),
    dict(id='F03', name='Logout', identities=['A', 'B'],
         operation='SDK logout, back navigation, no-token requests and delayed reads/streams, account switch and independent second tab.',
         expected='Local private state cleared, stale results rejected, no-token 401; other tab independent; no global-revocation claim.',
         failure='Previous-account cache, resurrected sign-in, fallback or false global logout.',
         additional_approval='Live session tests; separate G2B-07 authorization if server-wide revocation is required.',
         approval_ids=['G2B-06', 'G2B-08', 'G2B-09'], unresolved='Live session semantics not run.'),
    dict(id='F04', name='Password change/reset', identities=['A', 'OWNED_UNKNOWN_INBOX'],
         operation='Approved reset requests and official hosted handler; expiry, single-use, recipient/domain scope and old-session checks.',
         expected='Generic known/unknown outcome; genuine action binding/expiry/replay enforcement; approved old-session policy enforced.',
         failure='Enumeration, action replay, expiry acceptance, old-token authorization or mail outside approved inboxes.',
         additional_approval='Real mail, recipient/action host, password changes and timed expiry; no application change-password UI exists.',
         approval_ids=['G2B-02', 'G2B-03', 'G2B-05', 'G2B-07', 'G2B-08', 'G2B-09'],
         unresolved='Delivery, real expiry and provider abuse protections unqualified.'),
    dict(id='F05', name='Recovery/account change', identities=['A', 'P0'],
         operation='Approved real reauthentication/recovery and identity-change procedure; link/audit/approver revocation.',
         expected='Exact UID association; no email merge or ownership transfer; revoked approvals deny access.',
         failure='Self-approved elevation, stale link, overwritten historical approval or false completed recovery workflow.',
         additional_approval='Recovery identity policy and reviewed linking/account-change procedure/tooling before writes.',
         approval_ids=['G2B-05', 'G2B-07', 'G2B-08', 'G2B-10'],
         unresolved='Complete application recovery/reauthentication/account-change and link-approval workflow not implemented.'),
    dict(id='F06', name='Cross-user ownership', identities=['A', 'B', 'U'],
         operation='New synthetic project/file/result-identity/history own versus cross-user reads and safe metadata probes.',
         expected='Own access only; 401 invalid/missing, 403 or policy 404 other owner; no forged role/ID, stale substitution or private history.',
         failure='Cross-user access, original-data/ledger reference, role escalation or execution of prohibited workloads.',
         additional_approval='New fixtures and reviewed harmless probes; no solver/import/export execution tests even as denial probes.',
         approval_ids=['G2B-05', 'G2B-08', 'G2B-09'],
         unresolved='Live ownership unqualified; synthetic records do not qualify engineering truth or cloud durability.'),
    dict(id='F07', name='Browser session policy', identities=['A', 'B'],
         operation='Reload/close/multiple tabs, token refresh/real expiry, rejected sessions, stale async boundaries and persistence inspection.',
         expected='Memory-only per tab, re-login after reload, no legacy/cookie fallback, no account bleed; revocation on next protected request.',
         failure='Durable Firebase tokens, old private data, unintended tab sharing or unauthorized/replayed requests.',
         additional_approval='Session limitations and live timed window; server-wide revocation separately approved.',
         approval_ids=['G2B-06', 'G2B-08', 'G2B-09'],
         unresolved='Real browser/provider lifecycle and production HTTPS/XSS qualification remain pending.'),
]
for case in cases:
    case['status'] = 'NOT_RUN'
plan = dict(
    phase='Gate 2B', date='2026-10-24', timezone='Asia/Calcutta',
    purpose='APPROVAL_PREPARATION_ONLY', firebase_enabled=False,
    project_accessed=False, credentials_accessed=False, live_acceptance_authorized=False,
    public_launch='BLOCKED', project_decision='UNRESOLVED', approved_project_id=None,
    approved_web_app_id=None, approved_operator=None, approved_origin=None,
    proposed_origin='http://localhost:3017', proposed_backend='http://127.0.0.1:8003',
    proposed_auth_domain='<approved-project-id>.firebaseapp.com',
    existing_project_eligible='UNKNOWN_UNTIL_OWNER_ATTESTATION',
    provider_proposal='EMAIL_PASSWORD_ONLY', persistence_proposal='IN_MEMORY_PER_TAB',
    data_topology='NEW_STAGING_DB_WITH_USERS_AUDITS_AND_IDENTITY_LINKS_COLOCATED',
    provisioning_performed=False, genuine_test_results=False,
    proposed_test_envelope=dict(firebase_accounts=4, sdk_operations=100,
        backend_requests=300, recovery_messages=6, initiated_operations_per_second=2,
        expiry_window_minutes=75, hard_billing_cap=False),
    approvals=[dict(id=key, decision=name, status='PENDING', approved_by=None,
                    approved_at=None) for key, name in approvals],
    acceptance_cases=cases,
    runtime_permission_candidate=['firebaseauth.users.get'],
    current_credential_boundary='CERTIFICATE_FILE_ONLY_NOT_ADC_WIF',
    documents=['RESULTS.md', 'STAGING-CONFIGURATION.md', 'IAM-CREDENTIALS-AND-COSTS.md',
               'ACCEPTANCE-AND-ROLLBACK.md', 'APPROVAL-CHECKLIST.md'],
)
(OUT / 'approval-plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
inputs = json.loads((ROOT / 'docs/release-phase-c/gate-2a/verified-source-hashes.json').read_text())
manifest = {}
for name, expected in inputs.items():
    path = ROOT / 'frontend' / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == expected, name
    manifest['frontend/' + name] = actual
for name in ['backend/app/core/firebase_auth.py', 'backend/app/core/security.py',
             'backend/app/services/identity_links.py', 'backend/app/core/config.py',
             'backend/requirements.txt', 'frontend/package.json', 'frontend/package-lock.json',
             'run-website.bat', 'start-copilot-review.ps1', 'scripts/verify-local-node.cjs',
             'docs/release-security-40/40-CONTROL-MATRIX.json',
             'docs/release-security-40/40-CONTROL-MATRIX.md']:
    manifest[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
manifest_path = OUT / 'inputs-before.json'
if manifest_path.exists():
    assert json.loads(manifest_path.read_text()) == manifest, 'Inputs changed since packet preparation'
else:
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Prepared pending approval packet and', len(manifest), 'unchanged input hashes')

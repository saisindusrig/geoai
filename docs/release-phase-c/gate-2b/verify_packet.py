"""Documentation checks only; no app/SDK imports or service calls."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
plan = json.loads((OUT / 'approval-plan.json').read_text())
assert plan['purpose'] == 'APPROVAL_PREPARATION_ONLY'
for key in ['firebase_enabled', 'project_accessed', 'credentials_accessed',
            'live_acceptance_authorized', 'provisioning_performed', 'genuine_test_results']:
    assert plan[key] is False, key
assert plan['public_launch'] == 'BLOCKED'
assert all(plan[key] is None for key in ['approved_project_id', 'approved_web_app_id', 'approved_operator', 'approved_origin'])
ids = [row['id'] for row in plan['approvals']]
assert ids == [f'G2B-{i:02}' for i in range(1, 11)]
checklist = (OUT / 'APPROVAL-CHECKLIST.md').read_text(encoding='utf-8')
assert checklist.count('- [ ] **G2B-') == 10 and '- [x]' not in checklist.lower()
assert all(row['status'] == 'PENDING' and row['approved_by'] is None and row['approved_at'] is None for row in plan['approvals'])
assert [row['id'] for row in plan['acceptance_cases']] == [f'F{i:02}' for i in range(1, 8)]
for row in plan['acceptance_cases']:
    assert row['status'] == 'NOT_RUN'
    for field in ['operation', 'identities', 'expected', 'failure', 'additional_approval', 'unresolved']:
        assert row[field], (row['id'], field)
    assert set(row['approval_ids']) <= set(ids)
    assert f"## {row['id']} " in (OUT / 'ACCEPTANCE-AND-ROLLBACK.md').read_text(encoding='utf-8')
for name in plan['documents']:
    content = (OUT / name).read_text(encoding='utf-8')
    assert content.strip() and 'PRIVATE KEY-----' not in content
manifest = json.loads((OUT / 'inputs-before.json').read_text())
changed = [name for name, expected in manifest.items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
assert not changed, changed
before = json.loads((OUT / 'preservation-before.json').read_text())
after = json.loads((OUT / 'preservation-after.json').read_text())
assert before == after
result = dict(phase='Gate 2B', approval_preparation='COMPLETE',
              approval_decisions_pending=10, real_service_cases_not_run=7,
              application_manifest_and_matrix_hashes_unchanged=len(manifest),
              dev_rows=after['dev.db']['rows'], assistant_history_rows=after['assistant-history.db']['rows'],
              rows_and_schema_unchanged=True, document_checks='PASS',
              firebase_activation='NOT_AUTHORIZED', public_launch='BLOCKED')
(OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))

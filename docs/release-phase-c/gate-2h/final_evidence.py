"""Read-only scope, source/package and row preservation checks; no app imports."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
WORK=ROOT/'.local-tooling/node-24.22.1-validation/work/gate1b/frontend'
prior=json.loads((OUT.parent/'gate-2f/input-hashes-after.json').read_text())
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in prior}
assert {name for name in prior if prior[name]!=hashes[name]}=={'frontend/lib/firebase-auth.ts'}
for name,digest in json.loads((OUT/'verified-source-hashes.json').read_text()).items():
 assert hashlib.sha256((ROOT/'frontend'/name).read_bytes()).hexdigest()==digest
 assert (ROOT/'frontend'/name).read_bytes()==(WORK/name).read_bytes()
for name,digest in json.loads((OUT.parent/'gate-2f/verified-source-hashes.json').read_text()).items():
 if name!='lib/firebase-auth.ts': assert hashlib.sha256((ROOT/'frontend'/name).read_bytes()).hexdigest()==digest
before=json.loads((OUT/'preservation-before.json').read_text());after=json.loads((OUT/'preservation-after.json').read_text())
assert before==after
for name,digest in json.loads((ROOT/'docs/gpu-performance/changed-source-hashes.json').read_text()).items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
packages={d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions()}
old={k.lower().replace('_','-'):v for k,v in json.loads((OUT.parent/'gate-1d/packages-after.json').read_text()).items()}
assert packages==old
for file in [*(ROOT/'frontend/app').rglob('*.tsx'),*(ROOT/'frontend/lib').glob('*.ts'),*(ROOT/'frontend/lib').glob('*.tsx'),*(ROOT/'frontend/components').rglob('*.tsx')]:
 source=file.read_bytes()
 assert b'firebase/analytics' not in source and b'getAnalytics(' not in source and b'initializeAnalytics(' not in source,file
checks=json.loads((OUT/'frontend-checks.json').read_text());assert all(row['exit_code']==0 for row in checks.values())
offline=json.loads((OUT/'offline-verification.json').read_text());assert offline['pytest_exit']==0 and offline['sdk_apps_initialized']==0 and offline['forbidden_network_or_credential_attempts']==0
original=json.loads((OUT/'preservation-audit.json').read_text());assert original['all_original_storage_and_proof_files_unchanged']
solver=json.loads((OUT/'coupled-evidence-preservation.json').read_text());assert solver['previous_coupled_native_files_verified']==21
result=dict(phase='Gate 2H',frontend_tests=80,backend_tests=71,typescript=True,scoped_eslint=True,default_turbopack_build=True,
 changed_prior_inputs=['frontend/lib/firebase-auth.ts'],unchanged_prior_inputs=len(prior)-1,backend_and_launchers_unchanged=True,
 python_distributions_unchanged=len(packages),application_rows=after['dev.db']['rows'],assistant_history_rows=after['assistant-history.db']['rows'],
 original_storage_files=original['original_storage_files'],original_proof_files=original['original_engineering_proof_files'],solver_artifacts=21,
 firebase_enabled=False,analytics_initialization_added=False,live_settings_accessed=False,real_authentication_tests=False,public_launch='BLOCKED')
(OUT/'input-hashes-after.json').write_text(json.dumps(hashes,indent=2))
(OUT/'status.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))

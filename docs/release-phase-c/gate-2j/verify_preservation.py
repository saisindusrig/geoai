"""Compare original byte/row/source manifests. Does not load app or secret settings."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
source=json.loads((OUT/'source-asset-fingerprints-before.json').read_text())
changed=[name for name,sha in source.items() if digest(ROOT/name)!=sha]
db=json.loads((OUT/'database-file-fingerprints-before.json').read_text())
db_changed=[r['path'] for r in db if digest(ROOT/r['path'])!=r['sha256']]
prior=json.loads((OUT.parent/'gate-2h/input-hashes-after.json').read_text())
prior_changed=[name for name,sha in prior.items() if digest(ROOT/name)!=sha]
before=json.loads((OUT/'preservation-before.json').read_text());after=json.loads((OUT/'preservation-after.json').read_text())
candidate=json.loads((OUT/'safe-candidate-files.json').read_text())
cache_changed=[r['path'] for r in candidate if digest(ROOT/r['path'])!=r['sha256']]
for row in json.loads((OUT.parent/'gate-2i/archive-inventory.json').read_text())['files']:assert digest(ROOT/row['path'])==row['sha256']
archive=json.loads((OUT/'preservation-audit.json').read_text());solver=json.loads((OUT/'coupled-evidence-preservation.json').read_text())
result=dict(source_asset_fingerprints=len(source),changed_source_assets=changed,current_database_files=len(db),changed_database_files=db_changed,
 prior_application_inputs=len(prior),changed_prior_inputs=prior_changed,row_and_schema_baseline_matches=before==after,
 application_rows=after['dev.db']['rows'],assistant_history_rows=after['assistant-history.db']['rows'],
 safe_cache_files=len(candidate),changed_cache_candidates=cache_changed,
 original_storage_files=archive['original_storage_files'],original_proof_files=archive['original_engineering_proof_files'],
 all_original_storage_and_proof_files_unchanged=archive['all_original_storage_and_proof_files_unchanged'],solver_artifacts=solver['previous_coupled_native_files_verified'],
 deletions=0,migrations=0,environment_created=False,runtime_isolation_qualified=False,public_launch='BLOCKED')
(OUT/'preservation-comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
assert not changed and not db_changed and not prior_changed and not cache_changed and before==after

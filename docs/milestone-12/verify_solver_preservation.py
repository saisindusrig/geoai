"""Check previously delivered coupled solver artifacts; never restore or modify them."""
import json,hashlib,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/milestone-12'
db=ROOT/'docs/foundation-system/isolated/foundation.db'
with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
 body=json.loads(c.execute('select result_json from engineering_analyses where id=693').fetchone()[0])
case=body['cases'][0];checked=[]
for run in case['validation']['mesh_runs']:
 folder=ROOT/'docs/coupled-floor/solver-evidence'/run['run_id'];manifest=json.loads((folder/'manifest.json').read_text())
 for name,sha in manifest['artifact_sha256'].items():
  assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==sha,(run['run_id'],name)
  checked.append(str((folder/name).relative_to(ROOT)))
for name,sha in case['artifact_sha256'].items():assert hashlib.sha256((ROOT/'docs/coupled-floor/solver-evidence'/case['run_id']/name).read_bytes()).hexdigest()==sha,name
result=dict(previous_coupled_analysis=693,previous_coupled_native_files_verified=len(checked),files=checked,no_restore_or_modify=True)
(OUT/'coupled-evidence-preservation.json').write_text(json.dumps(result,indent=2));print(result['previous_coupled_native_files_verified'])

"""Produce exact candidate manifests and counts only. No deletion capabilities."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
inventory=json.loads((OUT/'inventory.json').read_text())
for group,row in inventory['groups'].items():
 if group.lower().endswith(('.db','.sqlite','.sqlite3','.db-wal','.db-shm','.db-journal')):row['classification']='NEVER DELETE AUTOMATICALLY: database or journal'
inventory.pop('git_excluded',None);inventory['root_git_excluded']=True
(OUT/'inventory.json').write_text(json.dumps(inventory,indent=2))
base=ROOT/'.local-tooling/node-24.22.1-validation/work/gate1b/frontend'
safe=[];manifest=[]
for gate in ('gate2a','gate2f','gate2f-ui-fixture','gate2h'):
 path=base/('.next-'+gate)/'cache'
 assert path.is_dir() and not path.is_symlink()
 owner='gate-2f' if gate.startswith('gate2f') else 'gate-2a' if gate=='gate2a' else 'gate-2h'
 assert (OUT.parent/owner/'RESULTS.md').is_file()
 files=[]
 for file in path.rglob('*'):
  assert not file.is_symlink() and not file.is_junction()
  if file.is_file():
   assert file.resolve().is_relative_to(path.resolve())
   assert file.suffix not in ('.db','.sqlite','.sqlite3','.cad','.dwg','.dxf','.ifc')
   assert not file.name.startswith('.env')
   row=dict(path=str(file.relative_to(ROOT)).replace('\\','/'),bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
   files.append(row);manifest.append(row)
 safe.append(dict(path=str(path.relative_to(ROOT)).replace('\\','/'),absolute_path=str(path),files=len(files),bytes=sum(x['bytes'] for x in files),
  category='SAFE TO CLEAN',authorization='NOT_AUTHORIZED',ownership_evidence='docs/release-phase-c/'+owner+'/RESULTS.md',
  prerequisites=['repeat ownership/hash and reparse checks','prove no active tooling process uses this path','explicit approval for exact manifest'],
  benefit='Regenerable compiler/image/font cache only; does not remove users or freshen application data',
  recovery='Retain compiled output and source/lockfiles. Rebuild only in guarded isolated copy with verified Node; no package install or network unless separately approved.'))
review=[]
for path,row in inventory['build_roots'].items():
 review.append(dict(path=path,**row,category='REVIEW BEFORE CLEANING',reason='Compiled output or historical qualification/failure evidence. Cache subset alone is separately listed; do not delete this whole root.',recovery='Retain immutable build/failure evidence unless an exact source/environment recovery snapshot is separately verified.'))
review.append(dict(path='backend/**/__pycache__/*.pyc (exact list in bytecode-candidates.json)',files=len(json.loads((OUT/'bytecode-candidates.json').read_text())),bytes=sum(x['bytes'] for x in json.loads((OUT/'bytecode-candidates.json').read_text())),category='REVIEW BEFORE CLEANING',reason='283 source-backed bytecode files, but normal backend is running; no pause/cleanup authorized.',recovery='Existing Python reimports matching retained source. First verify no sourceless modules and approve service pause.'))
result=dict(dry_run=True,deletion_authorized=False,deletions_executed=0,migrations_executed=0,safe_candidates=safe,review_candidates=review,
 safe_file_count=len(manifest),safe_logical_bytes=sum(x['bytes'] for x in manifest),safe_logical_MiB=round(sum(x['bytes'] for x in manifest)/2**20,2),
 allocated_disk_recovery_guaranteed=False,root_git_excluded=True,nested_reparse_points_not_followed=inventory['reparse_points_not_followed'])
(OUT/'safe-candidate-files.json').write_text(json.dumps(manifest,indent=2))
(OUT/'cleanup-dry-run.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ('dry_run','deletions_executed','migrations_executed','safe_file_count','safe_logical_bytes','safe_logical_MiB')},indent=2))

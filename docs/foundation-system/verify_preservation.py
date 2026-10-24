"""Reuse verified manifests. Read originals only; never restore/delete/change data."""
import hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/scripts'))
from project_cleanup_audit import database_fingerprint
backup=Path((ROOT/'.cleanup-backup-path').read_text().strip())
manifest=json.loads((backup/'source-manifest.json').read_text())
files=[r for r in manifest if r['path'].startswith(('backend/storage/','backend/.cad-proof-output/'))]
changed=[]
for row in files:
 path=ROOT/row['path']
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:changed.append(row['path'])
databases=[]
for row in json.loads((backup/'database-baseline.json').read_text()):
 path=ROOT/row['path'];saved=backup/'databases'/row['path']
 query='select type,name,tbl_name,sql from sqlite_master order by type,name'
 with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(saved.as_uri()+'?mode=ro',uri=True) as b:
  schema=a.execute(query).fetchall()==b.execute(query).fetchall()
 databases.append(dict(path=row['path'],rows_unchanged=database_fingerprint(path)==row['tables'],schema_unchanged=schema))
result=dict(original_storage_files=sum(r['path'].startswith('backend/storage/') for r in files),original_engineering_proof_files=sum(r['path'].startswith('backend/.cad-proof-output/') for r in files),changed_or_missing_files=changed,databases=databases,all_preserved=not changed and all(r['rows_unchanged'] and r['schema_unchanged'] for r in databases),backup_used=str(backup),no_restore_or_delete_performed=True)
Path(__file__).with_name('preservation-manifests.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='databases'},indent=2));print('Original databases checked:',len(databases));assert result['all_preserved']

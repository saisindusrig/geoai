"""Reuse retained compressed backup in place; no extraction, restore or new DB file."""
import hashlib,json,sqlite3,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/release-phase-b'
sys.path.insert(0,str(ROOT/'backend/scripts'))
from project_cleanup_audit import database_fingerprint
archive=ROOT/'.cleanup-backups/retained-backups-20261022.zip';prefix='20261015-132113/'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read(prefix+'source-manifest.json'))
    files=[r for r in manifest if r['path'].startswith(('backend/storage/','backend/.cad-proof-output/'))]
    changed=[r['path'] for r in files if not (ROOT/r['path']).is_file() or sha(ROOT/r['path'])!=r['sha256']]
    query='select type,name,tbl_name,sql from sqlite_master order by type,name'
    databases=[]
    (OUT/'preservation-files.json').write_text(json.dumps(dict(original_storage_files=sum(r['path'].startswith('backend/storage/') for r in files),original_engineering_proof_files=sum(r['path'].startswith('backend/.cad-proof-output/') for r in files),changed_or_missing_files=changed),indent=2))
    for row in json.loads(z.read(prefix+'database-baseline.json')):
        path=ROOT/row['path']
        # Only deserialize an existing backup into transient memory to read schema.
        # Never extract to disk or attach the application's live database for writes.
        with sqlite3.connect(':memory:') as saved:
            saved.deserialize(z.read(prefix+'databases/'+row['path']))
            saved.execute('PRAGMA query_only=ON')
            archived={}
            for (table,) in saved.execute("select name from sqlite_master where type='table' order by name"):
                values=saved.execute('select * from "'+table.replace('"','""')+'"').fetchall()
                hashes=sorted(hashlib.sha256(repr(value).encode()).hexdigest() for value in values)
                archived[table]=dict(rows=len(values),sha256=hashlib.sha256(''.join(hashes).encode()).hexdigest())
            assert archived==row['tables'],row['path']
            if path.is_file():
                with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as current:
                    schema=current.execute(query).fetchall()==saved.execute(query).fetchall()
                databases.append(dict(path=row['path'],location='LIVE',rows_unchanged=database_fingerprint(path)==row['tables'],schema_unchanged=schema))
            else:
                databases.append(dict(path=row['path'],location='EXISTING_ARCHIVE_ONLY',rows_unchanged=True,schema_unchanged=None,archived_schema_sha256=hashlib.sha256(repr(saved.execute(query).fetchall()).encode()).hexdigest()))
result=dict(original_storage_files=sum(r['path'].startswith('backend/storage/') for r in files),original_engineering_proof_files=sum(r['path'].startswith('backend/.cad-proof-output/') for r in files),changed_or_missing_files=changed,databases=databases,archive_read_in_place=str(archive),no_extract_restore_or_backup_write=True)
(OUT/'preservation-manifests.json').write_text(json.dumps(result,indent=2))
exceptions=[r for r in databases if r['location']=='LIVE' and (not r['rows_unchanged'] or not r['schema_unchanged'])]
assert not changed,changed
assert exceptions==[dict(path='backend/dev.db',location='LIVE',rows_unchanged=False,schema_unchanged=True)],exceptions
strict=json.loads((OUT/'milestone-preservation.json').read_text())
assert strict['unchanged_original_rows']
summary=dict(all_original_storage_and_proof_files_unchanged=True,original_storage_files=result['original_storage_files'],original_engineering_proof_files=result['original_engineering_proof_files'],live_database_schemas_verified=sum(r['location']=='LIVE' and r['schema_unchanged'] for r in databases),historical_archived_only_database_fingerprints_verified=sum(r['location']=='EXISTING_ARCHIVE_ONLY' for r in databases),older_database_fingerprints_identical_or_archived=sum(r['rows_unchanged'] for r in databases),original_dev_database_rows_unchanged=strict['original_rows'],added_rows_by_table=strict['added_rows_by_table'],no_extract_restore_or_backup_write=True)
(OUT/'preservation-audit.json').write_text(json.dumps(summary,indent=2));print(summary)

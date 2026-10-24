"""Read-only fingerprints of EVERY existing isolated row and spatial solver artifact."""
import sqlite3,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
database=ROOT/'docs/foundation-system/isolated/foundation.db'
with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as c:
 schema=c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()
 tables={}
 for (table,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
  tables[table]=sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest() for row in c.execute('select * from "'+table.replace('"','""')+'"'))
state=json.loads(json.dumps(dict(schema=schema,tables=tables)))
path=OUT/'isolated-original-rows.json'
if path.exists():assert json.loads(path.read_text())==state,'Existing isolated data changed; inspect without restoration'
else:path.write_text(json.dumps(state))
manifest=OUT/'spatial-evidence-baseline.json'
if not manifest.exists():
 files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in [ROOT/'docs/spatial-frame/solver-evidence',ROOT/'backend/storage/spatial-frame'] for p in folder.rglob('*') if p.is_file()}
 manifest.write_text(json.dumps(files,indent=2))
files=json.loads(manifest.read_text());changed=[name for name,digest in files.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
assert not changed,changed
result=dict(existing_isolated_rows_unchanged=True,isolated_rows=sum(map(len,tables.values())),existing_spatial_solver_files_unchanged=True,spatial_solver_files=len(files),no_restore_delete_or_record_updates=True)
(OUT/'review-preservation.json').write_text(json.dumps(result,indent=2));print(result)

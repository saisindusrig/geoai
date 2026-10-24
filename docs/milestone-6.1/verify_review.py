"""Verify existing review evidence in place against retained Milestone 5 hashes."""
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
previous=ROOT/'docs/milestone-5'
baseline=json.loads((previous/'isolated-original-rows.json').read_text())
db=ROOT/'docs/foundation-system/isolated/foundation.db'
with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
    schema=json.loads(json.dumps(c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()))
    assert schema==baseline['schema']
    tables={}
    for (name,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
        tables[name]=sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest() for row in c.execute('select * from "'+name.replace('"','""')+'"'))
    assert tables==baseline['tables'],'Existing isolated rows changed; never restore to satisfy a check'
manifest=json.loads((previous/'spatial-evidence-baseline.json').read_text())
changed=[name for name,sha in manifest.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha]
assert not changed,changed
result=dict(existing_isolated_rows_unchanged=True,isolated_rows=sum(map(len,tables.values())),appended_rows=0,
            spatial_solver_files_unchanged=True,spatial_solver_files=len(manifest),read_only=True)
Path(__file__).with_name('review-preservation.json').write_text(json.dumps(result,indent=2))
print(result)

"""Read-only reuse of Milestone 6 row/schema hashes; no original data copies."""
import hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/milestone-7'


def fingerprint(path):
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
        schema=json.loads(json.dumps(c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()))
        tables={}
        for (name,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
            tables[name]=sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest() for row in c.execute('select * from "'+name.replace('"','""')+'"'))
        return dict(schema=schema,tables=tables)


old=json.loads((ROOT/'docs/milestone-6/milestone-original-rows.json').read_text())
current=fingerprint(ROOT/'backend/dev.db')
assert old['schema']==current['schema']
assert all(not (Counter(rows)-Counter(current['tables'].get(name,[]))) for name,rows in old['tables'].items())
result=dict(unchanged_original_rows=True,all_rows_and_schemas_exactly_unchanged=old==current,
            original_rows=sum(map(len,old['tables'].values())),rows=sum(map(len,current['tables'].values())),
            added_rows_by_table={name:len(list((Counter(rows)-Counter(old['tables'].get(name,[]))).elements())) for name,rows in current['tables'].items() if Counter(rows)!=Counter(old['tables'].get(name,[]))})
(OUT/'milestone-preservation.json').write_text(json.dumps(result,indent=2));print(result)
history=ROOT/'backend/assistant-history.db'
if history.exists():
    current=fingerprint(history)
    baseline=OUT/'assistant-history-initial-hashes.json'
    if not baseline.exists():baseline.write_text(json.dumps(current))
    else:assert json.loads(baseline.read_text())==current,'Existing assistant history/accounting changed; inspect without restoring'
    (OUT/'assistant-history-preservation.json').write_text(json.dumps(dict(all_existing_history_and_accounting_unchanged=True,rows=sum(map(len,current['tables'].values()))),indent=2))

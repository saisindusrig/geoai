"""Read-only source audit and small response fixtures; never copies a database."""
import sqlite3,json,hashlib,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
c=sqlite3.connect((ROOT/'backend/dev.db').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(name,v): (OUT/name).write_text(json.dumps(v,indent=2,ensure_ascii=True),encoding='utf-8')
schema=c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()
fingerprints={}
for row in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
 t=row[0];fingerprints[t]=sorted(hashlib.sha256(repr(tuple(r)).encode()).hexdigest() for r in c.execute('select * from "'+t.replace('"','""')+'"'))
baseline=OUT/'milestone-original-rows.json'
current={'tables':fingerprints,'schema':[tuple(r) for r in schema]}
if not baseline.exists():write(baseline.name,current)
else:
 old=json.loads(baseline.read_text());assert old==json.loads(json.dumps(current)),'Original database changed during this milestone; inspect without restoration'
 write('milestone-preservation.json',{'all_rows_and_schemas_exactly_unchanged':True,'rows':sum(map(len,fingerprints.values()))})


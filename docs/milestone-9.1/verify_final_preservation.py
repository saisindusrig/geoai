from pathlib import Path
import json,sqlite3,hashlib,collections
root=Path.cwd();out=root/'docs/milestone-9.1';result={}
for name,filename in [('database','dev.db'),('assistant-history','assistant-history.db')]:
 before=json.loads((root/'docs/milestone-9'/(name+'-baseline.json')).read_text());c=sqlite3.connect((root/'backend'/filename).as_uri()+'?mode=ro',uri=True)
 schema=json.loads(json.dumps(c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()));assert schema==before['schema'];added={}
 for table,old in before['tables'].items():
  new=[hashlib.sha256(repr(tuple(r)).encode()).hexdigest() for r in c.execute('select * from "'+table+'"')];a=collections.Counter(old);b=collections.Counter(new);assert not a-b
  if b-a:added[table]=sum((b-a).values())
 result[name]={'all_original_rows_unchanged':True,'schema_unchanged':True,'original_rows':sum(map(len,before['tables'].values())),'added_rows_by_table':added,'exactly_unchanged':not bool(added)}
(out/'preservation.json').write_text(json.dumps(result,indent=2));print(result)

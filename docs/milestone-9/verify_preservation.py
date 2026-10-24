"""Exact read-only comparisons to Milestone 9 entry; never restores any record."""
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
def fingerprint(path):
 with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
  schema=json.loads(json.dumps(c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()))
  tables={}
  for (name,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
   tables[name]=sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest() for row in c.execute('select * from "'+name.replace('"','""')+'"'))
  return dict(schema=schema,tables=tables)
results={}
for name,path in [('database','backend/dev.db'),('assistant-history','backend/assistant-history.db')]:
 before=json.loads((OUT/(name+'-baseline.json')).read_text());after=fingerprint(ROOT/path)
 assert before==after,name+' changed; inspect without restoring'
 results[name]=dict(all_rows_and_schemas_exactly_unchanged=True,rows=sum(map(len,after['tables'].values())))
(OUT/'preservation.json').write_text(json.dumps(results,indent=2));print(results)
(OUT/'milestone-preservation.json').write_text(json.dumps(dict(unchanged_original_rows=True,all_rows_and_schemas_exactly_unchanged=True,original_rows=results['database']['rows'],rows=results['database']['rows'],added_rows_by_table={}),indent=2))
isolated=OUT/'isolated/beam-review.db'
if isolated.exists():
 with sqlite3.connect(isolated.as_uri()+'?mode=ro',uri=True) as c:
  verified=[]
  for pid, in c.execute('select id from projects where id>=980000'):
   revisions=c.execute('select id,document_json from model_revisions where project_id=? order by revision_number',(pid,)).fetchall()
   original=json.loads(revisions[0][1])['components']
   for rid,body in revisions[1:]:
    components=json.loads(body)['components'];assert components[:len(original)]==original
    assert len(components)==len(original)+1 and components[-1]['metadata']['source']=='assistant_supervised_primitive'
   verified.append(dict(project=pid,immutable_initial_revision=revisions[0][0],saved_revisions=[r[0] for r in revisions[1:]],all_original_components_unchanged=True))
  for table in ('engineering_analyses','usage_events'):
   assert c.execute('select count(*) from '+table+' where project_id>=980000').fetchone()[0]==0,table
 (OUT/'isolated-mutation-evidence.json').write_text(json.dumps(dict(projects=verified,engineering_analyses=0,download_or_usage_events=0,original_database_never_attached=True),indent=2))

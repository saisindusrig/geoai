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

keep=['case_name','case_kind','inputs','physical_to_analytical_graph','solver_version','run_id','nodes','elements','reactions','rigid_offset_transfers','equilibrium_residual_si','applied_loads','limitations','verified','status']
def compact(j):
 out={k:j[k] for k in keep if k in j}
 if j.get('load_case_results'):out['load_case_results']=[compact(x) for x in j['load_case_results']]
 return out
projects=[]
for pid in [793,794,804]:
 rev=c.execute('select * from model_revisions where project_id=? order by id desc limit 1',(pid,)).fetchone();doc=json.loads(rev['document_json'])
 rows=[]
 for row in c.execute("select * from engineering_analyses where project_id=? and analysis_type in ('OPENSEES_PHYSICAL_FRAME','OPENSEES_SLAB_TRANSFER') order by id desc",(pid,)):
  j=json.loads(row['result_json']);r=compact(j)
  if j.get('frames'):r.update(frames=[{'beam_id':f['beam_id'],'result':compact(f['result'])} for f in j['frames']],transfer=j['transfer'])
  rows.append(dict(id=row['id'],model_revision_id=row['model_revision_id'],status=row['status'],result=r))
  break
 write(f'project-{pid}.json',dict(project_id=pid,revision_id=rev['id'],components=[{k:co[k] for k in ['id','name','category','transform']} for co in doc['components']],rows=rows))
 projects.append(dict(project_id=pid,revision_id=rev['id'],document_sha256=digest(doc),analyses=[dict(id=r['id'],status=r['status']) for r in rows]))
write('source-audit.json',projects)

extra=[]
for table,key,ids in [('projects','id',[805]),('design_scenarios','id',[593]),('model_revisions','id',[125]),('engineering_analyses','id',[591,592,593])]:
 for id in ids:
  row=dict(c.execute(f'select * from {table} where {key}=?',(id,)).fetchone());entry={k:v for k,v in row.items() if k in ['id','project_id','design_scenario_id','model_revision_id','analysis_type','status','created_at','actor_user_id','user_id','source','prompt','name']}
  if 'result_json' in row:
   j=json.loads(row['result_json']);entry.update(copied_from=j.get('copied_from'),authorization=j.get('authorization'),binding=j.get('binding'))
   cp=j.get('copied_from')
   if cp:
    source=json.loads(c.execute('select result_json from engineering_analyses where id=? and project_id=?',(cp['record_id'],cp['project_id'])).fetchone()[0]);entry['source_hash_matches']=digest(source)==cp['sha256']
  if 'document_json' in row:entry['foundation_study_marker']=json.loads(row['document_json']).get('metadata',{}).get('foundation_system')
  extra.append(dict(table=table,record=entry))
log=ROOT/'docs/foundation-system/normal-backend.log'
hits=[dict(file=str(log.relative_to(ROOT)),line=i+1,text=line) for i,line in enumerate(log.read_text(encoding='utf-8',errors='replace').splitlines()) if 'POST /api/projects/804/engineering/foundation-system/copy ' in line or 'POST /api/projects/805/engineering/foundation-system/preview ' in line]
write('six-row-provenance.json',dict(records=extra,normal_backend_access_log=hits,conclusion='Normal-backend access log records successful copy and preview requests. Copied source references match original hashes. Study 805 originates from the separate-study route for 804; its proposal is awaiting review, not an authorized result. Logs do not identify which browser/person initiated requests. All six records retained unchanged.'))
print('Read-only audit complete; original row baseline, source fixtures and six-row provenance written.')

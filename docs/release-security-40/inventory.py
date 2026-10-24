"""Read-only release inventory. Never imports application startup or writes originals."""
import os,json,hashlib,sqlite3,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SKIP={'.git','node_modules','.venv','.next','.next-phase1','.cad-proof-deps','__pycache__','.pytest_cache'}
files=[]
for base,dirs,names in os.walk(ROOT):
 dirs[:]=[d for d in dirs if d not in SKIP and not (Path(base)==OUT)]
 for n in names:
  p=Path(base)/n;rel=p.relative_to(ROOT).as_posix();suffix=p.suffix.lower()
  if suffix in {'.db','.sqlite','.sqlite3','.dxf','.dwg','.ifc','.step','.stp','.glb','.gltf','.tcl','.tsv'} or ('solver-evidence/' in rel and p.is_file()):
   files.append({'path':rel,'bytes':p.stat().st_size,'kind':'database' if suffix in {'.db','.sqlite','.sqlite3'} else 'CAD/model' if suffix in {'.dxf','.dwg','.ifc','.step','.stp','.glb','.gltf'} else 'engineering evidence','disposition':'PRESERVE; never seed production','synthetic_provenance':'Candidate isolated/test path; not deletion authority' if re.search(r'(isolated|fixture|test|proof|solver-evidence)',rel,re.I) else 'Unknown or original; manual provenance review required'})
(OUT/'file-inventory.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
databases=[]
for row in files:
 if row['kind']!='database':continue
 p=ROOT/row['path']
 try:
  with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2) as c:
   c.execute('PRAGMA query_only=ON')
   tables={n:c.execute('select count(*) from "'+n.replace('"','""')+'"').fetchone()[0] for (n,) in c.execute("select name from sqlite_master where type='table'")}
  databases.append({'path':row['path'],'tables':tables,'classification':'isolated/test candidate' if re.search(r'(isolated|test|regression)',row['path'],re.I) else 'original/historical/unknown — preserve'})
 except sqlite3.Error as error:databases.append({'path':row['path'],'read_error_type':type(error).__name__,'classification':'UNVERIFIED — preserve'})
(OUT/'database-inventory.json').write_text(json.dumps(databases,indent=2),encoding='utf-8')
with sqlite3.connect((ROOT/'backend/dev.db').as_uri()+'?mode=ro',uri=True) as c:
 candidates={}
 for table in ['users','projects']:
  cols=['id','name','email'] if table=='users' else ['id','name','user_id']
  rows=c.execute('select '+','.join(cols)+' from '+table).fetchall()
  # Report IDs/reasons only: never export names, addresses, credentials or user content.
  selected=[]
  for row in rows:
   text=' '.join(str(v) for v in row[1:]).lower()
   matches=[word for word in ['synthetic','fixture','test','demo','acceptance','milestone','localhost','example.'] if word in text]
   if matches:selected.append({'id':row[0],'reason_markers':matches,'confidence':'heuristic only; no delete approval'})
  candidates[table]={'total_rows':len(rows),'candidate_rows':selected,'unclassified_count':len(rows)-len(selected)}
(OUT/'synthetic-record-candidates.json').write_text(json.dumps(candidates,indent=2),encoding='utf-8')
baseline=json.loads((ROOT/'docs/milestone-12/database-baseline.json').read_text());current={}
for name in baseline:
 with sqlite3.connect((ROOT/'backend'/name).as_uri()+'?mode=ro',uri=True) as c:
  schema=[list(r) for r in c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name')]
  tables={n:sorted(hashlib.sha256(repr(r).encode()).hexdigest() for r in c.execute('select * from "'+n.replace('"','""')+'"')) for (n,) in c.execute("select name from sqlite_master where type='table' order by name")}
  current[name]={'schema':schema,'tables':tables}
preservation={'matches_milestone_12_entry':current==baseline,'rows':{n:sum(map(len,v['tables'].values())) for n,v in current.items()},'original_database_writes':0,'deletions':0,'application_startup_imported':False}
(OUT/'preservation.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8');assert current==baseline
print(json.dumps({'files':len(files),'databases':len(databases),'preservation':preservation}))

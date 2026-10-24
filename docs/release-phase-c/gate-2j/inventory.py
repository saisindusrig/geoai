"""Metadata/static-code inventory only. No imports of app settings, execution or deletion."""
import ast
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def protected_group(parts):
 if parts[-1].lower().endswith(('.db','.sqlite','.sqlite3','.db-wal','.db-shm','.db-journal')):return 'NEVER DELETE AUTOMATICALLY: database or journal'
 if parts[0] in ('.cache','.cleanup-backups','docs','pytest-of-unknown','struvocivil-gate1d-v4c5a_2i'):return 'NEVER DELETE AUTOMATICALLY: historical evidence/fixtures/backup'
 if parts[:2] in [('backend','storage'),('backend','.cad-proof-output'),('backend','live-results')]:return 'NEVER DELETE AUTOMATICALLY: CAD/results/evidence'
 if any(p.startswith('.env') for p in parts):return 'NEVER DELETE AUTOMATICALLY: configuration/secrets'
 if any(p in ('node_modules','.venv','.venv-civicspan','.cad-proof-deps') for p in parts):return 'RETAIN: installed dependencies; not cleanup candidates'
 if parts[:3]==('.local-tooling','node-24.22.1-validation','runtime'):return 'RETAIN: launcher-required verified Node runtime'
 if parts[0]=='.local-tooling':return 'REVIEW BEFORE CLEANING: tooling/build/test working copies'
 if parts[:2]==('frontend','.cache'):return 'NEVER DELETE AUTOMATICALLY: historical screenshots'
 if any(p.startswith('.next') for p in parts):return 'REVIEW BEFORE CLEANING: generated build; normal runtime may depend on it'
 return 'RETAIN: application source/assets/configuration or unclassified'

start=time.monotonic();groups=defaultdict(lambda:dict(files=0,bytes=0));builds=defaultdict(lambda:dict(files=0,bytes=0))
links=[];errors=[];db_paths=[];archives=[];bytecode=[];fingerprints={};sources=[]
stack=[ROOT];total=0
while stack:
 folder=stack.pop()
 try:
  entries=list(os.scandir(folder))
 except OSError as e: errors.append(dict(path=str(folder.relative_to(ROOT)),error=type(e).__name__));continue
 for entry in entries:
  p=Path(entry.path);rel=p.relative_to(ROOT);parts=rel.parts
  if parts[0]=='.git' or p==OUT or OUT in p.parents:continue
  try:
   s=entry.stat(follow_symlinks=False)
   if entry.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:
    links.append(dict(path=rel.as_posix(),type='reparse_point_not_followed'));continue
   if entry.is_dir(follow_symlinks=False):stack.append(p);continue
   if not entry.is_file(follow_symlinks=False):continue
  except OSError as e:errors.append(dict(path=rel.as_posix(),error=type(e).__name__));continue
  total+=1;group='/'.join(parts[:2]) if len(parts)>1 else parts[0]
  groups[group]['files']+=1;groups[group]['bytes']+=s.st_size
  groups[group]['classification']=protected_group(tuple(parts[:2]) if len(parts)==2 else parts)
  for i,part in enumerate(parts):
   if part.startswith('.next'):
    key='/'.join(parts[:i+1]);builds[key]['files']+=1;builds[key]['bytes']+=s.st_size;break
  lower=p.name.lower()
  if lower.endswith(('.db','.sqlite','.sqlite3','.db-wal','.db-shm','.db-journal','.sqlite-wal','.sqlite-shm')):
   db_paths.append(dict(path=rel.as_posix(),bytes=s.st_size,classification='NEVER DELETE AUTOMATICALLY'))
  if lower.endswith(('.zip','.7z','.tar','.tar.gz','.bak')):archives.append(dict(path=rel.as_posix(),bytes=s.st_size))
  in_source=(parts[0]=='scripts' or parts[:2] in [('backend','app'),('backend','scripts'),('backend','tests'),('backend','alembic'),('frontend','app'),('frontend','components'),('frontend','lib'),('frontend','hooks'),('frontend','stores'),('frontend','scripts'),('frontend','e2e')])
  if in_source and p.suffix=='.pyc' and p.parent.name=='__pycache__':
   source=p.parent.parent/(p.name.split('.cpython-')[0]+'.py')
   if source.is_file():bytecode.append(dict(path=rel.as_posix(),bytes=s.st_size,source=source.relative_to(ROOT).as_posix(),sha256=sha(p)))
  # Preserve original application source/assets without reading secret config contents.
  is_app_file=in_source and '__pycache__' not in parts and p.suffix in {'.py','.ts','.tsx','.js','.cjs','.mjs','.css','.json','.svg'}
  is_asset=parts[:2]==('frontend','public')
  is_root= len(parts)==1 and p.suffix in {'.md','.bat','.ps1','.yml'}
  if is_app_file or is_asset or is_root:
   fingerprints[rel.as_posix()]=sha(p)
   if is_app_file:sources.append(rel.as_posix())
save('inventory.json',dict(files=total,bytes=sum(r['bytes'] for r in groups.values()),groups=dict(sorted(groups.items())),build_roots=dict(sorted(builds.items())),reparse_points_not_followed=links,errors=errors,root_git_excluded=True,own_new_evidence_excluded=True,elapsed_seconds=round(time.monotonic()-start,2)))
save('databases.json',db_paths);save('archives.json',archives);save('bytecode-candidates.json',bytecode);save('source-asset-fingerprints-before.json',fingerprints)
# Duplicate source is a review lead, never evidence of removability.
equal=defaultdict(list);functions=defaultdict(list)
for name in sources:
 equal[fingerprints[name]].append(name)
 if name.startswith('backend/app/') and name.endswith('.py'):
  try:tree=ast.parse((ROOT/name).read_text(encoding='utf-8-sig'))
  except (SyntaxError,UnicodeError):continue
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and len(node.body)>=3:
    digest=hashlib.sha256(ast.dump(ast.Module(body=node.body,type_ignores=[]),include_attributes=False).encode()).hexdigest()
    functions[digest].append(dict(path=name,line=node.lineno,function=node.name))
save('duplicate-review.json',dict(identical_file_groups=[v for v in equal.values() if len(v)>1],identical_function_body_groups=[v for v in functions.values() if len(v)>1],confirmed_unused_files=[],automatic_deletion_permitted=False))
# Classify records conservatively, without publishing addresses, password hashes or document content.
stats={}
for name in ('dev.db','assistant-history.db'):
 with sqlite3.connect((ROOT/'backend'/name).as_uri()+'?mode=ro',uri=True) as db:
  stats[name]={'tables':{table:db.execute('SELECT count(*) FROM "'+table.replace('"','""')+'"').fetchone()[0] for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}}
  if name=='dev.db':
   stats[name]['users']=[dict(id=row[0],role=row[1],classification='development-marker; retain' if row[2] else 'provenance_unverified; retain') for row in db.execute("SELECT id,role,lower(email) LIKE '%@example.%' OR lower(name) LIKE '%synthetic%' OR lower(name) LIKE '%dev user%' FROM users ORDER BY id")]
   stats[name]['projects']=[dict(id=row[0],owner_id=row[1],classification='synthetic/demo-name marker; retain' if row[2] else 'provenance_unverified; retain') for row in db.execute("SELECT id,user_id,lower(name) LIKE '%synthetic%' OR lower(name) LIKE '%demo%' OR lower(name) LIKE '%fixture%' FROM projects ORDER BY id")]
save('data-record-inventory.json',stats)
print(json.dumps(dict(files=total,groups=len(groups),build_roots=len(builds),database_files=len(db_paths),source_asset_fingerprints=len(fingerprints),candidate_bytecode_files=len(bytecode),scan_errors=len(errors),reparse_points_skipped=len(links)),indent=2))

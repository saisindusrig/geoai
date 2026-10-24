"""Static dependency accounting; never imports application or solver modules."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
from packaging.requirements import Requirement
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
pkg=json.loads((ROOT/'frontend/package.json').read_text());frontend=[]
for kind in ('dependencies','devDependencies'):
 for name,spec in pkg.get(kind,{}).items():
  file=ROOT/'frontend/node_modules'/name/'package.json'
  frontend.append(dict(name=name,declared=spec,kind=kind,installed_version=json.loads(file.read_text(encoding='utf-8-sig')).get('version') if file.is_file() else None))
backend=[]
for line in (ROOT/'backend/requirements.txt').read_text().splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 try:r=Requirement(line)
 except Exception:backend.append(dict(declaration=line,review='non-package requirement; retain manifest'));continue
 try:version=importlib.metadata.version(r.name)
 except importlib.metadata.PackageNotFoundError:version=None
 backend.append(dict(name=r.name,declaration=line,installed_version=version,specifier_satisfied=version in r.specifier if version else False))
versions={}
for file in (ROOT/'backend/alembic/versions').glob('*.py'):
 tree=ast.parse(file.read_text(encoding='utf-8-sig'));vals={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('revision','down_revision'):
   vals[node.targets[0].id]=ast.literal_eval(node.value)
 versions[str(file.relative_to(ROOT)).replace('\\','/')]=vals
parents={v['down_revision'] for v in versions.values() if isinstance(v.get('down_revision'),str)}
heads=[v['revision'] for v in versions.values() if v['revision'] not in parents]
fixtures=json.loads((ROOT/'docs/release-phase-c/gate-1a/static-fixture-inputs.json').read_text())
for row in fixtures:assert hashlib.sha256((ROOT/row['source']).read_bytes()).hexdigest()==row['sha256']
result=dict(frontend=frontend,backend=backend,alembic_revisions=versions,static_alembic_heads=heads,
 existing_identity_link_migration_found=any('auth_identity_links' in (ROOT/name).read_text() for name in versions),
 build_test_data_dependencies=fixtures,build_test_data_must_not_be_imported_into_new_runtime=True,
 required_retained_paths=['frontend/app','frontend/components','frontend/lib','frontend/hooks','frontend/stores','frontend/public','frontend/scripts',
 'frontend/package.json','frontend/package-lock.json','backend/app','backend/alembic','backend/requirements.txt','backend/cad-notices','backend/.cad-proof-deps',
 '.local-tooling/node-24.22.1-validation/runtime','scripts/verify-local-node.cjs','run-website.bat','start-copilot-review.ps1'],
 no_unused_package_claim=True,no_packages_installed=True)
(OUT/'dependency-accounting.json').write_text(json.dumps(result,indent=2))
db=json.loads((OUT/'databases.json').read_text())
for row in db:row['sha256']=hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()
(OUT/'database-file-fingerprints-before.json').write_text(json.dumps(db,indent=2))
print(json.dumps(dict(frontend_declared=len(frontend),frontend_missing=sum(not x['installed_version'] for x in frontend),backend_declared=len(backend),backend_missing_or_incompatible=sum(not x.get('specifier_satisfied',False) for x in backend),alembic_heads=heads,static_fixture_dependencies=len(fixtures),database_files_fingerprinted=len(db)),indent=2))

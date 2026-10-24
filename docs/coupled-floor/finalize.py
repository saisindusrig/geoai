"""Assert final native/browser/data evidence without modifying original data."""
import json,hashlib
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
for name,expected in [('frontend-final.log','382 passed'),('backend-final.log','290 passed'),('browser-final.log','6 passed')]:assert expected in (OUT/name).read_text(encoding='utf-8'),name
for name in ('typescript-final.log','eslint-final.log'):assert not (OUT/name).read_text(encoding='utf-8').strip(),name
demo=read('demo.json');r=demo['analysis']['result']['cases'][0]
assert demo['fixture']['project_id']==828 and demo['analysis']['status']=='VERIFIED'
assert not r['diaphragm_enabled'] and not r['two_storeys_enabled'] and not r['production_enabled']
for run in r['validation']['mesh_runs']:
 folder=OUT/'solver-evidence'/run['run_id'];manifest=json.loads((folder/'manifest.json').read_text())
 for name,sha in manifest['artifact_sha256'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==sha,(run['run_id'],name)
cases=[]
for width in (1280,1600):
 c=read(f'browser-{width}.json');assert c['modes']==7 and c['animation'] and c['picked_shell'] and not c['errors'] and not c['writes'];cases.append(c)
 downloaded=read(f'download-{width}.json');assert downloaded['id']==693 and downloaded['result']['evidence_sha256']==demo['analysis']['result']['evidence_sha256']
normal=read('milestone-preservation.json');assert normal==dict(all_rows_and_schemas_exactly_unchanged=True,rows=10245)
review=read('review-preservation.json');assert review['existing_isolated_rows_unchanged'] and review['preexisting_isolated_rows']==10479 and review['isolated_rows']==10484 and review['spatial_solver_files']==635 and review['existing_spatial_solver_files_unchanged']
preserved=read('preservation-manifests.json');assert not preserved['changed_or_missing_files'] and all(d['schema_unchanged'] for d in preserved['databases'])
prerequisites=read('reused-benchmarks.json');assert prerequisites['diaphragm']['status']=='BENCHMARK_VERIFIED' and prerequisites['plates'][-1]['relative_error']<.001
recording=read('demonstration.json');assert recording['real_browser_recording'] and not recording['errors'] and not recording['writes']
video=read('video-metadata.json');assert 15<video['duration_seconds']<240 and video['width']==1600 and video['height']==1000
files=['backend/app/main.py','backend/app/api/routes/coupled_floors.py','backend/app/services/design/coupled_floor.py','backend/app/services/design/coupled_ritz.py','backend/tests/test_coupled_floor.py','frontend/lib/coupled-floor.ts','frontend/lib/coupled-floor.test.ts','frontend/lib/structural-visual.ts','frontend/components/map/CesiumView.tsx','frontend/components/model-editor/CoupledFloorPanel.tsx','frontend/components/model-editor/CoupledFloorPanel.test.tsx','frontend/components/model-editor/ProfessionalModelEditor.tsx','frontend/e2e/coupled-floor.spec.ts']
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files};(OUT/'implementation-manifest.json').write_text(json.dumps(hashes,indent=2))
result=dict(frontend_tests=382,frontend_files=78,backend_tests=290,new_coupled_backend_tests=18,browser_workflows=6,viewports=[1280,1600],typescript='PASS',scoped_eslint='PASS',browser_acceptance=cases,project=828,analysis=693,native_and_independent_checks=r['validation']['checks'],native_equilibrium_and_substructure=r['comparisons'],normal_preservation=normal,review_preservation=review,original_storage_files=preserved['original_storage_files'],original_proof_files=preserved['original_engineering_proof_files'],original_database_schemas_checked=len(preserved['databases']),video=video,engineering_approval='DISABLED',unsupported=['Rigid diaphragm integration','Two-storey shell coupling','Lateral shell behavior','Shell stress fields','Physical connection/foundation/soil capacity','General floor geometry'])
(OUT/'test-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

"""Assert final usability, native regression, browser, media and preservation evidence."""
import json,hashlib
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
for name,expected in [('frontend-final.log','392 passed'),('workflow-final.log','10 passed'),('backend-regression.log','275 passed'),('backend-guidance.log','23 passed'),('browser-final.log','17 passed')]:assert expected in (OUT/name).read_text(encoding='utf-8'),name
for name in ['typescript-final.log','eslint-final.log']:assert not (OUT/name).read_text(encoding='utf-8').strip(),name
normal=read('milestone-preservation.json');assert normal==dict(all_rows_and_schemas_exactly_unchanged=True,rows=10245)
review=read('review-preservation.json');assert review['existing_isolated_rows_unchanged'] and review['preexisting_isolated_rows']==10484 and review['existing_spatial_solver_files_unchanged'] and review['spatial_solver_files']==635
source=read('preservation-manifests.json');assert not source['changed_or_missing_files'] and all(d['schema_unchanged'] for d in source['databases'])
coupled=read('coupled-evidence-preservation.json');assert coupled['previous_coupled_native_files_verified']==21
cases=[]
for width in (1280,1600):
 for pid in (793,794,804,814,823,822,828,829):
  c=read(f'browser-{pid}-{width}.json');assert c['keyboard'] and c['read_only'] and c['advanced_access'] and not c['writes'] and not c['errors'];cases.append(c)
  assert (OUT/f'after-{pid}-{width}.png').stat().st_size>10000
 assert (OUT/f'before-{width}.png').stat().st_size>10000
modified=read('modifying-acceptance.json');assert modified['project']==830 and modified['explicit_authorization'] and modified['technical_accordions_used']==0 and not modified['errors']
assert all(u.startswith('http://127.0.0.1:18001/api/projects/830/engineering/assembly/') for u in modified['writes'])
recording=read('demonstration.json');assert recording['steps']==['SELECT','INPUTS','ANALYZE','RESULTS'] and recording['explicit_authorization'] and recording['reopen_writes']==0 and not recording['errors']
video=read('video-metadata.json');assert 15<video['duration_seconds']<240 and video['width']==1600 and video['height']==1000
files=['frontend/components/model-editor/GuidedAnalysisWorkflow.tsx','frontend/components/model-editor/GuidedAnalysisWorkflow.test.tsx','frontend/components/model-editor/GuidedAnalysisResults.tsx','frontend/components/model-editor/GuidedFrameInputs.tsx','frontend/components/model-editor/ProfessionalModelEditor.tsx','frontend/components/model-editor/PhysicalFramePanel.tsx','frontend/components/model-editor/FoundationSystemPanel.tsx','frontend/lib/analysis-workflow.ts','frontend/lib/analysis-workflow.test.ts','frontend/e2e/guided-analysis.spec.ts','frontend/next.config.ts']
(OUT/'implementation-manifest.json').write_text(json.dumps({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},indent=2))
result=dict(frontend_tests=392,frontend_files=80,new_workflow_tests=10,relevant_backend_tests=298,backend_regression_tests=275,backend_guidance_and_elastic_tests=23,browser_workflows=17,viewports=[1280,1600],read_only_browser_matrix=cases,isolated_full_workflow=modified,typescript='PASS',scoped_eslint='PASS',normal_preservation=normal,isolated_preservation=review,original_storage_files=source['original_storage_files'],original_proof_files=source['original_engineering_proof_files'],original_database_schemas=len(source['databases']),previous_coupled_native_files_verified=coupled['previous_coupled_native_files_verified'],preexisting_stale_spatial_project_preserved=823,video=video,backend_numerical_methods_changed=False,automatic_solver_authorization=False,engineering_approval='DISABLED')
(OUT/'test-results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['read_only_browser_matrix']},indent=2))

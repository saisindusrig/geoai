"""Assert final artifacts and read-only preservation; never edit original data."""
import json,hashlib
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
for name,expected in [('frontend-final.log','375 passed'),('backend-final.log','272 passed'),('browser-verified.log','5 passed')]:assert expected in (OUT/name).read_text(),name
for name in ('typescript-release.log','lint-release.log'):assert not (OUT/name).read_text().strip(),name
for name,sha in json.loads((OUT/'implementation-manifest.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
cases=[]
for width in (1280,1600):
 case=json.loads((OUT/f'acceptance-{width}.json').read_text());assert case['animation'] and case['route_to_base'] and not case['writes'] and not case['errors'];cases.append(case)
 downloaded=json.loads((OUT/f'downloaded-floor-evidence-{width}.json').read_text());assert downloaded['analysis_id']==684 and all(c['status']=='VERIFIED' and not c['capabilities']['diaphragm'] and not c['capabilities']['slab_structural_analysis'] for c in downloaded['cases'])
old=json.loads((OUT/'milestone-preservation.json').read_text());assert old==dict(all_rows_and_schemas_exactly_unchanged=True,rows=10245)
review=json.loads((OUT/'review-preservation.json').read_text());assert review['existing_isolated_rows_unchanged'] and review['isolated_rows']==10478 and review['existing_spatial_solver_files_unchanged'] and review['spatial_solver_files']==635
source=json.loads((OUT/'preservation-manifests.json').read_text());assert not source['changed_or_missing_files'] and all(d['schema_unchanged'] for d in source['databases'])
research=json.loads((OUT/'mechanics-investigation.json').read_text());assert research['diaphragm']['status']=='BENCHMARK_VERIFIED' and research['plate']['status']=='BENCHMARK_VERIFIED' and research['integration_status']=='DISABLED'
video=json.loads((OUT/'video-metadata.json').read_text());assert 15<video['duration_seconds']<240 and video['width']==1600 and video['height']==1000
demo=json.loads((OUT/'demonstration.json').read_text());assert demo['surface_picked'] and demo['load_picked'] and demo['followed'][-1]=='column-F2-N7-13' and not demo['errors'] and not demo['writes']
for name in ('floor-system-walkthrough.webm','floors-overview-1600.png','selected-floor-route-1600.png','beam-transfer-inspection-1600.png','column-transfer-inspection-1600.png','animated-deformation-1600.png','prescribed-base-1600.png'):assert (OUT/name).is_file(),name
result=dict(frontend_tests=375,backend_tests=272,new_backend_floor_tests=10,browser_workflows=5,viewports=[1280,1600],typescript='PASS',scoped_eslint='PASS',browser_acceptance=cases,original_preservation=old,review_preservation=review,original_storage_files=source['original_storage_files'],original_cad_proof_files=source['original_engineering_proof_files'],database_schemas_checked=len(source['databases']),research_integration='DISABLED',video=video,implementation_hashes_verified=True,engineering_approval='DISABLED')
(OUT/'test-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

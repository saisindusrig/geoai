"""Assert delivered evidence exists and bind final verification without changing data."""
import json,hashlib
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
for filename,expected in [('frontend-release.log','366 passed'),('backend-release.log','262 passed'),('browser-release.log','8 passed')]:assert expected in (OUT/filename).read_text(),filename
for name in ('typescript-release.log','lint-release.log'):assert not (OUT/name).read_text().strip(),name
for filename,digest in json.loads((OUT/'implementation-manifest.json').read_text()).items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==digest,filename
acceptance=[]
for p in (822,823):
 for width in (1280,1600):
  row=json.loads((OUT/f'acceptance-{p}-{width}.json').read_text());assert row['modes']==7 and not row['writes'] and not row['errors'];acceptance.append(row)
auth=json.loads((OUT/'authorization-browser.json').read_text());assert auth['authorized_exact_hash'] and not auth['errors'] and all(url.startswith('http://127.0.0.1:18001/') for url in auth['writes'])
preservation=json.loads((OUT/'milestone-preservation.json').read_text());assert preservation==dict(all_rows_and_schemas_exactly_unchanged=True,rows=10245)
manifests=json.loads((OUT/'preservation-manifests.json').read_text());assert not manifests['changed_or_missing_files'] and all(d['schema_unchanged'] for d in manifests['databases'])
video=json.loads((OUT/'video-metadata.json').read_text());assert 15<video['duration_seconds']<180 and video['width']==1600 and video['height']==1000
recording=json.loads((OUT/'demonstration.json').read_text());assert recording['actual_member_label_picked'] and not recording['errors'] and not recording['writes']
for name in ('spatial-frame-walkthrough.webm','computed-My-1600.png','actual-deformation-1600.png','floor-2-member-inspection.png','slab-inspection-1600.png','independent-calculations.json'):assert (OUT/name).is_file(),name
result=dict(frontend_tests=366,backend_tests=262,spatial_backend_tests=26,browser_workflows=8,typescript='PASS',scoped_eslint='PASS',visual_acceptance=acceptance,authorization=auth,preservation=preservation,original_storage_files=manifests['original_storage_files'],original_cad_proof_files=manifests['original_engineering_proof_files'],database_schemas_checked=len(manifests['databases']),video=video,implementation_manifest_verified=True,engineering_approval='DISABLED')
(OUT/'test-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

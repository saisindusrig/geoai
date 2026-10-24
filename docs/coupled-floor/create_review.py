"""Append only one explicitly authorized synthetic project to attested isolated DB."""
import json,urllib.request
from pathlib import Path
OUT=Path(__file__).parent
def request(path,payload=None):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request('http://127.0.0.1:18001'+path,data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
attestation=request('/__spatial_validation')
assert attestation['original_writes'] is False and attestation['paid_inference'] is False
assert attestation['database'].replace('\\','/').endswith('/docs/foundation-system/isolated/foundation.db')
path=OUT/'demo.json'
if path.exists():raise SystemExit('Existing review retained; do not create duplicates')
fixture=request('/api/projects/823/engineering/coupled-floor/review-fixture',{'review_parametric_geometry':True})
path.write_text(json.dumps({'fixture':fixture},indent=2))
base=f"/api/projects/{fixture['project_id']}/engineering/coupled-floor"
proposal=request(base+'/review',{'model_revision_id':fixture['model_revision_id'],'review_parametric_geometry':True})
result=request(base+'/authorize-run',{'proposal_id':proposal['id'],'proposal_sha256':proposal['result']['proposal_sha256'],'authorize_solver':True})
path.write_text(json.dumps(dict(fixture=fixture,proposal=proposal,analysis=result,attestation=attestation),indent=2))
assert result['status']=='VERIFIED',result['status']
print(dict(project=fixture['project_id'],analysis=result['id'],status=result['status'],checks=result['result']['cases'][0]['validation']['checks']))

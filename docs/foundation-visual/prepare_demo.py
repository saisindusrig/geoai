"""Create a new review-only test study on the attested isolated database."""
from pathlib import Path
import json,httpx
ROOT=Path(__file__).resolve().parents[2]
c=httpx.Client(base_url='http://127.0.0.1:18001',timeout=60)
a=c.get('/__foundation_validation').json()
assert a['mode']=='foundation-isolated-20261015' and Path(a['database']).resolve()==(ROOT/'docs/foundation-system/isolated/foundation.db').resolve()
def call(method,path,**kw):
 r=c.request(method,path,**kw);assert r.is_success,(r.status_code,r.text[:1500]);return r.json()
study=call('POST','/api/projects/804/engineering/foundation-system/copy',json=dict(model_revision_id=124,authorize_separate_study=True))
base=f"/api/projects/{study['project_id']}/engineering/foundation-system"
h=call('GET',base,params={'model_revision_id':study['model_revision_id']})
p=call('POST',base+'/preview',json={'model_revision_id':study['model_revision_id'],'inputs':h['fixture']})
r=call('POST',base+'/authorize',json=dict(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_calculation=True))
out=dict(attestation=a,study=study,result_id=r['id'],computed_sha256=r['result']['computed_sha256'])
Path(__file__).with_name('demo.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))

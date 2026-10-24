"""All modifying HTTP traffic is pinned to the attested isolated port."""
from pathlib import Path
import json,sqlite3
import httpx
ROOT=Path(__file__).resolve().parents[2]
BASE='http://127.0.0.1:18001'
client=httpx.Client(base_url=BASE,timeout=60)
attestation=client.get('/__foundation_validation').json()
assert attestation==dict(mode='foundation-isolated-20261015',database=str((ROOT/'docs/foundation-system/isolated/foundation.db').resolve()),paid_inference=False,port=18001)
def call(method,path,expected=200,**kw):
 r=client.request(method,path,**kw)
 assert r.status_code==expected,(path,r.status_code,r.text[:1000])
 return r.json() if 'json' in r.headers.get('content-type','') else r.text
ref=call('GET','/api/projects/804/scenarios/592/model-revisions/latest')
rid=ref['id']
copy=call('POST','/api/projects/804/engineering/foundation-system/copy',json=dict(model_revision_id=rid,authorize_separate_study=True))
pid=copy['project_id'];rid=copy['model_revision_id'];base=f'/api/projects/{pid}/engineering/foundation-system'
h=call('GET',base,params=dict(model_revision_id=rid));q=h['fixture'];payload=dict(model_revision_id=rid,inputs=q)
call('GET',base,expected=404,params=dict(model_revision_id=rid),headers={'X-Mock-User-Id':'999'})
invalid=[{'factored_column_kn':0},{'material_source':''},{'classification':'REAL_PROJECT'},{'reviewed_synthetic_patch':False},{'steel_yield_mpa':420},{'profile':'UNKNOWN'},{'east_west':dict(diameter_mm=40,count=100)}]
for bad in invalid:call('POST',base+'/preview',expected=422,json={**payload,'inputs':{**q,**bad}})
p=call('POST',base+'/preview',json=payload)
auth=dict(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_calculation=True)
call('POST',base+'/authorize',expected=409,json={**auth,'proposal_sha256':'0'*64})
call('POST',base+'/authorize',expected=422,json={**auth,'authorize_calculation':False})
r=call('POST',base+'/authorize',json=auth)
assert call('POST',base+'/authorize',json=auth)['id']==r['id']
report=call('GET',base+f"/report/{r['id']}")
assert 'NOT A SAFETY CERTIFICATE' in report and 'REVIEWED_SYNTHETIC_CALCULATION' in report
(ROOT/'docs/foundation-system/example-report.html').write_text(report,encoding='utf8')
alts=call('POST',base+'/alternatives',json=payload);assert len(alts['scenarios'])==6
p2=call('POST',base+'/preview',json={**payload,'inputs':{**q,'factored_column_kn':q['factored_column_kn']*2}})
call('POST',base+'/authorize',expected=409,json=auth)
assert next(x for x in call('GET',base,params=dict(model_revision_id=rid))['records'] if x['id']==r['id'])['status']=='STALE'
auth2=dict(proposal_id=p2['id'],proposal_sha256=p2['result']['proposal_sha256'],authorize_calculation=True)
r2=call('POST',base+'/authorize',json=auth2)
revpath=f"/api/projects/{pid}/scenarios/{copy['scenario_id']}/model-revisions"
old=call('GET',revpath+'/latest');doc=old['document'];doc['metadata']['isolated_revision_validation']=True
new=call('POST',revpath,json=dict(base_revision_id=rid,document=doc,source='manual_edit'))
call('POST',base+'/authorize',expected=409,json=auth2)
assert 'STALE' in call('GET',base+f"/report/{r2['id']}")
out=dict(attestation=attestation,study=copy,invalid_inputs=len(invalid),ownership=True,wrong_hash=True,explicit_authorization=True,idempotent=True,superseded_proposal=True,new_revision_stale=True,report=True,alternatives=alts,reviewed_result=r)
(ROOT/'docs/foundation-system/api-results.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ('alternatives','reviewed_result')},indent=2))

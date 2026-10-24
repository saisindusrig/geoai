"""Actual supervised CAD edit/import through existing APIs, isolated DB only."""
from pathlib import Path
import json,httpx
ROOT=Path(__file__).resolve().parents[2]
c=httpx.Client(base_url='http://127.0.0.1:18001',timeout=60)
a=c.get('/__foundation_validation').json()
assert a['mode']=='foundation-isolated-20261015' and Path(a['database']).resolve()==(ROOT/'docs/foundation-system/isolated/foundation.db').resolve()
def call(method,path,**kw):
 r=c.request(method,path,**kw);assert r.is_success,(path,r.status_code,r.text[:1200]);return r.json()
copy=call('POST','/api/projects/804/engineering/foundation-system/copy',json=dict(model_revision_id=124,authorize_separate_study=True))
pid=copy['project_id'];rid=copy['model_revision_id'];sid=copy['scenario_id'];base=f'/api/projects/{pid}'
foundation=base+'/engineering/foundation-system';cad=base+'/engineering/drawing-cad';revs=base+f'/scenarios/{sid}/model-revisions'
state=call('GET',foundation,params=dict(model_revision_id=rid));q=state['fixture']
prop=call('POST',foundation+'/preview',json=dict(model_revision_id=rid,inputs=q));result=call('POST',foundation+'/authorize',json=dict(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_calculation=True))
doc=call('GET',revs+'/latest')['document'];f=next(p for p in doc['components'] if p['id']==state['geometry']['footing_id']);item=f['metadata']['drawing_cad']['input'].copy()
item.update(operation='update_generated',size_east_mm=1500,size_north_mm=1500,bottom_mm=-540,top_mm=0,plan_policy='EXPLICIT_GEOMETRY_OVERRIDE',override_reason='Explicit synthetic geometry alternative, independently reviewed dimensions. Original DXF and engineering approval remain unchanged.')
inputs=dict(classification='SYNTHETIC_VERIFICATION',items=[item],connections=doc['metadata']['drawing_cad_model']['inputs']['connections'],reviewed_by='Isolated foundation validation',geometry_only_no_analysis=True)
audit=call('GET',cad,params=dict(model_revision_id=rid))
p=call('POST',cad+'/preview',json=dict(model_revision_id=rid,source_reference_id=audit['source_reference_id'],review_record_id=audit['review_record_id'],inputs=inputs))
assert p['status']=='PREVIEW_READY_GEOMETRY_ONLY',p['result'].get('missing')
authorized=call('POST',cad+'/authorize',json=dict(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_geometry=True))
new=call('POST',revs,json=dict(base_revision_id=rid,document=authorized['result']['approved_document'],source='manual_edit'))
updated=call('GET',foundation,params=dict(model_revision_id=new['id']))
assert updated['geometry']['footing_size_m']==[1.5,1.5,.54]
assert next(r for r in updated['records'] if r['id']==result['id'])['status']=='STALE'
newp=call('POST',foundation+'/preview',json=dict(model_revision_id=new['id'],inputs=q))
assert newp['result']['computed']['actions']['factored_net_pressure_kpa']==96
file=next((ROOT/'docs/foundation-system/isolated/drawing-references/804').glob('*.dxf'))
imported=call('POST',base+'/engineering/study/drawings/import',data=dict(model_revision_id=str(new['id']),classification='SYNTHETIC_VERIFICATION'),files={'file':(file.name,file.read_bytes(),'application/dxf')})
assert imported['result']['entities']
out=dict(attestation=a,study=copy,authorized_geometry_proposal=p['id'],saved_revision=new['id'],preserved_component_id=f['id'],dimensions_m=updated['geometry']['footing_size_m'],old_result_stale=True,recomputed_net_pressure_kpa=96,actual_dxf_import_record=imported['id'],imported_entities=len(imported['result']['entities']),original_source_project_unchanged=True)
(ROOT/'docs/foundation-system/cad-edit-import-results.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))

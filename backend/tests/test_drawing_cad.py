from copy import deepcopy
from decimal import Decimal as D
import json
import pytest
from fastapi import HTTPException
from app.services.design import drawing_cad as cad
from app.api.routes import drawing_cad as route,engineering_study as study
from app.db.models import ModelRevision
from test_drawing_strength import source,correction
from test_physical_column import seed,doc

def fixture():
 s=source();ids={e['handle']:e['id'] for e in s['entities']};q=dict(classification='SYNTHETIC_VERIFICATION',reviewed_by='Explicit synthetic geometry tester',geometry_only_no_analysis=True,items=[],connections=[])
 for handle,role,name,x,y,sx,sy,z0,z1 in [('9C','COLUMN','CAD column SW',150,150,300,300,0,3200),('AE','COLUMN','CAD column SE',5850,150,300,300,0,3200),('96','BEAM','CAD beam South',3000,150,6000,200,3100,3400),('95','SLAB','CAD slab',3000,2000,6000,4000,3400,3600),('9A','FOOTING_OUTLINE','CAD footing SW',150,150,1200,1200,-450,0),('AC','FOOTING_OUTLINE','CAD footing SE',5850,150,1200,1200,-450,0)]:
  q['items'].append(dict(entity_id=ids[handle],role=role,name=name,center_east_mm=x,center_north_mm=y,size_east_mm=sx,size_north_mm=sy,bottom_mm=z0,top_mm=z1,material_name='Explicit synthetic material identity; no grade/E/fy',material_source='Verification input only; not measured/manufacturer material data',geometry_source='Explicit synthetic S-001 geometry declaration; plan is reference only',connectivity='EXPLICIT_ATTACHMENTS',connectivity_source='Explicit geometric attachments only, no analytical joint behavior'))
 for i,(a,b,p) in enumerate([('9A','9C',[150,150,0]),('9C','96',[150,150,3200]),('AC','AE',[5850,150,0]),('AE','96',[5850,150,3200]),('96','95',[3000,150,3400])]):q['connections'].append(dict(id=f'attachment-{i}',from_entity_id=ids[a],to_entity_id=ids[b],point_mm=p,behavior='DECLARED_GEOMETRIC_ATTACHMENT_NOT_ANALYTICAL_JOINT',source='Explicit synthetic common point only; no joint stiffness or capacity'))
 return q
def build(q=None,d=None):return cad.build(source(),dict(inputs=correction()),d or doc(),q or fixture())
def test_independent_geometry_units_and_preservation():
 d=doc();before=deepcopy(d);s=source();r=deepcopy(s);b=build(d=d);assert b['status']=='PREVIEW_READY_GEOMETRY_ONLY';assert d==before and s==r
 assert len(b['proposed_document']['components'])==len(d['components'])+6
 assert b['proposed_document']['components'][:len(d['components'])]==d['components']
 for it,c in zip(fixture()['items'],b['components']):
  expected=[float(D(str(it[k]))/D(1000)) for k in ['size_east_mm','size_north_mm']]+[float((D(str(it['top_mm']))-D(str(it['bottom_mm'])))/D(1000))]
  assert c['geometry']['size']==pytest.approx(expected);assert c['transform']['position'][2]==float((D(str(it['top_mm']))+D(str(it['bottom_mm'])))/D(2000));assert c['quantity']['included'] is False
 assert cad.digest({'a':0.0,'b':[1.0,.3]})==cad.digest({'a':0,'b':[1,.3]})
@pytest.mark.parametrize('field',['role','center_east_mm','center_north_mm','size_east_mm','size_north_mm','bottom_mm','top_mm','connectivity','name','material_name','material_source','geometry_source','connectivity_source'])
def test_missing_explicit_inputs_block(field):
 q=fixture();q['connections']=[];q['items'][0][field]=None if field in ['role','center_east_mm','center_north_mm','size_east_mm','size_north_mm','bottom_mm','top_mm','connectivity'] else '';r=build(q);assert r['status'].startswith('BLOCKED');assert r['proposed_document'] is None
@pytest.mark.parametrize('bad',['unknown','circle','plate','stair','duplicate','negative','nan','top','plan','update','unknown_edge','outside_edge','duplicate_edge','source','arbitrary'])
def test_rejections(bad):
 q=fixture();s=source();it=q['items'][0]
 if bad in ['circle','plate','stair']:it['entity_id']=next(e['id'] for e in s['entities'] if e['handle']=={'circle':'9D','plate':'9B','stair':'BE'}[bad])
 if bad=='unknown':it['entity_id']='unknown'
 if bad=='duplicate':q['items'].append(deepcopy(it))
 if bad=='negative':it['size_east_mm']=-300
 if bad=='nan':it['top_mm']=float('nan')
 if bad=='top':it['top_mm']=it['bottom_mm']
 if bad=='plan':it['size_east_mm']=400
 if bad=='update':it['operation']='update_generated'
 if bad=='unknown_edge':q['connections'][0]['to_entity_id']='unknown'
 if bad=='outside_edge':q['connections'][0]['point_mm'][2]=9000
 if bad=='duplicate_edge':q['connections'].append(deepcopy(q['connections'][0]))
 if bad=='source':s['classification']='REAL_PROJECT'
 if bad=='arbitrary':q['solver_script']='arbitrary'
 with pytest.raises(ValueError):cad.build(s,dict(inputs=correction()),doc(),q)
def test_edit_stable_identity_override_and_duplicate_creation():
 b=build();q=fixture()
 with pytest.raises(ValueError):build(q,b['proposed_document'])
 for i in q['items']:i['operation']='update_generated'
 q['items'][0]['top_mm']=3260;b2=build(q,b['proposed_document']);assert b2['components'][0]['id']==b['components'][0]['id'];assert b2['components'][0]['geometry']['size'][2]==3.26;assert b2['components'][1:]==b['components'][1:]
 q['items'][0].update(size_east_mm=320,plan_policy='EXPLICIT_GEOMETRY_OVERRIDE',override_reason='Explicit synthetic envelope deviation; original DXF untouched');assert build(q,b['proposed_document'])['status']=='PREVIEW_READY_GEOMETRY_ONLY'
def test_authorization_source_staleness_and_save_bypass(db_session,tmp_path,monkeypatch):
 db=db_session;d=seed(db);rev=db.get(ModelRevision,1);d['metadata']['drawing_review']={};d['metadata']['drawing_review']={'classification':'SYNTHETIC_VERIFICATION'};rev.document_json=d;db.commit();s=source();monkeypatch.setattr(study,'ROOT',tmp_path);p=tmp_path/'1';p.mkdir();(p/(s['source_sha256']+'.dxf')).write_bytes(__import__('test_drawing_strength').FILE.read_bytes())
 src=study.record(1,rev,study.SOURCE,'REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL',s,db,1);review=study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1)
 prop=route.preview(1,route.Save(model_revision_id=1,source_reference_id=src.id,review_record_id=review.id,inputs=fixture()),db,1)
 with pytest.raises(HTTPException):route.validate_save(1,rev,prop['result']['proposed_document'],db,1)
 with pytest.raises(HTTPException):route.authorize(1,route.Authorize(proposal_id=prop['id'],proposal_sha256='0'*64,authorize_geometry=True),db,1)
 a=route.authorize(1,route.Authorize(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_geometry=True),db,1);approved=a['result']['approved_document'];route.validate_save(1,rev,approved,db,1)
 assert route.authorize(1,route.Authorize(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_geometry=True),db,1)['id']==a['id']
 modified=deepcopy(approved);modified['components'][-1]['transform']['position'][0]+=1
 with pytest.raises(HTTPException):route.validate_save(1,rev,modified,db,1)
 # Real JS JSON number normalization does not invalidate approval.
 normalized=json.loads(json.dumps(approved),parse_float=lambda x:int(float(x)) if float(x).is_integer() else float(x));route.validate_save(1,rev,normalized,db,1)
 path=p/(s['source_sha256']+'.dxf');path.write_bytes(path.read_bytes()+b'\n')
 with pytest.raises(HTTPException):route.validate_save(1,rev,approved,db,1)
 path.write_bytes(__import__('test_drawing_strength').FILE.read_bytes());newreview=study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1)
 with pytest.raises(HTTPException):route.validate_save(1,rev,approved,db,1)
 assert route.out(db.get(__import__('app.db.models',fromlist=['EngineeringAnalysis']).EngineeringAnalysis,prop['id']),db,1)['status']=='STALE'
 assert src.result_json['entities']==s['entities'];assert review.result_json['inputs']==correction()

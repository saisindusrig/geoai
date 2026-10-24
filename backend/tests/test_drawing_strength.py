from copy import deepcopy
from pathlib import Path
from decimal import Decimal as D
import io, math
import ezdxf
import pytest
from fastapi import HTTPException
from app.services.design import drawing_review as drawing,engineering_codes as codes
ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/'docs/drawing-strength/sources/GeoAI_Practice_Platform_Plan_mm.dxf'
def source():return drawing.extract(FILE.read_bytes(),FILE.name,'UNVERIFIED')
def correction(s=None):
 s=s or source();e=s['entities'][0]
 return dict(corrections=[dict(entity_id=e['id'],label='SL-01 reviewed nominal exercise deck',role='SLAB',reviewed_dimensions_mm=[6000,4000],material='',property_classification='SYNTHETIC_VERIFICATION',source_reference='S-001 nominal member schedule and DXF handle 95',correction_reason='Review of nominal plan extents only; material and loads not supplied',matched_saved_component_id=None)],reviewed_by='Synthetic source reviewer',acknowledge_missing_engineering_inputs=True)
def test_exact_source_ids_units_notes_and_missing_inputs():
 s=source();assert s['classification']=='SYNTHETIC_VERIFICATION';assert len(s['entities'])==73;assert s['entity_counts']=={'LWPOLYLINE':18,'CIRCLE':16,'LINE':30,'TEXT':9};assert s['scale_to_m']==.001
 deck=s['entities'][0];assert deck['handle']=='95';assert deck['plan_dimensions_m']==[6,4];assert deck['points_m'][2]==[6,4,0];assert deck['points_native'][2]==[6000,4000,0];assert deck['material'] is None
 assert any('NOT FOR CONSTRUCTION' in n for n in s['notes']);assert all(e['engineering_status']=='UNVERIFIED' for e in s['entities']);assert s['analytical_model_status']=='BLOCKED'
 renamed=drawing.extract(FILE.read_bytes(),'other-name.dxf','SYNTHETIC_VERIFICATION');assert [e['id'] for e in renamed['entities']]==[e['id'] for e in s['entities']]
 r=drawing.review(s,correction(s),{'components':[]});assert r['analytical_model']['nodes']==[];assert r['analytical_model']['members']==[];assert s['entities'][0]['material'] is None

@pytest.mark.parametrize('bad',['real_classification','pdf','dwg','ifc','empty','invalid','oversized','unitless','out_of_plane','no_linework'])
def test_import_rejections(bad):
 b=FILE.read_bytes();name=FILE.name;cls='UNVERIFIED'
 if bad=='real_classification':cls='REAL_PROJECT'
 if bad in ['pdf','dwg','ifc']:name='file.'+bad
 if bad=='empty':b=b''
 if bad=='invalid':b=b'not a DXF'
 if bad=='oversized':b=b' '*2_000_001
 if bad in ['unitless','out_of_plane','no_linework']:
  d=ezdxf.new();d.units=0 if bad=='unitless' else 4
  if bad!='no_linework':d.modelspace().add_line((0,0,1 if bad=='out_of_plane' else 0),(1000,0,0))
  else:d.modelspace().add_text('Annotation only')
  out=io.StringIO();d.write(out);b=out.getvalue().encode()
 with pytest.raises(ValueError):drawing.extract(b,name,cls)

@pytest.mark.parametrize('kind',['LWPOLYLINE','POLYLINE','EXTRUSION'])
def test_curved_geometry_retained_as_unsupported_not_silently_straightened(kind):
 d=ezdxf.new();d.units=4;d.modelspace().add_line((0,0),(1000,0))
 if kind=='LWPOLYLINE':d.modelspace().add_lwpolyline([(0,0,1),(1000,0,0)],format='xyb')
 elif kind=='POLYLINE':p=d.modelspace().add_polyline2d([(0,0),(1000,0)]);p.vertices[0].dxf.bulge=1
 else:d.modelspace().add_circle((0,0),100,dxfattribs={'extrusion':(0,1,0)})
 out=io.StringIO();d.write(out)
 s=drawing.extract(out.getvalue().encode(),'curve.dxf','UNVERIFIED');assert len(s['unsupported_entities'])==1;assert len(s['entities'])==1

@pytest.mark.parametrize('bad',['unknown','duplicate','mapping','real','missing_source','negative','nan','anchor_role','script'])
def test_review_missing_sources_geometry_and_identity_rejection(bad):
 s=source();q=correction(s);c=q['corrections'][0]
 if bad=='unknown':c['entity_id']='missing'
 if bad=='duplicate':q['corrections'].append(deepcopy(c))
 if bad=='mapping':c['matched_saved_component_id']='nonexistent'
 if bad=='real':c['property_classification']='REAL_PROJECT'
 if bad=='missing_source':c['source_reference']=''
 if bad=='negative':c['reviewed_dimensions_mm'][0]=-1
 if bad=='nan':c['reviewed_dimensions_mm'][0]=float('nan')
 if bad=='anchor_role':c['role']='ANCHOR_REFERENCE'
 if bad=='script':q['solver_script']='arbitrary code'
 with pytest.raises(ValueError):drawing.review(s,q,{'components':[]})

def test_independent_nominal_strength_units_scaling_and_caps():
 q=codes.fixture();r=codes.calculate(q);assert r['nominal_strength_n']==float(D('245')*D('600'))==147000;assert r['effective_area_m2']==245/1e6;assert r['design_strength_phi_n'] is None;assert r['physical_connection_capacity']=='NOT_VERIFIED'
 half=deepcopy(q);half['effective_tensile_area_mm2']/=2;assert codes.calculate(half)['nominal_strength_kn']==73.5
 q['yield_strength_mpa']=250;r=codes.calculate(q);assert r['used_fu_mpa']==475;assert r['nominal_strength_n']==float(D('245')*D('475'))==116375
 q.update(yield_strength_mpa=600,ultimate_strength_mpa=1000);r=codes.calculate(q);assert r['used_fu_mpa']==pytest.approx(125000*6894.757293168361/1e6);assert r['governing_strength_limit']=='125000 psi';assert r['nominal_strength_n']==pytest.approx(float(D('245')*D('125000')*D('6894.757293168361')/D('1000000')))
 assert codes.benchmark()['status']=='VERIFIED';assert r['engineering_approval']=='DISABLED';assert abs(r['independent_inlb']['error_n'])<1e-6

@pytest.mark.parametrize('bad',['IS','AISC','edition','country','unverified','synthetic_promoted','source','area','nan','fu_below_fy','scope','script'])
def test_strength_rejects_unimplemented_or_unsourced_methods(bad):
 q=codes.fixture()
 if bad=='IS':q.update(method_id=codes.REGISTRY[1]['id'],country='IN',code_edition='IS 800:2007')
 if bad=='AISC':q.update(method_id=codes.REGISTRY[2]['id'],code_edition='AISC 360-22')
 if bad=='edition':q['code_edition']='ACI 318-25'
 if bad=='country':q['country']='IN'
 if bad=='unverified':q['input_classification']='UNVERIFIED'
 if bad=='synthetic_promoted':q['input_classification']='REAL_PROJECT'
 if bad=='source':q['material_source']=''
 if bad=='area':q['effective_tensile_area_mm2']=0
 if bad=='nan':q['ultimate_strength_mpa']=float('nan')
 if bad=='fu_below_fy':q['ultimate_strength_mpa']=200
 if bad=='scope':q['pure_axial_single_steel_element']=False
 if bad=='script':q['code']='arbitrary code'
 with pytest.raises(ValueError):codes.calculate(q)

def test_authorization_drawing_link_review_staleness_and_immutable_evidence(db_session):
 from test_physical_column import seed
 from app.db.models import ModelRevision,EngineeringAnalysis
 from app.api.routes import engineering_study as route
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json={**rev.document_json,'metadata':{'drawing_review':True,'engineering_method_review':True}};db_session.commit()
 src=route.record(1,rev,route.SOURCE,'REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL',source(),db_session,1)
 reviewed=route.save_review(1,route.ReviewSave(model_revision_id=1,source_reference_id=src.id,inputs=correction(src.result_json)),db_session,1);assert reviewed['result']['analytical_model']['members']==[]
 q=codes.fixture();q['linked_drawing_reference_id']=src.id;q['linked_drawing_entity_id']=next(e['id'] for e in src.result_json['entities'] if e['kind']=='CIRCLE')
 i=route.save_steel(1,route.SteelSave(model_revision_id=1,inputs=q),db_session,1);row=db_session.get(EngineeringAnalysis,i['id']);unchanged=deepcopy(row.result_json)
 with pytest.raises(HTTPException):route.run(1,route.Authorize(input_id=i['id'],input_sha256='0'*64,authorize_nominal_steel_term=True),db_session,1)
 a=route.Authorize(input_id=i['id'],input_sha256=i['result']['input_sha256'],authorize_nominal_steel_term=True);result=route.run(1,a,db_session,1);assert result['result']['nominal_strength_kn']==147;assert route.run(1,a,db_session,1)['id']==result['id'];assert row.result_json==unchanged
 changed=correction(src.result_json);changed['corrections'][0]['reviewed_dimensions_mm'][0]=5900
 route.save_review(1,route.ReviewSave(model_revision_id=1,source_reference_id=src.id,base_review_id=reviewed['id'],inputs=changed),db_session,1)
 assert route.output(db_session.get(EngineeringAnalysis,result['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,a,db_session,1)
 q['effective_tensile_area_mm2']=200;second=route.save_steel(1,route.SteelSave(model_revision_id=1,base_input_id=i['id'],inputs=q),db_session,1);assert second['id']!=i['id'];assert row.result_json==unchanged
 q['linked_drawing_entity_id']='invented'
 with pytest.raises(HTTPException):route.save_steel(1,route.SteelSave(model_revision_id=1,base_input_id=second['id'],inputs=q),db_session,1)
 # An implementation/edition manifest change cannot silently reuse the old result.
 q['linked_drawing_entity_id']=result['result']['linked_drawing']['entity_id'];third=route.save_steel(1,route.SteelSave(model_revision_id=1,base_input_id=second['id'],inputs=q),db_session,1)
 original=codes.REGISTRY[0]['method_version']
 try:
  codes.REGISTRY[0]['method_version']='changed-test-manifest'
  assert route.output(db_session.get(EngineeringAnalysis,third['id']),db_session,1)['status']=='STALE'
 finally:codes.REGISTRY[0]['method_version']=original

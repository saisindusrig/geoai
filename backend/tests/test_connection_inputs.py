"""Synthetic isolated tests only: these properties never enter saved actual review projects."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services.design import connection_inputs as c, anchor_contact_3d as mechanical

def audit():
 return dict(geometry=dict(objects=[{},dict(size_m=[.65,.65,.025]),dict(size_m=[1.2,1.2,.45])]),actual_anchor_local_positions=[dict(id=f'a{i+1}',position_east_north_m=p) for i,p in enumerate([[-.24,-.24],[-.24,.24],[.24,-.24],[.24,.24]])],demand=dict(compression_n=30000,demand_on_interface_enu_moment_nm=[0,-11753.693592818216,0],horizontal_shear_east_n=-10765.080571577306))
def evidence(category='engineer_declared_assumption'):
 return dict(category=category,reference='TEST ONLY isolated unit fixture; no physical evidence supplied',method='Explicit synthetic test values, never persisted as project properties',applicability='Test-only bounded linear mechanism, no physical capacity conclusion',reviewed_by='Unit-test reviewer')
def fixture():
 q=c.template(audit());q['saved_geometry_evidence']=evidence();q['mechanical_evidence']=evidence()
 def quantity(v):return dict(value=v,evidence=evidence())
 q.update(concrete_material='Test-only nominal contact material',contact_model_justification='Test-only homogeneous linear compression bed; not calibrated physical concrete',reference_plane_assumption='Test-only column-base N/M reference; horizontal shear moment transport excluded',contact_stiffness_n_m3=quantity(1e9),max_valid_pressure_pa=quantity(1e7),max_valid_contact_displacement_m=quantity(.005))
 q.update({key:True for key in c.FLAGS})
 for a in q['anchors']:
  a.update(material='Test-only steel material',geometry_and_material_evidence=evidence(),tension_load_path='Test-only independently declared effective linear axial spring to fixed ground, zero pretension, excludes physical embedment capacity')
  a.update({key:quantity(v) for key,v in dict(diameter_m=.02,effective_embedment_m=.3,tensile_area_m2=.000245,steel_modulus_pa=200e9,axial_stiffness_n_m=1e7,max_valid_tension_n=1e6,max_valid_opening_m=.005).items()})
 return q

def test_blank_draft_no_invented_properties_or_authorization():
 q=c.template(audit());r=c.assess(q,audit());assert r['status']=='BLOCKED_MISSING_ENGINEERING_INPUTS';assert q['contact_stiffness_n_m3']['value'] is None
 assert all(a['axial_stiffness_n_m']['value'] is None for a in q['anchors']);assert not q['engineer_input_review'];assert r['engineering_approval']=='DISABLED'
 with pytest.raises(ValueError,match='BLOCKED'):c.solve(q,audit())

@pytest.mark.parametrize('bad',['synthetic_contact','synthetic_anchor','synthetic_geometry','source','method','limits','reviewer','diameter','area','embedment','material','path','contact_justification','reference_plane',*c.FLAGS])
def test_evidence_mechanics_and_geometry_gates(bad):
 q=fixture()
 if bad=='synthetic_contact':q['contact_stiffness_n_m3']['evidence']['category']='synthetic_verification'
 if bad=='synthetic_anchor':q['anchors'][2]['axial_stiffness_n_m']['evidence']['category']='synthetic_verification'
 if bad=='synthetic_geometry':q['saved_geometry_evidence']['category']='synthetic_verification'
 if bad=='source':q['anchors'][0]['diameter_m']['evidence']['reference']=''
 if bad=='method':q['contact_stiffness_n_m3']['evidence']['method']=''
 if bad=='limits':q['max_valid_pressure_pa']['value']=None
 if bad=='reviewer':q['mechanical_evidence']['reviewed_by']=''
 if bad=='diameter':q['anchors'][0]['diameter_m']['value']=.2
 if bad=='area':q['anchors'][0]['tensile_area_m2']['value']=.001
 if bad=='embedment':q['anchors'][0]['effective_embedment_m']['value']=.5
 if bad=='material':q['anchors'][0]['material']=''
 if bad=='path':q['anchors'][0]['tension_load_path']=''
 if bad=='contact_justification':q['contact_model_justification']=''
 if bad=='reference_plane':q['reference_plane_assumption']=''
 if bad in c.FLAGS:q[bad]=False
 assert c.assess(q,audit())['status']=='BLOCKED_MISSING_ENGINEERING_INPUTS'
 with pytest.raises(ValueError):c.solve(q,audit())

@pytest.mark.parametrize('bad',['duplicate','unknown','negative','nan','infinity','extra','stiffness_domain'])
def test_reject_invalid_quantities_identity_and_arbitrary_arguments(bad):
 q=fixture()
 if bad=='duplicate':q['anchors'][0]['id']='a2'
 if bad=='unknown':q['anchors'][0]['id']='invented'
 if bad=='negative':q['anchors'][0]['steel_modulus_pa']['value']=-1
 if bad=='nan':q['contact_stiffness_n_m3']['value']=float('nan')
 if bad=='infinity':q['anchors'][0]['axial_stiffness_n_m']['value']=float('inf')
 if bad=='extra':q['solver_script']='arbitrary code'
 if bad=='stiffness_domain':q['anchors'][0]['axial_stiffness_n_m']['value']=1e14
 with pytest.raises(ValueError):c.assess(q,audit())

@pytest.mark.parametrize('limit',['max_valid_pressure_pa','max_valid_contact_displacement_m','max_valid_tension_n','max_valid_opening_m'])
def test_result_applicability_rejection(limit):
 q=fixture()
 if limit in q:q[limit]['value']=1e-12
 else:
  for a in q['anchors']:a[limit]['value']=1e-12
 with pytest.raises(ValueError,match='applicability'):c.solve(q,audit())

def test_known_answer_adapter_units_and_independent_equilibrium():
 q=fixture();a=audit();a['demand'].update(compression_n=84.5*1000,demand_on_interface_enu_moment_nm=[0,0,0]);r=c.solve(q,a)
 assert r['pressure_max_kpa']==pytest.approx(200);assert r['translation_down_m']==pytest.approx(.0002);assert r['active_contact_area_m2']==pytest.approx((650/1000)**2);assert all(v['tension_n']==0 for v in r['anchors'])
 assert r['status']=='COMPUTED_N_M_ONLY_WITH_DECLARED_INPUT_EVIDENCE';assert 'NOT_INDEPENDENTLY_AUTHENTICATED' in r['evidence_status'];assert r['inputs']['scope'].startswith('ACTUAL_SOURCE');assert r['engineering_approval']=='DISABLED'
 r=c.solve(q,audit());assert r['inputs']['compression_n']==30000;assert r['inputs']['moments_east_north_nm']==[0,-11753.693592818216];assert max(map(abs,r['equilibrium_residual_si']))<1e-6
 # Independently integrate the uniaxial triangular strip with analytic integrals.
 u,sx,sy=[r['translation_down_m'],*r['slopes_east_north_rad']];assert abs(sy)<1e-12
 left=-.325;right=min(.325,-u/sx);kc=1e9;L=.65
 C=kc*L*(u*(right-left)+sx*(right**2-left**2)/2)
 Q=kc*L*(u*(right**2-left**2)/2+sx*(right**3-left**3)/3)
 assert C==pytest.approx(r['compression_resultant_n'],abs=1e-6)
 tensions=sum(v['tension_n'] for v in r['anchors']);anchor_m=sum(v['position_east_north_m'][0]*v['tension_n'] for v in r['anchors'])
 assert C-tensions==pytest.approx(30000,abs=1e-6);assert -Q+anchor_m==pytest.approx(11753.693592818216,abs=1e-6)
 assert mechanical.benchmarks()['status']=='VERIFIED' # unchanged five-case method

def test_immutable_drafts_authorization_staleness_and_results(db_session,monkeypatch):
 from test_physical_column import seed
 from app.db.models import ModelRevision,EngineeringAnalysis
 from app.api.routes import connection_inputs as route
 from app.services.design import opensees_benchmark as common
 seed(db_session);rev=db_session.get(ModelRevision,1);src=SimpleNamespace(result_json={'source':'unchanged evidence'});actual=audit()
 monkeypatch.setattr(route,'audit',lambda *args:(rev,src,actual))
 first=route.save(1,route.Save(model_revision_id=1,inputs=c.template(actual)),db_session,1)
 assert first['status']=='BLOCKED_MISSING_ENGINEERING_INPUTS'
 with pytest.raises(HTTPException) as e:route.run(1,route.Authorize(input_id=first['id'],input_sha256=first['result']['input_sha256'],authorize_n_m_contact=True),db_session,1)
 assert e.value.status_code==422
 with pytest.raises(HTTPException):route.save(1,route.Save(model_revision_id=1,inputs=fixture()),db_session,1)
 q=fixture();second=route.save(1,route.Save(model_revision_id=1,base_input_id=first['id'],inputs=q),db_session,1);row=db_session.get(EngineeringAnalysis,second['id']);before=deepcopy(row.result_json)
 with pytest.raises(HTTPException):route.run(1,route.Authorize(input_id=second['id'],input_sha256='0'*64,authorize_n_m_contact=True),db_session,1)
 authorization=route.Authorize(input_id=second['id'],input_sha256=second['result']['input_sha256'],authorize_n_m_contact=True)
 result=route.run(1,authorization,db_session,1);assert route.run(1,authorization,db_session,1)['id']==result['id'];assert row.result_json==before
 assert route.output(db_session.get(EngineeringAnalysis,first['id']),db_session,1)['status']=='STALE'
 # Any property/source change invalidates old results even with identical values/geometry.
 q['anchors'][0]['axial_stiffness_n_m']['evidence']['reference']+=' revised provenance'
 route.save(1,route.Save(model_revision_id=1,base_input_id=second['id'],inputs=q),db_session,1)
 assert route.output(db_session.get(EngineeringAnalysis,result['id']),db_session,1)['status']=='STALE'
 assert row.result_json==before
 src.result_json={'source':'changed source'}
 assert route.output(db_session.get(EngineeringAnalysis,result['id']),db_session,1)['status']=='STALE'
 assert common.digest(before)==common.digest(row.result_json)

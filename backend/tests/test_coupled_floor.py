from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from app.services.design import coupled_floor as s,coupled_ritz
from app.api.routes import coupled_floors as route
from app.api.routes.physical_frames import Authorize
from app.db.models import ModelRevision,EngineeringAnalysis
from test_physical_column import seed

@pytest.fixture(autouse=True)
def artifacts(tmp_path,monkeypatch):monkeypatch.setattr(s,'ARTIFACTS',tmp_path)

def test_native_coupling_mesh_convergence_and_independent_plate_energy():
 r=s.validated_run();assert r['status']=='VERIFIED'
 assert r['center_uz_m']==pytest.approx(-.000937972021109,rel=1e-7)
 assert sum(n['applied'][2] for n in r['nodes'])==pytest.approx(-80000)
 assert sum(n['reaction'][2] for n in r['nodes'] if n['fixed'])==pytest.approx(80000,abs=1e-5)
 assert all(n['reaction'][2]==pytest.approx(20000,abs=1e-5) for n in r['nodes'] if n['fixed'])
 assert r['validation']['checks']['independent_center_relative_error']<.015
 assert r['validation']['checks']['independent_force_peak_normalized_error']<.03
 assert r['validation']['checks']['independent_moment_peak_normalized_error']<.05
 assert r['comparisons']['frame_displacement_error_m_rad']<1e-10
 assert max(v for k,v in r['comparisons'].items() if k!='frame_displacement_error_m_rad')<1e-6
 assert r['slabs']==[] and not r['production_enabled'] and not r['diaphragm_enabled'] and not r['two_storeys_enabled']
 tcl=(s.ARTIFACTS/r['run_id']/'model.tcl').read_text();assert 'beamUniform' not in tcl and 'rigidDiaphragm' not in tcl
 assert len(r['shell_global_nodal_resisting_forces'])==256

def test_ritz_independent_of_native_interface_data(monkeypatch):
 monkeypatch.setattr(s,'solve',lambda *a:pytest.fail('Independent Ritz must not invoke native solver'))
 r=coupled_ritz.solve(6);assert r['relative_residual']<1e-9
 assert r['center_uz_m']==pytest.approx(-.000943351306044,rel=1e-7)

def test_linear_pressure_scaling_and_work_energy(monkeypatch):
 original=s.model;base=s.solve(4)
 def half(mesh):
  m=original(mesh);m['pressure_pa']/=2;return m
 monkeypatch.setattr(s,'model',half);scaled=s.solve(4)
 assert scaled['center_uz_m']==pytest.approx(base['center_uz_m']/2,abs=1e-12)
 assert sum(n['reaction'][2] for n in scaled['nodes'])==pytest.approx(40000,abs=1e-6)
 assert all(m['uniform_global_n_m']==[0,0,0] for m in scaled['members'])
 assert sum(n['applied'][2]*n['displacement'][2] for n in base['nodes'])>0

@pytest.mark.parametrize('mesh',[0,3,32,-4,float('nan')])
def test_unreviewed_mesh_disabled(mesh):
 with pytest.raises(ValueError):s.model(mesh)

def test_shared_mesh_connectivity_no_double_loading_and_zero_offsets():
 m=s.model(16);q=m['frame'];shellnodes={n for e in m['quads'] for n in e['nodes']};framenodes={n['id'] for n in q['nodes'] if not n['fixed']}
 assert len(shellnodes)==289 and len(framenodes)==64 and framenodes.issubset(shellnodes)
 assert not q['slabs'] and not q['cases'][0]['nodal'] and q['cases'][0]['slab_factor']==0
 assert m['load_source']=='SHELL_CONSISTENT_NODAL_ONLY' and m['offset_m']==0
 doc=s.fixture();route.check_document(doc)
 assert len(doc['components'])==69

@pytest.mark.parametrize('change',['geometry','units','material','offset','diaphragm','pressure','identity'])
def test_modified_geometry_and_unsupported_assumptions_rejected(change):
 doc=s.fixture()
 if change=='geometry':doc['components'][0]['geometry']['size'][0]+=.1
 elif change=='units':doc['units']='imperial'
 elif change=='material':doc['components'][0]['material']['name']='changed'
 elif change=='identity':doc['components'][0]['id']='unbound'
 else:doc['metadata']['coupled_floor_review'][{'offset':'offset_m','diaphragm':'diaphragm','pressure':'pressure_pa'}[change]]=123
 with pytest.raises(ValueError):route.check_document(doc)

def test_owned_review_exact_authorization_staleness_replay_and_download(db_session,monkeypatch):
 seed(db_session);doc=s.fixture();doc.update(project_id=1,scenario_id=1);rev=db_session.get(ModelRevision,1);rev.document_json=doc;db_session.commit()
 # Native mechanics exercised independently above; isolate API authorization here.
 fake=dict(status='VERIFIED',run_id='api-fixture',nodes=[],members=[],shells=[],validation={'status':'VERIFIED'})
 (s.ARTIFACTS/'api-fixture').mkdir();monkeypatch.setattr(s,'validated_run',lambda:deepcopy(fake))
 p=route.review(1,route.Review(model_revision_id=1,review_parametric_geometry=True),db_session,1)
 auth=Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True)
 with pytest.raises(HTTPException):route.run(1,auth,db_session,1)
 with pytest.raises(HTTPException):route.history(1,db_session,99)
 auth.proposal_sha256=p['result']['proposal_sha256'];r=route.run(1,auth,db_session,1)
 assert r['status']=='VERIFIED' and route.run(1,auth,db_session,1)['id']==r['id']
 assert route.evidence(1,r['id'],db_session,1).media_type=='application/json'
 p2=route.review(1,route.Review(model_revision_id=1,review_parametric_geometry=True),db_session,1)
 assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 changed=deepcopy(doc);changed['components'][0]['name']='changed';rev.document_json=changed;db_session.commit()
 assert route.out(db_session.get(EngineeringAnalysis,p2['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,Authorize(proposal_id=p2['id'],proposal_sha256=p2['result']['proposal_sha256'],authorize_solver=True),db_session,1)

def test_no_unsupported_input_parameters():
 with pytest.raises(ValueError):route.Review(model_revision_id=1,review_parametric_geometry=True,diaphragm=True)
 with pytest.raises(ValueError):Authorize(proposal_id=1,proposal_sha256='a'*64,authorize_solver=False)

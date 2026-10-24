from copy import deepcopy
import json,math
import pytest
from app.services.design import eccentric_frame as benchmark,physical_frame as solver
from test_physical_frame import document,inputs
from test_physical_column import seed
from app.db.models import ModelRevision

def eccentric_doc(source):
 d=document(source);d['components'][1]['geometry']['size'][0]=4.3;d['components'][1]['transform']['position'][2]+=.1
 return d

def explicit(d):
 zero=deepcopy(d);zero['components'][1]['geometry']['size'][0]=4;zero['components'][1]['transform']['position'][2]-=.1
 q=inputs(zero);g=solver.geometry(d,q['component_ids'],allow_rigid_offsets=True)
 for j,o in zip(q['connections'],g['connection_offsets']):j.update(behavior='rigid_offset',offset_m=o['offset_m'],idealization_approved=True,source='Explicit synthetic massless rigid-arm idealization, not capacity approval')
 return q

def test_first_offset_benchmark_closed_form():
 r=benchmark.suite();assert r['status']=='VERIFIED';assert len(r['cases'])==8
 for c in r['cases']:assert c['rigid_offset_hand_verification']['passed'];assert max(map(abs,c['equilibrium_residual_si']))<1e-4
 assert r['cases'][0]['reactions'][0]['moment_nm']==pytest.approx(6000)
 assert r['cases'][4]['reactions'][0]['moment_nm']==pytest.approx(5600)
 assert r['cases'][4]['rigid_offset_transfers'][0]['offset_moment_nm']==pytest.approx(-400)

def test_saved_eccentric_mesh_units_hand_symmetry_and_local_mapping(db_session):
 seed(db_session);d=eccentric_doc(db_session.get(ModelRevision,1).document_json);q=explicit(d);runs=[solver.run({**q,'elements_per_member':n},d) for n in (1,2,4)];r=runs[0]
 assert all(x['status']=='VERIFIED' for x in runs)
 E,A,I,H,L,P,a,h=200e9,.06,.00045,3,4.3,20000,.15,.1
 k=24*E*I/H**3;b=12*E*I/H**2;c=2*E*A/H+48*E*I/L**3;dd=48*E*I*a/L**3-24*E*I/L**2;f=8*E*I/H+48*E*I*a*a/L**3-48*E*I*a/L**2+12*E*I/L
 eff=f-dd*dd/c;u=P/(k-b*b/eff);theta=-b*u/eff;v=-dd*theta/c
 for x in runs+[solver.run({**q,'units':'N-mm'},d)]:
  assert x['status']=='VERIFIED';node=next(n for n in x['nodes'] if n['id']==2);assert node['displacement_m']==pytest.approx([u,-v,theta],abs=1e-10)
  transfer=next(t for t in x['rigid_offset_transfers'] if t['node']==2);assert transfer['physical_end_displacement_si']==pytest.approx([u-h*theta,-v-a*theta,theta],abs=1e-10)
  fx,fy,m=transfer['physical_end_global_force_si'];assert transfer['offset_moment_nm']==pytest.approx(-a*fy-h*fx,abs=1e-7)
 assert r['physical_to_analytical_graph']['origin_enu_m']==[1,2,0]
 shifted=deepcopy(d)
 for member in shifted['components']:
  member['transform']['position']=[x+y for x,y in zip(member['transform']['position'],[12,-8,5])]
 g=solver.graph(shifted,q);assert g['origin_enu_m']==[13,-6,5];assert g['beam_offsets_m'][0]==pytest.approx([-.15,.1]);assert g['beam_offsets_m'][1]==pytest.approx([.15,.1])
 rr=solver.run(q,shifted)
 for actual,old in zip(rr['nodes'],r['nodes']):assert actual['position_m']==pytest.approx(old['position_m']);assert actual['displacement_m']==pytest.approx(old['displacement_m'],abs=1e-10)
 half=solver.run({**q,'load_n':10000},d);assert next(n for n in half['nodes'] if n['id']==2)['displacement_m']==pytest.approx([u/2,-v/2,theta/2],abs=1e-10)

@pytest.mark.parametrize('bad',['unapproved','vector','centerline','north','large','nan','missing','source'])
def test_no_inferred_or_unsupported_connection(db_session,bad):
 seed(db_session);d=eccentric_doc(db_session.get(ModelRevision,1).document_json);q=explicit(d)
 if bad=='unapproved':q['connections'][0]['idealization_approved']=False
 if bad=='vector':q['connections'][0]['offset_m'][0]+=.01
 if bad=='centerline':q['connections'][0]['behavior']='rigid'
 if bad=='north':d['components'][1]['transform']['position'][1]+=.1
 if bad=='large':d['components'][1]['geometry']['size'][0]=6
 if bad=='nan':q['connections'][0]['offset_m'][0]=float('nan')
 if bad=='missing':q['connections'][0].pop('offset_m')
 if bad=='source':q['connections'][0]['source']=''
 with pytest.raises(ValueError):solver.graph(d,q)

def test_offset_authorization_and_input_staleness(db_session,monkeypatch):
 import asyncio
 from app.api.routes import physical_frames as route
 from app.services.ai import nebius
 from fastapi import HTTPException
 from app.db.models import EngineeringAnalysis
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=eccentric_doc(rev.document_json);db_session.commit();q=explicit(rev.document_json)
 async def forbidden(*a,**k):raise AssertionError('No paid inference authorized')
 monkeypatch.setattr(nebius,'_request',forbidden)
 with pytest.raises(HTTPException):route.preview(1,route.Preview(model_revision_id=1,component_ids=q['component_ids']),db_session,1)
 preview=route.preview(1,route.Preview(model_revision_id=1,component_ids=q['component_ids'],allow_rigid_offsets=True),db_session,1);assert preview['connection_offsets'][0]['offset_length_m']>0
 saved=route.inputs(1,route.Save(model_revision_id=1,**q),db_session,1)
 p=asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,component_ids=q['component_ids'],allow_rigid_offsets=True,provider='mock',model='zai-org/GLM-5.3-Flash'),db_session,1))
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True),db_session,1)
 r=route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1);assert r['status']=='VERIFIED';assert r['result']['rigid_offset_verification_suite']['status']=='VERIFIED';assert r['result']['engineering_approval']=='DISABLED'
 q['connections'][0]['source']='Different explicit synthetic joint assumption requiring renewed review'
 route.inputs(1,route.Save(model_revision_id=1,base_input_id=saved['id'],**q),db_session,1)
 assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1)
 # Compact UI reads retain numerical/component evidence without mutating immutable full artifacts.
 before=db_session.get(EngineeringAnalysis,r['id']).result_json
 compact=route.history(1,db_session,1,compact=True)['records']
 item=next(v for v in compact if v['id']==r['id']);assert 'verification_suite' not in item['result'];assert item['result']['verification_evidence']['rigid_offset_status']=='VERIFIED';assert item['result']['rigid_offset_transfers']
 assert db_session.get(EngineeringAnalysis,r['id']).result_json==before
 manifest=route.artifact(1,r['id'],'manifest.json',db_session,1);assert json.loads(manifest['contents'])['rigid_offset_verification_suite']['status']=='VERIFIED'

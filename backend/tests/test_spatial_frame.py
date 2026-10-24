from copy import deepcopy
import json
import numpy as np
import pytest
from fastapi import HTTPException
from app.services.design import spatial_frame as s,spatial_review as fixtures
from app.api.routes import spatial_frames as route
from app.api.routes.physical_frames import Authorize
from app.db.models import ModelRevision,EngineeringAnalysis
from test_physical_column import seed

@pytest.fixture(autouse=True)
def artifacts(tmp_path,monkeypatch):monkeypatch.setattr(s,'ARTIFACTS',tmp_path)

def test_six_dof_closed_forms_three_axes_two_units():
 gate=fixtures.benchmarks();assert gate['status']=='VERIFIED';assert len(gate['checks'])==6
 assert max(c['max_abs_error'] for c in gate['checks'])<1e-16

@pytest.mark.parametrize('storeys',[1,2])
def test_connected_space_frame_equilibrium_superposition_and_units(storeys):
 doc,q=fixtures.fixture(storeys);s.validate(q,doc)
 results=[s.solve(q,c) for c in q['cases']]
 assert all(r['status']=='VERIFIED' for r in results)
 assert len(q['members'])==13*storeys
 for key in ['displacement','reaction']:
  a,b,c=[np.array([n[key] for n in r['nodes']]) for r in results]
  assert np.allclose(a+b,c,atol=1e-8)
 assert sum(n['reaction'][2] for n in results[0]['nodes'])==pytest.approx(160000*storeys,abs=1e-6)
 assert sum(n['reaction'][0] for n in results[1]['nodes'])==pytest.approx(-7500*storeys,abs=1e-6)
 mm=s.solve(q,q['cases'][2],'N-mm')
 assert np.allclose([n['displacement'] for n in mm['nodes']],[n['displacement'] for n in results[2]['nodes']],atol=1e-10)
 assert any(abs(m['end_forces'][3])>1 for m in results[2]['members']) # actual coupled torsion
 assert all(max(abs(v) for k,v in r['comparisons'].items() if k!='displacement_max_abs')<1e-6 for r in results)

def test_uniform_fixed_beam_section_values_and_deflection():
 # Two reviewed equal-span beams, fixed ends, slab loads 10 kN/m each.
 d,q=fixtures.fixture(1);d=deepcopy(d);q['members']=q['members'][6:10];q['slabs']=q['slabs'][:1];q['members']=[m for m in q['members'] if m['id'] in q['slabs'][0]['beams']]
 # Connect the two beams by one unloaded transverse beam, all four nodes fixed.
 q['members'].append(next(m for m in d['metadata']['spatial_frame_review']['input']['members'] if m['kind']=='beam' and m['nodes']==[7,10]))
 tags=set(i for m in q['members'] for i in m['nodes']);q['nodes']=[dict(n,fixed=True) for n in q['nodes'] if n['id'] in tags]
 # reference rejects all-fixed systems intentionally; add a free unloaded cantilever to retain a nontrivial solve.
 q['nodes'].append(dict(id=99,position=[0,0,6],fixed=False));col=deepcopy(q['members'][0]);col.update(id='free-column',nodes=[7,99],vecxz=[0,1,0],kind='column');q['members'].append(col)
 q['cases']=[q['cases'][0]];r=s.solve(q,q['cases'][0]);m=r['members'][0];EI=m['E']*m['Iy'];w=-10000;L=4
 assert r['status']=='VERIFIED'
 assert m['samples'][8]['displacement'][2]==pytest.approx(w*L**4/(384*EI),abs=1e-12)
 assert abs(m['samples'][0]['My'])==pytest.approx(abs(w)*L**2/12)
 assert abs(m['samples'][8]['My'])==pytest.approx(abs(w)*L**2/24)
 assert m['samples'][8]['Vz']==pytest.approx(0,abs=1e-7)

@pytest.mark.parametrize('bad',['duplicate','disconnected','missing','orientation','width','slab','geometry','section','rotation','nan','release','loadnode','fixed','case','rolled','parent','coordinate_range','orientation_range'])
def test_invalid_and_unsupported_disabled(bad):
 d,q=fixtures.fixture(2)
 if bad=='duplicate':q['members'].append(q['members'][0])
 if bad=='disconnected':q['nodes'].append(dict(id=99,position=[99,0,0],fixed=False))
 if bad=='missing':q['members'][0]['nodes'][1]=99
 if bad=='orientation':q['members'][0]['vecxz']=[0,0,1]
 if bad=='width':q['slabs'][0]['width_m']=3
 if bad=='slab':q['slabs'][0]['beams'][0]=q['members'][0]['id']
 if bad=='geometry':d['components'][0]['transform']['position'][0]=.01
 if bad=='section':q['members'][0]['Iy']*=2
 if bad=='rotation':d['components'][0]['transform']['rotation_deg'][1]=1
 if bad=='nan':q['members'][0]['J']=float('nan')
 if bad=='release':q['members'][0]['release']='hinge'
 if bad=='loadnode':q['cases'][0]['nodal']={99:[0]*6}
 if bad=='fixed':
  for n in q['nodes']:n['fixed']=False
 if bad=='case':q['cases'].append(q['cases'][0])
 if bad=='rolled':q['members'][0]['vecxz']=[1,1,0]
 if bad=='parent':d['components'][0]['parent_id']='unreviewed-parent'
 if bad=='coordinate_range':q['nodes'][0]['position'][0]=1001
 if bad=='orientation_range':q['members'][0]['vecxz']=[0,1001,0]
 with pytest.raises((ValueError,KeyError)):s.validate(q,d)

def test_revision_hash_authorization_idempotence_ownership_and_staleness(db_session):
 seed(db_session);doc,q=fixtures.fixture(1);rev=db_session.get(ModelRevision,1);doc.update(project_id=1,scenario_id=1);rev.document_json=doc;db_session.commit()
 p=route.review(1,route.Review(model_revision_id=1,inputs=q),db_session,1)
 auth=Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True)
 with pytest.raises(HTTPException):route.run(1,auth,db_session,1)
 with pytest.raises(HTTPException):route.history(1,db_session,99)
 auth.proposal_sha256=p['result']['proposal_sha256'];r=route.run(1,auth,db_session,1)
 assert r['status']=='VERIFIED';assert route.run(1,auth,db_session,1)['id']==r['id']
 assert route.evidence(1,r['id'],db_session,1).media_type=='application/json'
 newer=route.review(1,route.Review(model_revision_id=1,inputs=q),db_session,1)
 assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 changed=deepcopy(doc);changed['components'][0]['name']='renamed';rev.document_json=changed;db_session.commit()
 assert route.out(db_session.get(EngineeringAnalysis,newer['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,Authorize(proposal_id=newer['id'],proposal_sha256=newer['result']['proposal_sha256'],authorize_solver=True),db_session,1)

def test_artifacts_input_immutable_and_native_manifest(tmp_path):
 d,q=fixtures.fixture(1);before=json.dumps(q,sort_keys=True);r=s.solve(q,q['cases'][0]);assert json.dumps(q,sort_keys=True)==before
 folder=tmp_path/r['run_id'];assert (folder/'model.tcl').is_file();assert 'model BasicBuilder -ndm 3 -ndf 6' in (folder/'model.tcl').read_text()
 assert set(r['artifact_sha256'])=={'model.tcl','nodes.tsv','reactions.tsv','forces.tsv','stdout.txt','stderr.txt'}

def test_three_dimensional_mesh_refinement_and_stiffness_scaling():
 q=fixtures.cantilever(2);base=s.solve(q,q['cases'][0]);original=deepcopy(q['members'][0])
 for count in (2,4):
  mesh=deepcopy(q);mesh['nodes']=[mesh['nodes'][0]]+[dict(id=i+2,position=[0,0,3*(i+1)/count],fixed=False) for i in range(count)]
  mesh['members']=[dict(original,id=f'mesh-{i}',nodes=[i+1,i+2]) for i in range(count)];mesh['cases'][0]['nodal']={count+1:q['cases'][0]['nodal'][2]}
  r=s.solve(mesh,mesh['cases'][0]);assert r['status']=='VERIFIED';assert np.allclose(r['nodes'][-1]['displacement'],base['nodes'][-1]['displacement'],atol=1e-12)
 softer=deepcopy(q)
 for m in softer['members']:m['E']/=2;m['G']/=2
 r=s.solve(softer,softer['cases'][0]);assert np.allclose(r['nodes'][-1]['displacement'],np.array(base['nodes'][-1]['displacement'])*2,atol=1e-12)

def test_uniform_loads_and_recovered_fields_under_local_axis_permutation():
 doc,q=fixtures.fixture(1);a=s.solve(q,q['cases'][0]);permuted=deepcopy(q)
 for m in permuted['members']:
  if m['kind']=='beam' and m['nodes'][1]-m['nodes'][0]==1:m['vecxz']=[0,1,0]
 s.validate(permuted,doc);b=s.solve(permuted,permuted['cases'][0]);assert b['status']=='VERIFIED'
 for original,rotated in zip(a['members'],b['members']):
  assert np.allclose([s['displacement'] for s in original['samples']],[s['displacement'] for s in rotated['samples']],atol=1e-12)
 assert np.allclose([n['reaction'] for n in a['nodes']],[n['reaction'] for n in b['nodes']],atol=1e-7)


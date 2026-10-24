from copy import deepcopy
import asyncio,json
import pytest
from fastapi import HTTPException
from app.services.design import physical_frame as solver
from app.services.ai import nebius
from app.api.routes import physical_frames as route
from app.db.models import ModelRevision,EngineeringAnalysis
from test_physical_column import seed

def document(source):
 doc=deepcopy(source);doc['metadata'].pop('elastic_benchmark',None);doc['components']=doc['components'][:3]
 for c,(name,pos,size,kind) in zip(doc['components'],[('left',[1,2,1.5],[.3,.2,3],'column'),('beam',[3,2,3],[4,.2,.3],'beam'),('right',[5,2,1.5],[.3,.2,3],'column')]):
  c.update(name=name,category=kind,geometry={'kind':'box','size':size},parent_id=None);c['transform'].update(position=pos,rotation_deg=[0,0,0],scale=[1,1,1])
 return doc

def inputs(doc):
 ids=[c['id'] for c in doc['components']];g=solver.geometry(doc,ids)
 return dict(component_ids=ids,sections=[dict(component_id=m['component_id'],shape='solid_rectangle',elastic_modulus_pa=200e9,area_m2=m['solid_rectangle_area_m2'],inertia_m4=m['solid_rectangle_inertia_m4'],material_name='Synthetic elastic steel',material_source='Independent synthetic verification E, not project design',section_source='Explicit solid section declaration matching saved physical dimensions') for m in g['members']],connections=[dict(**j,behavior='rigid',source='Explicit synthetic rigid centerline idealization; capacity not checked') for j in g['candidate_joints']],supports='both_column_bases_fixed',support_source='Synthetic fixed base idealization, not foundation design',load_pattern='equal_horizontal_column_head_loads',load_n=20000,load_source='Synthetic equal horizontal nodal loads; no self weight',purpose='VERIFICATION_ONLY',elements_per_member=2,units='SI')

def test_physical_mapping_solver_mesh_units_loads_materials(db_session):
 seed(db_session);doc=document(db_session.get(ModelRevision,1).document_json);q=inputs(doc);results=[]
 for n in (1,2,4):
  r=solver.run({**q,'elements_per_member':n},doc);assert r['status']=='VERIFIED';assert all(c['passed'] for c in r['comparisons'].values());assert max(map(abs,r['equilibrium_residual_si']))<1e-4;results.append(r)
  assert r['input_file_sha256']==r['artifact_sha256']['model.tcl']
  assert {e['component_id'] for e in r['elements']}==set(q['component_ids']);assert r['physical_to_analytical_graph']['origin_enu_m']==[1,2,0]
 tip=lambda r:next(n for n in r['nodes'] if n['id']==2)['displacement_m']
 for r in results:assert tip(r)==pytest.approx(tip(results[0]),abs=1e-10)
 assert tip(solver.run({**q,'units':'N-mm'},doc))==pytest.approx(tip(results[0]),abs=1e-10)
 assert tip(solver.run({**q,'load_n':10000},doc))==pytest.approx([v*.5 for v in tip(results[0])],abs=1e-10)
 softer=deepcopy(q)
 for s in softer['sections']:s['elastic_modulus_pa']*=.5
 assert tip(solver.run(softer,doc))==pytest.approx([v*2 for v in tip(results[0])],abs=1e-10)
 nonuniform=deepcopy(q);nonuniform['sections'][0]['elastic_modulus_pa']=190e9
 assert solver.run(nonuniform,doc)['status']=='VERIFIED'

@pytest.mark.parametrize('bad',['offset','out_of_plane','rotation','category','section','references','joint','support','nonfinite','missing','duplicate'])
def test_reject_unsupported(db_session,bad):
 seed(db_session);doc=document(db_session.get(ModelRevision,1).document_json);q=inputs(doc)
 if bad=='offset':doc['components'][1]['geometry']['size'][0]=4.1
 if bad=='out_of_plane':doc['components'][1]['transform']['position'][1]+=.1
 if bad=='rotation':doc['components'][0]['transform']['rotation_deg'][0]=1
 if bad=='category':doc['components'][0]['category']='slab'
 if bad=='section':q['sections'][0]['inertia_m4']*=2
 if bad=='references':q['connections'][0]['column_id']='absent'
 if bad=='joint':q['connections'][0]['behavior']='pinned'
 if bad=='support':q['supports']='soil'
 if bad=='nonfinite':q['sections'][0]['elastic_modulus_pa']=float('nan')
 if bad=='missing':del q['sections'][0]['material_source']
 if bad=='duplicate':q['component_ids'][0]=q['component_ids'][1]
 with pytest.raises((ValueError,KeyError)):solver.graph(doc,q)

def test_authorization_offline_exact_revision_and_staleness(db_session,monkeypatch):
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=document(rev.document_json);db_session.commit();q=inputs(rev.document_json)
 async def forbidden(*a,**k):raise AssertionError('Paid inference prohibited')
 monkeypatch.setattr(nebius,'_request',forbidden)
 prepare=lambda provider='mock':asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,component_ids=q['component_ids'],provider=provider,model='zai-org/GLM-5.3-Flash'),db_session,1))
 p=prepare();assert p['status']=='NEEDS_INPUT'
 with pytest.raises(HTTPException):prepare('nebius')
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1)
 saved=route.inputs(1,route.Save(model_revision_id=1,**q),db_session,1);p=prepare();assert p['status']=='AWAITING_AUTHORIZATION'
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True),db_session,1)
 auth=route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True);r=route.run(1,auth,db_session,1);assert r['status']=='VERIFIED';assert route.run(1,auth,db_session,1)['id']==r['id']
 answer=asyncio.run(route.explain(1,p['id'],db_session,1));assert answer['result']['usage']['mock']
 q['load_n']=10000;route.inputs(1,route.Save(model_revision_id=1,base_input_id=saved['id'],**q),db_session,1)
 assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,auth,db_session,1)
 changed=deepcopy(rev.document_json);changed['components'][0]['transform']['position'][0]+=.1;rev.document_json=changed;db_session.commit()
 assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):prepare()


def test_independent_symmetric_hand_calculation(db_session):
 seed(db_session);doc=document(db_session.get(ModelRevision,1).document_json);q=inputs(doc);r=solver.run(q,doc)
 # Independently condensed symmetry equations, not the global stiffness assembler.
 E,A,I,H,L,P=200e9,.06,.00045,3,4,20000
 a=24*E*I/H**3;b=12*E*I/H**2;c=2*E*A/H+48*E*I/L**3;d=-24*E*I/L**2;f=8*E*I/H+12*E*I/L
 effective=f-d*d/c;u=P/(a-b*b/effective);theta=-b*u/effective;v=-d*theta/c
 heads={n['id']:n['displacement_m'] for n in r['nodes'] if n['id'] in (2,3)}
 assert heads[2]==pytest.approx([u,-v,theta],abs=1e-11)
 assert heads[3]==pytest.approx([u,v,theta],abs=1e-11)
 ry=E*A/H*v;moment=6*E*I/H**2*u+2*E*I/H*theta
 assert r['reactions'][0]['fx_n']==pytest.approx(-P/2)
 assert r['reactions'][0]['fy_n']==pytest.approx(ry)
 assert r['reactions'][0]['moment_nm']==pytest.approx(moment)
 assert 2*moment-ry*L==pytest.approx(P*H)


def test_selected_subset_not_whole_project(db_session):
 seed(db_session);rev=db_session.get(ModelRevision,1);doc=document(rev.document_json);q=inputs(doc)
 extra=deepcopy(doc['components'])
 for c in extra:c['id']+='-second';c['transform']['position'][0]+=10
 doc['components']+=extra;rev.document_json=doc;db_session.commit()
 route.inputs(1,route.Save(model_revision_id=1,**q),db_session,1)
 selected=[c['id'] for c in extra]
 p=asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,component_ids=selected,provider='mock',model='zai-org/GLM-5.3-Flash'),db_session,1))
 assert p['status']=='NEEDS_INPUT';assert set(p['result']['component_ids'])==set(selected)
 assert len(solver.geometry(doc,q['component_ids'])['members'])==3

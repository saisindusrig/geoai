from copy import deepcopy
import math, asyncio, json
import pytest
from app.services.design import elastic_frame as elastic, physical_frame as solver, gravity_frame as gravity
from test_eccentric_frame import eccentric_doc,explicit
from test_physical_column import seed
from app.db.models import ModelRevision,EngineeringAnalysis

def named(doc):
 q=explicit(doc)
 for k in ('load_pattern','load_n','load_source'):q.pop(k)
 ids=q['component_ids']
 q['load_cases']=[dict(name='Horizontal',source='Explicit synthetic +20 kN total East head loads',horizontal_n=20000),dict(name='Gravity',source='Synthetic uniform -2 kN/m beam and -1 kN per column top, no slab distribution',beam_uniform_n_per_m=-2000,vertical_nodal_loads=[dict(column_id=i,endpoint='top',fy_n=-1000) for i in (ids[0],ids[2])]),dict(name='Self weight',source='Synthetic explicit member weight only',self_weight=dict(densities=[dict(component_id=i,density_kg_m3=7850,source='Synthetic uniform density declaration') for i in ids],gravity_m_s2=9.81,direction='local_enu_negative_up',source='Synthetic g=9.81 m/s2, negative local Up'))]
 q['combination']=dict(name='H + G + SW',source='Synthetic unit-factor linear superposition; not code combination',factors=[dict(case_name=c['name'],factor=1) for c in q['load_cases']])
 return q

def symmetric_gravity_hand(g,case):
 """Three-DOF strain energy condensation, not the solver's member stiffness matrix."""
 left,beam,right=g['members'];c=left['section'];b=beam['section'];H=g['height_m'];L=beam['length_m'];a=-g['beam_offsets_m'][0][0];h=g['beam_offsets_m'][0][1];Bc=c['elastic_modulus_pa']*c['inertia_m4'];Bb=b['elastic_modulus_pa']*b['inertia_m4'];EA=c['elastic_modulus_pa']*c['area_m2'];EAb=b['elastic_modulus_pa']*b['area_m2'];w=case['uniform_global_by_component_n_per_m'][beam['component_id']][1];wc=case['uniform_global_by_component_n_per_m'][left['component_id']][1]
 k=24*Bc/H**3+4*EAb/L;cross=12*Bc/H**2-4*EAb*h/L;rot=8*Bc/H+4*EAb*h*h/L+4*Bb/L
 theta=w*(L*L/6-L*a)/(rot-cross*cross/k);u=-cross*theta/k;v=(w*L+sum(f[1] for f in case['nodal_loads_si'].values())+wc*H)/(2*EA/H)
 return dict(left_head=[u,v,theta],left_beam_end=[u-h*theta,v-a*theta,theta],midspan_v=v-a*theta+L*theta/4+w*L**4/(384*Bb),left_reaction=[-(12*Bc/H**3*u+6*Bc/H**2*theta),-EA/H*v-wc*H/2,6*Bc/H**2*u+2*Bc/H*theta],formula='Symmetric strain energy with rigid-arm kinematics: Kuu=24Bc/H³+4EAb/L; Kuθ=12Bc/H²-4EAb h/L; Kθθ=8Bc/H+4EAb h²/L+4Bb/L; Fθ=w(L²/6-La); Fv=wL+sumFy+wcH; θ=Fθ/(Kθθ-Kuθ²/Kuu), u=-Kuθθ/Kuu, v=Fv/(2EAc/H). Beam midpoint v-aθ+Lθ/4+wL⁴/(384Bb).')

def test_uniform_beam_prerequisite():
 r=gravity.suite();assert r['status']=='VERIFIED';assert len(r['cases'])==4
 for c in r['cases']:assert c['uniform_load_hand_verification']['passed']
 # One-element cantilever covers load particular solution where endpoint Hermite alone fails.
 for n in (1,2,4):
  q={**elastic.fixture('cantilever'),'elements_per_member':n};r=elastic.run(q,verification_loads={},verification_uniform={1:[0,-2000]});assert r['status']=='VERIFIED';assert r['nodes'][1]['displacement_m'][1]==pytest.approx(-2000*3**4/(8*200e9*8e-6),abs=1e-10)
 with pytest.raises(ValueError):elastic.run({**elastic.fixture('cantilever'),'kind':'fixed_beam','elements_per_member':1},verification_loads={},verification_uniform={1:[0,-2000]})

def test_eccentric_cases_weight_mesh_units_and_superposition(db_session):
 seed(db_session);doc=eccentric_doc(db_session.get(ModelRevision,1).document_json);q=named(doc);runs=[]
 for n,unit in [(1,'SI'),(2,'SI'),(4,'SI'),(2,'N-mm')]:
  r=solver.run({**q,'elements_per_member':n,'units':unit},doc);assert r['status']=='VERIFIED';assert r['superposition_verification']['passed'];runs.append(r)
  for case in r['load_case_results'][1:]:
   h=symmetric_gravity_hand(r['physical_to_analytical_graph'],case['applied_loads']);head=next(v for v in case['nodes'] if v['id']==2)['displacement_m'];assert head==pytest.approx(h['left_head'],abs=1e-10)
   midpoint=min([s for e in case['elements'] if e['component_id']==q['component_ids'][1] for s in e['samples']],key=lambda s:abs(s['position_m'][0]-2));assert midpoint['displacement_m'][1]==pytest.approx(h['midspan_v'],abs=1e-10)
   reaction=case['reactions'][0];assert [reaction['fx_n'],reaction['fy_n'],reaction['moment_nm']]==pytest.approx(h['left_reaction'],abs=1e-6)
  assert max(map(abs,r['equilibrium_residual_si']))<1e-4
 for r in runs[1:]:assert [n['displacement_m'] for n in r['nodes'][:4]]==pytest.approx(__import__('numpy').array([n['displacement_m'] for n in runs[0]['nodes'][:4]]),abs=1e-10)
 half=deepcopy(q)
 for f in half['combination']['factors']:f['factor']=.5
 r=solver.run(half,doc);assert r['status']=='VERIFIED';assert [n['displacement_m'] for n in r['nodes'][:4]]==pytest.approx(__import__('numpy').array([n['displacement_m'] for n in runs[1]['nodes'][:4]])*.5,abs=1e-10)

@pytest.mark.parametrize('bad',['missing_density','density_reference','gravity','direction','source','nodal_reference','duplicate_node','beam_reference','unknown_case','duplicate_case','mixed','empty','nan','unsupported','section','missing_joint'])
def test_missing_and_unsupported_load_inputs(db_session,bad):
 seed(db_session);doc=eccentric_doc(db_session.get(ModelRevision,1).document_json);q=named(doc);sw=q['load_cases'][2]['self_weight']
 if bad=='missing_density':sw['densities'].pop()
 if bad=='density_reference':sw['densities'][0]['component_id']='unknown'
 if bad=='gravity':sw.pop('gravity_m_s2')
 if bad=='direction':sw['direction']='slab_down'
 if bad=='source':q['load_cases'][1]['source']=''
 if bad=='nodal_reference':q['load_cases'][1]['vertical_nodal_loads'][0]['column_id']='unknown'
 if bad=='duplicate_node':q['load_cases'][1]['vertical_nodal_loads'][1]=q['load_cases'][1]['vertical_nodal_loads'][0]
 if bad=='beam_reference':q['load_cases'][1]['vertical_nodal_loads'][0]['column_id']=q['component_ids'][1]
 if bad=='unknown_case':q['combination']['factors'][0]['case_name']='Missing'
 if bad=='duplicate_case':q['load_cases'][0]['name']=q['load_cases'][1]['name']
 if bad=='mixed':q['load_n']=10
 if bad=='empty':q['load_cases'][0]['horizontal_n']=0
 if bad=='nan':q['load_cases'][1]['beam_uniform_n_per_m']=float('nan')
 if bad=='unsupported':q['load_cases'][1]['slab_tributary_area']=20
 if bad=='section':q['sections'][0]['area_m2']=.1
 if bad=='missing_joint':q['connections'][0]['idealization_approved']=False
 with pytest.raises(ValueError):solver.graph(doc,q)

def test_named_authorization_evidence_and_staleness(db_session,monkeypatch):
 from app.api.routes import physical_frames as route
 from app.services.ai import nebius
 from fastapi import HTTPException
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=eccentric_doc(rev.document_json);db_session.commit();q=named(rev.document_json)
 async def forbidden(*a,**k):raise AssertionError('No paid inference permitted')
 monkeypatch.setattr(nebius,'_request',forbidden)
 saved=route.inputs(1,route.Save(model_revision_id=1,**q),db_session,1);p=asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,component_ids=q['component_ids'],allow_rigid_offsets=True,provider='mock',model='zai-org/GLM-5.3-Flash'),db_session,1))
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True),db_session,1)
 r=route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1);assert r['status']=='VERIFIED';assert r['result']['uniform_load_verification_suite']['status']=='VERIFIED'
 assert 'eleLoad' in route.artifact(1,r['id'],'model.tcl',db_session,1,case_name='Gravity')['contents']
 with pytest.raises(HTTPException):route.artifact(1,r['id'],'model.tcl',db_session,1,case_name='../unknown')
 full=db_session.get(EngineeringAnalysis,r['id']).result_json;small=route.history(1,db_session,1,compact=True)['records'][0]['result'];assert 'uniform_load_verification_suite' not in small;assert 'independent_reference' not in small['load_case_results'][0];assert db_session.get(EngineeringAnalysis,r['id']).result_json==full
 q['load_cases'][1]['beam_uniform_n_per_m']=-1000;route.inputs(1,route.Save(model_revision_id=1,base_input_id=saved['id'],**q),db_session,1);assert route.out(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'

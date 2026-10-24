from copy import deepcopy
import pytest,numpy as np
from test_unequal_frame import document as original,inputs as old_inputs
from app.services.design import physical_frame as frame,unequal_frame as independent

def document():
 d=original();d['metadata']['unequal_gravity_review']={'version':'cad-planar-unequal-gravity/1','classification':'SYNTHETIC_VERIFICATION'};return d

def inputs():
 d=document();q=old_inputs(d);ids=q['component_ids'];source='Synthetic verification inputs only, not measured engineering properties'
 q.update(load_n=None,load_pattern=None,load_source=None,load_cases=[dict(name='Horizontal',source=source,horizontal_n=20000),dict(name='Gravity',source=source,vertical_nodal_loads=[dict(column_id=id,endpoint='top',fy_n=-1000) for id in [ids[0],ids[2]]],beam_uniform_n_per_m=-2000),dict(name='Self weight',source=source,self_weight=dict(densities=[dict(component_id=id,density_kg_m3=7850,source=source) for id in ids],gravity_m_s2=9.81,direction='local_enu_negative_up',source=source))],combination=dict(name='Linear sum',source='Synthetic unit-factor superposition, not code combination',factors=[dict(case_name=name,factor=1) for name in ['Horizontal','Gravity','Self weight']]))
 return frame.Inputs.model_validate(q).model_dump()

def test_exact_gauss_fixed_end_load_hand_benchmark():
 L=6;E=200e9;I=.00045;w=-2000
 k,fe=independent.member_integrals(L,E*.06,E*I,0,w)
 assert fe==pytest.approx([0,w*L/2,w*L*L/12,0,w*L/2,-w*L*L/12],abs=1e-9)
 assert w*L**4/(384*E*I)==pytest.approx(-.000075)
 f=-fe;x=L/2;assert -f[2]+f[1]*x+w*x*x/2==pytest.approx(3000)
 assert k==pytest.approx(k.T,abs=1e-6)

def test_independent_load_integration_without_existing_helpers(monkeypatch):
 from app.services.design import elastic_frame,frame_loads
 def forbidden(*a,**kw):raise AssertionError('Existing load/stiffness helper must not be reused')
 monkeypatch.setattr(frame_loads,'normalize',forbidden);monkeypatch.setattr(frame_loads,'combine',forbidden);monkeypatch.setattr(elastic_frame,'reference',forbidden)
 for name in ['Horizontal','Gravity','Self weight','Linear sum']:
  r=independent.reference(document(),inputs(),name);assert max(map(abs,r['free_equation_residual_si']))<1e-5;assert not r['geometry_response_symmetry_assumed'];assert np.linalg.eigvalsh(r['free_stiffness_si']).min()>0

def test_actual_uniform_axial_member_against_hand_solution():
 from app.services.design import elastic_frame as elastic
 for mesh in [1,2,4]:
  q={**elastic.fixture('cantilever'),'elements_per_member':mesh};w=-1000;L=q['length_m'];EA=q['elastic_modulus_pa']*q['area_m2']
  r=elastic.run(q,verification_loads={},verification_uniform={1:[w,0]});assert r['status']=='VERIFIED'
  assert r['reactions'][0]['fx_n']==pytest.approx(-w*L,abs=1e-6)
  for e in r['elements']:
   for s in e['samples']:
    x=s['position_m'][0];assert s['displacement_m'][0]==pytest.approx(w*(2*L*x-x*x)/(2*EA),abs=1e-10);assert s['axial_n']==pytest.approx(w*(L-x),abs=1e-6)

def test_missing_or_tampered_real_result_cannot_verify():
 d=document();q=inputs();r=frame.run(q,d)
 for field in ['moment_nm','shear_n','axial_n']:
  bad=deepcopy(r);bad['elements'][0]['samples'][1][field]+=100;assert not independent.verify(d,q,bad)['passed']
 bad=deepcopy(r);bad['elements'][0]['samples']=[]
 with pytest.raises(ValueError):independent.verify(d,q,bad)
 bad=deepcopy(r);bad['elements'][0]['component_id']='unknown'
 with pytest.raises(ValueError):independent.verify(d,q,bad)

def test_real_solver_all_cases_mesh_units_scaling():
 d=document();before=deepcopy(d);q=inputs();baseline=None
 heads=lambda c:[v for n in [2,3] for v in next(x for x in c['nodes'] if x['id']==n)['displacement_m']]
 for mesh,units in [(1,'SI'),(2,'SI'),(4,'SI'),(2,'N-mm')]:
  r=frame.run({**q,'elements_per_member':mesh,'units':units},d);assert r['status']=='VERIFIED';assert r['superposition_verification']['passed'];cases=[*r['load_case_results'],r]
  assert all(c['unequal_frame_independent_verification']['passed'] for c in cases)
  for c in cases:
   assert max(map(abs,c['equilibrium_residual_si']))<1e-4
   assert max(abs(v) for values in c['joint_equilibrium_residuals_si'].values() for v in values)<1e-4
  if baseline:
   for c,b in zip(cases,baseline):assert heads(c)==pytest.approx(heads(b),abs=1e-10)
  else:baseline=cases
  assert sum(x['fy_n'] for x in cases[1]['reactions'])==pytest.approx(14000,abs=1e-6)
  weight=7850*9.81*(.09*(3.26+3.2)+.06*6)
  assert sum(x['fy_n'] for x in cases[2]['reactions'])==pytest.approx(weight,abs=1e-6)
 half=deepcopy(q)
 for c in half['load_cases']:
  c['horizontal_n']/=2;c['beam_uniform_n_per_m']/=2
  for v in c['vertical_nodal_loads']:v['fy_n']/=2
  if c['self_weight']:c['self_weight']['gravity_m_s2']/=2
 r=frame.run(half,d)
 for c,b in zip([*r['load_case_results'],r],baseline):assert heads(c)==pytest.approx([v/2 for v in heads(b)],abs=1e-10)
 softer=deepcopy(q)
 for section in softer['sections']:section['elastic_modulus_pa']/=2
 r=frame.run(softer,d)
 for c,b in zip([*r['load_case_results'],r],baseline):assert heads(c)==pytest.approx([v*2 for v in heads(b)],abs=1e-10)
 assert d==before

@pytest.mark.parametrize('bad',['scope','density','density_source','gravity','direction','unknown_node','duplicate_node','unknown_weight_member','duplicate_density','slab','foundation','unknown_case','offset','approval','nan','area','load_path'])
def test_invalid_input_rejection(bad):
 d=document();q=inputs();sw=q['load_cases'][2]['self_weight']
 if bad=='scope':d['metadata'].pop('unequal_gravity_review')
 if bad=='density':sw['densities'][0]['density_kg_m3']=0
 if bad=='density_source':sw['densities'][0]['source']=''
 if bad=='gravity':sw['gravity_m_s2']=0
 if bad=='direction':sw['direction']='unknown'
 if bad=='unknown_node':q['load_cases'][1]['vertical_nodal_loads'][0]['column_id']='absent'
 if bad=='duplicate_node':q['load_cases'][1]['vertical_nodal_loads'][1]=deepcopy(q['load_cases'][1]['vertical_nodal_loads'][0])
 if bad=='unknown_weight_member':sw['densities'][0]['component_id']='absent'
 if bad=='duplicate_density':sw['densities'][1]=deepcopy(sw['densities'][0])
 if bad=='slab':q['slab_distribution']='one_way'
 if bad=='foundation':q['supports']='soil_springs'
 if bad=='unknown_case':q['combination']['factors'][0]['case_name']='absent'
 if bad=='offset':q['connections'][0]['offset_m'][1]=0
 if bad=='approval':q['connections'][1]['idealization_approved']=False
 if bad=='nan':q['load_cases'][1]['beam_uniform_n_per_m']=float('nan')
 if bad=='area':q['sections'][1]['area_m2']/=2
 if bad=='load_path':q['load_cases'][1]['automatic_load_path']=True
 with pytest.raises(ValueError):frame.graph(d,q)

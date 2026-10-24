from copy import deepcopy
import pytest
import numpy as np
from app.services.design import physical_frame as frame,unequal_frame as independent,drawing_cad as cad
from test_cad_frame import documents,inputs as equal_inputs,IDS

def document():
 d,_=documents();d['metadata']['unequal_frame_review']={'version':independent.VERSION,'classification':'SYNTHETIC_VERIFICATION'};return d
def inputs(d=None):
 d=d or document();_,equal=documents();q=deepcopy(equal_inputs(equal));g=frame.geometry(d,IDS,allow_rigid_offsets=True)
 for i,j in enumerate(q['connections']):j.update(offset_m=g['connection_offsets'][i]['offset_m'],source='Explicit synthetic individually reviewed original unequal-column rigid offset; no capacity approval')
 return q
def test_exact_original_geometry_mapping_no_alignment():
 d=document();before=deepcopy(d);g=frame.graph(d,inputs(d));assert d==before
 assert g['unequal_heights'];assert g['column_heights_m']==[3.26,3.2];assert [n['position_m'][1] for n in g['nodes']]==[0,3.26,3.2,0]
 assert [m['length_m'] for m in g['members']]==[3.26,6,3.2]
 assert g['beam_offsets_m'][0]==pytest.approx([-.15,-.01]);assert g['beam_offsets_m'][1]==pytest.approx([.15,.05]);assert g['members'][1]['centerline_endpoints_m'][0][1]==3.25
 assert all(m['cad_source']['source_entity_id'].startswith('dxf:') for m in g['members'])
def test_full_energy_matrix_is_independent_of_existing_helpers(monkeypatch):
 from app.services.design import elastic_frame as elastic
 def forbidden(*a,**k):raise AssertionError('Symmetric/reused mesh or stiffness helper prohibited')
 monkeypatch.setattr(elastic,'mesh',forbidden);monkeypatch.setattr(elastic,'reference',forbidden);monkeypatch.setattr(elastic,'offset_operator',forbidden)
 r=independent.reference(document(),inputs());K=np.array(r['free_stiffness_si']);assert K.shape==(6,6);assert min(np.linalg.eigvalsh(K))>0;assert r['geometry_response_symmetry_assumed'] is False
 assert r['nodes'][2][0]!=pytest.approx(r['nodes'][3][0],abs=1e-10);assert r['nodes'][2][2]!=pytest.approx(r['nodes'][3][2],abs=1e-10)
 assert max(map(abs,r['free_equation_residual_si']))<1e-6
def test_opensees_unequal_mesh_units_scaling_materials_and_equal_comparison():
 d=document();q=inputs(d);before=deepcopy(d);results=[]
 for n in [1,2,4]:
  r=frame.run({**q,'elements_per_member':n},d);assert r['status']=='VERIFIED';assert r['unequal_frame_independent_verification']['passed'];assert max(map(abs,r['equilibrium_residual_si']))<1e-4;assert all(v['passed'] for v in r['comparisons'].values());results.append(r)
  assert next(x for x in r['nodes'] if x['id']==2)['position_m'][1]==3.26;assert next(x for x in r['nodes'] if x['id']==3)['position_m'][1]==3.2
  assert {e['component_id'] for e in r['elements']}==set(IDS)
 heads=lambda r:[v for node in [2,3] for v in next(n for n in r['nodes'] if n['id']==node)['displacement_m']]
 for r in results:assert heads(r)==pytest.approx(heads(results[0]),abs=1e-10)
 assert heads(frame.run({**q,'units':'N-mm'},d))==pytest.approx(heads(results[0]),abs=1e-10)
 assert heads(frame.run({**q,'load_n':10000},d))==pytest.approx([v/2 for v in heads(results[0])],abs=1e-10)
 softer=deepcopy(q)
 for s in softer['sections']:s['elastic_modulus_pa']/=2;s['material_source']='Explicit synthetic E=100 GPa stiffness scaling test, not measured steel'
 assert heads(frame.run(softer,d))==pytest.approx([v*2 for v in heads(results[0])],abs=1e-10)
 nonuniform=deepcopy(q);nonuniform['sections'][0].update(elastic_modulus_pa=190e9,material_source='Explicit synthetic SW E=190 GPa nonsymmetric material variation test');assert frame.run(nonuniform,d)['unequal_frame_independent_verification']['passed']
 _,equal=documents();eq=frame.run(equal_inputs(equal),equal);assert heads(eq)!=pytest.approx(heads(results[0]),abs=1e-7);assert d==before
@pytest.mark.parametrize('bad',['scope','unapproved_left','unapproved_right','wrong_left','wrong_right','references','out_of_plane','rotation','different_base','long_offset','large_height_difference','slab','missing_E','incorrect_I','gravity','arbitrary'])
def test_reject_unsupported_connections_and_inputs(bad):
 d=document();q=inputs(d);c=next(c for c in d['components'] if c['id']==IDS[0])
 if bad=='scope':d['metadata'].pop('unequal_frame_review')
 if bad=='unapproved_left':q['connections'][0]['idealization_approved']=False
 if bad=='unapproved_right':q['connections'][1]['idealization_approved']=False
 if bad=='wrong_left':q['connections'][0]['offset_m'][1]=.05
 if bad=='wrong_right':q['connections'][1]['offset_m'][1]=-.01
 if bad=='references':q['connections'][0]['column_id']='absent'
 if bad=='out_of_plane':c['transform']['position'][1]+=.01
 if bad=='rotation':c['transform']['rotation_deg'][1]=.1
 if bad=='different_base':c['transform']['position'][2]+=.01
 if bad=='long_offset':next(c for c in d['components'] if c['id']==IDS[1])['transform']['position'][2]=4
 if bad=='large_height_difference':c['geometry']['size'][2]=4;c['transform']['position'][2]=2
 if bad=='slab':q['component_ids'][0]='drawing-cad:614f117ae2a74794:95'
 if bad=='missing_E':q['sections'][0].pop('elastic_modulus_pa')
 if bad=='incorrect_I':q['sections'][0]['inertia_m4']/=2
 if bad=='gravity':q.update(load_cases=[dict(name='gravity',source='Synthetic deliberately unsupported load case',beam_uniform_n_per_m=-1000)],load_n=None,load_pattern=None,load_source=None)
 if bad=='arbitrary':q['solver_script']='arbitrary'
 with pytest.raises(ValueError):frame.graph(d,q)

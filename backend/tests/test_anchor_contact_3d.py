from copy import deepcopy
import numpy as np
import pytest
from app.services.design import anchor_contact_3d as c,anchor_contact as p

def test_independent_five_known_answer_cases():
 b=c.benchmarks();assert b['status']=='VERIFIED';assert len(b['cases'])==5
 for case in b['cases']:
  r=case['computed'];assert max(map(abs,r['equilibrium_residual_si']))<1e-6;assert min(a['tension_n'] for a in r['anchors'])>=0;assert min(s['pressure_pa'] for s in r['pressure_samples'])>=0
  assert r['independent_quadrature']['area_m2']==pytest.approx(r['active_contact_area_m2'],abs=1e-12)
 assert b['cases'][3]['computed']['active_contact_area_m2']==pytest.approx(.21125)

def test_2d_reduction_all_forces_contact_and_rotation():
 r=c.run(c.fixture('2d_reduction'));two=p.benchmark()['computed'];assert r['translation_down_m']==pytest.approx(two['translation_down_m'],abs=1e-12);assert r['slopes_east_north_rad']==pytest.approx([two['rotation_slope_rad'],0],abs=1e-12)
 assert r['compression_resultant_n']==pytest.approx(two['compression_resultant_n'],abs=1e-6);assert [a['tension_n'] for a in r['anchors']]==pytest.approx([a['tension_n'] for a in two['anchors']],abs=1e-6)
 assert r['contact_first_moments_nm']==pytest.approx([two['compression_first_moment_nm'],0],abs=1e-6)

def test_biaxial_scaling_unit_conversion_and_reflection():
 q=c.fixture();r=c.run(q);h=deepcopy(q);h['compression_n']=q['compression_n']/1000*1000*.5;h['moments_east_north_nm']=[m/1000*1000*.5 for m in q['moments_east_north_nm']];h['width_east_m']=650/1000;h['length_north_m']=650/1000;half=c.run(h)
 assert half['active_contact_area_m2']==pytest.approx(r['active_contact_area_m2']);assert half['pressure_max_kpa']==pytest.approx(r['pressure_max_kpa']*.5);assert half['rotations_east_north_rad']==pytest.approx([x*.5 for x in r['rotations_east_north_rad']]);assert [a['tension_n'] for a in half['anchors']]==pytest.approx([a['tension_n']*.5 for a in r['anchors']],abs=1e-6)
 q['moments_east_north_nm']=[-x for x in q['moments_east_north_nm']];ref=c.run(q);assert ref['compression_centroid_east_north_m']==pytest.approx([.1625,.1625]);assert ref['anchors'][0]['tension_n']==pytest.approx(4800)

def test_active_polygon_exact_area_and_two_independent_integrators():
 for state in [[.0002,0,0],[0,-.001,0],[0,-.001,-.001],[.00005,-.0008,.0003]]:
  poly=c.active_polygon(.65,.65,state);G=c.moments(poly);numerical,area=c.quadrature(poly,np.array(state),1e9);assert area==pytest.approx(G[0,0],abs=1e-12);assert numerical==pytest.approx(1e9*G@state,abs=1e-7)
 assert c.active_polygon(.65,.65,[-.001,0,0])==[]

@pytest.mark.parametrize('bad',['contact','anchor','negative','source','nan','infinity','outside','duplicate','lever','load_path','pretension','shear','review','actual_scope','extra','rotation','anchor_count','dimension'])
def test_invalid_input_rejection(bad):
 q=c.fixture()
 if bad=='contact':q.pop('contact_stiffness_n_m3')
 if bad=='anchor':q['anchors'][0].pop('axial_stiffness_n_m')
 if bad=='negative':q['anchors'][0]['axial_stiffness_n_m']=-1
 if bad=='source':q['contact_stiffness_source']=''
 if bad=='nan':q['anchors'][0]['position_east_north_m'][0]=float('nan')
 if bad=='infinity':q['moments_east_north_nm'][0]=float('inf')
 if bad=='outside':q['anchors'][0]['position_east_north_m'][1]=.4
 if bad=='duplicate':q['anchors'][1]=deepcopy(q['anchors'][0])
 if bad=='lever':q['anchors'][0]['effective_lever_arms_m']=[0,0]
 if bad=='load_path':q['fixed_anchor_ground_assumption']=False
 if bad=='pretension':q['no_pretension']=False
 if bad=='shear':q['horizontal_shear_excluded']=False
 if bad=='review':q['engineer_idealization_reviewed']=False
 if bad=='actual_scope':q['scope']='ACTUAL_PROJECT'
 if bad=='extra':q['arbitrary_script']='code'
 if bad=='rotation':q['moments_east_north_nm']=[1e7,-1e7]
 if bad=='anchor_count':q['anchors'].pop()
 if bad=='dimension':q['width_east_m']=0
 with pytest.raises((ValueError,ArithmeticError)):c.run(q)

from copy import deepcopy
import pytest
from app.services.design import anchor_contact as c

def test_independently_worked_benchmark():
 b=c.benchmark();r=b['computed'];assert b['status']=='VERIFIED';assert r['compression_resultant_n']==pytest.approx(22500);assert r['contact_interval_east_m']==pytest.approx([-.3,0],abs=1e-12);assert r['compression_centroid_east_m']==pytest.approx(-.2);assert [a['tension_n'] for a in r['anchors']]==pytest.approx([0,0,4000,2400]);assert r['total_anchor_tension_n']==pytest.approx(6400)
 assert abs(r['force_residual_n'])<1e-7;assert abs(r['moment_residual_nm'])<1e-7;assert min(s['pressure_pa'] for s in r['pressure_samples'])==0

def test_scaling_units_and_signed_symmetry():
 q=c.fixture();r=c.run(q);half=deepcopy(q);half['compression_n']=16.1*1000*.5;half['moment_negative_north_nm']=5.876*1000*.5;h=c.run(half)
 assert h['pressure_max_kpa']==pytest.approx(r['pressure_max_kpa']/2);assert h['rotation_slope_rad']==pytest.approx(r['rotation_slope_rad']/2);assert [a['tension_n'] for a in h['anchors']]==pytest.approx([a['tension_n']/2 for a in r['anchors']]);assert h['contact_interval_east_m']==pytest.approx(r['contact_interval_east_m'],abs=1e-10)
 q['moment_negative_north_nm']*=-1;rev=c.run(q);assert rev['compression_centroid_east_m']==pytest.approx(.2);assert [a['tension_n'] for a in rev['anchors']]==pytest.approx([2400,4000,0,0]);assert min(a['tension_n'] for a in rev['anchors'])>=0

def test_centered_all_anchors_slack():
 q=c.fixture();q['moment_negative_north_nm']=0;r=c.run(q);assert all(a['tension_n']==0 for a in r['anchors']);assert r['compression_resultant_n']==pytest.approx(q['compression_n']);assert r['pressure_max_kpa']==pytest.approx(q['compression_n']/(.6*.5)/1000)

@pytest.mark.parametrize('bad',['missing_contact','missing_anchor','zero_stiffness','negative_stiffness','nan','source','north_offset','duplicate','lever_arm','outside','pretension','load_path','actual_scope','script','extreme_rotation'])
def test_reject_unsupported_mechanics(bad):
 q=c.fixture()
 if bad=='missing_contact':q.pop('contact_stiffness_n_m3')
 if bad=='missing_anchor':q['anchors'][0].pop('axial_stiffness_n_m')
 if bad=='zero_stiffness':q['anchors'][0]['axial_stiffness_n_m']=0
 if bad=='negative_stiffness':q['contact_stiffness_n_m3']=-1
 if bad=='nan':q['anchors'][0]['axial_stiffness_n_m']=float('nan')
 if bad=='source':q['contact_stiffness_source']=''
 if bad=='north_offset':q['anchors'][0]['y_north_m']=.24
 if bad=='duplicate':q['anchors'][0]=q['anchors'][1]
 if bad=='lever_arm':q['anchors'][0]['effective_lever_arm_m']=.24
 if bad=='outside':q['anchors'][0]['x_east_m']=.31
 if bad=='pretension':q['no_pretension']=False
 if bad=='load_path':q['fixed_anchor_ground_assumption']=False
 if bad=='actual_scope':q['scope']='ACTUAL_PROJECT'
 if bad=='script':q['solver_script']='code'
 if bad=='extreme_rotation':q['moment_negative_north_nm']=1e7
 with pytest.raises((ValueError,ArithmeticError)):c.run(q)

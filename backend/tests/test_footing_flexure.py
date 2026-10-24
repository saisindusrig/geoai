from copy import deepcopy
import math
import pytest
from pydantic import ValidationError
from app.services.design import footing_flexure as s

def fixture(**changes):
 q=dict(classification='SYNTHETIC_VERIFICATION',method=s.METHOD,footing_id='f',column_id='c',B_m=1.2,L_m=1.2,thickness_m=.45,column_east_m=.3,column_north_m=.3,column_load_kn=144,uniform_net_pressure_kpa=100,bearing_reference_up_m=-.45,load_reference_up_m=0,eccentricity_east_m=0,eccentricity_north_m=0,horizontal_shear_kn=0,applied_moment_knm=0,soil_reaction='PRESCRIBED_UNIFORM_UPWARD_FULL_CONTACT',self_weight='EXCLUDED_SYNTHETIC_NET_PRESSURE_BENCHMARK',load_path='REVIEWED_HYPOTHETICAL_DIRECT_COLUMN_PATCH',reviewed_footprint=True,reviewed_assumptions=True)
 q.update({k:'Explicit synthetic source declaration only; actual site and physical connection data unverified.' for k in ['geometry_source','footprint_source','load_source','pressure_source','reference_source','load_path_source','applicability']});q.update(changes);return s.Input(**q)
def document():
 def part(id,role,size,z):return dict(id=id,name=id,category=role,geometry=dict(kind='box',size=size),transform=dict(position=[.15,.15,z],rotation_deg=[0,0,0],scale=[1,1,1]),metadata=dict(drawing_cad=dict(source_entity_id='dxf:test:'+id)))
 return {'components':[part('f','foundation',[1.2,1.2,.45],-.225),part('c','column',[.3,.3,3.26],1.63)]}
def test_independent_hand_units_and_four_face_cuts():
 q=fixture();r=s.calculate(q);assert r['upward_force_kn']==144;assert abs(r['force_residual_kn'])<1e-10
 for f in r['faces']:
  assert f['projection_m']==pytest.approx(.45);assert f['moment_knm_per_m']==pytest.approx(10.125);assert f['full_cut_moment_knm']==pytest.approx(12.15);assert f['upward_cut_force_kn']==pytest.approx(54)
  assert f['diagram'][0]['moment_knm_per_m']==pytest.approx(10.125);assert f['diagram'][-1]['moment_knm_per_m']==0
 assert float(r['decimal_hand']['one_metre_strip_Nmm'])==pytest.approx(.1*1000*450**2/2)
 for ref in r['independent_integration']:
  assert ref['upward_force_kn']==pytest.approx(144);assert abs(ref['moment_about_east_knm'])<1e-10;assert abs(ref['moment_about_north_knm'])<1e-10
 assert r['engineering_approval']=='DISABLED';assert r['reinforcement_capacity']=='NOT_IMPLEMENTED';assert r['actual_foundation_safety']=='BLOCKED'
def test_scaling_geometry_and_reference_plane_translation():
 a=s.calculate(fixture());b=s.calculate(fixture(column_load_kn=288,uniform_net_pressure_kpa=200));c=s.calculate(fixture(B_m=2.4,L_m=2.4,column_east_m=.6,column_north_m=.6,column_load_kn=576));d=s.calculate(fixture(bearing_reference_up_m=9.55,load_reference_up_m=10))
 for x,y in zip(a['faces'],b['faces']):assert y['moment_knm_per_m']==pytest.approx(2*x['moment_knm_per_m'])
 assert c['faces'][0]['moment_knm_per_m']==pytest.approx(4*a['faces'][0]['moment_knm_per_m']);assert c['faces'][0]['full_cut_moment_knm']==pytest.approx(8*a['faces'][0]['full_cut_moment_knm']);assert d['faces']==a['faces']
 assert s.audit_geometry(document(),fixture())['footing_id']=='f'
@pytest.mark.parametrize('bad',[{'B_m':0},{'L_m':2},{'column_north_m':.4},{'column_east_m':1.2,'column_north_m':1.2},{'uniform_net_pressure_kpa':-1},{'uniform_net_pressure_kpa':0},{'column_load_kn':100},{'bearing_reference_up_m':0},{'eccentricity_east_m':.1},{'eccentricity_north_m':.1},{'horizontal_shear_kn':1},{'applied_moment_knm':1},{'soil_reaction':'NONUNIFORM'},{'soil_reaction':'UPLIFT'},{'load_path':'UNKNOWN_ACTUAL_CONNECTION'},{'self_weight':'AUTO_CONCRETE_DENSITY'},{'reviewed_footprint':False},{'reviewed_assumptions':False},{'pressure_source':''},{'load_path_source':''},{'classification':'REAL_PROJECT'},{'fy_mpa':500},{'uniform_net_pressure_kpa':math.nan}])
def test_rejection(bad):
 with pytest.raises(ValidationError):fixture(**bad)
@pytest.mark.parametrize('bad',['offset','rotation','scale','missing','dimension','gap','role','source'])
def test_saved_geometry_rejection(bad):
 d=document();c=d['components'][1];f=d['components'][0]
 if bad=='offset':c['transform']['position'][0]+=.01
 if bad=='rotation':c['transform']['rotation_deg'][0]=1
 if bad=='scale':c['transform']['scale'][0]=2
 if bad=='missing':d['components'].pop()
 if bad=='dimension':f['geometry']['size'][0]=1.3
 if bad=='gap':c['transform']['position'][2]+=.1
 if bad=='role':f['category']='slab'
 if bad=='source':c['metadata']={}
 with pytest.raises(ValueError):s.audit_geometry(d,fixture())

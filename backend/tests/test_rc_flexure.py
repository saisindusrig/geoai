import math
import pytest
from pydantic import ValidationError
from app.services.design import rc_flexure as s

def fixture(**changes):
 q=dict(classification='SYNTHETIC_VERIFICATION',method=s.METHOD,demand_result_id=563,footing_id='drawing-cad:614f117ae2a74794:9A',direction='EAST_WEST_SINGLE_BOTTOM_LAYER',layout='EQUAL_SPACING_OUTER_CENTERS_AT_COVER_PLUS_HALF_DIAMETER',section_width_mm=1200,thickness_mm=450,concrete_fc_mpa=25,concrete_strength_basis='SYNTHETIC_CYLINDER_COMPRESSION',steel_fy_mpa=500,steel_E_mpa=200000,cover_mm=75,end_cover_mm=75,bar_diameter_mm=20,bar_count=8,effective_depth_mm=365,alpha=.85,beta=.85,concrete_limit_strain=.003,declared_steel_strain_limit=.05,declared_action_knm=250,design_action_basis='INDEPENDENT_SYNTHETIC_ACTION_NOT_CODE_FACTORED',comparison_basis='NOMINAL_EQUILIBRIUM_TARGET_ONLY_NO_STRENGTH_FACTOR',load_path='REVIEWED_HYPOTHETICAL_DIRECT_COLUMN_PATCH',reviewed_assumptions=True,country='UNSELECTED',jurisdiction='',standard='NONE',edition='')
 q.update({k:'Synthetic verification declaration only; no actual material or site evidence. Declared benchmark assumptions, not experimentally verified.' for k in ['concrete_source','steel_source','steel_E_source','cover_source','bar_source','effective_depth_source','arrangement_source','strain_model_source','design_action_source','load_path_source']});q.update(changes);return s.Input(**q)

def test_hand_equilibrium_inverse_and_units():
 r=s.calculate(fixture());p=r['provided'];As=8*math.pi*20**2/4;T=As*500;a=T/(.85*25*1200);c=a/.85
 assert p['steel_area_mm2']==pytest.approx(As);assert p['neutral_axis_c_mm']==pytest.approx(c)
 assert p['nominal_moment_knm']==pytest.approx(T*(365-a/2)/1e6)
 assert abs(p['force_residual_N'])<1e-8;assert p['tension_strain']==pytest.approx(.003*(365-c)/c)
 assert p['independent_c_mm']==pytest.approx(c);assert r['required_nominal_equilibrium']['nominal_moment_knm']==pytest.approx(250)
 assert r['required_nominal_equilibrium']['steel_area_mm2']==pytest.approx(r['independent_inverse_steel_mm2'])
 assert r['design_strength_knm'] is None;assert r['code_required_steel_mm2'] is None
 # SI check: Pa*m2*m /1000 gives kN m.
 assert p['nominal_moment_knm']==pytest.approx((As/1e6)*500e6*(.365-a/2000)/1000)

def test_scaling_and_context_does_not_enable_codes():
 a=s.calculate(fixture());b=s.calculate(fixture(section_width_mm=2400,bar_count=16,declared_action_knm=500))
 assert b['provided']['nominal_moment_knm']==pytest.approx(2*a['provided']['nominal_moment_knm'])
 assert b['required_nominal_equilibrium']['steel_area_mm2']==pytest.approx(2*a['required_nominal_equilibrium']['steel_area_mm2'])
 c=s.calculate(fixture(country='INDIA',standard='IS456',jurisdiction='Synthetic review',edition='2000'))
 assert c['provided']==a['provided'];assert c['code_checks']=='DISABLED'

@pytest.mark.parametrize('bad',[{'concrete_source':''},{'effective_depth_mm':360},{'bar_count':8.5},{'country':'INDIA'},{'standard':'ACI318','country':'INDIA','edition':'2019','jurisdiction':'test'},{'concrete_fc_mpa':40},{'reviewed_assumptions':False},{'steel_fy_mpa':float('nan')},{'classification':'REAL_PROJECT'},{'bar_count':40,'bar_diameter_mm':40,'effective_depth_mm':355},{'phi':.9}])
def test_invalid_inputs(bad):
 with pytest.raises(ValidationError):fixture(**bad)

@pytest.mark.parametrize('bad',[{'declared_action_knm':1},{'declared_action_knm':10000},{'bar_count':2,'bar_diameter_mm':8,'effective_depth_mm':371},{'bar_count':30,'bar_diameter_mm':30,'effective_depth_mm':360}])
def test_strain_and_inversion_domain(bad):
 with pytest.raises((ValueError,ValidationError)):s.calculate(fixture(**bad))

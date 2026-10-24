from decimal import Decimal
import math
import pytest
from pydantic import ValidationError
from app.services.design.bearing_capacity import Input,calculate
def fixture(**changes):
 values=dict(dict(classification='SYNTHETIC_VERIFICATION',method='PRANDTL_SURFACE_STRIP_PHI_ZERO_V1',geometry='INFINITE_STRIP',B_m=2,foundation_depth_m=0,su_kpa=50,phi_deg=0,unit_weight_kn_m3=18,strength_basis='TOTAL_STRESS_UNDRAINED',soil_extent='HOMOGENEOUS_INFINITE_IDEALIZATION',groundwater='EXCLUDED_SYNTHETIC_IDEALIZATION',groundwater_correction=False,loading='VERTICAL_CONCENTRIC_PER_UNIT_LENGTH',vertical_load_kn_per_m=150,shear_kn_per_m=0,moment_knm_per_m=0,ground_slope_deg=0,interface='ROUGH_HORIZONTAL_STRIP_IDEALIZATION',reference_up_m=0,resistance_method='GLOBAL_FS_ON_NET_ULTIMATE',global_factor=3,strength_source='Prescribed synthetic su=50 kPa, phi=0 and gamma=18 kN/m³; no site strength data',geometry_source='Synthetic ideal infinite surface strip, B=2 m, Df=0 m',groundwater_source='Groundwater/pore-pressure correction explicitly excluded in this synthetic idealization',load_source='Synthetic vertical concentric line load=150 kN per metre',factor_source='Synthetic declared global factor=3 on net ultimate; no code factor or safety approval',applicability='Homogeneous phi=0 undrained infinite half-space; rough horizontal rigid surface strip; level ground; vertical concentric loading only; no groundwater correction.',reviewed_assumptions=True),**changes)
 for field,text in {
  'strength_source':f"Synthetic declared su={values['su_kpa']} kPa; phi={values['phi_deg']} deg; gamma={values['unit_weight_kn_m3']} kN/m3. No site investigation.",
  'geometry_source':f"Synthetic infinite surface strip B={values['B_m']} m; Df={values['foundation_depth_m']} m.",
  'load_source':f"Synthetic vertical concentric line load={values['vertical_load_kn_per_m']} kN/m.",
  'factor_source':f"Synthetic declared global FS={values['global_factor']} on net ultimate; not a code design factor."
 }.items():
  if field not in changes:values[field]=text
 return Input(**values)

def test_independent_factor_pressure_and_per_metre_hand():
 r=calculate(fixture());pi=Decimal('3.141592653589793238462643383279502884197');net=50*(pi+2)
 assert r['ultimate_net_kpa']==pytest.approx(float(net),rel=1e-13)
 assert r['strength_only_allowable_net_kpa']==pytest.approx(float(net/3),rel=1e-13)
 assert r['ultimate_resistance_kn_per_m']==pytest.approx(514.1592653589793)
 assert r['strength_only_allowable_kn_per_m']==pytest.approx(171.3864217863264)
 assert r['applied_pressure_kpa']==75
 assert r['ultimate_gross_kpa']==r['ultimate_net_kpa'];assert r['factors']['Nq']==1;assert r['factors']['Ngamma']==0
 errors=[abs(x['Nc_limit']-(math.pi+2)) for x in r['independent_factors']];assert errors[-1]<errors[0];assert errors[-1]<1e-7
 # Independent N/mm² units: su=.05 MPa -> qu=.257079632679 MPa.
 assert r['ultimate_net_kpa']/1000==pytest.approx(.05*(math.pi+2))
 assert r['engineering_approval']=='DISABLED';assert r['actual_cad_capacity']=='BLOCKED'

def test_strength_width_loading_and_factor_scaling():
 a=calculate(fixture());b=calculate(fixture(su_kpa=100));c=calculate(fixture(B_m=4));d=calculate(fixture(vertical_load_kn_per_m=300));e=calculate(fixture(global_factor=6));g=calculate(fixture(unit_weight_kn_m3=25))
 assert b['ultimate_net_kpa']==2*a['ultimate_net_kpa'];assert c['ultimate_net_kpa']==a['ultimate_net_kpa'];assert c['ultimate_resistance_kn_per_m']==2*a['ultimate_resistance_kn_per_m'];assert d['applied_pressure_kpa']==2*a['applied_pressure_kpa'];assert e['strength_only_allowable_net_kpa']==a['strength_only_allowable_net_kpa']/2;assert g['ultimate_net_kpa']==a['ultimate_net_kpa']

@pytest.mark.parametrize('bad',[{'geometry':'RECTANGLE'},{'foundation_depth_m':1},{'phi_deg':30},{'shear_kn_per_m':1},{'moment_knm_per_m':1},{'ground_slope_deg':1},{'groundwater_correction':True},{'groundwater':'UNKNOWN'},{'soil_extent':'LAYERED'},{'classification':'REAL_PROJECT'},{'su_kpa':0},{'su_kpa':math.nan},{'B_m':0},{'global_factor':1},{'resistance_method':'LRFD'},{'reviewed_assumptions':False},{'strength_source':''},{'factor_source':''},{'load_source':''},{'groundwater_source':''},{'geometry_source':''},{'winkler_k':20000000}])
def test_unsupported_or_missing_inputs(bad):
 with pytest.raises(ValidationError):fixture(**bad)

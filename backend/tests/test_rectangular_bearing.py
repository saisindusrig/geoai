import math
import pytest
from pydantic import ValidationError
from app.services.design import rectangular_bearing as s
from test_bearing_capacity import fixture as strip

def fixture(**changes):
 q=strip().model_dump()
 for key in ['vertical_load_kn_per_m','shear_kn_per_m','moment_knm_per_m']:q.pop(key)
 q.update(method='FHWA_SURFACE_RECTANGLE_PHI_ZERO_V1',geometry='SQUARE',B_m=1.2,L_m=1.2,loading='VERTICAL_CONCENTRIC_TOTAL',vertical_load_kn=100,shear_east_kn=0,shear_north_kn=0,moment_east_knm=0,moment_north_knm=0,torsion_knm=0,eccentricity_east_m=0,eccentricity_north_m=0,interface='ROUGH_HORIZONTAL_RIGID_RECTANGLE',ground_reference_up_m=0,total_load_includes_footing=True,load_path='SYNTHETIC_DIRECT_VERTICAL_AT_BEARING_PLANE',reference_source='Synthetic common ground and bearing reference plane; no site datum implied.')
 q.update(changes)
 for field,text in {'strength_source':f"Synthetic su={q['su_kpa']} kPa; gamma={q['unit_weight_kn_m3']} kN/m3; phi={q['phi_deg']} deg; no site data.",'geometry_source':f"Synthetic {q['geometry']}, B={q['B_m']} m L={q['L_m']} m Df={q['foundation_depth_m']} m.",'load_source':f"Synthetic direct concentric total N={q['vertical_load_kn']} kN, includes footing weight; no CAD transfer.",'factor_source':f"Synthetic declared global FS={q['global_factor']} on net ultimate; not code compliance."}.items():
  if field not in changes:q[field]=text
 return s.Input(**q)

def test_square_independent_hand_and_units():
 r=s.calculate(fixture());assert r['factors']['sc']==pytest.approx(1.2);assert r['factors']['Nc']==pytest.approx(5.141592653589793)
 assert r['ultimate_gross_kpa']==pytest.approx(308.4955592153876);assert r['ultimate_resistance_kn']==pytest.approx(444.2336052701581)
 assert r['strength_only_allowable_gross_kpa']==pytest.approx(102.8318530717959);assert r['applied_pressure_kpa']==pytest.approx(69.44444444444444)
 assert float(r['decimal_hand']['ultimate_force_N'])==pytest.approx(r['ultimate_resistance_kn']*1000)
 assert float(r['decimal_hand']['applied_N_per_mm2'])*1000==pytest.approx(r['applied_pressure_kpa'])
 assert r['actual_cad_capacity']=='BLOCKED';assert r['engineering_approval']=='DISABLED'

def test_rectangle_scaling_and_source_consistency():
 a=s.calculate(fixture());b=s.calculate(fixture(geometry='RECTANGLE',L_m=2.4));assert b['factors']['sc']==pytest.approx(1.1)
 assert b['ultimate_gross_kpa']==pytest.approx(282.7875959474386)
 for changes,field,multiple in [({'su_kpa':100},'ultimate_gross_kpa',2),({'B_m':2.4,'L_m':2.4},'ultimate_resistance_kn',4),({'vertical_load_kn':200},'applied_pressure_kpa',2),({'global_factor':6},'strength_only_allowable_gross_kpa',.5)]:assert s.calculate(fixture(**changes))[field]==pytest.approx(a[field]*multiple)
 assert s.calculate(fixture(unit_weight_kn_m3=25))['ultimate_gross_kpa']==a['ultimate_gross_kpa']
 assert '100' in fixture(su_kpa=100).strength_source;assert '2.4' in fixture(B_m=2.4,L_m=2.4).geometry_source

@pytest.mark.parametrize('bad',[{'B_m':0},{'L_m':1},{'L_m':2.4},{'geometry':'RECTANGLE','L_m':6},{'phi_deg':1},{'foundation_depth_m':.5},{'ground_reference_up_m':1},{'shear_east_kn':1},{'shear_north_kn':1},{'moment_east_knm':1},{'moment_north_knm':1},{'torsion_knm':1},{'eccentricity_east_m':.1},{'eccentricity_north_m':.1},{'soil_extent':'LAYERED'},{'groundwater':'UNKNOWN'},{'groundwater_correction':True},{'load_path':'ACTUAL_CONNECTION'},{'classification':'REAL_PROJECT'},{'su_kpa':math.nan},{'reference_source':''},{'strength_source':''},{'reviewed_assumptions':False},{'total_load_includes_footing':False},{'vertical_load_kn':0}])
def test_unsupported_inputs_rejected(bad):
 with pytest.raises(ValidationError):fixture(**bad)

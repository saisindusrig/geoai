import math
import pytest
from app.services.design import footing_bearing as f,plate_contact as p

def test_independent_hand_benchmark_and_equilibrium():
 r=f.benchmark();assert len(r['cases'])==6
 for c in r['cases']:
  a=c['result']
  if c['independent']:assert abs(a['force_residual_n'])<1e-6;assert abs(a['moment_residual_nm'])<1e-6;assert a['pressure_min_kpa']>=0
  else:assert a['pressure_min_kpa'] is None
 assert r['cases'][0]['result']['pressure_min_kpa']==50
 assert r['cases'][1]['result']['pressure_max_kpa']==80
 assert r['cases'][1]['result']['pressure_min_kpa']==20
@pytest.mark.parametrize('values',[(0,0,2,2),(-1,0,2,2),(1000,float('nan'),2,2),(1000,0,0,2),(1000,0,2,-2)])
def test_invalid_geometry_or_demand(values):
 with pytest.raises(ValueError):p.assess(*values)
def test_scaling_kern_and_unit_reference():
 a=p.assess(200000,40000,2,2);b=p.assess(100000,20000,2,2);assert b['pressure_max_kpa']==a['pressure_max_kpa']/2;assert b['eccentricity_m']==a['eccentricity_m']
 assert p.assess(200000,200000/3,2,2)['contact_state']=='KERN_BOUNDARY_ZERO_EDGE_PRESSURE'
 # Independently N/mm²: N/A +/- M/S; 200kN,40e6 Nmm,2000mm square.
 assert a['pressure_max_kpa']/1000==pytest.approx(200000/4000000+40000000/(2000*2000**2/6))
@pytest.mark.parametrize('field',['footing_dimensions_m','concrete_strength_mpa','soil_bearing_input_kpa','contact_reference_up_m'])
def test_entered_engineering_values_require_sources(field):
 from app.api.routes.cad_soil import EngineeringInputs
 value=[1.2,1.2,.45] if field=='footing_dimensions_m' else 0 if field=='contact_reference_up_m' else 25
 with pytest.raises(ValueError):EngineeringInputs(classification='ENGINEER_DECLARED',**{field:value})
 source={'footing_dimensions_m':'dimension_source','concrete_strength_mpa':'concrete_source','soil_bearing_input_kpa':'soil_source','contact_reference_up_m':'reference_source'}[field]
 q=EngineeringInputs(classification='ENGINEER_DECLARED',**{field:value,source:'Explicit declared source; not experimentally verified'})
 assert getattr(q,field)==value

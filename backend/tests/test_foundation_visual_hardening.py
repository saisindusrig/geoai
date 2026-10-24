"""Independent full-stress anchorage and corrected IS soil-cut location audit."""
from decimal import Decimal as D,localcontext
import pytest
from test_foundation_system import q
from app.services.design.foundation_system import rc_checks

def test_full_design_stress_development_independent_decimal():
 with localcontext() as ctx:
  ctx.prec=50
  # BIS26.2.1,26.2.1.1: M25 bond1.4MPa, deformed tension factor1.6.
  tau=D('1.4')*D('1.6');force_per_mm=D(20)*D('.87')*D(500)
  required=force_per_mm/(4*tau)
  available=(D(1200)-D(300))/2-D(75)
  shortfall=required-available
 r=rc_checks(q(),1200,300,450,18.225,150)
 for layer in r['layers']:
  check=layer['development']
  assert check['required_mm']==pytest.approx(float(required),rel=1e-14)
  assert check['available_mm']==float(available)==375
  assert check['required_mm']-check['available_mm']==pytest.approx(float(shortfall))
  assert check['status']=='EXCEEDS_IMPLEMENTED_CHECK'
 assert float(required)==pytest.approx(970.9821428571429)

def test_amendment1_location_is_d_on_soil_without_enabling_unverified_resistance():
 r=rc_checks(q(),1200,300,450,18.225,150)
 # Independently integrate net150kN/m2 outside each amended soil section.
 # Face150mm; outeredge600mm. Upper/lower d345/365mm.
 expected=[D('150')*D('1.2')*(D('.6')-D('.15')-D('.365')),D('150')*D('1.2')*(D('.6')-D('.15')-D('.345'))]
 for layer,V in zip(r['layers'],expected):
  assert layer['one_way_demand_kn']==pytest.approx(float(V))
  assert layer['one_way_section_from_center_mm']==150+layer['effective_depth_mm']
  assert 'Amendment 1' in layer['one_way']['reason']
  assert layer['one_way']['status']=='DISABLED'
  assert 'resistance' not in layer['one_way']

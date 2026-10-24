"""Independent known answers, pressure quadrature, units and applicability."""
from copy import deepcopy
from decimal import Decimal as D,localcontext
import math
import pytest
from pydantic import ValidationError
from app.services.design import foundation_system as s
from app.api.routes.foundation_system import fixture
from test_footing_flexure import fixture as demand_fixture,document

def q(**changes):return s.Input(**{**fixture(demand_fixture()),**changes})
def geometry():return s.footing_flexure.audit_geometry(document(),demand_fixture())

def test_integrated_independent_si_equilibrium_and_quantities():
 r=s.calculate(q(),geometry(),demand_fixture())
 # Hand integration in N/mm: 0.15 N/mm2 on 1200mm wide, 450mm projection.
 assert r['factored_bending']['faces'][0]['full_cut_moment_knm']==pytest.approx(18.225)
 assert r['unfactored_bending']['faces'][0]['full_cut_moment_knm']==pytest.approx(12.15)
 assert r['actions']['service_footing_weight_kn']==pytest.approx(16.2)
 assert r['contact']['pmax_pa']==pytest.approx(111250)
 assert r['contact']['delta_down_m']==pytest.approx(.0055625)
 assert r['bearing']['applied_pressure_kpa']==pytest.approx(111.25)
 assert r['rc']['layers'][0]['effective_depth_mm']==365
 assert r['rc']['layers'][1]['effective_depth_mm']==345
 assert r['rc']['layers'][0]['one_way_demand_kn']==pytest.approx(15.3)
 assert r['rc']['layers'][1]['one_way_demand_kn']==pytest.approx(18.9)
 assert r['rc']['punching']['demand_kn']==pytest.approx(153.59625)
 assert r['rc']['punching']['resistance']==pytest.approx(1112.625)
 assert r['rc']['layers'][0]['development']['required_mm']==pytest.approx(970.9821428571429)
 assert r['rc']['layers'][0]['development']['available_mm']==375
 assert r['rc']['layers'][0]['development']['status']=='EXCEEDS_IMPLEMENTED_CHECK'
 assert r['rc']['quantities']['concrete_gross_m3']==pytest.approx(.648)
 assert r['rc']['quantities']['steel_mass_kg']==pytest.approx(16*math.pi*.02**2/4*1.05*7850)
 assert r['transfer']['equilibrium_residual_nm']==[0,0,0]
 assert r['engineering_approval']=='DISABLED'

def test_aci_published_shear_example_without_rounded_si_coefficients():
 # ACI's 12ft square footing, 24in square column, h30in, cover3in,
 # two No8 mats; upper d25.5in. Use published rounded qu6.7ksf,
 # since the example uses that pressure (not 960/144) for shear cuts.
 B=3657.6;c=609.6;h=762;pressure=6.7*4.4482216152605/(.3048**2)
 inp=q(profile='ACI318-14',concrete_cylinder_mpa=4000*.006894757293168,steel_yield_mpa=60000*.006894757293168,cover_mm=76.2,east_west={'diameter_mm':25.4,'count':13},north_south={'diameter_mm':25.4,'count':13})
 r=s.rc_checks(inp,B,c,h,1005*4.4482216152605*.3048,pressure)
 upper=r['layers'][1]
 assert upper['effective_depth_mm']/25.4==pytest.approx(25.5)
 assert upper['one_way']['demand']/4.4482216152605==pytest.approx(231.15)
 assert upper['one_way']['resistance']/4.4482216152605==pytest.approx(348.3565070441,rel=1e-8)
 assert r['punching']['perimeter_mm']/25.4==pytest.approx(198)
 assert r['punching']['demand_kn']/4.4482216152605==pytest.approx(850.7953125)
 assert r['punching']['resistance']/4.4482216152605==pytest.approx(957.9803943714,rel=1e-8)
 assert upper['development']['required_mm']/25.4==pytest.approx(28.4604989415)
 assert upper['development']['available_mm']/25.4==pytest.approx(57)

def test_is_stress_block_independent_decimal_and_inverse():
 r=s.rc_checks(q(),1200,300,450,18.225,150)
 with localcontext() as ctx:
  ctx.prec=40
  steel=D('8')*D('3.141592653589793238462643383279502884197')*D(20)**2/4
  tension=steel*D(435)
  xu=tension/(D('.36')*D(25)*D(1200))
  moment=tension*(D(365)-D('.42')*xu)/D(1000000)
 assert r['layers'][0]['flexure']['resistance']==pytest.approx(float(moment),rel=1e-13)
 required=r['layers'][0]['required_steel']['flexural_mm2']
 # Separate N/m mechanics against the inverse solution.
 T=required/1e6*435e6;x=T/(.36*25e6*1.2)
 assert T*(.365-.42*x)/1000==pytest.approx(18.225)
 assert r['layers'][0]['one_way']['status']=='DISABLED'

def test_distributed_pressure_independent_cells_and_layer_depths():
 r=s.rc_checks(q(),1200,300,450,18.225,150)
 # Integrate independent N/mm2 cells outside upper-layer shear and punching cuts.
 depth=345;dx=.3;one=sum(.15*1200*dx for _ in range(round((600-150-depth)/dx)))/1000
 assert one==pytest.approx(r['layers'][1]['one_way_demand_kn'])
 # Entire area minus independent central rectangular patch, no perimeter formula.
 total=.15*1200*1200;patch=.15*645*645
 assert (total-patch)/1000==pytest.approx(r['punching']['demand_kn'])

@pytest.mark.parametrize('changes',[{'cover_mm':0},{'stiffness_kn_m3':0},{'factored_column_kn':-1},{'factored_column_kn':float('nan')},{'reviewed_synthetic_patch':False},{'classification':'REAL_PROJECT'},{'profile':'ACI318-11'},{'steel_yield_mpa':420},{'east_west':{'diameter_mm':20,'count':8.5}},{'unknown':1}])
def test_input_rejections(changes):
 with pytest.raises(ValidationError):q(**changes)

def test_collision_perimeter_depth_and_edition_gates():
 for B,c,h,inp in [(1200,300,450,q(east_west={'diameter_mm':40,'count':100})),(1200,300,100,q()),(1200,1100,450,q()),(1200,1200,450,q())]:
  with pytest.raises(ValueError):s.rc_checks(inp,B,c,h,20,150)
 for profile in ('ACI318-19','ACI318-25'):
  r=s.rc_checks(q(profile=profile),1200,300,450,20,150)
  assert r['punching']['status']=='DISABLED'
  assert all(layer['flexure']['status']=='DISABLED' and layer['one_way']['status']=='DISABLED' for layer in r['layers'])

def test_service_factored_strengths_independent_and_alternatives_nonmutating():
 src=demand_fixture();g=geometry();before=deepcopy(g)
 a=s.calculate(q(),g,src);b=s.calculate(q(factored_column_kn=432),g,src)
 assert a['contact']==b['contact'] and a['bearing']==b['bearing']
 assert b['rc']['punching']['demand_kn']==pytest.approx(2*a['rc']['punching']['demand_kn'])
 c=s.calculate(q(concrete_cube_mpa=30),g,src)
 assert c['rc']['layers'][0]['nominal']==a['rc']['layers'][0]['nominal']
 assert c['rc']['layers'][0]['flexure']!=a['rc']['layers'][0]['flexure']
 assert len(s.alternatives(q(),g,src)['scenarios'])==6
 assert g==before and src==demand_fixture()

from decimal import Decimal,localcontext
import math
import pytest
from pydantic import ValidationError
from app.services.design.elastic_settlement import Profile,Load,calculate,numerical

def fixture_profile():
 return dict(classification='SYNTHETIC_VERIFICATION',borehole_id='SYNTHETIC-BH-01',location_enu_m=[0,0,0],ground_reference_up_m=0,reference_source_id='verification',groundwater_depth_m=3,groundwater_source_id='verification',sources=[dict(id='verification',reference='GeoAI prescribed synthetic half-space benchmark, not site investigation',investigation='Independent elastic Green-function integration and hand worked benchmark; groundwater display reference only')],layers=[dict(id='soil-1',description='Synthetic homogeneous isotropic elastic half-space',top_depth_m=0,bottom_depth_m=None,extent='UNBOUNDED_IDEALIZATION',extent_source_id='verification',extent_kind='SYNTHETIC',unit_weight_kn_m3=dict(value=18,kind='SYNTHETIC',source_id='verification'),E_mpa=dict(value=20,kind='SYNTHETIC',source_id='verification'),poisson=dict(value=.3,kind='SYNTHETIC',source_id='verification'))],applicability='Homogeneous isotropic linear elastic infinite half-space; uniform flexible surface loading; no effective-stress, consolidation or groundwater coupling.')
def fixture_load(**kwargs):
 return Load(**dict(dict(classification='SYNTHETIC_VERIFICATION',B_m=2,L_m=2,N_n=200000,reference_up_m=0,source='Prescribed synthetic uniform patch load, not transferred CAD footing demand',idealization='uniform_flexible_rectangular_surface_patch',reviewed_assumptions=True),**kwargs))

def test_square_decimal_hand_and_units():
 p=Profile(**fixture_profile());r=calculate(p,fixture_load())
 # Decimal derivation in mm, N, MPa. Integral=8*a*ln(1+sqrt(2)).
 with localcontext() as c:
  c.prec=40;a=Decimal(1000);I=8*a*(1+Decimal(2).sqrt()).ln();s=Decimal('.05')*(1-Decimal('.3')**2)*I/(Decimal(str(math.pi))*Decimal(20))
 assert r['centre_settlement_m']*1000==pytest.approx(float(s),rel=1e-13)
 assert r['uniform_pressure_pa']==50000;assert r['force_balance_residual_n']==0
 assert r['winkler_stiffness']=='NOT_DERIVED';assert r['winkler_displacement']=='NOT_USED_OR_ADDED'
 assert r['centre_settlement_m']==pytest.approx(.005106008656286539,rel=1e-7)
 refs=r['numerical_reference'];assert abs(refs[-1]['centre_settlement_m']/r['centre_settlement_m']-1)<abs(refs[0]['centre_settlement_m']/r['centre_settlement_m']-1)

@pytest.mark.parametrize('B,L',[(1,2),(2,1),(1,4),(4,1),(1,10),(.1,.1),(20,20)])
def test_shape_symmetry_and_reference(B,L):
 p=Profile(**fixture_profile());q=fixture_load(B_m=B,L_m=L,N_n=50000*B*L);r=calculate(p,q);reverse=calculate(p,fixture_load(B_m=L,L_m=B,N_n=q.N_n));assert reverse['centre_settlement_m']==pytest.approx(r['centre_settlement_m'])
 assert r['numerical_reference'][-1]['load_relative_error']<5e-5

def test_load_material_scaling_gamma_groundwater_not_used():
 p=fixture_profile();a=calculate(Profile(**p),fixture_load());b=calculate(Profile(**p),fixture_load(N_n=100000));assert b['centre_settlement_m']==a['centre_settlement_m']/2
 p['layers'][0]['E_mpa']['value']=40;c=calculate(Profile(**p),fixture_load());assert c['centre_settlement_m']==a['centre_settlement_m']/2
 p['layers'][0]['unit_weight_kn_m3']['value']=25;p['groundwater_depth_m']=1;d=calculate(Profile(**p),fixture_load());assert d['centre_settlement_m']==c['centre_settlement_m']

@pytest.mark.parametrize('bad',['E','nu','source','groundwater','gap','overlap','synthetic_real','extent_source','measured_infinite'])
def test_invalid_profile(bad):
 p=fixture_profile();l=p['layers'][0]
 if bad=='E':l['E_mpa']['value']=0
 if bad=='nu':l['poisson']['value']=.5
 if bad=='source':l['E_mpa']['source_id']='missing'
 if bad=='groundwater':p['groundwater_source_id']=None
 if bad=='gap':l['top_depth_m']=1
 if bad=='overlap':p['layers'].append(dict(l,id='soil-2'))
 if bad=='synthetic_real':p['classification']='REAL_PROJECT'
 if bad=='extent_source':l['extent_source_id']='missing'
 if bad=='measured_infinite':l['extent_kind']='MEASURED'
 with pytest.raises(ValidationError):Profile(**p)

@pytest.mark.parametrize('bad',['finite','layered','unknown','missing_E','embedded','aspect','large_displacement','actual'])
def test_unsupported_scope(bad):
 p=fixture_profile();q=fixture_load();l=p['layers'][0]
 if bad in ['finite','layered']:l.update(extent='FINITE',bottom_depth_m=2)
 if bad=='layered':p['layers'].append(dict(l,id='soil-2',top_depth_m=2,bottom_depth_m=4))
 if bad=='unknown':l['extent']='UNKNOWN'
 if bad=='missing_E':l['E_mpa']=None
 if bad=='embedded':q=fixture_load(reference_up_m=-.45)
 if bad=='aspect':q=fixture_load(B_m=.05,L_m=20)
 if bad=='large_displacement':l['E_mpa']['value']=.01
 if bad=='actual':
  p['classification']='REAL_PROJECT';l['extent_kind']='ENGINEER_ASSUMED'
  for k in ['E_mpa','poisson','unit_weight_kn_m3']:l[k]['kind']='MEASURED'
 with pytest.raises(ValueError):calculate(Profile(**p),q)

@pytest.mark.parametrize('change',[{'N_n':0},{'N_n':-1},{'B_m':math.nan},{'idealization':'rigid_footing'},{'classification':'REAL_PROJECT'},{'reviewed_assumptions':False}])
def test_invalid_load(change):
 with pytest.raises(ValidationError):fixture_load(**change)

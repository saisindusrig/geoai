import math
import pytest
from pydantic import ValidationError
from app.services.design.soil_contact import Inputs,calculate

def fixture(**kwargs):
 return Inputs(**dict(dict(classification='SYNTHETIC_VERIFICATION',B_m=2,L_m=2,N_n=200000,My_nm=100000,k_n_m3=20000000,contact_law='uniform_linear_compression_only_winkler',reference_up_m=0,source='Synthetic independently prescribed verification values, not site properties',applicability='Rigid rectangle and uniform independent spring bed; uniaxial moment; small rotation only',reviewed=True),**kwargs))

@pytest.mark.parametrize('m,state,area,pmax,delta,theta',[(0,'FULL_CONTACT',4,50000,.0025,0),(40000,'FULL_CONTACT',4,80000,.0025,.0015),(200000/3,'FULL_CONTACT',4,100000,.0025,.0025),(100000,'PARTIAL_CONTACT',3,400000/3,.02/9,.04/9),(-100000,'PARTIAL_CONTACT',3,400000/3,.02/9,-.04/9)])
def test_hand_cases(m,state,area,pmax,delta,theta):
 r=calculate(fixture(My_nm=m));assert r['state']==state
 for actual,expected in [(r['contact_area_m2'],area),(r['pmax_pa'],pmax),(r['delta_down_m'],delta),(r['theta_north_rad'],theta)]:assert actual==pytest.approx(expected)
 assert r['force_integral_n']==pytest.approx(200000)
 assert r['moment_integral_nm']==pytest.approx(m,abs=1e-8)
 assert all(s['p_pa']>=0 for s in r['pressure_samples'])
 for ref in r['numerical_reference']:
  assert ref['force_n']==pytest.approx(200000,abs=1e-7)
  assert ref['moment_nm']==pytest.approx(m,abs=1e-7)
 errors=[abs(x['theta_rad']-theta) for x in r['numerical_reference']]
 if theta:assert errors[-1]<errors[0]

@pytest.mark.parametrize('N,M',[(0,0),(0,1000),(-10,0),(200000,200000),(200000,-200000),(200000,210000)])
def test_no_equilibrium(N,M):
 r=calculate(fixture(N_n=N,My_nm=M));assert 'pressure_samples' not in r;assert 'delta_down_m' not in r

def test_scaling_stiffness_units_and_reference():
 a=calculate(fixture());b=calculate(fixture(N_n=100000,My_nm=50000));c=calculate(fixture(k_n_m3=40000000,reference_up_m=-.45))
 assert b['contact_area_m2']==a['contact_area_m2'];assert b['pmax_pa']==a['pmax_pa']/2
 assert b['delta_down_m']==a['delta_down_m']/2;assert c['delta_down_m']==a['delta_down_m']/2
 # Independent N/mm units: q=0.05 N/mm²; k=.02 N/mm³ -> 2.5 mm.
 full=calculate(fixture(My_nm=0));assert full['delta_down_m']*1000==pytest.approx((200000/(2000*2000))/(20000000/1e9))

@pytest.mark.parametrize('change',[{'k_n_m3':0},{'B_m':-1},{'N_n':math.nan},{'source':''},{'reviewed':False},{'classification':'REAL_PROJECT'},{'contact_law':'soil_continuum'},{'unknown':1}])
def test_invalid(change):
 with pytest.raises(ValidationError):fixture(**change)

def test_rotation_limit():
 assert calculate(fixture(k_n_m3=1))['state']=='OUTSIDE_SMALL_ROTATION_DOMAIN'

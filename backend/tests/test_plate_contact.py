from copy import deepcopy
import math
import pytest
from app.services.design import plate_contact as c,foundation_interface as f
from test_foundation_interface import fixture,document,source

def contact_inputs():
 q=fixture();q.update(demand_scope='actual_N_M_contact_feasibility',contact_assumption='rigid_plate_contact_feasibility',contact_reference_assumption='column_base_N_M_only_no_shear_translation');return q

def test_independent_known_answers_and_signed_edges():
 r=c.benchmarks();assert r['status']=='VERIFIED';assert len(r['cases'])==7
 for moment,edges in [(5000,[500,166.6666666667]),(-5000,[166.6666666667,500])]:
  a=c.assess(100000,moment,.6,.5);assert a['pressure_at_minus_east_edge_kpa']==pytest.approx(edges[0]);assert a['pressure_at_plus_east_edge_kpa']==pytest.approx(edges[1]);assert a['integrated_force_n']==pytest.approx(100000);assert a['integrated_moment_nm']==pytest.approx(-moment)

def test_actual_saved_plate_resultant_outside_footprint():
 q=contact_inputs();d=f.demands(source(),q['source_beam_id'],q['column_id']);a=f.calculate(f.prepare(document(),q,d));r=a['contact']
 assert r['eccentricity_m']==pytest.approx(.3917897864272739);assert r['eccentricity_east_m']==pytest.approx(-.3917897864272739);assert r['kern_limit_m']==pytest.approx(.1083333333333333);assert r['footprint_half_width_m']==.325
 assert r['contact_state']=='RESULTANT_OUTSIDE_FOOTPRINT';assert r['compression_only_equilibrium']=='IMPOSSIBLE';assert r['pressure_min_kpa'] is None;assert r['pressure_max_kpa'] is None;assert a['status']=='VERIFIED_CONTACT_FEASIBILITY_ONLY';assert a['full_connection_status']=='NOT_YET_VERIFIED';assert a['engineering_approval']=='DISABLED'

@pytest.mark.parametrize('e,state',[(0,'FULL_CONTACT_LINEAR'),(.099,'FULL_CONTACT_LINEAR'),(.1,'KERN_BOUNDARY_ZERO_EDGE_PRESSURE'),(.10001,'CONTACT_LOSS_PARTIAL_UNSUPPORTED'),(.299,'CONTACT_LOSS_PARTIAL_UNSUPPORTED'),(.3,'CONTACT_LOSS_PARTIAL_UNSUPPORTED'),(.301,'RESULTANT_OUTSIDE_FOOTPRINT'),(-.301,'RESULTANT_OUTSIDE_FOOTPRINT')])
def test_contact_loss_and_footprint_bounds(e,state):
 r=c.assess(100000,100000*e,.6,.5);assert r['contact_state']==state
 if 'UNSUPPORTED' in state or 'OUTSIDE' in state:assert r['pressure_min_kpa'] is None and r['pressure_max_kpa'] is None

def test_scaling_and_mm_units_independent():
 r=c.assess(100000,5000,600/1000,500/1000);h=c.assess(50000,2500,.6,.5)
 assert r['eccentricity_east_m']==h['eccentricity_east_m'];assert h['pressure_max_kpa']==r['pressure_max_kpa']/2
 assert r['independent_n_mm2_at_edges']==pytest.approx([.5,1/6]);assert abs(r['force_residual_n'])<1e-7;assert abs(r['moment_residual_nm'])<1e-7
 # Scale N alone changes e and can cause contact loss; do not scale the pressure of the old state.
 assert c.assess(10000,5000,.6,.5)['contact_state']=='RESULTANT_OUTSIDE_FOOTPRINT'

@pytest.mark.parametrize('bad',['zero','uplift','nan','infinity','zero_width','negative_length','missing_reference','missing_ack','wrong_idealization','script'])
def test_rejection(bad):
 q=contact_inputs();d=f.demands(source(),q['source_beam_id'],q['column_id'])
 if bad in ('zero','uplift','nan','infinity','zero_width','negative_length'):
  args=[100000,5000,.6,.5]
  if bad=='zero':args[0]=0
  if bad=='uplift':args[0]=-10
  if bad=='nan':args[1]=float('nan')
  if bad=='infinity':args[0]=float('inf')
  if bad=='zero_width':args[2]=0
  if bad=='negative_length':args[3]=-1
  with pytest.raises(ValueError):c.assess(*args)
  return
 if bad=='missing_reference':q.pop('contact_reference_assumption')
 if bad=='missing_ack':q['excluded_shear_moment_acknowledged']=False
 if bad=='wrong_idealization':q['contact_assumption']='concentric_full_contact_massless_rigid_plate'
 if bad=='script':q['partial_contact_script']='code'
 with pytest.raises(ValueError):f.prepare(document(),q,d)

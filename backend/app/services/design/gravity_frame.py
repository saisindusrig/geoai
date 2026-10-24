"""Uniform-load prerequisite and hand verification; synthetic values only."""
import math
from app.services.design import elastic_frame as elastic

def fixed_beam_hand(q,wy):
 L=q['length_m'];EI=q['elastic_modulus_pa']*q['inertia_m4']
 return dict(reaction_y_n=-wy*L/2,left_end_moment_nm=-wy*L*L/12,right_end_moment_nm=wy*L*L/12,midspan_displacement_m=wy*L**4/(384*EI),formula='Fixed-fixed Euler-Bernoulli: Ry=-wL/2; Mi=-wL²/12, Mj=+wL²/12; v(x)=w x²(L-x)²/(24EI); V(x)=-wL/2+w x; M(x)=wL²/12-wLx/2+w x²/2')

def suite():
 cases=[]
 for n,units,scale in [(2,'SI',1),(4,'SI',1),(2,'N-mm',1),(2,'SI',.5)]:
  q={**elastic.fixture('cantilever'),'kind':'fixed_beam','length_m':4,'elements_per_member':n,'units':units}
  wy=-2000*scale;r=elastic.run(q,verification_loads={},verification_uniform={1:[0,wy]});h=fixed_beam_hand(q,wy)
  if r['status']!='VERIFIED':raise ValueError('Uniform beam prerequisite failed: '+str(r.get('error')))
  samples=[s for e in r['elements'] for s in e['samples']];mid=min(samples,key=lambda s:abs(s['position_m'][0]-2))
  checks=[math.isclose(mid['displacement_m'][1],h['midspan_displacement_m'],abs_tol=1e-10),all(math.isclose(a['fy_n'],h['reaction_y_n'],abs_tol=1e-6) for a in r['reactions']),math.isclose(r['elements'][0]['local_end_forces_si'][2],h['left_end_moment_nm'],abs_tol=1e-6),math.isclose(r['elements'][-1]['local_end_forces_si'][5],h['right_end_moment_nm'],abs_tol=1e-6)]
  L=q['length_m'];EI=q['elastic_modulus_pa']*q['inertia_m4'];errors=[]
  for s in samples:
   x=s['position_m'][0];expected=[wy*x*x*(L-x)**2/(24*EI),-wy*L/2+wy*x,wy*L*L/12-wy*L*x/2+wy*x*x/2]
   actual=[s['displacement_m'][1],s['shear_n'],s['moment_nm']];errors.extend(abs(a-b) for a,b in zip(actual,expected))
   checks.append(all(math.isclose(a,b,abs_tol=1e-6) for a,b in zip(actual,expected)))
  if not all(checks):raise ValueError('Uniform-load closed-form fixed-end forces, reactions or sample diagram/deflection verification failed')
  r['uniform_load_hand_verification']={'passed':True,'reference':h,'sample_error_max_m_n_nm':max(errors)};cases.append(r)
 return dict(status='VERIFIED',method='Actual OpenSees uniform-load fixed-fixed beam; closed form at every sample plus independent consistent-load stiffness; 2/4 meshes, N-mm, half load',cases=cases)

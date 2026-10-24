"""Fixed, reproducible rigid-offset mechanics benchmark. Not an engineering design."""
import math
from app.services.design import elastic_frame as elastic

def hand(q,offset):
 L,E,A,I=q['length_m'],q['elastic_modulus_pa'],q['area_m2'],q['inertia_m4']
 Fx,Fy=1000.,-2000.;rx,ry=offset
 M=ry*Fx-rx*Fy
 rotation=Fy*L**2/(2*E*I)+M*L/(E*I)
 physical_u=Fx*L/(E*A);physical_v=Fy*L**3/(3*E*I)+M*L**2/(2*E*I)
 return dict(master_tip=[physical_u+ry*rotation,physical_v-rx*rotation,rotation],physical_tip=[physical_u,physical_v,rotation],base_reaction=[-Fx,-Fy,-((L-rx)*Fy+ry*Fx)],physical_tip_moment_nm=M,formula='Mphysical=ry Fx-rx Fy; theta=Fy L²/(2EI)+Mphysical L/EI; uxphysical=Fx L/EA; uyphysical=Fy L³/(3EI)+Mphysical L²/(2EI); umaster=uphysical+[ry theta,-rx theta]; Rm=-[(L-rx)Fy+ry Fx]',sources='Explicit synthetic verification loads Fx=1000 N, Fy=-2000 N; E=200 GPa, A=0.01 m², I=8e-6 m⁴; fixed support, Euler-Bernoulli, massless rigid end offset, not physical connection capacity')

def suite():
 cases=[]
 for offset in ([0.,0.],[.15,.1]):
  for n,units in [(1,'SI'),(2,'SI'),(4,'SI'),(2,'N-mm')]:
   q={**elastic.fixture('cantilever'),'elements_per_member':n,'units':units,'load_n':2000}
   r=elastic.run(q,verification_offsets=[[0.,0.],offset],verification_loads={2:(1000.,-2000.,0.)});h=hand(q,offset)
   if r['status']!='VERIFIED':raise ValueError('Rigid-offset mechanics failed: '+str(r.get('error')))
   tip=next(v for v in r['nodes'] if v['id']==2)['displacement_m'];reaction=r['reactions'][0]
   actual=[reaction['fx_n'],reaction['fy_n'],reaction['moment_nm']]
   check=all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-10) for a,b in zip(tip,h['master_tip'])) and all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-7) for a,b in zip(actual,h['base_reaction']))
   end=r['elements'][-1];check=check and math.isclose(end['local_end_forces_si'][5],h['physical_tip_moment_nm'],abs_tol=1e-7)
   check=check and all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-10) for a,b in zip(end['samples'][-1]['displacement_m'],h['physical_tip'][:2]))
   if not check:raise ValueError('Independent rigid-offset hand calculation failed')
   r['rigid_offset_hand_verification']={'passed':True,'reference':h,'max_displacement_error_m':max(abs(a-b) for a,b in zip(tip,h['master_tip']))};cases.append(r)
 return dict(status='VERIFIED',method='OpenSees Linear -jntOffset; global analytical offsets in metres, SI output; independent cantilever closed-form plus global stiffness and node equilibrium checks',cases=cases)

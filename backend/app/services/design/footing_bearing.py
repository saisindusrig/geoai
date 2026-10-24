"""Rigid footing pressure mechanics only; capacity and actual transfer remain blocked."""
from decimal import Decimal
import math
from app.services.design import plate_contact

def benchmark():
 cases=[]
 for N,M,state,edges in [(200000,0,'FULL_CONTACT_LINEAR',[50,50]),(200000,40000,'FULL_CONTACT_LINEAR',[80,20]),(100000,20000,'FULL_CONTACT_LINEAR',[40,10]),(200000,-40000,'FULL_CONTACT_LINEAR',[20,80]),(200000,80000,'CONTACT_LOSS_PARTIAL_UNSUPPORTED',None),(200000,200001,'RESULTANT_OUTSIDE_FOOTPRINT',None)]:
  r=plate_contact.assess(N,M,2,2)
  assert r['contact_state']==state
  evidence=None
  if edges:
   # Independent hand units: kN,m -> kPa; section modulus LB²/6.
   n=Decimal(str(N))/1000;m=Decimal(str(M))/1000;B=Decimal(2);L=Decimal(2);S=L*B*B/6
   hand=[float(n/(B*L)+m/S),float(n/(B*L)-m/S)]
   assert hand==edges
   assert all(math.isclose(a,b,abs_tol=1e-9) for a,b in zip(hand,[r['pressure_at_minus_east_edge_kpa'],r['pressure_at_plus_east_edge_kpa']]))
   evidence=dict(hand_pressure_kpa=hand,formula='q=N/(BL) ± M/(LB²/6); N in kN, M in kN·m, lengths m → kPa',force_residual_n=r['force_residual_n'],moment_residual_nm=r['moment_residual_nm'])
  cases.append(dict(inputs=dict(N_n=N,M_nm=M,B_m=2,L_m=2),result=r,independent=evidence))
 return dict(status='VERIFIED_SYNTHETIC_MECHANICS_ONLY',classification='SYNTHETIC_VERIFICATION',cases=cases,engineering_approval='DISABLED',soil_capacity='NOT_CHECKED',limitations=['Nominal rigid rectangular footing, uniaxial full-contact linear pressure only','No physical column-footing moment or shear transfer established','No partial-contact pressure, uplift resistance, concrete/reinforcement strength, soil capacity or settlement','Footing self-weight and shear reference-plane moment translation excluded from this synthetic benchmark'])

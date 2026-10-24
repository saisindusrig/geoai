"""Wrench transport in saved East/North/Up; demands only, not connection mechanics."""
import math
from app.services.design.frame_loads import Strict
from pydantic import Field
class Link(Strict):
 column_id:str
 footing_id:str
 column_reference_m:list[float]=Field(min_length=3,max_length=3)
 plate_reference_m:list[float]=Field(min_length=3,max_length=3)
 footing_reference_m:list[float]=Field(min_length=3,max_length=3)
 source:str=Field(min_length=10,max_length=500)
 assumption:str=Field(min_length=20,max_length=700)
 reviewed:bool

def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def transport(force,moment,old,new):
 if any(len(x)!=3 or any(not math.isfinite(v) for v in x) for x in [force,moment,old,new]):raise ValueError('Finite three-dimensional SI vectors required')
 r=[a-b for a,b in zip(old,new)];couple=cross(r,force);out=[a+b for a,b in zip(moment,couple)]
 # Independent common-origin equilibrium: M_old + O cross F = M_new + P cross F.
 residual=[a+b-c-d for a,b,c,d in zip(moment,cross(old,force),out,cross(new,force))]
 if max(map(abs,residual))>1e-7:raise ValueError('Reference transport equilibrium failed')
 return dict(force_enu_n=force,moment_enu_nm=out,r_old_minus_new_m=r,offset_couple_nm=couple,equilibrium_residual_nm=residual,sign_convention='r = old reference - new reference; M_new = M_old + r × F. Right-handed East/North/Up. Source analytical moment about -North maps to ENU My=-M_source.',status='VERIFIED_STATIC_DEMAND_TRANSPORT_ONLY',physical_connection_capacity='NOT_VERIFIED',soil_pressure='BLOCKED')

def benchmarks():
 cases=[([0,0,-100000],[0,0,0],[.2,0,0],[0,0,0],[0,20000,0]),([10000,0,-30000],[0,10000,0],[0,0,0],[0,0,-.45],[0,14500,0]),([10,20,30],[4,5,6],[1,2,3],[0,0,0],[4,5,6]),([0,10,0],[0,0,0],[2,0,0],[0,0,0],[0,0,20]),([10,20,30],[3,4,5],[2,-3,4],[-2,1,-1],[-217,-66,125])]
 output=[]
 for F,M,O,P,expected in cases:
  r=transport(F,M,O,P);assert all(math.isclose(a,b,abs_tol=1e-8) for a,b in zip(r['moment_enu_nm'],expected));back=transport(F,r['moment_enu_nm'],P,O);assert all(math.isclose(a,b,abs_tol=1e-8) for a,b in zip(back['moment_enu_nm'],M));output.append(dict(force=F,moment=M,old=O,new=P,hand_expected_nm=expected,result=r))
 return dict(status='VERIFIED',cases=output,limitations='Static equivalence only; no capacity, soil contact, stiffness or displacement solution')

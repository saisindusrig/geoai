"""Synthetic rigid rectangular footing on a uniform compression-only Winkler bed.

ENU: positive applied My puts the compression resultant toward positive East.
Downward penetration w(x)=delta+theta*x; upward soil pressure=k*max(w,0).
This is mechanics verification, not soil suitability or allowable settlement.
"""
import math
import numpy as np
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict

class Inputs(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 B_m:float=Field(ge=.001,le=20)
 L_m:float=Field(ge=.001,le=20)
 N_n:float=Field(ge=-1e8,le=1e8)
 My_nm:float=Field(ge=-1e9,le=1e9)
 k_n_m3:float=Field(ge=1,le=1e12)
 contact_law:Literal['uniform_linear_compression_only_winkler']
 reference_up_m:float=Field(ge=-1000,le=1000)
 source:str=Field(min_length=20,max_length=1000)
 applicability:str=Field(min_length=30,max_length=1500)
 reviewed:Literal[True]

def numerical(q,cells=800):
 """Independent discretized strip springs, active-set 2-DOF stiffness solve."""
 x=(np.arange(cells)+.5)*q.B_m/cells-q.B_m/2
 a=q.B_m*q.L_m/cells
 active=np.ones(cells,dtype=bool)
 for iteration in range(100):
  v=np.stack((np.ones(cells),x),axis=1)
  K=q.k_n_m3*a*(v[active].T@v[active])
  u=np.linalg.solve(K,np.array([q.N_n,q.My_nm]))
  w=v@u;new=w>0
  if np.array_equal(new,active):break
  active=new
 else:raise ValueError('Independent numerical reference did not converge')
 p=q.k_n_m3*np.maximum(w,0)
 return dict(cells=cells,iterations=iteration+1,delta_m=float(u[0]),theta_rad=float(u[1]),contact_area_m2=float(a*active.sum()),force_n=float(p.sum()*a),moment_nm=float((p*x).sum()*a),pmax_pa=float(q.k_n_m3*max(u[0]+abs(u[1])*q.B_m/2,0)))

def calculate(q:Inputs):
 base=dict(classification=q.classification,engineering_approval='DISABLED',actual_project_analysis='BLOCKED',inputs=q.model_dump(),sign_convention='East x; applied My positive; soil upward reaction has My=-integral(x*p*dA). w downward=delta+theta*x; theta about positive North.',applicability_bounds=dict(dimensions_m=[.001,20],stiffness_n_m3=[1,1e12],rotation_rad=.05),limitations=['Uniform independent linear springs and rigid footing; no continuum soil interaction','Synthetic stiffness is not a measured soil modulus or allowable settlement','No shear, torsion, biaxial contact, capacity, concrete/reinforcement, groundwater, IS/US checks or physical transfer approval'])
 if q.N_n<=0:return {**base,'state':'NO_COMPRESSION_EQUILIBRIUM','reason':'Positive compressive N required; zero-load displacement is nonunique and tensile support is excluded'}
 e=q.My_nm/q.N_n;B,L,k=q.B_m,q.L_m,q.k_n_m3
 base.update(eccentricity_m=e,kern_halfwidth_m=B/6,footprint_halfwidth_m=B/2)
 if abs(e)>=B/2:return {**base,'state':'IMPOSSIBLE_FINITE_CONTACT_EQUILIBRIUM','reason':'Resultant at/outside footprint; finite compression pressure cannot equilibrate the wrench'}
 if abs(e)<=B/6+1e-12*B:
  delta=q.N_n/(k*B*L);theta=q.My_nm/(k*L*B**3/12);lo,hi=-B/2,B/2;state='FULL_CONTACT'
 else:
  width=3*(B/2-abs(e));s=math.copysign(1,e);slope=2*q.N_n/(L*k*width**2);theta=s*slope;delta=slope*(width-B/2)
  lo,hi=(B/2-width,B/2) if s>0 else (-B/2,-B/2+width);state='PARTIAL_CONTACT'
 if abs(theta)>.05:return {**base,'state':'OUTSIDE_SMALL_ROTATION_DOMAIN','reason':'Rotation exceeds declared 0.05 rad applicability bound; no supported displacement result'}
 # Independent two-point Gaussian pressure integration over the active interval.
 mid=(lo+hi)/2;half=(hi-lo)/2;xs=[mid-half/math.sqrt(3),mid+half/math.sqrt(3)]
 forces=[k*max(delta+theta*x,0)*L*half for x in xs]
 force=sum(forces);moment=sum(x*f for x,f in zip(xs,forces))
 refs=[numerical(q,n) for n in [200,400,800]]
 residual=[force-q.N_n,moment-q.My_nm]
 if max(abs(residual[0])/q.N_n,abs(residual[1])/max(q.N_n*B,1))>1e-10:raise ValueError('Pressure integration equilibrium failed')
 ref=refs[-1]
 if abs(ref['delta_m']-delta)>max(1e-7,abs(delta)*2e-4) or abs(ref['theta_rad']-theta)>max(1e-7,abs(theta)*2e-4):raise ValueError('Independent spring-bed verification failed')
 return {**base,'state':state,'verification':'VERIFIED_SYNTHETIC_MECHANICS_ONLY','contact_interval_east_m':[lo,hi],'contact_area_m2':(hi-lo)*L,'pmin_pa':max(0,k*(delta-abs(theta)*B/2)),'pmax_pa':k*(delta+abs(theta)*B/2),'delta_down_m':delta,'theta_north_rad':theta,'opposite_edge_gap_m':max(0,-delta+abs(theta)*B/2),'force_integral_n':force,'moment_integral_nm':moment,'residual_n_nm':residual,'numerical_reference':refs,'pressure_samples':[dict(x_m=-B/2+B*i/40,p_pa=k*max(delta+theta*(-B/2+B*i/40),0),down_m=delta+theta*(-B/2+B*i/40)) for i in range(41)],'formulas':'Full: delta=N/(kBL), theta=M/(k LB^3/12). Partial: a=3(B/2-|M/N|), pmax=2N/(La), theta=sign(M)*pmax/(ka), delta=pmax/(ka)*(a-B/2).'}

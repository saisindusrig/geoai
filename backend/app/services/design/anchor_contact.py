"""Bounded planar rigid plate with explicitly declared unilateral elastic springs.
No anchor, concrete, plate or foundation capacity is calculated.
"""
import math
import numpy as np
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict

class Anchor(Strict):
 id:str=Field(min_length=1,max_length=80)
 x_east_m:float=Field(ge=-1,le=1)
 y_north_m:Literal[0.0]
 effective_lever_arm_m:float=Field(ge=-1,le=1)
 axial_stiffness_n_m:float=Field(gt=1e3,le=1e12)
 source:str=Field(min_length=10,max_length=400)
class Inputs(Strict):
 scope:Literal['SEPARATE_SYNTHETIC_BENCHMARK_NOT_ACTUAL_PROJECT']
 width_east_m:float=Field(ge=.2,le=2)
 length_north_m:float=Field(ge=.2,le=2)
 compression_n:float=Field(gt=0,le=1e7)
 moment_negative_north_nm:float=Field(ge=-1e7,le=1e7)
 load_source:str=Field(min_length=10,max_length=400)
 contact_stiffness_n_m3:float=Field(gt=1e5,le=1e13)
 contact_stiffness_source:str=Field(min_length=10,max_length=400)
 anchors:list[Anchor]=Field(min_length=2,max_length=6)
 mechanical_assumption:Literal['PLANAR_MASSLESS_RIGID_PLATE_ELASTIC_WINKLER_COMPRESSION_AND_INDEPENDENT_TENSION_SPRINGS']
 mechanical_source:str=Field(min_length=10,max_length=600)
 fixed_anchor_ground_assumption:Literal[True]
 horizontal_shear_excluded:Literal[True]
 no_pretension:Literal[True]
 engineer_idealization_reviewed:Literal[True]

def validate(q):
 q=Inputs.model_validate(q).model_dump();ids=[a['id'] for a in q['anchors']];xs=[a['x_east_m'] for a in q['anchors']]
 if len(set(ids))!=len(ids) or len(set(xs))!=len(xs):raise ValueError('Distinct individual anchor identities and planar positions required')
 if any(abs(a['x_east_m'])>=q['width_east_m']/2 or abs(a['effective_lever_arm_m']-a['x_east_m'])>1e-10 for a in q['anchors']):raise ValueError('Declared signed lever arm must match anchor position relative to column-center reference inside plate')
 return q

def response(q,u,theta):
 B=q['width_east_m'];L=q['length_north_m'];k=q['contact_stiffness_n_m3'];lo=-B/2;hi=B/2
 if abs(theta)<1e-16:
  if u<=0:hi=lo
 elif theta>0:lo=max(lo,min(hi,-u/theta))
 else:hi=max(lo,min(hi,-u/theta))
 j0=hi-lo;j1=(hi*hi-lo*lo)/2;j2=(hi**3-lo**3)/3
 C=k*L*(u*j0+theta*j1);Q=k*L*(u*j1+theta*j2);K=k*L*np.array([[j0,j1],[j1,j2]]);T=[];net=np.array([C,Q])
 for a in q['anchors']:
  x=a['x_east_m'];w=u+theta*x;t=a['axial_stiffness_n_m']*max(-w,0);T.append(dict(id=a['id'],x_east_m=x,y_north_m=0,effective_lever_arm_m=x,opening_m=max(-w,0),tension_n=t,axial_stiffness_n_m=a['axial_stiffness_n_m'],status='ACTIVE_TENSION' if t>0 else 'SLACK_ZERO_TENSION',source=a['source']));net-=np.array([t,x*t])
  if w<0:K+=a['axial_stiffness_n_m']*np.array([[1,x],[x,x*x]])
 return net,K,dict(compression_resultant_n=C,compression_first_moment_nm=Q,contact_interval_east_m=[lo,hi],anchors=T)

def run(inputs):
 q=validate(inputs);B=q['width_east_m'];L=q['length_north_m'];k=q['contact_stiffness_n_m3'];target=np.array([q['compression_n'],-q['moment_negative_north_nm']]);state=np.array([target[0]/(k*L*B),target[1]/(k*L*B**3/12)]);scale=np.array([1,1/B]);log=[]
 for iteration in range(60):
  net,K,r=response(q,*state);residual=net-target;norm=float(np.linalg.norm(residual*scale));log.append(dict(iteration=iteration,residual_force_n=float(residual[0]),residual_moment_nm=float(residual[1])))
  if norm<1e-7:break
  if np.linalg.cond(K)>1e12:raise ValueError('Insufficient active compression/anchor constraints; unsupported singular mechanism')
  step=np.linalg.solve(K,-residual);accepted=False
  for j in range(30):
   trial=state+step*(.5**j);nr,_,_=response(q,*trial)
   if np.linalg.norm((nr-target)*scale)<norm:state=trial;accepted=True;break
  if not accepted:raise ValueError('Unilateral contact iteration failed; no result invented')
 else:raise ValueError('Unilateral contact did not converge')
 u,theta=map(float,state)
 if abs(theta)>.01 or max(abs(u-theta*B/2),abs(u+theta*B/2))>.01*B:raise ValueError('Outside bounded small-displacement rigid-plate verification domain')
 lo,hi=r['contact_interval_east_m'];samples=[dict(x_east_m=float(x),pressure_pa=max(0,k*(u+theta*x))) for x in np.linspace(-B/2,B/2,33)]
 # Independent two-point quadrature over actual active interval: exact for p and xp.
 mid=(lo+hi)/2;dx=(hi-lo)/(2*math.sqrt(3));weight=L*(hi-lo)/2;C=sum(max(0,k*(u+theta*x))*weight for x in (mid-dx,mid+dx));Q=sum(x*max(0,k*(u+theta*x))*weight for x in (mid-dx,mid+dx));T=sum(a['tension_n'] for a in r['anchors']);AT=sum(a['effective_lever_arm_m']*a['tension_n'] for a in r['anchors']);f=C-T-q['compression_n'];m=Q-AT+q['moment_negative_north_nm']
 if min(s['pressure_pa'] for s in samples)<0 or min(a['tension_n'] for a in r['anchors'])<0 or abs(f)>1e-6 or abs(m)>1e-6:raise ValueError('Independent force/moment/unilateral verification failed')
 return dict(status='VERIFIED_SYNTHETIC_MECHANICAL_BENCHMARK_ONLY',inputs=q,translation_down_m=u,rotation_slope_rad=theta,**r,pressure_samples=samples,pressure_max_kpa=max(s['pressure_pa'] for s in samples)/1000,compression_centroid_east_m=Q/C if C>0 else None,total_anchor_tension_n=T,force_residual_n=f,moment_residual_nm=m,independent_quadrature_compression_n=C,independent_quadrature_first_moment_nm=Q,iterations=log,formulas=['w(x)=u+θx, downward positive [m]','p(x)=kc max(w,0) [Pa]; C=∫p dA; Q=∫x p dA','Ti=ki max(−w(xi),0) [N], each anchor stiffness declared individually','C−ΣTi=N; Q−ΣxiTi+Mapplied=0'],limitations=['Synthetic planar massless rigid plate and elastic nominal compression bed only; not contact FEA or concrete material calibration','All anchors on the North centerline; biaxial force/moment coupling unsupported','No pretension, prying, bolt/footing flexibility beyond individually declared axial springs, gaps or contact holes','Fixed spring-ground load path must be explicitly declared; no embedment resistance inferred','Anchor strength, concrete breakout/crushing, plate bending, welds, footing/soil and code compliance NOT VERIFIED','Horizontal shear transfer excluded; no engineering approval'],engineering_approval='DISABLED',physical_capacity='NOT_YET_VERIFIED')

def fixture():
 return dict(scope='SEPARATE_SYNTHETIC_BENCHMARK_NOT_ACTUAL_PROJECT',width_east_m=.6,length_north_m=.5,compression_n=16100,moment_negative_north_nm=5876,load_source='Synthetic independently worked N=16.1 kN, M=5.876 kNm; not actual project demand',contact_stiffness_n_m3=1e9,contact_stiffness_source='Explicit synthetic nominal compression stiffness 1e9 N/m3; not inferred from concrete strength',anchors=[dict(id=f'benchmark-anchor-{i+1}',x_east_m=x,y_north_m=0,effective_lever_arm_m=x,axial_stiffness_n_m=stiff,source='Explicit independent synthetic axial stiffness, fixed spring ground') for i,(x,stiff) in enumerate([(-.24,1e7),(-.20,2e7),(.20,2e7),(.24,1e7)])],mechanical_assumption='PLANAR_MASSLESS_RIGID_PLATE_ELASTIC_WINKLER_COMPRESSION_AND_INDEPENDENT_TENSION_SPRINGS',mechanical_source='Explicit synthetic idealization: nominal elastic compression bed, four separate zero-pretension tension springs, fixed spring ground; no resistance or capacity claims',fixed_anchor_ground_assumption=True,horizontal_shear_excluded=True,no_pretension=True,engineer_idealization_reviewed=True)

def benchmark():
 # Hand prescribes u=0,theta=-.001. Contact [-.3,0], p=-1e6*x Pa.
 # C=.5*300000*.3/2=22500 N; centroid=-.2; Q=-4500 Nm.
 # T(.20)=20e6*.0002=4000; T(.24)=10e6*.00024=2400.
 # N=22500-6400=16100; M=4500+.20*4000+.24*2400=5876 Nm.
 r=run(fixture());checks=[math.isclose(r['translation_down_m'],0,abs_tol=1e-12),math.isclose(r['rotation_slope_rad'],-.001,abs_tol=1e-12),math.isclose(r['compression_resultant_n'],22500,abs_tol=1e-6),math.isclose(r['pressure_max_kpa'],300,abs_tol=1e-6),all(math.isclose(a['tension_n'],expected,abs_tol=1e-6) for a,expected in zip(r['anchors'],[0,0,4000,2400]))]
 if not all(checks):raise ValueError('Independent compression-plus-anchor known-answer benchmark failed')
 return dict(status='VERIFIED',hand=dict(u_m=0,theta_rad=-.001,contact_width_m=.3,compression_n=22500,centroid_east_m=-.2,pressure_max_kpa=300,anchor_tensions_n=[0,0,4000,2400],total_tension_n=6400,net_axial_n=16100,contact_moment_nm=-4500,anchor_moment_nm=-1376,applied_moment_nm=5876,formula='C=0.5×300000Pa×0.3m×0.5m=22500N; Q=C×(-0.2m)=-4500Nm; T(.20)=20MN/m×0.2mm=4000N; T(.24)=10MN/m×0.24mm=2400N; N=C−6400=16100N; M=4500+800+576=5876Nm'),computed=r)

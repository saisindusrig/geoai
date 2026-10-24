"""Three-DOF nominal rigid-plate verification; exact polygon integration, no capacity design."""
import math
import numpy as np
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict
from app.services.design import anchor_contact as planar

class Anchor(Strict):
 id:str=Field(min_length=1,max_length=80)
 position_east_north_m:list[float]=Field(min_length=2,max_length=2)
 effective_lever_arms_m:list[float]=Field(min_length=2,max_length=2)
 axial_stiffness_n_m:float=Field(gt=1e3,le=1e12)
 source:str=Field(min_length=10,max_length=400)
class Inputs(Strict):
 scope:Literal['SEPARATE_SYNTHETIC_3D_BENCHMARK_NOT_ACTUAL_PROJECT']
 case_name:str=Field(min_length=3,max_length=80)
 width_east_m:float=Field(ge=.2,le=2)
 length_north_m:float=Field(ge=.2,le=2)
 compression_n:float=Field(gt=0,le=1e7)
 moments_east_north_nm:list[float]=Field(min_length=2,max_length=2)
 load_source:str=Field(min_length=10,max_length=400)
 contact_stiffness_n_m3:float=Field(gt=1e5,le=1e13)
 contact_stiffness_source:str=Field(min_length=10,max_length=400)
 anchors:list[Anchor]=Field(min_length=4,max_length=4)
 mechanical_assumption:Literal['THREE_DOF_MASSLESS_RIGID_PLATE_LINEAR_COMPRESSION_BED_AND_INDIVIDUAL_TENSION_SPRINGS']
 mechanical_source:str=Field(min_length=10,max_length=600)
 fixed_anchor_ground_assumption:Literal[True]
 horizontal_shear_excluded:Literal[True]
 no_pretension:Literal[True]
 engineer_idealization_reviewed:Literal[True]

def validate(inputs):
 q=Inputs.model_validate(inputs).model_dump();ids=[];ps=[]
 if any(abs(m)>1e7 for m in q['moments_east_north_nm']):raise ValueError('Moment outside bounded verification range')
 for a in q['anchors']:
  p=a['position_east_north_m'];ids.append(a['id']);ps.append(tuple(p))
  if abs(p[0])>=q['width_east_m']/2 or abs(p[1])>=q['length_north_m']/2 or any(abs(v-w)>1e-10 for v,w in zip(p,a['effective_lever_arms_m'])):raise ValueError('Anchor must lie inside plate; explicit signed lever arms must match physical reference positions')
 if len(set(ids))!=4 or len(set(ps))!=4:raise ValueError('Four distinct anchor identities and positions required')
 return q

def active_polygon(B,L,state):
 poly=[[-B/2,-L/2],[B/2,-L/2],[B/2,L/2],[-B/2,L/2]];u,sx,sy=state;out=[]
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];wa=u+sx*a[0]+sy*a[1];wb=u+sx*b[0]+sy*b[1]
  if wa>=0:out.append(a)
  if (wa>=0)!=(wb>=0):
   t=wa/(wa-wb);out.append([a[j]+t*(b[j]-a[j]) for j in (0,1)])
 clean=[]
 for p in out:
  if not clean or math.dist(p,clean[-1])>1e-13:clean.append(p)
 if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-13:clean.pop()
 return clean if len(clean)>=3 else []

def moments(poly):
 """Exact signed polygon area and degree-two monomial integrals (shoelace formulas)."""
 A=Sx=Sy=X2=Y2=XY=0.
 for i,(x,y) in enumerate(poly):
  xx,yy=poly[(i+1)%len(poly)];cross=x*yy-xx*y;A+=cross/2;Sx+=(x+xx)*cross/6;Sy+=(y+yy)*cross/6;X2+=(x*x+x*xx+xx*xx)*cross/12;Y2+=(y*y+y*yy+yy*yy)*cross/12;XY+=(2*x*y+x*yy+xx*y+2*xx*yy)*cross/24
 return np.array([[A,Sx,Sy],[Sx,X2,XY],[Sy,XY,Y2]])

def quadrature(poly,state,k):
 """Independent triangle quadrature, exact for linear pressure and both first moments."""
 force=np.zeros(3);area=0.
 if len(poly)<3:return force,area
 a=np.array(poly[0])
 for i in range(1,len(poly)-1):
  b=np.array(poly[i]);c=np.array(poly[i+1]);triangle=abs(float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])))/2;area+=triangle
  for weights in [(2/3,1/6,1/6),(1/6,2/3,1/6),(1/6,1/6,2/3)]:
   xy=weights[0]*a+weights[1]*b+weights[2]*c;v=np.array([1,*xy]);p=k*max(float(v@state),0);force+=v*p*triangle/3
 return force,area

def response(q,state):
 poly=active_polygon(q['width_east_m'],q['length_north_m'],state);G=moments(poly);K=q['contact_stiffness_n_m3']*G;contact=K@state;net=contact.copy();anchors=[]
 for a in q['anchors']:
  x,y=a['position_east_north_m'];v=np.array([1,x,y]);w=float(v@state);opening=max(-w,0);t=a['axial_stiffness_n_m']*opening;net-=v*t
  if w<0:K+=a['axial_stiffness_n_m']*np.outer(v,v)
  anchors.append(dict(**a,opening_m=opening,tension_n=t,status='ACTIVE_TENSION' if t>1e-8 else 'SLACK_ZERO_TENSION'))
 return net,K,contact,poly,anchors,G[0,0]

def run(inputs):
 q=validate(inputs);B=q['width_east_m'];L=q['length_north_m'];k=q['contact_stiffness_n_m3'];Mx,My=q['moments_east_north_nm'];target=np.array([q['compression_n'],My,-Mx]);state=target/(k*np.array([B*L,L*B**3/12,B*L**3/12]));scales=np.array([1,1/B,1/L]);log=[]
 for iteration in range(80):
  net,K,contact,poly,anchors,area=response(q,state);residual=net-target;norm=float(np.linalg.norm(residual*scales));log.append(dict(iteration=iteration,residual_si=residual.tolist()))
  if norm<1e-7:break
  if not np.isfinite(K).all() or np.linalg.cond(K)>1e12:raise ValueError('Unsupported singular or ill-conditioned active contact/anchor mechanism')
  step=np.linalg.solve(K,-residual);accepted=False
  for j in range(35):
   trial=state+step*.5**j;rn=response(q,trial)[0]
   if np.linalg.norm((rn-target)*scales)<norm:state=trial;accepted=True;break
  if not accepted:raise ValueError('3D unilateral contact line search failed; no result invented')
 else:raise ValueError('3D unilateral contact did not converge')
 u,sx,sy=map(float,state)
 if max(abs(sx),abs(sy))>.01 or max(abs(u+sx*x+sy*y) for x in [-B/2,B/2] for y in [-L/2,L/2])>.01*min(B,L):raise ValueError('Outside bounded small-displacement rigid-plate verification domain')
 independently,ind_area=quadrature(poly,state,k);a_force=sum(a['tension_n'] for a in anchors);a_x=sum(a['position_east_north_m'][0]*a['tension_n'] for a in anchors);a_y=sum(a['position_east_north_m'][1]*a['tension_n'] for a in anchors);force=independently[0]-a_force-q['compression_n'];mxe=independently[2]-a_y+Mx;myn=-independently[1]+a_x+My
 if not np.allclose(independently,contact,rtol=1e-10,atol=1e-6) or abs(ind_area-area)>1e-10 or max(abs(force),abs(mxe),abs(myn))>1e-6:raise ValueError('Independent 3D area/force/both-moment equilibrium verification failed')
 samples=[dict(position_east_north_m=[float(x),float(y)],pressure_pa=max(0,k*(u+sx*x+sy*y))) for x in np.linspace(-B/2,B/2,17) for y in np.linspace(-L/2,L/2,17)]
 if any(a['tension_n']<0 for a in anchors) or any(s['pressure_pa']<0 for s in samples):raise ValueError('Unilateral pressure/tension constraint failed')
 vertices=[dict(position_east_north_m=p,pressure_pa=max(0,k*(u+sx*p[0]+sy*p[1]))) for p in poly]
 return dict(status='VERIFIED_SYNTHETIC_3D_MECHANICS_ONLY',inputs=q,translation_down_m=u,slopes_east_north_rad=[sx,sy],rotations_east_north_rad=[-sy,sx],compression_resultant_n=float(contact[0]),contact_first_moments_nm=contact[1:].tolist(),active_contact_area_m2=float(area),active_contact_fraction=float(area/(B*L)),active_contact_polygon_east_north_m=poly,pressure_vertices=vertices,pressure_samples=samples,pressure_max_kpa=max((v['pressure_pa'] for v in vertices),default=0)/1000,anchors=anchors,total_anchor_tension_n=a_force,equilibrium_residual_si=[float(force),float(mxe),float(myn)],independent_quadrature=dict(force_and_first_moments_si=independently.tolist(),area_m2=ind_area),compression_centroid_east_north_m=(contact[1:]/contact[0]).tolist() if contact[0]>0 else None,iterations=log,formulas=['w=u+sx*x+sy*y downward [m]; rotations about East/North=[−sy,sx] [rad]','p=kc max(w,0) [Pa]; exact active polygon integration','Ti=ki max(−w(xi,yi),0) [N], each anchor stiffness explicit','C−ΣTi=N; Qy−ΣyiTi+Mx=0; −Qx+ΣxiTi+My=0'],limitations=['Separate synthetic benchmark; actual-project mechanics remain blocked until all input evidence/load paths are reviewed','Nominal homogeneous compression-only elastic bed and four separate linear tension-only springs; not concrete/contact/bolt capacity FEA','No pretension, holes, prying, plate bending, weld behavior, embedment resistance or material nonlinearity','Fixed spring-ground is a declared idealization, not a verified physical footing/anchor load path','Horizontal shear, torsion, physical anchor capacity, concrete breakout, footing/soil capacity and code compliance NOT VERIFIED'],engineering_approval='DISABLED',physical_capacity='NOT_YET_VERIFIED')

def fixture(case='biaxial'):
 if case=='2d_reduction':
  p=planar.fixture();B=p['width_east_m'];L=p['length_north_m'];N=p['compression_n'];Ms=[0,-p['moment_negative_north_nm']];positions=[[a['x_east_m'],0] for a in p['anchors']];stiff=[a['axial_stiffness_n_m'] for a in p['anchors']]
 else:
  B=L=.65;a=.325;k=1e9;positions=[[-.24,-.24],[-.24,.24],[.24,-.24],[.24,.24]];stiff=[1e7]*4;C=k*.001*L*a*a/2;Q=-C*2*a/3
  if case=='symmetric':N=k*.0002*B*L;Ms=[0,0]
  elif case=='uniaxial':N=C-4800;Ms=[0,Q-1152]
  elif case=='asymmetric':stiff[2]=2e7;N=C-7200;Ms=[-576,Q-1728]
  elif case=='biaxial':N=k*.001*4*a**3/3-4800;Ms=[-Q+1152,Q-1152]
  else:raise ValueError('Unknown independently benchmarked case')
 return dict(scope='SEPARATE_SYNTHETIC_3D_BENCHMARK_NOT_ACTUAL_PROJECT',case_name=case,width_east_m=B,length_north_m=L,compression_n=N,moments_east_north_nm=Ms,load_source='Explicit independently worked synthetic load case '+case+'; never assigned to actual project',contact_stiffness_n_m3=1e9,contact_stiffness_source='Explicit synthetic nominal contact stiffness 1 GN/m3; no concrete or soil calibration implied',anchors=[dict(id=f'3d-benchmark-anchor-{i+1}',position_east_north_m=p,effective_lever_arms_m=p,axial_stiffness_n_m=stiff[i],source='Individually declared synthetic axial stiffness and fixed spring ground, not bolt resistance') for i,p in enumerate(positions)],mechanical_assumption='THREE_DOF_MASSLESS_RIGID_PLATE_LINEAR_COMPRESSION_BED_AND_INDIVIDUAL_TENSION_SPRINGS',mechanical_source='Explicit synthetic zero-pretension rigid-plate homogeneous compression bed and independent fixed-ground tension springs; no physical load-path/capacity approval',fixed_anchor_ground_assumption=True,horizontal_shear_excluded=True,no_pretension=True,engineer_idealization_reviewed=True)

def benchmarks():
 out=[];a=.325;C=.65*a*a*1e6/2;Q=-C*2*a/3
 for case in ['symmetric','uniaxial','asymmetric','biaxial','2d_reduction']:
  q=fixture(case);r=run(q)
  if case=='symmetric':hand=dict(state=[.0002,0,0],C=84500,area=.4225,tensions=[0,0,0,0],pressure_max_kpa=200)
  elif case=='uniaxial':hand=dict(state=[0,-.001,0],C=C,area=.21125,tensions=[0,0,2400,2400],pressure_max_kpa=325)
  elif case=='asymmetric':hand=dict(state=[0,-.001,0],C=C,area=.21125,tensions=[0,0,4800,2400],pressure_max_kpa=325)
  elif case=='biaxial':hand=dict(state=[0,-.001,-.001],C=4*a**3*1e6/3,area=.21125,tensions=[0,0,0,4800],pressure_max_kpa=650)
  else:
   p=planar.benchmark()['computed'];hand=dict(state=[p['translation_down_m'],p['rotation_slope_rad'],0],C=p['compression_resultant_n'],area=.15,tensions=[x['tension_n'] for x in p['anchors']],pressure_max_kpa=p['pressure_max_kpa'])
  if not(np.allclose([r['translation_down_m'],*r['slopes_east_north_rad']],hand['state'],atol=1e-11,rtol=0) and math.isclose(r['compression_resultant_n'],hand['C'],abs_tol=1e-6) and math.isclose(r['active_contact_area_m2'],hand['area'],abs_tol=1e-10) and math.isclose(r['pressure_max_kpa'],hand['pressure_max_kpa'],abs_tol=1e-6) and np.allclose([x['tension_n'] for x in r['anchors']],hand['tensions'],atol=1e-6,rtol=0)):raise ValueError('Independent 3D known-answer verification failed: '+case)
  out.append(dict(case=case,hand=hand,computed=r))
 return dict(status='VERIFIED',cases=out,reference='Known prescribed rigid-plate states; rectangular full contact / half-strip / half-square triangle exact hand integrals; unequal individual springs; 2D analytical reduction verified. Independent triangle quadrature checks all three equilibrium equations.')

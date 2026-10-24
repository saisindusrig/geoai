"""Demand-only column-face cantilever cuts; synthetic prescribed pressure, not RC capacity."""
import math
from decimal import Decimal,localcontext
from typing import Literal
from pydantic import Field,model_validator
from app.services.design.frame_loads import Strict
METHOD='CAD_FOOTING_CANTILEVER_DEMAND_V1'
REFERENCE='https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/technical-guidance-documents/structure-and-bridge/VDMASD.pdf'
class Input(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 method:Literal['CAD_FOOTING_CANTILEVER_DEMAND_V1']
 footing_id:str=Field(min_length=1,max_length=200)
 column_id:str=Field(min_length=1,max_length=200)
 B_m:float=Field(gt=0,le=20)
 L_m:float=Field(gt=0,le=20)
 thickness_m:float=Field(gt=0,le=5)
 column_east_m:float=Field(gt=0,le=10)
 column_north_m:float=Field(gt=0,le=10)
 column_load_kn:float=Field(gt=0,le=100000)
 uniform_net_pressure_kpa:float=Field(gt=0,le=100000)
 bearing_reference_up_m:float=Field(ge=-1000,le=1000)
 load_reference_up_m:float=Field(ge=-1000,le=1000)
 eccentricity_east_m:Literal[0]
 eccentricity_north_m:Literal[0]
 horizontal_shear_kn:Literal[0]
 applied_moment_knm:Literal[0]
 soil_reaction:Literal['PRESCRIBED_UNIFORM_UPWARD_FULL_CONTACT']
 self_weight:Literal['EXCLUDED_SYNTHETIC_NET_PRESSURE_BENCHMARK']
 load_path:Literal['REVIEWED_HYPOTHETICAL_DIRECT_COLUMN_PATCH']
 reviewed_footprint:Literal[True]
 reviewed_assumptions:Literal[True]
 geometry_source:str=Field(min_length=20,max_length=1000)
 footprint_source:str=Field(min_length=20,max_length=1000)
 load_source:str=Field(min_length=20,max_length=1000)
 pressure_source:str=Field(min_length=20,max_length=1000)
 reference_source:str=Field(min_length=20,max_length=1000)
 load_path_source:str=Field(min_length=40,max_length=1500)
 applicability:str=Field(min_length=40,max_length=2000)
 @model_validator(mode='after')
 def supported(self):
  if not math.isclose(self.B_m,self.L_m,rel_tol=0,abs_tol=1e-10) or not math.isclose(self.column_east_m,self.column_north_m,rel_tol=0,abs_tol=1e-10):raise ValueError('First benchmark supports symmetric square footing and square column patch only')
  if self.column_east_m>=self.B_m or self.column_north_m>=self.L_m:raise ValueError('Column patch must be strictly inside footing with positive projections')
  if not math.isclose(self.uniform_net_pressure_kpa*self.B_m*self.L_m,self.column_load_kn,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('Prescribed net upward pressure must equilibrate the declared column load; no bearing-capacity value is imported')
  if not math.isclose(self.load_reference_up_m-self.bearing_reference_up_m,self.thickness_m,rel_tol=0,abs_tol=1e-9):raise ValueError('Load plane must be at footing top, pressure plane at footing bottom')
  return self

def audit_geometry(doc,q:Input):
 by_id={c['id']:c for c in doc['components']}
 try:f=by_id[q.footing_id];c=by_id[q.column_id]
 except KeyError as e:raise ValueError('Selected saved footing/column identity not found') from e
 for part,role in [(f,'foundation'),(c,'column')]:
  if part['category']!=role or part['geometry']['kind']!='box':raise ValueError('Only explicit saved foundation/column box envelopes supported')
  if any(abs(v)>1e-10 for v in part['transform']['rotation_deg']) or any(abs(v-1)>1e-10 for v in part['transform']['scale']):raise ValueError('Rotated/scaled envelopes require separate validation')
  if not part.get('metadata',{}).get('drawing_cad',{}).get('source_entity_id'):raise ValueError('Saved CAD source identity required')
 if any(abs(f['transform']['position'][i]-c['transform']['position'][i])>1e-9 for i in [0,1]):raise ValueError('Nonconcentric saved geometry is unsupported; geometry will not be aligned automatically')
 expected=[*f['geometry']['size'],*c['geometry']['size'][:2],f['transform']['position'][2]-f['geometry']['size'][2]/2,f['transform']['position'][2]+f['geometry']['size'][2]/2]
 entered=[q.B_m,q.L_m,q.thickness_m,q.column_east_m,q.column_north_m,q.bearing_reference_up_m,q.load_reference_up_m]
 if any(not math.isclose(a,b,rel_tol=0,abs_tol=1e-9) for a,b in zip(expected,entered)):raise ValueError('Explicit dimensions/reference planes do not match the saved envelopes')
 if not math.isclose(c['transform']['position'][2]-c['geometry']['size'][2]/2,q.load_reference_up_m,abs_tol=1e-9,rel_tol=0):raise ValueError('Saved column bottom does not meet declared footing top; no connection inferred')
 return dict(footing_id=f['id'],column_id=c['id'],footing_source=f['metadata']['drawing_cad']['source_entity_id'],column_source=c['metadata']['drawing_cad']['source_entity_id'],center_east_north_m=f['transform']['position'][:2],footing_size_m=f['geometry']['size'],column_size_m=c['geometry']['size'],bearing_up_m=q.bearing_reference_up_m,column_face_up_m=q.load_reference_up_m,connection_status='SYNTHETIC_PATCH_ONLY_ACTUAL_CONNECTION_UNVERIFIED')

def independent_integrals(q,n):
 # Separate rectangular-cell pressure integration. No production moment expression used.
 pressure=q.uniform_net_pressure_kpa;area=q.B_m*q.L_m;global_n=0.;mx=0.;my=0.
 for i in range(n):
  for j in range(n):
   x=-q.B_m/2+(i+.5)*q.B_m/n;y=-q.L_m/2+(j+.5)*q.L_m/n;force=pressure*area/(n*n)
   global_n+=force;mx+=force*y;my-=force*x
 faces={}
 for name,width,edge,face in [('East',q.L_m,q.B_m/2,q.column_east_m/2),('West',q.L_m,q.B_m/2,q.column_east_m/2),('North',q.B_m,q.L_m/2,q.column_north_m/2),('South',q.B_m,q.L_m/2,q.column_north_m/2)]:
  ds=(edge-face)/n;moment=0.;force=0.
  for i in range(n):
   arm=(i+.5)*ds;cell_force=pressure*width*ds;moment+=cell_force*arm;force+=cell_force
  faces[name]=dict(force_kn=force,face_moment_knm=moment)
 return dict(cells_per_axis=n,upward_force_kn=global_n,moment_about_east_knm=mx,moment_about_north_knm=my,faces=faces)

def calculate(q:Input):
 p=q.uniform_net_pressure_kpa;faces=[]
 for name,a,width,axis,sign in [('East',(q.B_m-q.column_east_m)/2,q.L_m,'north',-1),('West',(q.B_m-q.column_east_m)/2,q.L_m,'north',1),('North',(q.L_m-q.column_north_m)/2,q.B_m,'east',1),('South',(q.L_m-q.column_north_m)/2,q.B_m,'east',-1)]:
  m=p*a*a/2;faces.append(dict(face=name,projection_m=a,cut_width_m=width,moment_knm_per_m=m,full_cut_moment_knm=m*width,upward_cut_force_kn=p*a*width,external_moment_axis=axis,external_moment_sign=sign,diagram=[dict(distance_from_face_m=a*i/20,moment_knm_per_m=m*(1-i/20)**2) for i in range(21)]))
 refs=[independent_integrals(q,n) for n in [1,2,8,32]]
 with localcontext() as ctx:
  ctx.prec=40;D=lambda x:Decimal(str(x));a=(D(q.B_m)-D(q.column_east_m))/2;hand=D(p)*a*a/2
  # Independent N/mm units: pressure kPa/1000, projection metres*1000, one-metre strip=1000 mm.
  hand_nmm=(D(p)/1000)*(a*1000)*(a*1000)*1000/2
 for ref in refs:
  if not math.isclose(ref['upward_force_kn'],q.column_load_kn,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('Independent pressure integration failed')
  for face in faces:
   if not math.isclose(ref['faces'][face['face']]['face_moment_knm'],face['full_cut_moment_knm'],rel_tol=1e-12,abs_tol=1e-10):raise ValueError('Independent face moment integration failed')
 if not math.isclose(float(hand),faces[0]['moment_knm_per_m'],rel_tol=1e-13):raise ValueError('Independent Decimal verification failed')
 return dict(method_version=METHOD,status='VERIFIED_SYNTHETIC_DEMAND_ONLY',inputs=q.model_dump(),faces=faces,upward_force_kn=p*q.B_m*q.L_m,column_load_kn=q.column_load_kn,force_residual_kn=p*q.B_m*q.L_m-q.column_load_kn,global_moment_residual_knm=[refs[-1]['moment_about_east_knm'],refs[-1]['moment_about_north_knm']],independent_integration=refs,decimal_hand=dict(moment_knm_per_m=str(hand),one_metre_strip_Nmm=str(hand_nmm)),formula='a_EW=(B-cE)/2; a_NS=(L-cN)/2; for each full-width cut: w=q_net*b; V=w*a; M_face=w*a^2/2; per metre m=q_net*a^2/2; m(s)=q_net*(a-s)^2/2 from face toward free edge. q_net*B*L=N.',sign_convention='ENU axes; upward pressure +Up. External face moment is r cross F: East -My, West +My, North +Mx, South -Mx. Report positive demand magnitudes; internal resisting cut moment is opposite. No capacity/sign-of-reinforcement verdict.',reference=REFERENCE,reference_note='VDOT ASD manual section4.4.11.1.1: isolated footing as cantilever; column-face section; integrate forces on one side. Used solely to document the mechanics idealization, not compliance.',limitations=['Demand only; no reinforcement area, effective depth or material strengths inferred','Orthogonal full-width cuts overlap in area: never sum their four upward forces as separate reactions or their magnitudes as one global moment','Prescribed uniform NET upward pressure with footing self-weight deliberately excluded from this synthetic equilibrium benchmark','No plate/shell FEA, cracking, stiffness, deflection, nonuniform reaction, uplift, eccentricity, shear or physical connection transfer','Actual steel-column/base-plate/RC-footing behavior remains unverified; the reviewed column envelope is only a hypothetical load patch','No reinforcement adequacy, one-way shear, punching, footing/soil safety or IS/US code checks'],actual_foundation_safety='BLOCKED',engineering_approval='DISABLED',reinforcement_capacity='NOT_IMPLEMENTED',shear_capacity='NOT_IMPLEMENTED',design_code_checks='DISABLED')

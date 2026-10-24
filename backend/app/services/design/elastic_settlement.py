"""Uniform flexible rectangular surface traction on an isotropic elastic half-space.

Centre displacement only; NOT rigid-footing settlement, layered analysis or Winkler.
Integrates Boussinesq surface Green function Gzz=(1-nu²)/(pi E r).
"""
import math
import numpy as np
from typing import Literal
from pydantic import Field,model_validator
from app.services.design.frame_loads import Strict

class Source(Strict):
 id:str=Field(min_length=1,max_length=80)
 reference:str=Field(min_length=10,max_length=1000)
 investigation:str=Field(min_length=10,max_length=1500)
class Property(Strict):
 value:float
 kind:Literal['MEASURED','CORRELATED','ENGINEER_ASSUMED','SYNTHETIC']
 source_id:str=Field(min_length=1,max_length=80)
class Layer(Strict):
 id:str=Field(min_length=1,max_length=80)
 description:str=Field(min_length=3,max_length=300)
 top_depth_m:float=Field(ge=0,le=1000)
 bottom_depth_m:float|None=Field(default=None,gt=0,le=1000)
 extent:Literal['FINITE','UNBOUNDED_IDEALIZATION','UNKNOWN']
 extent_source_id:str=Field(min_length=1,max_length=80)
 extent_kind:Literal['MEASURED','CORRELATED','ENGINEER_ASSUMED','SYNTHETIC']
 unit_weight_kn_m3:Property|None=None
 E_mpa:Property|None=None
 poisson:Property|None=None
class Profile(Strict):
 classification:Literal['REAL_PROJECT','UNVERIFIED','SYNTHETIC_VERIFICATION']
 borehole_id:str=Field(min_length=1,max_length=100)
 location_enu_m:list[float]=Field(min_length=3,max_length=3)
 ground_reference_up_m:float=Field(ge=-1000,le=1000)
 reference_source_id:str=Field(min_length=1,max_length=80)
 groundwater_depth_m:float|None=Field(default=None,ge=0,le=1000)
 groundwater_source_id:str|None=None
 sources:list[Source]=Field(min_length=1,max_length=40)
 layers:list[Layer]=Field(min_length=1,max_length=40)
 applicability:str=Field(min_length=30,max_length=2000)
 @model_validator(mode='after')
 def validate_profile(self):
  sources={s.id for s in self.sources}
  if len(sources)!=len(self.sources) or len({l.id for l in self.layers})!=len(self.layers):raise ValueError('Unique source/layer identities required')
  if self.reference_source_id not in sources:raise ValueError('Ground/reference evidence missing')
  if abs(self.location_enu_m[2]-self.ground_reference_up_m)>1e-9:raise ValueError('Borehole location Up must equal declared ground reference')
  if self.groundwater_depth_m is not None and self.groundwater_source_id not in sources:raise ValueError('Groundwater observation/reference source required')
  if self.groundwater_depth_m is None and self.groundwater_source_id is not None:raise ValueError('Unknown groundwater cannot have a numeric observation source')
  depth=0.
  for i,l in enumerate(self.layers):
   if l.extent_source_id not in sources:raise ValueError('Layer depth/extent evidence missing')
   if abs(l.top_depth_m-depth)>1e-9:raise ValueError('Layers must be ordered contiguous from ground depth zero; no gaps or overlaps')
   if l.bottom_depth_m is None and i!=len(self.layers)-1:raise ValueError('Unbounded idealization only permitted for last layer')
   if (l.extent=='FINITE')!=(l.bottom_depth_m is not None):raise ValueError('Finite extent requires an explicit bottom depth; unknown/unbounded extent requires no invented bottom')
   if l.extent=='UNBOUNDED_IDEALIZATION' and l.extent_kind not in ['ENGINEER_ASSUMED','SYNTHETIC']:raise ValueError('Infinite half-space extent is an idealization, not a measured/correlated depth')
   if l.bottom_depth_m is not None and l.bottom_depth_m<=l.top_depth_m:raise ValueError('Positive layer thickness required')
   depth=l.bottom_depth_m if l.bottom_depth_m is not None else depth
   for name,p,bounds in [('unit weight',l.unit_weight_kn_m3,(0,40)),('E',l.E_mpa,(0,1e6)),('Poisson',l.poisson,(-1,.5))]:
    if p is not None:
     if p.source_id not in sources:raise ValueError(f'{name} investigation evidence missing')
     if not bounds[0]<p.value<bounds[1]:raise ValueError(f'{name} outside supported physical bounds')
     if self.classification!='SYNTHETIC_VERIFICATION' and p.kind=='SYNTHETIC':raise ValueError('Synthetic properties cannot be promoted into a real/unverified profile')
   if l.extent_kind=='SYNTHETIC' and self.classification!='SYNTHETIC_VERIFICATION':raise ValueError('Synthetic extent cannot be promoted into a real/unverified profile')
  return self

class Load(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 B_m:float=Field(ge=.05,le=20)
 L_m:float=Field(ge=.05,le=20)
 N_n:float=Field(gt=0,le=1e8)
 reference_up_m:float=Field(ge=-1000,le=1000)
 source:str=Field(min_length=20,max_length=1000)
 idealization:Literal['uniform_flexible_rectangular_surface_patch']
 reviewed_assumptions:Literal[True]

def blockers(p:Profile):
 missing=[]
 if p.groundwater_depth_m is None:missing.append('Groundwater depth/observation UNKNOWN; no groundwater or effective-stress calculation')
 for l in p.layers:
  if l.extent=='UNKNOWN':missing.append(f'Layer {l.id}: bottom depth/extent UNKNOWN')
  for key in ['unit_weight_kn_m3','E_mpa','poisson']:
   if getattr(l,key) is None:missing.append(f'Layer {l.id}: {key} and sourced investigation evidence missing')
 return missing

def numerical(B,L,N,E,nu,angles=1024):
 """Independent 2D polar-area quadrature of point-load displacement kernel.

No rectangular closed-form influence factor is used. Midpoint angles and
8-point radial Gaussian quadrature integrate the prescribed traction cells.
"""
 phi=(np.arange(angles)+.5)*2*math.pi/angles
 R=np.minimum(B/2/np.abs(np.cos(phi)),L/2/np.abs(np.sin(phi)))
 g,weights=np.polynomial.legendre.leggauss(8)
 r=R[:,None]*(g[None,:]+1)/2
 dr=R[:,None]*weights[None,:]/2;dphi=2*math.pi/angles
 dA=r*dr*dphi
 traction=N/(B*L)
 force=float(np.sum(traction*dA))
 displacement=float(np.sum(traction*dA*(1-nu**2)/(math.pi*E*r)))
 return dict(angular_cells=angles,radial_points=8,integrated_area_m2=float(np.sum(dA)),integrated_load_n=force,centre_settlement_m=displacement,load_relative_error=abs(force/N-1))

def validate_domain(p:Profile,q:Load):
 if p.classification!='SYNTHETIC_VERIFICATION':raise ValueError('Actual project settlement BLOCKED: physical transfer and site applicability not validated')
 if len(p.layers)!=1 or p.layers[0].top_depth_m!=0 or p.layers[0].extent!='UNBOUNDED_IDEALIZATION':raise ValueError('Only explicitly unbounded single homogeneous half-space supported; no layered/finite-depth averaging')
 l=p.layers[0]
 if not l.E_mpa or not l.poisson:raise ValueError('Explicit sourced E and Poisson ratio required')
 if l.extent_kind!='SYNTHETIC' or l.E_mpa.kind!='SYNTHETIC' or l.poisson.kind!='SYNTHETIC':raise ValueError('First benchmark requires explicitly synthetic mechanical properties/extent')
 if abs(q.reference_up_m-p.ground_reference_up_m)>1e-9:raise ValueError('Surface load reference must match explicit ground plane; embedded footing unsupported')
 B,L,E,nu=q.B_m,q.L_m,l.E_mpa.value*1e6,l.poisson.value
 if max(B/L,L/B)>10:raise ValueError('Aspect ratio exceeds independently tested domain 1:10')
 return l

def calculate(p:Profile,q:Load):
 l=validate_domain(p,q)
 B,L,E,nu=q.B_m,q.L_m,l.E_mpa.value*1e6,l.poisson.value
 a,b=B/2,L/2;pressure=q.N_n/(B*L)
 influence=4*(a*math.asinh(b/a)+b*math.asinh(a/b))
 s=pressure*(1-nu**2)*influence/(math.pi*E)
 if s/min(B,L)>.01:raise ValueError('Displacement exceeds declared small-displacement domain s/min(B,L)<=0.01')
 refs=[numerical(B,L,q.N_n,E,nu,n) for n in [512,2048,8192]]
 if abs(refs[-1]['centre_settlement_m']/s-1)>3e-5 or refs[-1]['load_relative_error']>5e-5:raise ValueError('Independent surface-kernel integration did not meet verification tolerance')
 return dict(status='VERIFIED_SYNTHETIC',method='flexible-rectangle-centre-halfspace/1',centre_settlement_m=s,uniform_pressure_pa=pressure,applied_load_n=q.N_n,area_m2=B*L,force_balance_residual_n=pressure*B*L-q.N_n,E_pa=E,poisson=nu,influence_integral_m=influence,numerical_reference=refs,reference='https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/ltpp/05152/chapt2.cfm',formula='s_center=q(1-nu²)/(pi E) * 4[a asinh(b/a)+b asinh(a/b)], a=B/2, b=L/2. Derived by integrating Boussinesq surface point-load kernel (1-nu²)/(pi E r).',profile=p.model_dump(),load=q.model_dump(),winkler_stiffness='NOT_DERIVED',winkler_displacement='NOT_USED_OR_ADDED',engineering_approval='DISABLED',actual_project_analysis='BLOCKED',limitations=['Flexible uniformly loaded surface patch centre displacement only, not rigid-footing settlement','Homogeneous isotropic linear elastic infinite half-space; small displacement','No layer averaging, finite-depth correction, embedment, moments, contact loss, shear or nonlinear response','Unit weight and groundwater are stored references only; no pore-pressure/effective-stress or consolidation calculation','No bearing capacity, allowable settlement, construction recommendation, IS/US compliance or engineering safety approval'])

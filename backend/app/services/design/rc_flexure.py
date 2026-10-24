"""Declared synthetic rectangular-block nominal mechanics; no code factors or approval."""
import math
from typing import Literal
from decimal import Decimal,localcontext
from pydantic import Field,model_validator
from app.services.design.frame_loads import Strict
METHOD='RC_RECTANGULAR_NOMINAL_STRAIN_V1'
REFERENCE='https://www.fhwa.dot.gov/publications/research/infrastructure/bridge/05056/chapt3a.cfm'
class Input(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 method:Literal['RC_RECTANGULAR_NOMINAL_STRAIN_V1']
 demand_result_id:int=Field(gt=0)
 footing_id:str=Field(min_length=1,max_length=200)
 direction:Literal['EAST_WEST_SINGLE_BOTTOM_LAYER']
 layout:Literal['EQUAL_SPACING_OUTER_CENTERS_AT_COVER_PLUS_HALF_DIAMETER']
 section_width_mm:float=Field(gt=0,le=5000)
 thickness_mm:float=Field(gt=0,le=2000)
 concrete_fc_mpa:float=Field(ge=20,le=28)
 concrete_strength_basis:Literal['SYNTHETIC_CYLINDER_COMPRESSION']
 steel_fy_mpa:float=Field(ge=250,le=600)
 steel_E_mpa:float=Field(ge=180000,le=210000)
 cover_mm:float=Field(gt=0,le=200)
 end_cover_mm:float=Field(gt=0,le=200)
 bar_diameter_mm:float=Field(ge=8,le=40)
 bar_count:int=Field(ge=2,le=40,strict=True)
 effective_depth_mm:float=Field(gt=0,le=2000)
 alpha:Literal[0.85]
 beta:Literal[0.85]
 concrete_limit_strain:Literal[0.003]
 declared_steel_strain_limit:float=Field(gt=.003,le=.05)
 declared_action_knm:float=Field(gt=0,le=10000)
 design_action_basis:Literal['INDEPENDENT_SYNTHETIC_ACTION_NOT_CODE_FACTORED']
 comparison_basis:Literal['NOMINAL_EQUILIBRIUM_TARGET_ONLY_NO_STRENGTH_FACTOR']
 load_path:Literal['REVIEWED_HYPOTHETICAL_DIRECT_COLUMN_PATCH']
 reviewed_assumptions:Literal[True]
 country:Literal['UNSELECTED','INDIA','UNITED_STATES']
 jurisdiction:str=Field(max_length=200)
 standard:Literal['NONE','IS456','ACI318']
 edition:str=Field(max_length=32)
 concrete_source:str=Field(min_length=20,max_length=1200)
 steel_source:str=Field(min_length=20,max_length=1200)
 steel_E_source:str=Field(min_length=20,max_length=1200)
 cover_source:str=Field(min_length=20,max_length=1200)
 bar_source:str=Field(min_length=20,max_length=1200)
 effective_depth_source:str=Field(min_length=20,max_length=1200)
 arrangement_source:str=Field(min_length=20,max_length=1200)
 strain_model_source:str=Field(min_length=40,max_length=1500)
 design_action_source:str=Field(min_length=40,max_length=1500)
 load_path_source:str=Field(min_length=40,max_length=1500)
 @model_validator(mode='after')
 def supported(self):
  expected=self.thickness_mm-self.cover_mm-self.bar_diameter_mm/2
  if not math.isclose(self.effective_depth_mm,expected,rel_tol=0,abs_tol=1e-8):raise ValueError('Explicit d must equal h - bottom clear cover - bar diameter/2 for one bottom layer')
  usable=self.section_width_mm-2*(self.cover_mm+self.bar_diameter_mm/2)
  if usable<=0 or usable/(self.bar_count-1)<=self.bar_diameter_mm:raise ValueError('Bars collide or violate geometric envelope; detailing adequacy remains unverified')
  if self.effective_depth_mm>=self.thickness_mm or self.cover_mm>=self.thickness_mm/2:raise ValueError('Unsupported cover/depth geometry')
  if self.declared_steel_strain_limit<=self.steel_fy_mpa/self.steel_E_mpa:raise ValueError('Declared strain range must include yield; no extrapolation beyond it')
  if self.standard=='NONE':
   if self.country!='UNSELECTED' or self.jurisdiction or self.edition:raise ValueError('Choose a complete explicit jurisdiction/standard/edition context or leave all unselected')
  elif not self.jurisdiction.strip() or not self.edition.strip() or (self.standard=='IS456' and self.country!='INDIA') or (self.standard=='ACI318' and self.country!='UNITED_STATES'):raise ValueError('Standard requires explicit matching country, jurisdiction and edition; checks remain disabled')
  return self

def independent_neutral_axis(q,As):
 # Root of strain-compatible C(c)-T(c), independent of the yielded closed-form c.
 lo=1e-10;hi=q.effective_depth_mm
 for _ in range(100):
  c=(lo+hi)/2;eps=q.concrete_limit_strain*(q.effective_depth_mm-c)/c
  residual=q.alpha*q.concrete_fc_mpa*q.section_width_mm*q.beta*c-As*min(q.steel_E_mpa*eps,q.steel_fy_mpa)
  if residual>0:hi=c
  else:lo=c
 return (lo+hi)/2

def section(q,As):
 a=As*q.steel_fy_mpa/(q.alpha*q.concrete_fc_mpa*q.section_width_mm);c=a/q.beta
 if not 0<c<q.effective_depth_mm:raise ValueError('Neutral axis outside supported singly reinforced tension section')
 strain=q.concrete_limit_strain*(q.effective_depth_mm-c)/c;yield_strain=q.steel_fy_mpa/q.steel_E_mpa
 if strain<yield_strain-1e-12:raise ValueError('Non-yielding/over-reinforced section unsupported; do not assume steel reaches fy')
 if strain>q.declared_steel_strain_limit+1e-12:raise ValueError('Steel strain exceeds explicitly sourced supported range; extrapolation rejected')
 C=q.alpha*q.concrete_fc_mpa*q.section_width_mm*a;T=As*q.steel_fy_mpa;M=T*(q.effective_depth_mm-a/2)/1e6
 cn=independent_neutral_axis(q,As)
 if not math.isclose(c,cn,rel_tol=1e-10,abs_tol=1e-9):raise ValueError('Independent strain-equilibrium solution failed')
 return dict(steel_area_mm2=As,block_depth_a_mm=a,neutral_axis_c_mm=c,tension_strain=strain,yield_strain=yield_strain,steel_stress_mpa=q.steel_fy_mpa,compression_N=C,tension_N=T,force_residual_N=C-T,lever_arm_mm=q.effective_depth_mm-a/2,nominal_moment_knm=M,independent_c_mm=cn)

def calculate(q:Input):
 As=q.bar_count*math.pi*q.bar_diameter_mm**2/4;provided=section(q,As);K=q.alpha*q.concrete_fc_mpa*q.section_width_mm;target=q.declared_action_knm*1e6
 discriminant=q.effective_depth_mm**2-2*target/K
 if discriminant<=0:raise ValueError('Target outside singly reinforced nominal inversion domain')
 # Rationalized smaller root avoids cancellation for small moments.
 a_req=(2*target/K)/(q.effective_depth_mm+math.sqrt(discriminant));required_As=K*a_req/q.steel_fy_mpa;required=section(q,required_As)
 # Separate bisection in c on the supported yielded/strain-limited interval.
 lo=q.concrete_limit_strain*q.effective_depth_mm/(q.concrete_limit_strain+q.declared_steel_strain_limit);hi=q.concrete_limit_strain*q.effective_depth_mm/(q.concrete_limit_strain+q.steel_fy_mpa/q.steel_E_mpa)
 for _ in range(100):
  c=(lo+hi)/2;C=K*q.beta*c;moment=C*(q.effective_depth_mm-q.beta*c/2)
  if moment<target:lo=c
  else:hi=c
 c_inverse=(lo+hi)/2;As_inverse=K*q.beta*c_inverse/q.steel_fy_mpa
 if not math.isclose(required_As,As_inverse,rel_tol=1e-10):raise ValueError('Independent inverse steel-area verification failed')
 with localcontext() as ctx:
  ctx.prec=40;D=lambda x:Decimal(str(x));pi=Decimal('3.141592653589793238462643383279502884197');steel=D(q.bar_count)*pi*D(q.bar_diameter_mm)**2/4;T=steel*D(q.steel_fy_mpa);a=T/(D(q.alpha)*D(q.concrete_fc_mpa)*D(q.section_width_mm));hand=T*(D(q.effective_depth_mm)-a/2)/Decimal(1000000)
 if not math.isclose(float(hand),provided['nominal_moment_knm'],rel_tol=1e-13):raise ValueError('Independent Decimal resistance verification failed')
 spacing=(q.section_width_mm-2*(q.cover_mm+q.bar_diameter_mm/2))/(q.bar_count-1)
 return dict(method_version=METHOD,status='VERIFIED_SYNTHETIC_NOMINAL_MECHANICS_ONLY',inputs=q.model_dump(),provided=provided,required_nominal_equilibrium=required,independent_inverse_steel_mm2=As_inverse,spacing_mm=spacing,clear_spacing_mm=spacing-q.bar_diameter_mm,decimal_hand=dict(steel_area_mm2=str(steel),tension_N=str(T),a_mm=str(a),nominal_moment_knm=str(hand)),declared_action_knm=q.declared_action_knm,nominal_action_ratio=q.declared_action_knm/provided['nominal_moment_knm'],design_strength_knm=None,code_required_steel_mm2=None,design_strength_status='DISABLED_NO_STRENGTH_FACTOR',code_checks='DISABLED',engineering_approval='DISABLED',actual_footing_safety='BLOCKED',formula='Plane sections: eps_s=eps_cu*(d-c)/c. C=alpha*fc*b*beta*c; T=As*min(Es*eps_s,fy). Supported yielded case: a=As*fy/(alpha*fc*b), c=a/beta, Mn=As*fy*(d-a/2). As_target solves Mn=M_declared ONLY as nominal-equilibrium comparison. No phi or material factors.',reference=REFERENCE,reference_note='Archived FHWA-HRT-05-056, discussion of rectangular stress blocks and strain compatibility. Declared benchmark block/strain values only; no ACI/IS factors or compliance inferred.',limitations=['Synthetic cylinder strength and ideal elastic-perfectly-plastic steel only, no actual material evidence','One straight bottom reinforcement layer along East-West; no orthogonal mat, compression steel, prestress or axial section force','20<=fc<=28 MPa, 250<=fy<=600 MPa, declared steel strain <=0.05; reject non-yielding or excessive-strain states','Steel area for target is nominal-equilibrium mathematics, not code-required design steel','Declared action is independently sourced and is not a factored version of saved unfactored footing demand','No minimum steel, spacing/detailing, development, anchorage, cracking, one-way shear, punching or footing approval','Selecting country/standard/edition records context only; no automatic strength definitions, stress blocks or factors change'])

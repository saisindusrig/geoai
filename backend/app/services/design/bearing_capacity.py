"""Prandtl phi=0 surface infinite-strip bearing resistance, synthetic scope only."""
import math
from decimal import Decimal,localcontext
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict

REFERENCE='https://www.fhwa.dot.gov/engineering/geotech/pubs/010943.pdf'
class Input(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 method:Literal['PRANDTL_SURFACE_STRIP_PHI_ZERO_V1']
 geometry:Literal['INFINITE_STRIP']
 B_m:float=Field(ge=.05,le=20)
 foundation_depth_m:float=Field(ge=0,le=0)
 su_kpa:float=Field(gt=0,le=1000)
 phi_deg:float=Field(ge=0,le=0)
 unit_weight_kn_m3:float=Field(gt=0,le=40)
 strength_basis:Literal['TOTAL_STRESS_UNDRAINED']
 soil_extent:Literal['HOMOGENEOUS_INFINITE_IDEALIZATION']
 groundwater:Literal['EXCLUDED_SYNTHETIC_IDEALIZATION']
 groundwater_correction:Literal[False]
 loading:Literal['VERTICAL_CONCENTRIC_PER_UNIT_LENGTH']
 vertical_load_kn_per_m:float=Field(gt=0,le=100000)
 shear_kn_per_m:float=Field(ge=0,le=0)
 moment_knm_per_m:float=Field(ge=0,le=0)
 ground_slope_deg:float=Field(ge=0,le=0)
 interface:Literal['ROUGH_HORIZONTAL_STRIP_IDEALIZATION']
 reference_up_m:float=Field(ge=-1000,le=1000)
 resistance_method:Literal['GLOBAL_FS_ON_NET_ULTIMATE']
 global_factor:float=Field(gt=1,le=10)
 strength_source:str=Field(min_length=20,max_length=1000)
 geometry_source:str=Field(min_length=20,max_length=1000)
 groundwater_source:str=Field(min_length=20,max_length=1000)
 load_source:str=Field(min_length=20,max_length=1000)
 factor_source:str=Field(min_length=20,max_length=1000)
 applicability:str=Field(min_length=40,max_length=2000)
 reviewed_assumptions:Literal[True]

def independent_factors():
 """Central finite-difference limit of general Nq, without using Nc=pi+2."""
 rows=[]
 def nq(t):return math.exp(math.pi*math.tan(t))*math.tan(math.pi/4+t/2)**2
 for h in [.01,.001,.0001,.00001]:
  c=(nq(h)-nq(-h))/(2*math.tan(h))
  rows.append(dict(phi_step_rad=h,Nc_limit=c,Nq_zero=nq(0),Ngamma_zero=(nq(0)-1)*math.tan(1.4*0)))
 return rows

def calculate(q:Input):
 Nc=math.pi+2;Nq=1.;Ng=0.;overburden=q.unit_weight_kn_m3*q.foundation_depth_m
 net=q.su_kpa*Nc;gross=net+overburden*Nq+.5*q.unit_weight_kn_m3*q.B_m*Ng
 allowable_net=net/q.global_factor;allowable_gross=allowable_net+overburden
 refs=independent_factors()
 with localcontext() as ctx:
  ctx.prec=40;pi=Decimal('3.141592653589793238462643383279502884197');hand=(pi+2)*Decimal(str(q.su_kpa));hand_allow=hand/Decimal(str(q.global_factor))
 if abs(refs[-1]['Nc_limit']/Nc-1)>1e-7 or not math.isclose(gross,float(hand),rel_tol=1e-13):raise ValueError('Independent bearing factor/Decimal verification failed')
 applied=q.vertical_load_kn_per_m/q.B_m
 return dict(status='VERIFIED_SYNTHETIC_MECHANICS',method_version=q.method,inputs=q.model_dump(),factors=dict(Nc=Nc,Nq=Nq,Ngamma=Ng,shape=1,depth=1,inclination=1),overburden_kpa=overburden,ultimate_net_kpa=net,ultimate_gross_kpa=gross,ultimate_resistance_kn_per_m=gross*q.B_m,strength_only_allowable_net_kpa=allowable_net,strength_only_allowable_gross_kpa=allowable_gross,strength_only_allowable_kn_per_m=allowable_gross*q.B_m,applied_pressure_kpa=applied,applied_to_strength_reference_ratio=applied/allowable_gross,design_code_resistance='NOT_IMPLEMENTED',engineering_approval='DISABLED',actual_cad_capacity='BLOCKED',formula='Surface infinite strip: qu_net=su*(pi+2); Nq=1; Ngamma=0; q0=gamma*Df=0. qu_gross=qu_net. qallow_net=qu_net/declared global FS; qallow_gross=qallow_net+q0. Resistance per metre=q*B. Applied q=vertical line load/B.',independent_factors=refs,decimal_hand=dict(Nc=str(pi+2),ultimate_kpa=str(hand),strength_reference_kpa=str(hand_allow)),units='su,q in kPa=kN/m²; B,Df m; gamma kN/m³; vertical load/resistance kN/m; moment kN·m/m',reference=REFERENCE,reference_note='FHWA GEC 6 (2002), printed pp.51-53 / PDF pp.57-59, equations 5-2/3/4 and Table 5-1: strip factors Nc=2+pi, Nq=1, Ngamma=0 at phi=0; rounded table Nc=5.14. Corroborated by USACE EM 1110-2-2502 (1989), equations 5-3a/b/c/d.',published_rounded_factor_comparison=dict(Nc_rounded=5.14,ultimate_rounded_kpa=q.su_kpa*5.14,rounding_difference_kpa=net-q.su_kpa*5.14),limitations=['Ideal infinite surface strip only, not rectangular/square CAD footings','Homogeneous phi=0 total-stress idealization; explicit sourced synthetic su, no strength inferred from E or unit weight','Groundwater/pore-pressure corrections excluded; exclusion is not a site groundwater observation','No embedment, eccentricity, inclination, shear, layered soil, slope or adjacent footing effects','Strength-only allowable reference with declared global FS; settlement and site suitability not checked','Failure mechanism display is an illustrative schematic, not a computed collapse field','No Winkler/contact or elastic settlement result is used; no IS/US compliance or safety approval'])

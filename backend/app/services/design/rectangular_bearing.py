"""Narrow synthetic surface rectangle: FHWA GEC6 phi=0 shape correction."""
import math
from decimal import Decimal,localcontext
from typing import Literal
from pydantic import Field,model_validator
from app.services.design.frame_loads import Strict
from app.services.design.bearing_capacity import independent_factors,REFERENCE
class Input(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 method:Literal['FHWA_SURFACE_RECTANGLE_PHI_ZERO_V1']
 geometry:Literal['RECTANGLE','SQUARE']
 B_m:float=Field(ge=.05,le=20)
 foundation_depth_m:float=Field(ge=0,le=0)
 su_kpa:float=Field(gt=0,le=1000)
 phi_deg:float=Field(ge=0,le=0)
 unit_weight_kn_m3:float=Field(gt=0,le=40)
 strength_basis:Literal['TOTAL_STRESS_UNDRAINED']
 soil_extent:Literal['HOMOGENEOUS_INFINITE_IDEALIZATION']
 groundwater:Literal['EXCLUDED_SYNTHETIC_IDEALIZATION']
 groundwater_correction:Literal[False]
 loading:Literal['VERTICAL_CONCENTRIC_TOTAL']
 vertical_load_kn:float=Field(gt=0,le=100000)
 shear_east_kn:float=Field(ge=0,le=0)
 moment_east_knm:float=Field(ge=0,le=0)
 ground_slope_deg:float=Field(ge=0,le=0)
 interface:Literal['ROUGH_HORIZONTAL_RIGID_RECTANGLE']
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
 L_m:float=Field(ge=.05,le=80)
 ground_reference_up_m:float=Field(ge=-1000,le=1000)
 shear_north_kn:float=Field(ge=0,le=0)
 moment_north_knm:float=Field(ge=0,le=0)
 torsion_knm:float=Field(ge=0,le=0)
 eccentricity_east_m:float=Field(ge=0,le=0)
 eccentricity_north_m:float=Field(ge=0,le=0)
 total_load_includes_footing:Literal[True]
 load_path:Literal['SYNTHETIC_DIRECT_VERTICAL_AT_BEARING_PLANE']
 reference_source:str=Field(min_length=20,max_length=1000)
 @model_validator(mode='after')
 def supported(self):
  if not self.B_m<=self.L_m<5*self.B_m:raise ValueError('Require B <= L < 5B; long-strip transition not implemented')
  if self.geometry=='SQUARE' and not math.isclose(self.B_m,self.L_m,abs_tol=1e-12,rel_tol=0):raise ValueError('Square requires B=L; do not relabel rectangular geometry')
  if not math.isclose(self.reference_up_m,self.ground_reference_up_m,abs_tol=1e-10,rel_tol=0):raise ValueError('Surface method requires bearing plane = ground reference elevation')
  return self

def calculate(q:Input):
 nc=math.pi+2;ratio=q.B_m/q.L_m;sc=1+ratio/5;area=q.B_m*q.L_m
 ultimate=q.su_kpa*nc*sc;allow=ultimate/q.global_factor;applied=q.vertical_load_kn/area
 # Separately expanded, high-precision hand calculation; no call to the production formula.
 with localcontext() as ctx:
  ctx.prec=40;D=lambda x:Decimal(str(x));pi=Decimal('3.141592653589793238462643383279502884197');n=pi+2
  base=D(q.su_kpa)*n;increment=base*D(q.B_m)/(5*D(q.L_m));hand=base+increment
  area_mm2=D(q.B_m)*1000*D(q.L_m)*1000
  ultimate_N=(hand/1000)*area_mm2;pressure_N_mm2=(D(q.vertical_load_kn)*1000)/area_mm2
 refs=independent_factors()
 if not math.isclose(ultimate,float(hand),rel_tol=1e-13) or abs(refs[-1]['Nc_limit']/nc-1)>1e-7:raise ValueError('Independent factor and Decimal verification failed')
 return dict(status='VERIFIED_SYNTHETIC_FORMULA_IMPLEMENTATION',method_version=q.method,inputs=q.model_dump(),factors=dict(Nc=nc,Nq=1,Ngamma=0,sc=sc,sq=1,sgamma=1,depth=1,inclination=1),area_m2=area,aspect_B_over_L=ratio,overburden_kpa=0,ultimate_net_kpa=ultimate,ultimate_gross_kpa=ultimate,ultimate_resistance_kn=ultimate*area,strength_only_allowable_gross_kpa=allow,strength_only_allowable_kn=allow*area,applied_pressure_kpa=applied,applied_to_strength_reference_ratio=applied/allow,independent_factors=refs,decimal_hand=dict(base_strip_pressure_kpa=str(base),shape_increment_kpa=str(increment),ultimate_kpa=str(hand),ultimate_force_N=str(ultimate_N),applied_N_per_mm2=str(pressure_N_mm2)),formula='Nc=pi+2; sc=1+B/(5L); q_ult=su*Nc*sc; A=B*L; Q_ult=q_ult*A; q_reference=q_ult/FS; q_applied=N_total/A. Df=0, phi=0: surcharge and unit-weight terms zero.',reference=REFERENCE,reference_note='FHWA GEC 6 (2002), printed pp.51-56; Eq.5-2, Table5-1 and Table5-2 phi=0 row; sc=1+B/(5L), sq=sgamma=1. This is an implemented reference formulation, not AASHTO/IS/US code compliance.',units='B,L,elevations m; su and pressures kPa=kN/m2; total loads and resistance kN; moments kN*m; gamma kN/m3.',engineering_approval='DISABLED',actual_cad_capacity='BLOCKED',design_code_resistance='NOT_IMPLEMENTED',limitations=['Synthetic direct load at bearing plane only; no actual column/plate/footing transfer inferred','Surface rectangular/square rough horizontal footing; B<=L<5B; homogeneous phi=0 undrained total stress only','No layering, groundwater correction, embedment, inclination, eccentricity, shear, moments, slopes or nearby-footing effects','Strength-only reference uses a declared global factor; not site allowable capacity, settlement or safety','Shape correction is an established empirical formulation; hand verification is not a new physical validation experiment','Failure schematic is illustrative, not computed collapse, soil stress or deformation','Footing/anchor/concrete capacity, IS/US compliance, soil suitability and engineering approval disabled'])

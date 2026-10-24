"""Bounded foundation orchestration. Synthetic evidence, never engineering approval.

Existing mechanics are called rather than reimplemented. New code checks have
explicit edition/domain gates and remain separate from nominal mechanics.
"""
import math
from types import SimpleNamespace
from typing import Literal
from pydantic import Field,model_validator
from app.services.design.frame_loads import Strict
from app.services.design import footing_flexure,rc_flexure,soil_contact,rectangular_bearing,demand_transport

VERSION='FOUNDATION_INTEGRATED_V1'
ACI='https://www.concrete.org/portals/0/files/pdf/318-example-1_rf_r1.pdf'
IS='https://law.resource.org/pub/in/bis/S03/is.456.2000.pdf'
PROFILES={
 'ACI318-14':dict(country='UNITED_STATES',edition='2014',source=ACI,scope='Published square footing example; normalweight, no shear reinforcement'),
 'IS456-2000-A1A2':dict(country='INDIA',edition='2000; scan includes amendments 1 and 2',source=IS,scope='Bounded published provisions; not verification of later amendments'),
 'ACI318-19':dict(country='UNITED_STATES',edition='2019',source=ACI,scope='DISABLED: edition requirements not independently verified'),
 'ACI318-25':dict(country='UNITED_STATES',edition='2025',source=ACI,scope='DISABLED: edition requirements not independently verified'),
}
class Layer(Strict):
 diameter_mm:float=Field(ge=8,le=40)
 count:int=Field(ge=2,le=100,strict=True)
class Input(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']='SYNTHETIC_VERIFICATION'
 profile:Literal['ACI318-14','IS456-2000-A1A2','ACI318-19','ACI318-25']
 jurisdiction:str=Field(min_length=3,max_length=200)
 load_standard:Literal['MANUALLY_DECLARED_NO_AUTOMATIC_COMBINATIONS','ASCE7-16','ASCE7-22','IS875-1987']
 factored_column_kn:float=Field(gt=0,le=100000)
 factored_action_source:str=Field(min_length=30,max_length=1500)
 concrete_cylinder_mpa:float=Field(ge=20,le=28)
 concrete_cube_mpa:Literal[20,25,30,35,40]
 steel_yield_mpa:float=Field(ge=250,le=600)
 steel_modulus_mpa:float=Field(ge=180000,le=210000)
 concrete_unit_weight_kn_m3:float=Field(gt=0,le=30)
 steel_density_kg_m3:float=Field(gt=0,le=10000)
 cover_mm:float=Field(ge=10,le=200)
 aggregate_mm:float=Field(gt=0,le=80)
 east_west:Layer
 north_south:Layer
 stiffness_kn_m3:float=Field(gt=0,le=1e9)
 undrained_strength_kpa:float=Field(gt=0,le=1000)
 soil_global_factor:float=Field(gt=1,le=10)
 material_source:str=Field(min_length=30,max_length=1500)
 soil_source:str=Field(min_length=30,max_length=1500)
 detailing_source:str=Field(min_length=30,max_length=1500)
 reviewed_synthetic_patch:Literal[True]
 @model_validator(mode='after')
 def materials(self):
  if self.profile=='IS456-2000-A1A2' and self.steel_yield_mpa not in (415,500):raise ValueError('IS subset requires explicitly declared Fe415 or Fe500 deformed steel')
  return self

def disabled(reason):return dict(status='DISABLED',reason=reason)
def check(demand,resistance,unit,clause,**extra):
 return dict(status='WITHIN_IMPLEMENTED_CHECK' if demand<=resistance else 'EXCEEDS_IMPLEMENTED_CHECK',demand=demand,resistance=resistance,unit=unit,ratio=demand/resistance if resistance else None,clause=clause,**extra)

def rc_checks(q:Input,B,c,h,Mu,pressure):
 """B,c,h mm; Mu kN m; pressure factored NET kPa. Straight uniform mats.
 No holes/edges/moment transfer, prestress, shear steel, hooks, laps or dowels.
 """
 if c>=B or c<=0 or B<=0 or h<=0:raise ValueError('Positive square footing and smaller concentric column required')
 d1=h-q.cover_mm-q.east_west.diameter_mm/2
 d2=h-q.cover_mm-q.east_west.diameter_mm-q.north_south.diameter_mm/2
 if min(d1,d2)<=h/2:raise ValueError('Two bottom layers must fit in the tension half of the footing')
 ds=[d1,d2];d=min(ds);a=(B-c)/2
 if c+d>=B:raise ValueError('Interior punching perimeter must lie strictly inside footing')
 out=[];volume=B*B*h/1e9;steel_volume=0
 for name,bar,depth in zip(['EAST_WEST_LOWER','NORTH_SOUTH_UPPER'],[q.east_west,q.north_south],ds):
  As=bar.count*math.pi*bar.diameter_mm**2/4
  spacing=(B-2*q.cover_mm-bar.diameter_mm)/(bar.count-1);clear=spacing-bar.diameter_mm
  if clear<=0:raise ValueError('Reinforcement bars collide or do not fit')
  length=(B-2*q.cover_mm)/1000
  steel_volume+=As/1e6*length
  nominal_q=SimpleNamespace(effective_depth_mm=depth,steel_fy_mpa=q.steel_yield_mpa,steel_E_mpa=q.steel_modulus_mpa,alpha=.85,beta=.85,concrete_fc_mpa=q.concrete_cylinder_mpa,section_width_mm=B,concrete_limit_strain=.003,declared_steel_strain_limit=.05)
  try:nominal=rc_flexure.section(nominal_q,As)
  except ValueError as e:nominal=disabled(str(e))
  # The demand is the integral outside one full-width section at d from face.
  Vu=pressure*(B/1000)*max(a-depth,0)/1000
  row=dict(direction=name,effective_depth_mm=depth,steel_area_mm2=As,bar_diameter_mm=bar.diameter_mm,bar_count=bar.count,spacing_mm=spacing,clear_spacing_mm=clear,straight_length_m=length,nominal=nominal,one_way_demand_kn=Vu,one_way_section_from_center_mm=c/2+depth)
  if q.profile=='ACI318-14':
   # Exact conversion retains published US coefficients, avoids rounded SI equivalents.
   psi=q.concrete_cylinder_mpa/0.006894757293168;inch=25.4
   Vc=2*math.sqrt(psi)*(B/inch)*(depth/inch)*4.4482216152605/1000
   row['one_way']=check(Vu,.75*Vc,'kN','ACI318-14 22.5.5.1,21.2.1; normalweight, Vs=0',nominal_resistance_kn=Vc,strength_factor=.75)
   if nominal.get('tension_strain',0)>=.005:
    row['flexure']=check(Mu,.9*nominal['nominal_moment_knm'],'kN m','ACI318-14 22.2,21.2.2; tension-controlled only',strength_factor=.9)
    # Monotonic inverse on tension-controlled branch, using existing nominal solver.
    lo=1e-6;hi=.85*q.concrete_cylinder_mpa*B*.85*(.003*depth/.008)/q.steel_yield_mpa
    if Mu>.9*(hi*q.steel_yield_mpa*(depth-(hi*q.steel_yield_mpa/(.85*q.concrete_cylinder_mpa*B))/2)/1e6):row['required_steel']=disabled('Demand outside tension-controlled singly reinforced domain')
    else:
     for _ in range(90):
      mid=(lo+hi)/2;block=mid*q.steel_yield_mpa/(.85*q.concrete_cylinder_mpa*B)
      if .9*mid*q.steel_yield_mpa*(depth-block/2)/1e6<Mu:lo=mid
      else:hi=mid
     row['required_steel']=dict(flexural_mm2=(lo+hi)/2,minimum_mm2=.0018*B*h,status='GRADE60_MINIMUM_ONLY' if math.isclose(q.steel_yield_mpa,413.68543759008,rel_tol=1e-5) else 'MINIMUM_STEEL_DISABLED_NON_GRADE60',note='Minimum 0.0018 gross only for declared 60 ksi steel; no extrapolation to other grades')
     if row['required_steel']['status']=='GRADE60_MINIMUM_ONLY':
      required=max((lo+hi)/2,.0018*B*h)
      row['required_steel'].update(required_mm2=required,minimum_bar_count=math.ceil(required/(math.pi*bar.diameter_mm**2/4)))
      row['steel_area']=check(required,As,'mm2','ACI318-14 published example: 60 ksi minimum gross ratio 0.0018')
   else:row['flexure']=disabled('Nominal section unavailable or tensile strain below 0.005; no phi inferred')
   row['spacing']=disabled('Geometric spacing reported; full code spacing and durability provisions not verified')
   row['cover']=check(76.2,q.cover_mm,'mm','ACI published example: cast against earth 3 in; exposure qualification still required')
   # Restrict the published example development expression to its documented factors.
   if bar.diameter_mm>=25.4 and q.cover_mm+q.east_west.diameter_mm+q.north_south.diameter_mm<=304.8:
    cb=min(q.cover_mm+bar.diameter_mm/2,spacing/2);ratio=min(cb/bar.diameter_mm,2.5)
    ld=max(304.8,(3/40)*(q.steel_yield_mpa/.006894757293168)/(math.sqrt(psi)*ratio)*bar.diameter_mm)
    row['development']=check(ld,a-q.cover_mm,'mm','ACI318-14 25.4.2.2/25.4.2.4; uncoated bottom bars >=No8, normalweight, Ktr=0',required_mm=ld,available_mm=a-q.cover_mm)
   else:row['development']=disabled('Published development subset limited to uncoated bottom bars >=25.4mm and <=304.8mm concrete below')
  elif q.profile=='IS456-2000-A1A2':
   xu=.87*q.steel_yield_mpa*As/(.36*q.concrete_cube_mpa*B);limit=.48 if q.steel_yield_mpa==415 else .46
   Mr=.87*q.steel_yield_mpa*As*(depth-.42*xu)/1e6
   row['flexure']=check(Mu,Mr,'kN m','IS456:2000 38.1; design stress block, not nominal strength',neutral_axis_mm=xu,neutral_axis_limit_mm=limit*depth) if xu<=limit*depth else disabled('Over-reinforced IS design section; steel design stress not assumed')
   lo=0.;hi=.36*q.concrete_cube_mpa*B*limit*depth/(.87*q.steel_yield_mpa)
   maxM=.87*q.steel_yield_mpa*hi*(depth-.42*limit*depth)/1e6
   if Mu<=maxM:
    for _ in range(90):
     mid=(lo+hi)/2;x=.87*q.steel_yield_mpa*mid/(.36*q.concrete_cube_mpa*B)
     if .87*q.steel_yield_mpa*mid*(depth-.42*x)/1e6<Mu:lo=mid
     else:hi=mid
    required=max((lo+hi)/2,.0012*B*h)
    row['required_steel']=dict(status='SUPPORTED_DEFORMED_STEEL',flexural_mm2=(lo+hi)/2,minimum_mm2=.0012*B*h,required_mm2=required,minimum_bar_count=math.ceil(required/(math.pi*bar.diameter_mm**2/4)))
    row['steel_area']=check(required,As,'mm2','IS456 26.5.2.1,34.3; square uniform distribution')
   else:row['required_steel']=disabled('Demand exceeds singly reinforced limiting moment')
   row['one_way']=disabled('IS456 Amendment 1, PDF page12, corrects 34.2.4.1(a): soil cut at d, piles at d/2. Soil-cut demand is calculated. Table19 resistance, interpolation and applicability remain independently unvalidated; resistance stays disabled.')
   minclear=max(bar.diameter_mm,q.aggregate_mm+5)
   row['spacing']=dict(minimum_clear=check(minclear,clear,'mm','IS456 26.3.2; no placement exception used'),maximum_centres=check(spacing,min(3*depth,300),'mm','IS456 26.3.3(b)(1)'))
   row['cover']=check(max(50,bar.diameter_mm),q.cover_mm,'mm','IS456 26.4.2.2; footing minimum only, exposure/fire qualification excluded')
   row['diameter']=check(bar.diameter_mm,h/8,'mm','IS456 26.5.2.2')
   bond={20:1.2,25:1.4,30:1.5,35:1.7,40:1.9}[q.concrete_cube_mpa]*1.6
   ld=bar.diameter_mm*.87*q.steel_yield_mpa/(4*bond)
   row['development']=check(ld,a-q.cover_mm,'mm','IS456 26.2.1,26.2.1.1,34.2.4.3; full design stress, deformed straight bars, no curtailment',required_mm=ld,available_mm=a-q.cover_mm,bond_mpa=bond)
  else:
   for key in ('flexure','one_way','spacing','cover','development','required_steel'):row[key]=disabled('Selected edition requirements not verified; no compliance inferred from another edition')
  out.append(row)
 bo=4*(c+d);Vp=pressure*(B*B-(c+d)**2)/1e6
 if q.profile=='ACI318-14':
  psi=q.concrete_cylinder_mpa/.006894757293168;vc=min(4,6,40*d/bo+2)*math.sqrt(psi)
  Vn=vc*(bo/25.4)*(d/25.4)*4.4482216152605/1000
  punching=check(Vp,.75*Vn,'kN','ACI318-14 22.6.5.2; interior square patch, no unbalanced moment',nominal_resistance_kn=Vn,strength_factor=.75)
 elif q.profile=='IS456-2000-A1A2':punching=check(Vp,.25*math.sqrt(q.concrete_cube_mpa)*bo*d/1000,'kN','IS456 31.6.3.1,34.2.4.1(b); ks=1 for square patch; conservative smaller d')
 else:punching=disabled('Selected edition not verified')
 return dict(layers=out,punching={**punching,'demand_kn':Vp,'perimeter_mm':bo,'effective_depth_mm':d,'offset_from_column_face_mm':d/2},quantities=dict(concrete_gross_m3=volume,steel_volume_m3=steel_volume,steel_mass_kg=steel_volume*q.steel_density_kg_m3,concrete_net_displacement_m3=volume-steel_volume,note='Straight bottom mats only. No dowels, hooks, laps, chairs, waste, excavations or procurement allowance.'),methods=dict(units='B,c,h,d,bo,cover,spacing in mm; As mm2; strengths MPa=N/mm2; pressure kPa; actions kN/kN m',depth='EW d=h-cover-diaEW/2; NS d=h-cover-diaEW-diaNS/2. Orthogonal touching bottom layers, EW lower.',demands='a=(B-c)/2; Vu_oneway=q_u*(B/1000)*max(a-d,0)/1000; bo=4*(c+min(dEW,dNS)); Vu_punch=q_u*(B^2-(c+d)^2)/1e6. No unbalanced moment.',ACI_shear='Original IN-LB coefficients: Vc_1=2*sqrt(fc_psi)*b_in*d_in lbf; vc_p=min(4,2+4/beta,40*d/bo+2)*sqrt(fc_psi) psi; beta=1, lambda=1, phi_v=.75. Convert using 25.4mm/in and 4.4482216152605N/lbf.',ACI_flexure='Existing nominal section service, alpha=beta1=.85, epsilon_cu=.003, fc cylinder20..28MPa. phi=.9 only if epsilon_t>=.005. Existing nominal solver strain-domain ceiling .05 retained.',IS_flexure='T=.87fy*As; xu=T/(.36fck*b); Mdesign=T*(d-.42xu); xu/d <=.48 Fe415 or .46 Fe500. Cube fck is independently declared; no nominal/design conversion.',IS_punching='ks=min(.5+shortColumn/longColumn,1)=1; tau_design=.25*sqrt(fck); Vdesign=tau_design*bo*d/1000. Smaller orthogonal d used conservatively.',IS_development='Ld=dia*(.87fy)/(4*tau_bd); deformed tension tau_bd=1.6*[1.2,1.4,1.5,1.7,1.9] for M20/25/30/35/40. Straight available length from column face to end =a-cover; no hooks/curtailment/dowels.',references=[ACI,IS]),independent_benchmark_registry=dict(ACI_318_14_published_example=dict(B_in=144,c_in=24,h_in=30,upper_d_in=25.5,fc_psi=4000,net_qu_ksf=6.7,oneway_Vu_kip=231.15,oneway_phiVc_kip=348.3565070441,punching_Vu_kip=850.7953125,punching_phiVc_kip=957.9803943714,straight_Ld_in=28.4604989415,note='Independent Decimal arithmetic from declared inputs. Published rounded values: 231/348 kip and 851/958 kip. Tests also verify SI pressure integration, inverse flexure, separate cube/cylinder declarations and quantities.'),tests='backend/tests/test_foundation_system.py; backend/tests/test_foundation_system_api.py; see local validation logs for execution results'))

def calculate(q:Input,geometry,source_demand:footing_flexure.Input):
 B,L,h=geometry['footing_size_m'];c=source_demand.column_east_m
 if abs(B-L)>1e-9:raise ValueError('Integrated profile supports square footings only')
 # Retain exact verified source demand and recompute with its existing method.
 unfactored=footing_flexure.calculate(source_demand)
 factored_input=footing_flexure.Input(**{**source_demand.model_dump(),'column_load_kn':q.factored_column_kn,'uniform_net_pressure_kpa':q.factored_column_kn/(B*L),'load_source':q.factored_action_source,'pressure_source':'Independent factored column action divided by saved area; uniform net reaction benchmark'})
 factored=footing_flexure.calculate(factored_input)
 selfweight=B*L*h*q.concrete_unit_weight_kn_m3;gross=source_demand.column_load_kn+selfweight
 source=q.soil_source
 contact=soil_contact.calculate(soil_contact.Inputs(classification='SYNTHETIC_VERIFICATION',B_m=B,L_m=L,N_n=gross*1000,My_nm=0,k_n_m3=q.stiffness_kn_m3*1000,contact_law='uniform_linear_compression_only_winkler',reference_up_m=source_demand.bearing_reference_up_m,source=source,applicability='Synthetic homogeneous rigid footing, uniform Winkler stiffness, concentric service gross actions only.',reviewed=True))
 bearing=rectangular_bearing.calculate(rectangular_bearing.Input(classification='SYNTHETIC_VERIFICATION',method='FHWA_SURFACE_RECTANGLE_PHI_ZERO_V1',geometry='SQUARE',B_m=B,L_m=L,foundation_depth_m=0,su_kpa=q.undrained_strength_kpa,phi_deg=0,unit_weight_kn_m3=18,strength_basis='TOTAL_STRESS_UNDRAINED',soil_extent='HOMOGENEOUS_INFINITE_IDEALIZATION',groundwater='EXCLUDED_SYNTHETIC_IDEALIZATION',groundwater_correction=False,loading='VERTICAL_CONCENTRIC_TOTAL',vertical_load_kn=gross,shear_east_kn=0,shear_north_kn=0,moment_east_knm=0,moment_north_knm=0,torsion_knm=0,eccentricity_east_m=0,eccentricity_north_m=0,ground_slope_deg=0,interface='ROUGH_HORIZONTAL_RIGID_RECTANGLE',reference_up_m=source_demand.bearing_reference_up_m,ground_reference_up_m=source_demand.bearing_reference_up_m,resistance_method='GLOBAL_FS_ON_NET_ULTIMATE',global_factor=q.soil_global_factor,strength_source=source,geometry_source=source_demand.geometry_source,groundwater_source=source,load_source=source_demand.load_source,factor_source=source,applicability='Synthetic surface undrained homogeneous phi-zero square footing. No site soil capacity or settlement qualification.',reviewed_assumptions=True,total_load_includes_footing=True,load_path='SYNTHETIC_DIRECT_VERTICAL_AT_BEARING_PLANE',reference_source=source_demand.reference_source))
 transfer=demand_transport.transport([0,0,-source_demand.column_load_kn*1000],[0,0,0],[0,0,source_demand.load_reference_up_m],[0,0,source_demand.bearing_reference_up_m])
 rc=rc_checks(q,B*1000,c*1000,h*1000,factored['faces'][0]['full_cut_moment_knm'],q.factored_column_kn/(B*L))
 return dict(version=VERSION,status='VERIFIED_BOUNDED_SYNTHETIC_WORKFLOW',geometry=geometry,actions=dict(service_column_kn=source_demand.column_load_kn,service_footing_weight_kn=selfweight,service_gross_soil_kn=gross,factored_column_kn=q.factored_column_kn,factored_net_pressure_kpa=q.factored_column_kn/(B*L),factored_source=q.factored_action_source,load_combination_status='DISABLED_MANUAL_ACTION_ONLY',note='Uniform footing weight acts downward and cancels its own uniform upward reaction in NET RC cuts. Service soil checks use gross actions. No automatic load factors.'),transfer=transfer,contact=contact,bearing=bearing,unfactored_bending=unfactored,factored_bending=factored,rc=rc,profile=PROFILES[q.profile],limitations=['Synthetic reviewed column patch only; actual steel plate, anchors, dowels and connection capacity remain unverified','Winkler displacement is not consolidation/continuum settlement or a settlement acceptance check','Surface homogeneous undrained bearing idealization; no geotechnical site design or code capacity','No eccentric, biaxial, edge/corner, sloping/stepped, pile, opening, shear reinforcement or seismic detailing support','Durability, crack width, fatigue, construction tolerances and complete detailing are not established','Country/edition selection enables only listed verified subsets. ASCE/IS automatic load combinations disabled','Concrete cylinder and cube strengths are independent declarations; no conversion inferred'],engineering_approval='DISABLED',actual_foundation_safety='BLOCKED')

def alternatives(q,geometry,source):
 results=[]
 # Independent scenario calculations: never alter a model or authorize a proposal.
 for width,depth,extra in [(1,1,0),(1.25,1,0),(1,1.2,0),(1.25,1.2,0),(1,1,2),(1,1.2,2)]:
  B=source.B_m*width;h=source.thickness_m*depth
  s=footing_flexure.Input(**{**source.model_dump(),'B_m':B,'L_m':B,'thickness_m':h,'bearing_reference_up_m':source.load_reference_up_m-h,'uniform_net_pressure_kpa':source.column_load_kn/B**2})
  g={**geometry,'footing_size_m':[B,B,h],'bearing_up_m':s.bearing_reference_up_m}
  try:
   variant=Input(**{**q.model_dump(),'east_west':{**q.east_west.model_dump(),'count':q.east_west.count+extra},'north_south':{**q.north_south.model_dump(),'count':q.north_south.count+extra}})
   r=calculate(variant,g,s);results.append(dict(width_m=B,thickness_m=h,additional_bars_each_direction=extra,factored_moment_knm=r['factored_bending']['faces'][0]['full_cut_moment_knm'],settlement_mm=r['contact']['delta_down_m']*1000,punching=r['rc']['punching'],layers=r['rc']['layers'],quantities=r['rc']['quantities']))
  except ValueError as e:results.append(dict(width_m=B,thickness_m=h,status='OUTSIDE_DOMAIN',reason=str(e)))
 return dict(status='UNSAVED_COMPARISONS_REVIEW_REQUIRED',scenarios=results,authorization='No model changes. Use existing geometry preview/apply/save with engineering review; recalculate on new revision.')

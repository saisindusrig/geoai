"""Traceable demand interface and bounded compression-only pressure, no capacity design."""
import math
from decimal import Decimal
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict

UNSUPPORTED=['Moment-bearing distributions','Anchor tension and shear','Plate bending','Weld behavior','Footing reinforcement capacity','Soil capacity','Settlement','IS/ACI/AISC compliance','Physical connection and foundation safety']
class Selection(Strict):
 column_id:str
 plate_id:str
 footing_id:str
class Steel(Strict):
 material_name:str=Field(min_length=3,max_length=100)
 elastic_modulus_pa:float=Field(gt=1e6,le=1e13)
 yield_strength_mpa:float=Field(gt=0,le=2000)
 source:str=Field(min_length=5,max_length=300)
class Concrete(Strict):
 strength_mpa:float=Field(gt=0,le=200)
 strength_basis:Literal['cube','cylinder']
 source:str=Field(min_length=5,max_length=300)
class Reinforcement(Strict):
 status:Literal['not_defined_capacity_excluded','declared_unverified']
 information:str=Field(min_length=10,max_length=1000)
 source:str=Field(min_length=5,max_length=300)
class Soil(Strict):
 status:Literal['not_defined_soil_analysis_excluded','declared_unverified']
 assumptions:str=Field(min_length=10,max_length=1000)
 source:str=Field(min_length=5,max_length=300)
class Anchor(Strict):
 id:str=Field(min_length=1,max_length=100)
 position_enu_m:list[float]=Field(min_length=3,max_length=3)
 diameter_m:float=Field(gt=0,le=.1)
 embedment_m:float=Field(gt=0,le=2)
 source:str=Field(min_length=5,max_length=300)
class Anchors(Strict):
 status:Literal['not_defined_anchor_analysis_excluded','synthetic_engineer_declared_unverified']
 information:str=Field(min_length=10,max_length=1000)
 items:list[Anchor]=Field(max_length=8)
class Inputs(Selection):
 source_analysis_id:int=Field(gt=0)
 source_beam_id:str
 plate_dimensions_m:list[float]=Field(min_length=3,max_length=3)
 footing_dimensions_m:list[float]=Field(min_length=3,max_length=3)
 dimension_source:str=Field(min_length=5,max_length=400)
 steel:Steel
 concrete:Concrete
 reinforcement:Reinforcement
 soil:Soil
 anchors:Anchors
 contact_assumption:Literal['concentric_full_contact_massless_rigid_plate','rigid_plate_contact_feasibility']
 contact_reference_assumption:Literal['column_base_N_M_only_no_shear_translation']|None=None
 contact_source:str=Field(min_length=10,max_length=500)
 demand_scope:Literal['explicit_axial_component_only','full_reaction_concentric_only','actual_N_M_contact_feasibility']
 excluded_shear_moment_acknowledged:bool
 rigid_plate_idealization_approved:Literal[True]
 geometry_reviewed:Literal[True]
 purpose:Literal['SYNTHETIC_VERIFICATION_ONLY']

def geometry(doc,selection):
 q=Selection.model_validate(selection).model_dump()
 if doc.get('units')!='metric' or doc.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Metric local ENU geometry required')
 cs=doc.get('components',[]);by={c['id']:c for c in cs}
 if len(by)!=len(cs):raise ValueError('Duplicate component identities')
 if len(set(q.values()))!=3 or any(id not in by for id in q.values()):raise ValueError('Three distinct saved column, plate and footing references required')
 objects=[]
 for key,category in [('column_id','column'),('plate_id','base_plate'),('footing_id','foundation')]:
  c=by[q[key]];t=c.get('transform',{});size=c.get('geometry',{}).get('size',[]);pos=t.get('position',[])
  if c.get('category')!=category or c.get('geometry',{}).get('kind')!='box' or len(size)!=3 or len(pos)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in size+pos) or min(size)<=0:raise ValueError('Supported positive saved box geometry required')
  if t.get('rotation_deg')!=[0,0,0] or t.get('scale')!=[1,1,1]:raise ValueError('Rotated/scaled foundation geometry unsupported')
  if any(c.get('geometry',{}).get(k) or c.get('metadata',{}).get(k) for k in ('holes','openings','cutouts')):raise ValueError('Contact openings/holes or cutouts unsupported; nominal solid rectangles only')
  if key=='column_id' and c.get('parent_id'):raise ValueError('Independent saved column required')
  if key!='column_id' and (c.get('parent_id')!=q['column_id'] or q['column_id'] not in c.get('metadata',{}).get('references',[])):raise ValueError('Plate and footing must explicitly reference selected column; proximity is insufficient')
  status=c.get('metadata',{}).get('engineering_status','unknown')
  objects.append(dict(component_id=c['id'],name=c['name'],category=category,size_m=size,position_enu_m=pos,engineering_status=status,definition='CONCEPTUAL_PLACEHOLDER' if status!='engineering_defined_unverified' else 'ENGINEER_DEFINED_UNVERIFIED'))
 col,plate,foot=objects;cp,pp,fp=[x['position_enu_m'] for x in objects];csz,psz,fsz=[x['size_m'] for x in objects]
 if any(abs(cp[i]-pp[i])>1e-8 or abs(cp[i]-fp[i])>1e-8 for i in (0,1)):raise ValueError('Concentric column/plate/footing centers required; no silent geometry movement')
 if any(csz[i]>psz[i] or psz[i]>fsz[i] for i in (0,1)) or psz[2]>=min(psz[:2])/2:raise ValueError('Unsupported column footprint, plate or footing proportions')
 column_bottom=cp[2]-csz[2]/2;plate_top=pp[2]+psz[2]/2;plate_bottom=pp[2]-psz[2]/2;foot_top=fp[2]+fsz[2]/2
 if abs(column_bottom-plate_top)>1e-8 or abs(plate_bottom-foot_top)>1e-8:raise ValueError('Saved interface elevations contain a gap/overlap; contact cannot be assumed')
 saved_anchors=[c['id'] for c in cs if c.get('category') in ('anchor','anchor_bolt') and (c.get('parent_id') in q.values() or any(id in q.values() for id in c.get('metadata',{}).get('references',[])))]
 if saved_anchors:raise ValueError('Saved anchor geometry adapter not yet verified; do not substitute invented anchor positions')
 return dict(objects=objects,column_base_enu_m=[cp[0],cp[1],column_bottom],plate_contact_z_m=plate_bottom,contact_area_m2=psz[0]*psz[1],saved_anchor_ids=saved_anchors,anchor_geometry_status='NOT_SAVED',reinforcement_geometry_status='NOT_SAVED',coordinate_mapping='Local [East,North,Up] meters; source frame [X,Y] = [East,Up], positive moment about −North',physical_capacity='NOT_YET_VERIFIED')

def demands(source,beam_id,column_id):
 if source.get('status')!='VERIFIED':raise ValueError('Numerically verified source solver result required')
 f=next((f for f in source['frames'] if f['beam_id']==beam_id),None)
 if not f:raise ValueError('Unknown source frame')
 r=f['result'];g=r['physical_to_analytical_graph'];m=next((m for m in g['members'] if m['component_id']==column_id and m['axis']=='Up'),None)
 if not m:raise ValueError('Selected column not present in saved solver graph')
 a=next((a for a in r['reactions'] if a['node']==m['node_ids'][0]),None)
 if not a:raise ValueError('Actual fixed-base reaction absent')
 if not all(math.isfinite(a[k]) for k in ('fx_n','fy_n','moment_nm')):raise ValueError('Nonfinite source reactions')
 return dict(column_id=column_id,node=a['node'],compression_n=a['fy_n'],demand_on_interface_enu_force_n=[-a['fx_n'],0,-a['fy_n']],demand_on_interface_enu_moment_nm=[0,a['moment_nm'],0],horizontal_shear_east_n=-a['fx_n'],moment_about_negative_north_nm=-a['moment_nm'],support_reaction_si=a,solver_version=r['solver_version'],run_id=r['run_id'],source_frame_inputs=r['inputs'],source_model_revision_id=r.get('model_revision_id'),solver_input_sha256=r.get('input_file_sha256'),solver_artifact_sha256=r['artifact_sha256'],conversion='Interface action is opposite support reaction. N compression=Ry; VEast=−Rx; M about −North=−Rmoment.',reference_point='Saved column base / solver retained support node; full shear/moment translation to plate underside and footing is NOT YET VERIFIED.',verification_status='VERIFIED_NUMERICAL_DEMAND_NOT_CAPACITY')

def prepare(doc,inputs,demand):
 q=Inputs.model_validate(inputs).model_dump();g=geometry(doc,{k:q[k] for k in ('column_id','plate_id','footing_id')});col,plate,foot=g['objects']
 for declared,actual in [(q['plate_dimensions_m'],plate['size_m']),(q['footing_dimensions_m'],foot['size_m'])]:
  if not all(math.isfinite(v) and v>0 and math.isclose(v,w,rel_tol=0,abs_tol=1e-9) for v,w in zip(declared,actual)):raise ValueError('Explicit declared dimensions must match saved geometry; revise model to change dimensions')
 if q['column_id']!=demand['column_id']:raise ValueError('Demand column identity mismatch')
 if demand['compression_n']<=0:raise ValueError('Compression-only calculation rejects uplift or zero axial force')
 nonconcentric=abs(demand['horizontal_shear_east_n'])>1e-6 or abs(demand['moment_about_negative_north_nm'])>1e-6
 if q['demand_scope']=='full_reaction_concentric_only' and nonconcentric:raise ValueError('Full source demand has shear/moment: concentric compression-only distribution unsupported')
 if q['demand_scope']=='explicit_axial_component_only' and not q['excluded_shear_moment_acknowledged']:raise ValueError('Explicit acknowledgement of excluded full shear and moment required')
 if q['demand_scope']=='actual_N_M_contact_feasibility':
  if q['contact_assumption']!='rigid_plate_contact_feasibility' or q['contact_reference_assumption']!='column_base_N_M_only_no_shear_translation' or not q['excluded_shear_moment_acknowledged']:raise ValueError('Explicit N/M contact-assessment idealization, column-base reference and excluded shear acknowledgement required')
 elif q['contact_assumption']!='concentric_full_contact_massless_rigid_plate' or q['contact_reference_assumption'] is not None:raise ValueError('Concentric calculation requires its original contact idealization')
 anchors=q['anchors'];pp=plate['position_enu_m'];psz=plate['size_m'];fsz=foot['size_m'];fp=foot['position_enu_m']
 if anchors['status']=='not_defined_anchor_analysis_excluded' and anchors['items']:raise ValueError('Undefined anchor declaration cannot contain fabricated positions')
 if anchors['status']=='synthetic_engineer_declared_unverified' and not anchors['items']:raise ValueError('Explicit anchor geometry required for declared anchors')
 ids=[];locations=[]
 for a in anchors['items']:
  p=a['position_enu_m'];d=a['diameter_m'];embed=a['embedment_m'];ids.append(a['id']);locations.append(p)
  if abs(p[2]-(pp[2]+psz[2]/2))>1e-8 or any(abs(p[i]-pp[i])+d/2>psz[i]/2 for i in (0,1)) or p[2]-embed<fp[2]-fsz[2]/2 or embed<=psz[2]:raise ValueError('Anchor must lie in plate footprint with declared embedment inside footing')
  if all(abs(p[i]-col['position_enu_m'][i])<col['size_m'][i]/2+d/2 for i in (0,1)):raise ValueError('Anchor intersects column footprint')
 if len(set(ids))!=len(ids) or any(math.dist(a,b)<(anchors['items'][i]['diameter_m']+anchors['items'][j]['diameter_m'])/2 for i,a in enumerate(locations) for j,b in enumerate(locations) if j>i):raise ValueError('Duplicate or overlapping anchors')
 return dict(geometry=g,demand=demand,inputs=q,unsupported=[dict(check=k,status='NOT_YET_VERIFIED') for k in UNSUPPORTED],engineering_approval='DISABLED',scope='Isolated axial component only; full connection demand NOT VERIFIED' if nonconcentric else 'Concentric compression-only idealization; no capacity check',bearing_assumption='Uniform nominal gross rectangular plate contact; discrete anchors are location declarations only. Anchor-hole/contact-loss geometry not modeled; no actual contact stress solution.')

def pressure(force_n,length_m,width_m):
 if not all(math.isfinite(v) and v>0 for v in (force_n,length_m,width_m)):raise ValueError('Positive finite compression and dimensions required')
 A=length_m*width_m;p=force_n/A
 # Independent decimal N/mm² conversion and discrete area integration, not a capacity formula.
 dm=Decimal(str(length_m))*1000;wm=Decimal(str(width_m))*1000
 independent_mpa=float(Decimal(str(force_n))/(dm*wm));integrated=sum(p*A/64 for _ in range(64))
 if not math.isclose(p/1e6,independent_mpa,rel_tol=1e-12) or not math.isclose(integrated,force_n,rel_tol=1e-12):raise ValueError('Bearing units/equilibrium verification failed')
 return dict(compression_n=force_n,area_m2=A,pressure_pa=p,pressure_kpa=p/1000,pressure_mpa=p/1e6,independent_n_mm2=independent_mpa,integrated_reaction_n=integrated,equilibrium_error_n=integrated-force_n,formula='A=B×L [m²]; p=N/A [N/m²=Pa]; kPa=Pa/1000; MPa=Pa/1e6=N/mm²',verification='VERIFIED_ARITHMETIC_AND_EQUILIBRIUM',capacity_check='NOT_YET_VERIFIED')

def benchmark():
 # Independently worked known answer: 100 kN / (500 mm × 400 mm)=0.5 N/mm².
 r=pressure(100000,.5,.4)
 if not math.isclose(r['pressure_pa'],500000,abs_tol=1e-8) or not math.isclose(r['integrated_reaction_n'],100000,abs_tol=1e-6):raise ValueError('Known-answer benchmark failed')
 return dict(status='VERIFIED',reference='Synthetic concentric N=100 kN, B=500 mm, L=400 mm: p=100000/200000=0.5 N/mm²=500 kPa; pA=100 kN. No strength comparison.',result=r)
def calculate(prepared):
 q=prepared['inputs']
 if q['demand_scope']=='actual_N_M_contact_feasibility':
  from app.services.design import plate_contact
  c=plate_contact.assess(prepared['demand']['compression_n'],prepared['demand']['moment_about_negative_north_nm'],*q['plate_dimensions_m'][:2]);suite=plate_contact.benchmarks()
  return {**prepared,'bearing':pressure(prepared['demand']['compression_n'],*q['plate_dimensions_m'][:2]),'contact':c,'contact_benchmarks':suite,'status':'VERIFIED_CONTACT_FEASIBILITY_ONLY','scope':'Actual N/M contact feasibility at column base reference; horizontal shear transfer and physical capacity NOT YET VERIFIED','full_connection_status':'NOT_YET_VERIFIED','bearing_assumption':'Nominal gross rigid plate N/M law only within kern. No pressure distribution returned outside kern; no partial contact or anchor resistance invented. Shear reference-plane transport is excluded.','concrete_strength_used_in_calculation':False,'steel_strength_used_in_calculation':False,'soil_or_reinforcement_used_in_calculation':False}
 p=pressure(prepared['demand']['compression_n'],*q['plate_dimensions_m'][:2]);b=benchmark()
 return {**prepared,'bearing':p,'benchmark':b,'status':'VERIFIED_COMPRESSION_IDEALIZATION_ONLY','full_connection_status':'NOT_YET_VERIFIED','concrete_strength_used_in_calculation':False,'steel_strength_used_in_calculation':False,'soil_or_reinforcement_used_in_calculation':False}

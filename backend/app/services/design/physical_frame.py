"""Saved physical, three-member XZ frame: bounded geometry and explicit idealization."""
import math,json
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from app.services.design import elastic_frame as elastic,opensees_benchmark as common
from app.services.design import frame_loads

LIMITS=['Selected saved solid-rectangular members only; XZ plane, vertical columns and horizontal beam', 'Explicit rigid centerline/short planar massless rigid-offset joints and fixed column bases are idealizations, not verified connection or foundation capacities', 'Explicit horizontal/vertical column-head nodal loads, vertical uniform beam loads, and selected-member self-weight with complete density/gravity declarations only; no automatic slab distribution', 'Linear Euler-Bernoulli elasticity and explicitly factored linear superposition only: no shear deformation, out-of-plane, buckling, nonlinear or whole-building analysis', 'Engineering approval and IS/US code checks DISABLED']
FILES=elastic.FILES
class Section(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 component_id:str=Field(min_length=1,max_length=200)
 shape:Literal['solid_rectangle']
 elastic_modulus_pa:float=Field(gt=1e6,le=1e13)
 area_m2:float=Field(gt=1e-6,le=10)
 inertia_m4:float=Field(gt=1e-10,le=10)
 material_name:str=Field(min_length=3,max_length=100)
 material_source:str=Field(min_length=5,max_length=300)
 section_source:str=Field(min_length=5,max_length=300)
class Joint(BaseModel):
 model_config=ConfigDict(extra='forbid')
 column_id:str
 beam_id:str
 column_endpoint:Literal['top']
 beam_endpoint:Literal['left','right']
 behavior:Literal['rigid','rigid_offset']
 offset_m:list[float]|None=Field(default=None,min_length=2,max_length=2)
 idealization_approved:bool=False
 source:str=Field(min_length=5,max_length=300)
class Inputs(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 component_ids:list[str]=Field(min_length=3,max_length=3)
 sections:list[Section]=Field(min_length=3,max_length=3)
 connections:list[Joint]=Field(min_length=2,max_length=2)
 supports:Literal['both_column_bases_fixed']
 support_source:str=Field(min_length=5,max_length=300)
 load_pattern:Literal['equal_horizontal_column_head_loads']|None=None
 load_n:float|None=Field(default=None,gt=0,le=1e7)
 load_source:str|None=Field(default=None,min_length=5,max_length=300)
 load_cases:list[frame_loads.LoadCase]|None=Field(default=None,min_length=1,max_length=4)
 combination:frame_loads.Combination|None=None
 purpose:Literal['VERIFICATION_ONLY']
 elements_per_member:Literal[1,2,4]
 units:Literal['SI','N-mm']
 @model_validator(mode='after')
 def explicit_load_mode(self):
  if self.load_cases is None:
   if self.load_pattern is None or self.load_n is None or self.load_source is None or self.combination is not None:raise ValueError('Explicit legacy horizontal load or complete named load cases required')
  elif any(v is not None for v in (self.load_pattern,self.load_n,self.load_source)):raise ValueError('Choose named load cases or legacy horizontal load, not both')
  return self

def geometry(doc,ids,*,allow_rigid_offsets=False):
 if len(ids)!=3 or len(set(ids))!=3:raise ValueError('Select exactly two distinct columns and one beam')
 if doc.get('units')!='metric' or doc.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Saved geometry must use metric local ENU')
 lookup={c['id']:c for c in doc['components']}
 if any(i not in lookup for i in ids):raise ValueError('Missing saved component reference')
 cs=[lookup[i] for i in ids]
 for c in cs:
  t=c['transform'];size=c['geometry'].get('size',[])
  if c.get('parent_id') or c['geometry'].get('kind')!='box' or len(size)!=3 or any(not math.isfinite(v) or v<=0 for v in size):raise ValueError('Only independent positive solid rectangular boxes supported')
  if t.get('rotation_deg')!=[0,0,0] or t.get('scale')!=[1,1,1]:raise ValueError('Rotated/scaled or out-of-plane members unsupported')
  if len(t.get('position',[]))!=3 or any(not math.isfinite(v) for v in t['position']):raise ValueError('Invalid saved coordinates')
 columns=sorted([c for c in cs if c['category']=='column'],key=lambda c:c['transform']['position'][0]);beams=[c for c in cs if c['category']=='beam']
 if len(columns)!=2 or len(beams)!=1:raise ValueError('Slabs, foundations and other member categories unsupported: select two columns and one beam')
 left,right=columns;beam=beams[0];ordered=[left,beam,right];p=[c['transform']['position'] for c in ordered];sizes=[c['geometry']['size'] for c in ordered]
 origin=[p[0][0],p[0][1],p[0][2]-sizes[0][2]/2];L=p[2][0]-p[0][0];H=sizes[0][2];HR=sizes[2][2]
 unequal=not math.isclose(HR,H,abs_tol=1e-7,rel_tol=0)
 if unequal and (not doc.get('metadata',{}).get('unequal_frame_review') or not all(c['id'].startswith('drawing-cad:') for c in cs)):raise ValueError('Unequal-height columns require the dedicated CAD unequal-frame review scope')
 if unequal and abs(H-HR)>.5:raise ValueError('Unequal column height difference outside the validated 0.5 m domain')
 if not(0<L<=50 and 0<H<=50 and 0<HR<=50):raise ValueError('Unsupported frame span/height')
 expected=[[origin[0],origin[1],origin[2]+H/2],[origin[0]+L/2,origin[1],origin[2]+H],[origin[0]+L,origin[1],origin[2]+HR/2]]
 for a,b in zip([p[0],p[2]],[expected[0],expected[2]]):
  if any(not math.isclose(x,y,abs_tol=1e-7,rel_tol=0) for x,y in zip(a,b)):raise ValueError('Nonplanar or unequal-height columns unsupported')
 if not math.isclose(p[1][1],origin[1],abs_tol=1e-7,rel_tol=0) or not math.isclose(p[1][0],origin[0]+L/2,abs_tol=1e-7,rel_tol=0):raise ValueError('Nonplanar or asymmetric beam geometry unsupported')
 beam_ends=[[p[1][0]-sizes[1][0]/2-origin[0],p[1][2]-origin[2]],[p[1][0]+sizes[1][0]/2-origin[0],p[1][2]-origin[2]]]
 offsets=[[beam_ends[0][0],beam_ends[0][1]-H],[beam_ends[1][0]-L,beam_ends[1][1]-HR]]
 eccentric=any(abs(v)>1e-7 for r in offsets for v in r)
 if eccentric and not allow_rigid_offsets:raise ValueError('Centerline endpoints do not coincide: explicit approved rigid-offset idealization required; touching objects are not joints')
 if any(math.hypot(*r)>min(.5,.2*min(L,H,HR)) for r in offsets) or p[1][2]<=origin[2]:raise ValueError('Offsets outside the validated short planar rigid-arm domain')
 if any(sizes[k][2 if k!=1 else 0]<=max(sizes[k][j] for j in range(3) if j!=(2 if k!=1 else 0)) for k in range(3)):raise ValueError('Ambiguous member longitudinal axis')
 members=[]
 for index,c in enumerate(ordered):
  size=c['geometry']['size'];width,depth=(size[1],size[0]) if c['category']=='column' else (size[1],size[2])
  members.append(dict(component_id=c['id'],name=c['name'],position_enu_m=c['transform']['position'],size_m=size,axis='Up' if c['category']=='column' else 'East',length_m=size[2] if c['category']=='column' else sizes[1][0],centerline_endpoints_m=[[[0,0],[0,H]],beam_ends,[[L,0],[L,HR]]][index],solid_rectangle_area_m2=width*depth,solid_rectangle_inertia_m4=width*depth**3/12,node_ids=[[1,2],[2,3],[4,3]][index]))
  if c['id'].startswith('drawing-cad:'):
   from app.services.design.cad_frame import identity
   members[-1]['cad_source']=identity(c)
 connection_offsets=[dict(column_id=c['id'],beam_id=beam['id'],beam_endpoint=end,retained_node_id=node,offset_m=r,offset_length_m=math.hypot(*r),column_top_m=[x,h],beam_end_m=xy) for c,end,node,r,x,h,xy in zip(columns,['left','right'],[2,3],offsets,[0,L],[H,HR],beam_ends)]
 return dict(beam_offsets_m=offsets if eccentric else None,connection_offsets=connection_offsets,kind='physical_assembly',length_m=L,height_m=H,column_heights_m=[H,HR],unequal_heights=unequal,node_positions_m=[[0,0],[0,H],[L,HR],[L,0]],method_version='cad-planar-unequal/1' if unequal else 'physical-planar-equal/3',origin_enu_m=origin,coordinate_mapping='Analytical X = saved East - origin.E; Y = saved Up - origin.U; rotation about -North; physical North constant',members=members,component_ids=[c['id'] for c in ordered],candidate_joints=[dict(column_id=left['id'],beam_id=beam['id'],column_endpoint='top',beam_endpoint='left'),dict(column_id=right['id'],beam_id=beam['id'],column_endpoint='top',beam_endpoint='right')],geometric_tolerance_m=1e-7,note='Observed endpoints and offsets are geometry facts only. Explicit joint declarations required; no geometry snapping. Coincidence tolerance 1e-7 m; massless rigid arms retain the full saved beam elastic length, including overhangs, not an automatic clear-span or connection-capacity interpretation.')

def graph(doc,inputs):
 q=Inputs.model_validate(inputs).model_dump();g=geometry(doc,q['component_ids'],allow_rigid_offsets=any(j['behavior']=='rigid_offset' for j in q['connections']))
 sections={s['component_id']:s for s in q['sections']}
 if len(sections)!=3 or set(sections)!=set(q['component_ids']):raise ValueError('Exactly one explicit section/material record per selected physical component required')
 for m in g['members']:
  s=sections[m['component_id']]
  if not math.isclose(s['area_m2'],m['solid_rectangle_area_m2'],rel_tol=1e-8,abs_tol=1e-12) or not math.isclose(s['inertia_m4'],m['solid_rectangle_inertia_m4'],rel_tol=1e-8,abs_tol=1e-14):raise ValueError('Explicit solid section A/Iz must match saved dimensions and in-plane orientation')
  m['section']=s
 actual=[{k:j[k] for k in ('column_id','beam_id','column_endpoint','beam_endpoint')} for j in q['connections']]
 if sorted(actual,key=str)!=sorted(g['candidate_joints'],key=str):raise ValueError('Joint references must explicitly connect both beam ends to their corresponding column tops')
 for declared,observed in zip(sorted(q['connections'],key=lambda j:j['beam_endpoint']),g['connection_offsets']):
  nonzero=observed['offset_length_m']>1e-7
  if nonzero and declared['behavior']!='rigid_offset':raise ValueError('Every nonzero offset requires an explicit rigid-offset declaration')
  if declared['behavior']=='rigid_offset':
   if declared['idealization_approved'] is not True or declared['offset_m'] is None or any(not math.isfinite(v) for v in declared['offset_m']) or any(not math.isclose(a,b,rel_tol=0,abs_tol=1e-8) for a,b in zip(declared['offset_m'],observed['offset_m'])):raise ValueError('Approve each rigid-offset idealization and declare its exact observed signed vector in metres')
  elif declared['offset_m'] not in (None,[0,0]) or declared['idealization_approved']:raise ValueError('Centerline declaration cannot contain an offset approval or nonzero vector')
 if g['unequal_heights'] and q.get('load_cases') and not doc.get('metadata',{}).get('unequal_gravity_review'):raise ValueError('Unequal CAD frame milestone supports explicit horizontal column-head nodal loads only; distributed, gravity and superposition cases remain unvalidated for this extension')
 if g['unequal_heights'] and q.get('load_cases'):g['method_version']='cad-planar-unequal-gravity/1'
 g.update(joints=q['connections'],supports={'nodes':[1,4],'dofs':['ux','uy','rotation'],'source':q['support_source']},loads={'nodes':[2,3],'each_fx_n':q['load_n']/2,'source':q['load_source']} if q['load_cases'] is None else {'cases':frame_loads.normalize(q,g),'combination':q['combination']},nodes=[dict(id=i,position_m=xy,position_enu_m=[g['origin_enu_m'][0]+xy[0],g['origin_enu_m'][1],g['origin_enu_m'][2]+xy[1]]) for i,xy in enumerate(g['node_positions_m'],1)])
 return g

def run(inputs,document):
 q=Inputs.model_validate(inputs).model_dump();g=graph(document,q);first=q['sections'][0]
 solver_inputs=dict(kind='portal',length_m=g['length_m'],height_m=min(g['column_heights_m']),elastic_modulus_pa=first['elastic_modulus_pa'],area_m2=first['area_m2'],inertia_m4=first['inertia_m4'],load_n=q['load_n'] if q['load_cases'] is None else 0,material_source=first['material_source'],section_source=first['section_source'],load_source=q['load_source'] or 'Explicit named SI load cases; legacy horizontal load disabled',joints='rigid',restraints='fixed_base',purpose=q['purpose'],elements_per_member=q['elements_per_member'],units=q['units'])
 if q['load_cases'] is None:
  result=elastic.run(solver_inputs,assembly_graph=g)
 else:
  cases=g['loads']['cases'];case_results=[]
  def solve_case(case):
   uniform={i+1:case['uniform_global_by_component_n_per_m'][m['component_id']] for i,m in enumerate(g['members'])}
   r=elastic.run(solver_inputs,assembly_graph=g,verification_loads=case['nodal_loads_si'],verification_uniform=uniform)
   r.update(case_name=case['name'],case_kind='INDEPENDENT_LINEAR_LOAD_CASE',applied_loads=case,physical_to_analytical_graph=g)
   if g['unequal_heights']:
    from app.services.design.unequal_frame import verify
    r['unequal_frame_independent_verification']=verify(document,q,r)
    if not r['unequal_frame_independent_verification']['passed']:raise ValueError('Independent unequal gravity load case verification failed')
   (common.ARTIFACTS/r['run_id']/'manifest.json').write_text(json.dumps(r,indent=2))
   if r['status']!='VERIFIED':raise ValueError('Named load case failed: '+str(r.get('error')))
   return r
  for case in cases:case_results.append(solve_case(case))
  result=case_results[0].copy()
  if q['combination']:
   combined=frame_loads.combine(cases,q['combination']);result=solve_case(combined);verification=verify_superposition(result,case_results,q['combination'])
   if not verification['passed']:raise ValueError('Independent linear superposition failed')
   result.update(case_kind='LINEAR_SUPERPOSITION_VERIFIED_AGAINST_COMBINED_SOLVE',superposition_verification=verification)
  result['load_case_results']=case_results

 if g.get('beam_offsets_m'):result['rigid_offset_method']='OpenSees geomTransf Linear -jntOffset; retained column-head nodes, elastic beam ends at actual saved centerlines; Mretained=Mend+rx Fy-ry Fx; uxend=uxretained-ry theta, uyend=uyretained+rx theta'
 if g['unequal_heights']:
  from app.services.design.unequal_frame import verify
  result['unequal_frame_independent_verification']=verify(document,q,result)
  if not result['unequal_frame_independent_verification']['passed']:raise ValueError('Independent full nonsymmetric geometry verification failed')
 result.update(engineering_approval='DISABLED',code_checks='DISABLED',inputs=q,inputs_sha256=common.digest(q),physical_to_analytical_graph=g,limitations=LIMITS)
 (common.ARTIFACTS/result["run_id"]/"manifest.json").write_text(json.dumps(result,indent=2))
 return result


def verify_superposition(combined,cases,combination):
 pairs=[(next(r for r in cases if r['case_name']==f['case_name']),f['factor']) for f in combination['factors']]
 groups=[]
 for name,key in [('nodes','displacement_m'),('elements','local_end_forces_si')]:
  for i,row in enumerate(combined[name]):
   for j,v in enumerate(row[key]):groups.append((v,sum(r[name][i][key][j]*factor for r,factor in pairs),name))
 for i,row in enumerate(combined['reactions']):
  for key in ('fx_n','fy_n','moment_nm'):groups.append((row[key],sum(r['reactions'][i][key]*factor for r,factor in pairs),'reactions'))
 for i,e in enumerate(combined['elements']):
  for j,s in enumerate(e['samples']):
   for key in ('moment_nm','shear_n','axial_n'):
    groups.append((s[key],sum(r['elements'][i]['samples'][j][key]*factor for r,factor in pairs),'diagrams'))
   for k,v in enumerate(s['displacement_m']):groups.append((v,sum(r['elements'][i]['samples'][j]['displacement_m'][k]*factor for r,factor in pairs),'sample_displacement'))
 for i,t in enumerate(combined.get('rigid_offset_transfers',[])):
  for key in ('offset_moment_nm',):groups.append((t[key],sum(r['rigid_offset_transfers'][i][key]*factor for r,factor in pairs),'offset_moment'))
 return dict(passed=all(math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-10 if label in ('nodes','sample_displacement') else 1e-6) for a,b,label in groups),factors=combination['factors'],checks=len(groups),max_errors={label:max(abs(a-b) for a,b,k in groups if k==label) for label in {k for _,_,k in groups}},method='Actual independently solved cases multiplied by explicitly declared factors; compared with a separate actual combined-load OpenSees solve including nodal/sample displacement, local forces, diagrams, reactions and offset moments. Linear elastic superposition only; no code combination or approval.')

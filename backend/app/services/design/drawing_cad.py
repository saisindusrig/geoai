"""Explicit supervised envelope mapping; no structural sections or analytical joints inferred."""
from copy import deepcopy
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict
from app.services.design import opensees_benchmark as common

TAG='reviewed-dxf-parametric/1'
LAYERS={'COLUMNS','BEAMS','SLAB','FOOTINGS_CONCEPT'}
ROLES={'COLUMN':'column','BEAM':'beam','SLAB':'slab','FOOTING_OUTLINE':'foundation'}
MISSING=['Structural sections A/I, material E/fy/strength and design grade are not supplied by nominal envelopes','Loads, supports and analytical joint behavior require independent engineering input/review','Reinforcement, connections, anchors, foundation/soil capacity and code compliance NOT VERIFIED']
class Item(Strict):
 entity_id:str
 operation:Literal['create','update_generated']='create'
 role:Literal['COLUMN','BEAM','SLAB','FOOTING_OUTLINE']|None=None
 name:str=Field(default='',max_length=120)
 center_east_mm:float|None=Field(default=None,ge=-1e7,le=1e7)
 center_north_mm:float|None=Field(default=None,ge=-1e7,le=1e7)
 size_east_mm:float|None=Field(default=None,gt=0,le=500000)
 size_north_mm:float|None=Field(default=None,gt=0,le=500000)
 bottom_mm:float|None=Field(default=None,ge=-100000,le=100000)
 top_mm:float|None=Field(default=None,ge=-100000,le=100000)
 material_name:str=Field(default='',max_length=200)
 material_source:str=Field(default='',max_length=600)
 geometry_source:str=Field(default='',max_length=600)
 plan_policy:Literal['MATCH_REVIEWED_PLAN','EXPLICIT_GEOMETRY_OVERRIDE']='MATCH_REVIEWED_PLAN'
 override_reason:str=Field(default='',max_length=600)
 connectivity:Literal['EXPLICIT_ATTACHMENTS','ISOLATED_GEOMETRY_NO_ANALYSIS']|None=None
 connectivity_source:str=Field(default='',max_length=600)
class Connection(Strict):
 id:str=Field(min_length=3,max_length=80)
 from_entity_id:str
 to_entity_id:str
 point_mm:list[float]=Field(min_length=3,max_length=3)
 behavior:Literal['DECLARED_GEOMETRIC_ATTACHMENT_NOT_ANALYTICAL_JOINT']
 source:str=Field(min_length=10,max_length=600)
class Inputs(Strict):
 classification:Literal['SYNTHETIC_VERIFICATION']
 items:list[Item]=Field(min_length=1,max_length=20)
 connections:list[Connection]=Field(default_factory=list,max_length=60)
 reviewed_by:str=Field(default='',max_length=120)
 geometry_only_no_analysis:bool=False

def generated_id(e):return 'drawing-cad:'+e['id'].removeprefix('dxf:')
def rectangle(e):
 if e['layer'] not in LAYERS or e['kind'] not in ['LWPOLYLINE','POLYLINE'] or not e.get('closed'):return False
 p=e.get('points_m',[])
 if len(p)!=4:return False
 xs=sorted(set(round(v[0],10) for v in p));ys=sorted(set(round(v[1],10) for v in p))
 return len(xs)==len(ys)==2 and len(set((round(v[0],10),round(v[1],10)) for v in p))==4 and all(abs(p[i][0]-p[(i+1)%4][0])<1e-10 or abs(p[i][1]-p[(i+1)%4][1])<1e-10 for i in range(4))
def digest(value):
 def normalize(v):
  if isinstance(v,float) and v.is_integer():return int(v)
  if isinstance(v,list):return [normalize(x) for x in v]
  if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
  return v
 return common.digest(normalize(value))
def component_hash(c):return digest({k:c.get(k) for k in ['id','parent_id','name','category','geometry','transform','material','quantity','metadata'] if k!='metadata'})
def is_generated(c):return c.get('id','').startswith('drawing-cad:')

def build(source,review,document,inputs):
 q=Inputs.model_validate(inputs).model_dump()
 if source['classification']!='SYNTHETIC_VERIFICATION':raise ValueError('This milestone supports synthetic verification drawings only')
 entities={e['id']:e for e in source['entities']};corrections={c['entity_id']:c for c in review['inputs']['corrections']};existing={c['id']:c for c in document['components']};ids=[];missing=[];components=[]
 def need(path,why):missing.append(dict(path=path,reason=why))
 if len(q['reviewed_by'].strip())<3:need('reviewed_by','Explicit reviewer attribution required; not engineering approval')
 if not q['geometry_only_no_analysis']:need('geometry_only_no_analysis','Acknowledge envelope geometry only, no solver or safety approval')
 for item in q['items']:
  id=item['entity_id'];ids.append(id);e=entities.get(id)
  if not e or not rectangle(e):raise ValueError('Only known axis-aligned rectangular column/beam/slab/footing source outlines supported; circles, notes, stairs and plates blocked')
  cid=generated_id(e);current=existing.get(cid)
  if item['operation']=='create' and current:raise ValueError('Duplicate source entity: generated component already exists; explicitly select update_generated')
  if item['operation']=='update_generated' and (not current or current.get('metadata',{}).get('drawing_cad',{}).get('generator')!=TAG):raise ValueError('Only previously generated CAD components may be updated; original context members are protected')
  prefix=id+'.'
  for field in ['role','center_east_mm','center_north_mm','size_east_mm','size_north_mm','bottom_mm','top_mm','connectivity']:
   if item[field] is None:need(prefix+field,'Explicit value required; never inferred from the plan')
  for field in ['name','material_name','material_source','geometry_source','connectivity_source']:
   if len(item[field].strip())<(3 if field in ['name','material_name'] else 10):need(prefix+field,'Explicit synthetic identification/source required; no invented material or load path')
  if item['top_mm'] is not None and item['bottom_mm'] is not None and item['top_mm']<=item['bottom_mm']:raise ValueError('Top elevation must be greater than bottom elevation')
  if any(item[k] is None for k in ['role','center_east_mm','center_north_mm','size_east_mm','size_north_mm','bottom_mm','top_mm']):continue
  bounds=e['plan_bounds_m'];corr=corrections.get(id,{});width,length=[v*1000 for v in e['plan_dimensions_m']]
  if corr.get('reviewed_dimensions_mm'):width,length=corr['reviewed_dimensions_mm']
  expected=[(bounds[0]+bounds[2])*500,(bounds[1]+bounds[3])*500,width,length]
  actual=[item[k] for k in ['center_east_mm','center_north_mm','size_east_mm','size_north_mm']]
  role_match={'COLUMN':'COLUMN','BEAM':'BEAM','SLAB':'SLAB','FOOTING_OUTLINE':'FOUNDATION'}[item['role']]
  differs=any(abs(a-b)>1e-6 for a,b in zip(actual,expected)) or corr.get('role','UNVERIFIED') not in ['UNVERIFIED',role_match]
  if item['plan_policy']=='MATCH_REVIEWED_PLAN' and differs:raise ValueError('Entered plan geometry/role differs from unchanged reviewed reference; explicit override and source reason required')
  if item['plan_policy']=='EXPLICIT_GEOMETRY_OVERRIDE' and len(item['override_reason'].strip())<20:need(prefix+'override_reason','Explain the explicit geometry deviation without changing original drawing/corrections')
  color={'COLUMN':'#80B7DC','BEAM':'#A7C6DE','SLAB':'#BECBD3','FOOTING_OUTLINE':'#8298AC'}[item['role']]
  c=dict(id=cid,parent_id=None,name=item['name'],category=ROLES[item['role']],visible=True,locked=False,geometry=dict(kind='box',size=[item['size_east_mm']/1000,item['size_north_mm']/1000,(item['top_mm']-item['bottom_mm'])/1000]),transform=dict(position=[item['center_east_mm']/1000,item['center_north_mm']/1000,(item['top_mm']+item['bottom_mm'])/2000],rotation_deg=[0,0,0],scale=[1,1,1]),material=dict(name=item['material_name'],color=color,roughness=.8,metalness=0),quantity=dict(included=False),metadata=dict(engineering_status='SYNTHETIC_UNVERIFIED_ENVELOPE',drawing_cad=dict(generator=TAG,source_entity_id=id,source_sha256=source['source_sha256'],classification='SYNTHETIC_VERIFICATION',input=item,representation='PARAMETRIC_BOX_ENVELOPE_NOT_ENGINEERING_SECTION',missing_engineering_inputs=MISSING)))
  c['metadata']['drawing_cad']['component_sha256']=component_hash(c)
  if current and component_hash(current)==component_hash(c) and {k:v for k,v in current['metadata']['drawing_cad']['input'].items() if k!='operation'}=={k:v for k,v in item.items() if k!='operation'}:c=deepcopy(current)
  components.append(c)
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate entities in proposal rejected')
 available={c['metadata']['drawing_cad']['source_entity_id']:c for c in document['components'] if is_generated(c) and c.get('metadata',{}).get('drawing_cad',{}).get('source_sha256')==source['source_sha256']};available.update({c['metadata']['drawing_cad']['source_entity_id']:c for c in components})
 edge_ids=[];pairs=[];connected=set()
 for edge in q['connections']:
  a,b=edge['from_entity_id'],edge['to_entity_id'];edge_ids.append(edge['id']);pairs.append(tuple(sorted([a,b])))
  if a==b or a not in available or b not in available:raise ValueError('Connection references must identify distinct proposed or existing generated source entities')
  if any(abs(v)>1e7 for v in edge['point_mm']):raise ValueError('Connection point outside bounded local coordinates')
  for id in [a,b]:
   c=available[id];p=c['transform']['position'];size=c['geometry']['size']
   if any(abs(edge['point_mm'][i]/1000-p[i])>size[i]/2+1e-9 for i in range(3)):raise ValueError('Declared attachment point does not lie in both entered envelopes; no touching/connection inferred')
  connected.update([a,b])
 if len(edge_ids)!=len(set(edge_ids)) or len(pairs)!=len(set(pairs)):raise ValueError('Duplicate connection identities/pairs rejected')
 for item in q['items']:
  if item['connectivity']=='EXPLICIT_ATTACHMENTS' and item['entity_id'] not in connected:need(item['entity_id']+'.connections','Explicit attachment reference and point required, not inferred from overlap')
 for id,c in available.items():
  if id not in ids and c['metadata']['drawing_cad']['input'].get('connectivity')=='EXPLICIT_ATTACHMENTS' and id not in connected:need(id+'.connections','Retain/review existing explicit attachment declarations when modifying this assembly')
 candidate=deepcopy(document)
 candidate.get('structural_layout',{}).pop('approval',None)
 if not missing:
  mapped={c['id']:c for c in components};candidate['components']=[mapped.pop(c['id'],c) for c in candidate['components']]+list(mapped.values())
  candidate.setdefault('metadata',{}).pop('cad_geometry_authorization_id',None)
  candidate['metadata']['drawing_cad_model']=dict(generator=TAG,source_sha256=source['source_sha256'],inputs=q,engineering_approval='DISABLED',analysis_status='BLOCKED_NO_VERIFIED_SECTIONS_LOADS_OR_ANALYTICAL_JOINTS')
 return dict(status='BLOCKED_MISSING_GEOMETRY_INPUTS' if missing else 'PREVIEW_READY_GEOMETRY_ONLY',inputs=q,missing=missing,components=components if not missing else [],proposed_document=candidate if not missing else None,connections=q['connections'],source_classification='SYNTHETIC_VERIFICATION',engineering_approval='DISABLED',limitations=MISSING,unit_mapping='Explicit mm values / 1000 → local ENU metres; source outlines/corrections retained unchanged')

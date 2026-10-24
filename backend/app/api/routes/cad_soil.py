"""Owned immutable demand links and synthetic footing benchmark, no invented soil input."""
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field,model_validator
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.physical_frames import context
from app.api.routes import slab_transfers,engineering_study
from app.services.design import drawing_cad as cad,footing_bearing
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/cad-soil',tags=['engineering'])

class EngineeringInputs(Strict):
 classification:str=Field(pattern=r'^(MEASURED|MANUFACTURER_DATA|ENGINEER_DECLARED|SYNTHETIC_VERIFICATION|UNVERIFIED)$')
 footing_dimensions_m:list[float]|None=Field(default=None,min_length=3,max_length=3)
 dimension_source:str=''
 concrete_strength_mpa:float|None=Field(default=None,gt=0,le=200)
 concrete_source:str=''
 soil_bearing_input_kpa:float|None=Field(default=None,gt=0,le=10000)
 soil_source:str=''
 contact_reference_up_m:float|None=Field(default=None,ge=-100,le=100)
 reference_source:str=''
 @model_validator(mode='after')
 def sourced(self):
  import math
  if self.footing_dimensions_m is not None and any(not math.isfinite(v) or v<=0 for v in self.footing_dimensions_m):raise ValueError('Positive reviewed footing dimensions required')
  for value,source in [(self.footing_dimensions_m,self.dimension_source),(self.concrete_strength_mpa,self.concrete_source),(self.soil_bearing_input_kpa,self.soil_source),(self.contact_reference_up_m,self.reference_source)]:
   if value is not None and len(source.strip())<10:raise ValueError('Every entered engineering value requires explicit source evidence')
  return self

class Mapping(Strict):
 column_id:str
 footing_id:str|None=None
 source:str=Field(min_length=10,max_length=400)
 reviewed:bool
 engineering_inputs:EngineeringInputs|None=None
class Review(Strict):
 model_revision_id:int=Field(gt=0)
 mappings:list[Mapping]=Field(min_length=4,max_length=4)
class Authorize(Strict):
 review_id:int=Field(gt=0)
 review_sha256:str=Field(min_length=64,max_length=64)
 authorize_benchmark:bool

def audit_data(pid,rid,db,user):
 rev,_=context(pid,rid,db,user);meta=rev.document_json.get('metadata',{}).get('cad_soil_path_review')
 if not meta:raise HTTPException(422,'Separate CAD foundation review required')
 source=slab_transfers.owned(meta['source_project_id'],meta['source_analysis_id'],slab_transfers.RUN,db,user)
 if slab_transfers.output(source,db,user)['status']!='VERIFIED':raise HTTPException(409,'Original saved structural evidence stale or unavailable')
 original=db.get(ModelRevision,source.model_revision_id);by={c['id']:c for c in rev.document_json['components']};original_by={c['id']:c for c in original.document_json['components']};rows=[]
 participating=source.result_json['cad_source_provenance']['component_sources']
 if any(by.get(id)!=original_by[id] for id in participating):raise HTTPException(409,'Copied slab/frame geometry changed; original reactions cannot be reused')
 from app.api.routes.drawing_cad import source_context
 _,src,drawing_review=source_context(pid,rid,db,user)
 for frame in source.result_json['frames']:
  g=frame['result']['physical_to_analytical_graph']
  for reaction in frame['result']['reactions']:
   m=next(m for m in g['members'] if m['node_ids'][0]==reaction['node']);id=m['component_id'];c=by.get(id)
   if c!=original_by[id]:raise HTTPException(409,'Copied column geometry differs from exact source reaction revision')
   p=c['transform']['position'];z=p[2]-c['geometry']['size'][2]/2
   # Candidates are labeled observed geometry only, never a structural link.
   candidates=[dict(footing_id=f['id'],name=f['name'],size_m=f['geometry']['size'],position_enu_m=f['transform']['position'],source_entity_id=f.get('metadata',{}).get('drawing_cad',{}).get('source_entity_id'),definition='SYNTHETIC_UNVERIFIED_OUTLINE') for f in by.values() if f['id'].startswith('drawing-cad:') and f['category']=='foundation' and all(abs(f['transform']['position'][i]-p[i])<1e-8 for i in [0,1])]
   outlines=[dict(entity_id=e['id'],handle=e['handle'],plan_points_m=e['points_m']) for e in src.result_json['entities'] if e.get('layer')=='FOOTINGS_CONCEPT' and cad.rectangle(e) and abs(sum(t[0] for t in e['points_m'])/4-p[0])<1e-8 and abs(sum(t[1] for t in e['points_m'])/4-p[1])<1e-8]
   rows.append(dict(column_id=id,column_name=c['name'],base_enu_m=[p[0],p[1],z],source_beam_id=frame['beam_id'],source_node_id=reaction['node'],compression_n=reaction['fy_n'],shear_east_n=reaction['fx_n'],moment_negative_north_nm=reaction['moment_nm'],observed_footing_candidates=candidates,source_footing_outlines=outlines,reference_only_eccentricity_m=reaction['moment_nm']/reaction['fy_n'] if reaction['fy_n']>0 else None,nominal_outline_kern_m=candidates[0]['size_m'][0]/6 if candidates else None,contact_warning='UPLIFT_OR_ZERO_COMPRESSION_UNSUPPORTED' if reaction['fy_n']<=0 else 'OUTSIDE_OUTLINE_KERN_REFERENCE_ONLY' if candidates and abs(reaction['moment_nm']/reaction['fy_n'])>candidates[0]['size_m'][0]/6 else 'ACTUAL_CONTACT_BLOCKED_NO_REVIEWED_TRANSFER',connection='NOT_DECLARED',actual_analysis='BLOCKED',missing=['Explicit column-to-footing stable identity link and reviewed load path','Reviewed footing dimensions and reference/contact elevations','Sourced concrete properties and reinforcement information','Sourced soil bearing/contact assumptions and applicability','Moment/shear transfer across physical connection and reference-plane translation; no silent omission']))
 return dict(model_revision_id=rid,source_project_id=source.project_id,source_revision_id=source.model_revision_id,source_analysis_id=source.id,source_analysis_sha256=cad.digest(source.result_json),model_sha256=cad.digest(rev.document_json),rows=rows,source_dxf_sha256=src.result_json['source_sha256'],source_reference_record_id=src.id,source_reference_record_sha256=cad.digest(src.result_json),drawing_review_record_id=drawing_review.id,drawing_review_sha256=cad.digest(drawing_review.result_json),status='BLOCKED_ACTUAL_FOUNDATION_SOIL_INPUTS',engineering_approval='DISABLED',code_checks='DISABLED')
@router.get('/audit')
def audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):return audit_data(project_id,model_revision_id,db,user_id)
@router.post('/review')
def review(project_id:int,q:Review,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 a=audit_data(project_id,q.model_revision_id,db,user_id);ids={r['column_id'] for r in a['rows']}
 if len({m.column_id for m in q.mappings})!=4 or {m.column_id for m in q.mappings}!=ids or not all(m.reviewed for m in q.mappings):raise HTTPException(422,'Review exactly four actual source columns; no duplicate or unreviewed identities')
 by={c['id']:c for c in db.get(ModelRevision,q.model_revision_id).document_json['components']}
 for m in q.mappings:
  if m.footing_id:
   f=by.get(m.footing_id);c=by[m.column_id]
   if not f or f['category']!='foundation' or not cad.is_generated(f):raise HTTPException(422,'Reviewed saved CAD footing required; missing footing remains blocked')
   if any(abs(f['transform']['position'][i]-c['transform']['position'][i])>1e-8 for i in [0,1]):raise HTTPException(422,'Off-center footing mapping outside supported domain')
   if m.engineering_inputs and m.engineering_inputs.footing_dimensions_m and any(abs(a-b)>1e-8 for a,b in zip(m.engineering_inputs.footing_dimensions_m,f['geometry']['size'])):raise HTTPException(422,'Reviewed dimensions must match saved footing; use authorized CAD edit to change geometry')
   cad_source=f['metadata']['drawing_cad'];
   if cad_source['component_sha256']!=cad.component_hash(f):raise HTTPException(422,'Footing geometry/source identity changed')
 data=dict(audit=a,mappings=q.model_dump()['mappings'],classification='SYNTHETIC_VERIFICATION',actual_analysis='BLOCKED',engineering_approval='DISABLED');data['review_sha256']=cad.digest(data)
 row=EngineeringAnalysis(project_id=project_id,model_revision_id=q.model_revision_id,analysis_type='CAD_SOIL_REVIEW',algorithm_version='cad-soil/1',status='REVIEWED_ACTUAL_ANALYSIS_BLOCKED',result_json=data,actor_user_id=user_id);db.add(row);db.commit();db.refresh(row);return dict(id=row.id,result=data)
@router.post('/benchmark')
def run(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(id=q.review_id,project_id=project_id,analysis_type='CAD_SOIL_REVIEW').first()
 if not row:raise HTTPException(404,'Review not found')
 current=audit_data(project_id,row.model_revision_id,db,user_id)
 latest_review=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='CAD_SOIL_REVIEW').order_by(EngineeringAnalysis.id.desc()).first()
 if latest_review.id!=row.id:raise HTTPException(409,'Review changed; authorize the latest saved identity review')
 if not q.authorize_benchmark or q.review_sha256!=row.result_json['review_sha256'] or current!=row.result_json['audit']:raise HTTPException(409,'Exact current review and explicit benchmark authorization required')
 data=dict(benchmark=footing_bearing.benchmark(),review_id=row.id,review_sha256=q.review_sha256,audit=current,actual_analysis='BLOCKED',authorization='Explicit synthetic benchmark only; no actual soil or capacity approval')
 r=EngineeringAnalysis(project_id=project_id,model_revision_id=row.model_revision_id,analysis_type='CAD_SOIL_BENCHMARK',algorithm_version='cad-soil/1',status='VERIFIED_SYNTHETIC_ACTUAL_BLOCKED',result_json=data,actor_user_id=user_id);db.add(r);db.commit();db.refresh(r);return dict(id=r.id,result=data)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 current=audit_data(project_id,model_revision_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_(['CAD_SOIL_REVIEW','CAD_SOIL_BENCHMARK'])).order_by(EngineeringAnalysis.id.desc()).all()
 latest_review=next((r for r in rows if r.analysis_type=='CAD_SOIL_REVIEW'),None)
 return dict(records=[dict(id=r.id,status=r.status if r.result_json['audit']==current and (r.analysis_type!='CAD_SOIL_BENCHMARK' or r.result_json['review_id']==latest_review.id) else 'STALE',result=r.result_json) for r in rows])

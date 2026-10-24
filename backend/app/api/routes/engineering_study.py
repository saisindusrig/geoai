"""Local drawing references and independently benchmarked nominal steel term only."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form,Response
from pydantic import Field
from sqlalchemy.orm import Session
from app.db.models import EngineeringAnalysis,Project
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context
from app.services.assistant.storage import lock_project
from app.services.design import drawing_review as drawing,engineering_codes as codes,opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/study',tags=['engineering'])
SOURCE='DRAWING_REFERENCE';REVIEW='DRAWING_REVIEW';INPUT='ANCHOR_STEEL_INPUT';RUN='ANCHOR_STEEL_RESULT'
ROOT=Path(settings.LOCAL_STORAGE_DIR)/'drawing-references'
def checked(pid,rid,db,user,marker):
 rev,_=context(pid,rid,db,user)
 # Drawing references can be reviewed alongside any saved model. This does
 # not enable analytical conversion or the separately gated strength methods.
 if marker!='drawing_review' and not rev.document_json.get('metadata',{}).get(marker):raise HTTPException(422,'Separate review project required')
 return rev
def latest(pid,sid,kind,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=kind).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);r=db.query(EngineeringAnalysis).filter_by(project_id=pid,id=id,analysis_type=kind).first()
 if not r:raise HTTPException(404,'Owned engineering evidence not found')
 return r
def output(row,db,user):
 r=row.result_json;status=row.status
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user,latest=row.analysis_type not in [SOURCE,REVIEW])
  kind=SOURCE if row.analysis_type==SOURCE else REVIEW if row.analysis_type==REVIEW else INPUT
  current=latest(row.project_id,rev.design_scenario_id,kind,db)
  if common.digest(rev.document_json)!=r['model_document_sha256'] or (r.get('input_record_id') if row.analysis_type==RUN else row.id)!=(current.id if current else None):status='STALE'
  if row.analysis_type in [INPUT,RUN] and r.get('method_provenance')!=codes.manifest():status='STALE'
  if r.get('source_reference_id'):
   src=owned(row.project_id,r['source_reference_id'],SOURCE,db,user)
   if output(src,db,user)['status']=='STALE':status='STALE'
  if r.get('linked_drawing'):
   link=r['linked_drawing'];src=owned(link['project_id'],link['id'],SOURCE,db,user)
   current_review=latest(src.project_id,src.result_json['scenario_id'],REVIEW,db)
   if output(src,db,user)['status']=='STALE' or common.digest(src.result_json)!=link['source_record_sha256'] or (current_review.id if current_review else None)!=link['review_id']:status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def record(pid,rev,kind,status,result,db,user):
 r={**result,'scenario_id':rev.design_scenario_id,'model_document_sha256':common.digest(rev.document_json),'engineering_approval':'DISABLED'}
 if kind in [INPUT,RUN]:r['method_provenance']=codes.manifest()
 if kind in [INPUT,REVIEW]:r['input_sha256']=common.digest(r)
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rev.id,analysis_type=kind,algorithm_version='drawing-reference/1' if kind in [SOURCE,REVIEW] else codes.VERSION,status=status,result_json=r,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
class ReviewSave(drawing.Strict):
 model_revision_id:int=Field(gt=0)
 source_reference_id:int=Field(gt=0)
 base_review_id:int|None=None
 inputs:drawing.Review
class SteelSave(drawing.Strict):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
 inputs:codes.Inputs
class Authorize(drawing.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_nominal_steel_term:Literal[True]
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([SOURCE,REVIEW,INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(40).all()
 return dict(records=[dict(analysis_type=r.analysis_type,**output(r,db,user_id)) for r in rows],code_registry=codes.REGISTRY,capabilities=dict(dxf='Local 2D reference: LINE/POLYLINE, circle/text annotations; no inferred structural semantics',ifc='Structural IFC import NOT IMPLEMENTED; experimental CAD representations are not a tested IFC file importer',dwg='NOT IMPLEMENTED',pdf='Manual source reference only; automatic drawing-to-structure extraction NOT IMPLEMENTED',legacy_survey_dxf='PostGIS gated; LINE/LWPOLYLINE/POLYLINE without structural semantics or reliable millimetre handling'))
@router.post('/drawings/import')
async def upload(project_id:int,model_revision_id:int=Form(...),classification:drawing.Classification=Form(...),file:UploadFile=File(...),db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);rev=checked(project_id,model_revision_id,db,user_id,'drawing_review');content=await file.read(2_000_001);name=Path(file.filename or '').name
 try:r=drawing.extract(content,name,classification)
 except ValueError as e:raise HTTPException(422,str(e))
 path=ROOT/str(project_id)/(r['source_sha256']+'.dxf');path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():path.write_bytes(content)
 return output(record(project_id,rev,SOURCE,'REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL',r,db,user_id),db,user_id)
@router.get('/drawings/{reference_id}/source')
def download(project_id:int,reference_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,reference_id,SOURCE,db,user_id);p=ROOT/str(project_id)/(row.result_json['source_sha256']+'.dxf')
 if not p.exists():raise HTTPException(404,'Source file unavailable')
 content=p.read_bytes()
 import hashlib
 if hashlib.sha256(content).hexdigest()!=row.result_json['source_sha256']:raise HTTPException(409,'Source hash mismatch')
 return Response(content,media_type='application/dxf',headers={'Content-Disposition':'attachment; filename="source.dxf"'})
@router.post('/drawings/review')
def save_review(project_id:int,payload:ReviewSave,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);rev=checked(project_id,payload.model_revision_id,db,user_id,'drawing_review');src=owned(project_id,payload.source_reference_id,SOURCE,db,user_id);old=latest(project_id,rev.design_scenario_id,REVIEW,db)
 if output(src,db,user_id)['status']=='STALE' or payload.base_review_id!=(old.id if old else None):raise HTTPException(409,'Current drawing and latest review required')
 try:r=drawing.review(src.result_json,payload.inputs.model_dump(),rev.document_json)
 except ValueError as e:raise HTTPException(422,str(e))
 return output(record(project_id,rev,REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',{**r,'source_reference_id':src.id},db,user_id),db,user_id)
@router.get('/linkable-drawings')
def references(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).join(Project,EngineeringAnalysis.project_id==Project.id).filter(Project.user_id==user_id,EngineeringAnalysis.analysis_type==SOURCE).order_by(EngineeringAnalysis.id.desc()).limit(100).all()
 return dict(references=[dict(id=r.id,project_id=r.project_id,filename=r.result_json['filename'],classification=r.result_json['classification'],status=output(r,db,user_id)['status'],anchor_reference_entities=[dict(id=e['id'],layer=e['layer'],kind=e['kind']) for e in r.result_json['entities'] if e['kind']=='CIRCLE']) for r in rows])
def link(q,db,user):
 id=q.get('linked_drawing_reference_id');entity=q.get('linked_drawing_entity_id')
 if id is None:
  if entity:raise ValueError('Linked drawing entity requires an owned source drawing')
  return None
 src=db.query(EngineeringAnalysis).filter_by(id=id,analysis_type=SOURCE).first()
 if not src:raise ValueError('Source drawing not found')
 get_owned_project(src.project_id,db,user)
 if output(src,db,user)['status']=='STALE':raise ValueError('Linked source drawing is stale')
 if not any(e['id']==entity and e['kind']=='CIRCLE' for e in src.result_json['entities']):raise ValueError('Explicit known anchor-reference circle identity required; circle is not a physical bolt or tensile area')
 if src.result_json['classification']!='REAL_PROJECT' and q['input_classification']=='REAL_PROJECT':raise ValueError('Non-real drawing reference cannot authorize real-project property classification')
 review=latest(src.project_id,src.result_json['scenario_id'],REVIEW,db)
 return dict(id=src.id,project_id=src.project_id,entity_id=entity,classification=src.result_json['classification'],source_record_sha256=common.digest(src.result_json),review_id=review.id if review else None,notice='Traceable drawing reference only. Effective tensile area and steel properties must be independently supplied; not inferred from a circle.')
@router.get('/strength/fixture')
def fixture(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 checked(project_id,model_revision_id,db,user_id,'engineering_method_review');return dict(inputs=codes.fixture(),benchmark=codes.benchmark())
@router.post('/strength/inputs')
def save_steel(project_id:int,payload:SteelSave,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);rev=checked(project_id,payload.model_revision_id,db,user_id,'engineering_method_review');old=latest(project_id,rev.design_scenario_id,INPUT,db)
 if payload.base_input_id!=(old.id if old else None):raise HTTPException(409,'Steel method inputs changed; reload')
 q=payload.inputs.model_dump()
 try:
  codes.calculate(q);linked=link(q,db,user_id)
 except ValueError as e:raise HTTPException(422,str(e))
 return output(record(project_id,rev,INPUT,'AWAITING_EXPLICIT_NOMINAL_TERM_AUTHORIZATION',dict(inputs=q,linked_drawing=linked,preview=dict(formula=codes.REGISTRY[0]['formula'],scope='Nominal steel term only; no phi, factored demand or full connection approval')),db,user_id),db,user_id)
@router.post('/strength/authorize')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);row=owned(project_id,payload.input_id,INPUT,db,user_id);r=row.result_json
 if payload.input_sha256!=r['input_sha256'] or output(row,db,user_id)['status']=='STALE':raise HTTPException(409,'Exact current saved method inputs required')
 prior=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=RUN).filter(EngineeringAnalysis.result_json['input_record_id'].as_integer()==row.id).first()
 if prior:return output(prior,db,user_id)
 try:bench=codes.benchmark();result=codes.calculate(r['inputs']);link(r['inputs'],db,user_id)
 except ValueError as e:raise HTTPException(422,str(e))
 rev=checked(project_id,row.model_revision_id,db,user_id,'engineering_method_review');result.update(input_record_id=row.id,input_sha256=r['input_sha256'],linked_drawing=r['linked_drawing'],independent_benchmark=bench,authorization=dict(actor_user_id=user_id,time=datetime.now(timezone.utc).isoformat(),scope='Nominal steel tensile term only'))
 return output(record(project_id,rev,RUN,result['status'],result,db,user_id),db,user_id)

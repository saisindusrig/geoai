"""Immutable, explicitly authorized synthetic footing demand records."""
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.physical_frames import context as model_context
from app.api.routes.drawing_cad import source_context
from app.services.design import footing_flexure as s,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/footing-flexure',tags=['engineering'])
PROPOSAL='FOOTING_FLEXURE_PROPOSAL';RESULT='FOOTING_FLEXURE_RESULT'
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 benchmark:s.Input
class Authorize(Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_synthetic_demand:bool

def context(pid,rid,db,user):
 rev,src,review=source_context(pid,rid,db,user);doc=rev.document_json;marker=doc.get('metadata',{}).get('footing_flexure_review')
 if not marker:raise HTTPException(422,'Separate footing-flexure synthetic review copy required')
 original,original_src,original_review=source_context(marker['source_project_id'],marker['source_revision_id'],db,user)
 profiles=db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type='SOIL_PROFILE').order_by(EngineeringAnalysis.id).all()
 return dict(model_revision_id=rid,model_sha256=cad.digest(doc),source_project_id=marker['source_project_id'],source_revision_id=marker['source_revision_id'],source_model_sha256=cad.digest(original.document_json),drawing_reference_id=src.id,drawing_sha256=cad.digest(src.result_json),drawing_bytes_sha256=src.result_json['source_sha256'],drawing_review_id=review.id,drawing_review_sha256=cad.digest(review.result_json),source_drawing_sha256=cad.digest(original_src.result_json),source_review_sha256=cad.digest(original_review.result_json),soil_profiles_reference_only=[dict(id=p.id,sha256=cad.digest(p.result_json)) for p in profiles],actual_foundation_safety='BLOCKED',engineering_approval='DISABLED')

def prepare(pid,q,db,user):
 binding=context(pid,q.model_revision_id,db,user)
 try:geometry=s.audit_geometry(db.get(ModelRevision,q.model_revision_id).document_json,q.benchmark)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return dict(inputs=q.model_dump(),binding=binding,geometry=geometry,scope='Synthetic column-face bending demand only; no soil pressure imported from bearing resistance',engineering_approval='DISABLED')

def store(pid,rid,kind,status,data,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version=s.METHOD,status=status,result_json=data,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return dict(id=row.id,status=row.status,result=row.result_json)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding=context(project_id,model_revision_id,db,user_id);doc=db.get(ModelRevision,model_revision_id).document_json
 records=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,RESULT])).order_by(EngineeringAnalysis.id.desc()).all();latest=next((r.id for r in records if r.analysis_type==PROPOSAL),None)
 candidates=[dict(id=c['id'],name=c['name'],role=c['category'],geometry=c['geometry'],transform=c['transform'],source_entity_id=c.get('metadata',{}).get('drawing_cad',{}).get('source_entity_id'),material_status='UNVERIFIED_ENVELOPE_NOT_SECTION') for c in doc['components'] if c['category'] in ['column','foundation'] and c.get('metadata',{}).get('drawing_cad')]
 return dict(audit=binding,candidates=candidates,records=[dict(id=r.id,type=r.analysis_type,status=r.status if r.model_revision_id==model_revision_id and cad.digest(r.result_json['binding'])==cad.digest(binding) and (r.analysis_type==PROPOSAL or r.result_json['authorized_proposal_id']==latest) else 'STALE',result=r.result_json) for r in records])
@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 body=prepare(project_id,q,db,user_id);body['proposal_sha256']=cad.digest(body);return store(project_id,q.model_revision_id,PROPOSAL,'AWAITING_AUTHORIZATION',body,db,user_id)
@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type=PROPOSAL).first()
 if not row:raise HTTPException(404,'Proposal not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=PROPOSAL).order_by(EngineeringAnalysis.id.desc()).first();inp=Preview(**row.result_json['inputs']);fresh=prepare(project_id,inp,db,user_id)
 if not q.authorize_synthetic_demand or latest.id!=row.id or q.proposal_sha256!=row.result_json['proposal_sha256'] or cad.digest(fresh['binding'])!=cad.digest(row.result_json['binding']) or cad.digest(fresh['geometry'])!=cad.digest(row.result_json['geometry']):raise HTTPException(409,'Exact latest supported demand proposal authorization required')
 try:computed=s.calculate(inp.benchmark)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return store(project_id,inp.model_revision_id,RESULT,'VERIFIED_SYNTHETIC_DEMAND_ONLY',{**row.result_json,'computed':computed,'computed_sha256':cad.digest(computed),'authorized_proposal_id':row.id},db,user_id)

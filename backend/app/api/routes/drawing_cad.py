"""Immutable supervised geometry proposals. No solver execution or engineering approval."""
import hashlib
from copy import deepcopy
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from sqlalchemy.orm import Session
from app.db.models import EngineeringAnalysis,ModelRevision
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.physical_frames import context
from app.api.routes import engineering_study as study
from app.services.assistant.storage import lock_project
from app.services.design import drawing_cad as cad

router=APIRouter(prefix='/api/projects/{project_id}/engineering/drawing-cad',tags=['engineering'])
PROPOSAL='CAD_GEOMETRY_PROPOSAL';AUTH='CAD_GEOMETRY_AUTHORIZATION'
def source_context(pid,rid,db,user):
 rev,_=context(pid,rid,db,user)
 if not rev.document_json.get('metadata',{}).get('drawing_review'):raise HTTPException(422,'Separate drawing review project required')
 src=study.latest(pid,rev.design_scenario_id,study.SOURCE,db);review=study.latest(pid,rev.design_scenario_id,study.REVIEW,db)
 if not src or not review or review.result_json.get('source_reference_id')!=src.id:raise HTTPException(409,'Current imported source and engineer review required')
 path=study.ROOT/str(pid)/(src.result_json['source_sha256']+'.dxf')
 if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=src.result_json['source_sha256']:raise HTTPException(409,'Original drawing bytes changed or unavailable')
 if src.result_json['classification']!='SYNTHETIC_VERIFICATION':raise HTTPException(422,'Synthetic verification only')
 return rev,src,review
def provenance(rev,src,review):return dict(model_revision_id=rev.id,scenario_id=rev.design_scenario_id,model_sha256=cad.digest(rev.document_json),source_reference_id=src.id,source_sha256=cad.digest(src.result_json),review_record_id=review.id,review_sha256=cad.digest(review.result_json))
def current(row,db,user):
 try:
  rev,src,review=source_context(row.project_id,row.model_revision_id,db,user)
  return provenance(rev,src,review)==row.result_json['provenance']
 except HTTPException:return False
def owned(pid,id,kind,db,user):return study.owned(pid,id,kind,db,user)
def out(row,db,user):return dict(id=row.id,analysis_type=row.analysis_type,status=row.status if current(row,db,user) else 'STALE',model_revision_id=row.model_revision_id,result=row.result_json)
def record(pid,rev,kind,status,r,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rev.id,analysis_type=kind,algorithm_version=cad.TAG,status=status,result_json=r,actor_user_id=user);db.add(row);db.flush();return row
class Save(cad.Strict):
 model_revision_id:int=Field(gt=0)
 source_reference_id:int=Field(gt=0)
 review_record_id:int=Field(gt=0)
 inputs:cad.Inputs
class Authorize(cad.Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_geometry:Literal[True]
@router.get('')
def audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,src,review=source_context(project_id,model_revision_id,db,user_id)
 return dict(source=src.result_json,source_reference_id=src.id,review_record_id=review.id,review=review.result_json,entities=[dict(**e,eligible=cad.rectangle(e),blocking_reason=None if cad.rectangle(e) else 'Unsupported entity/layer: no automatic interpretation') for e in src.result_json['entities']],records=[out(r,db,user_id) for r in db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,AUTH])).order_by(EngineeringAnalysis.id.desc()).limit(30)])
@router.post('/preview')
def preview(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);rev,src,review=source_context(project_id,payload.model_revision_id,db,user_id)
 if (src.id,review.id)!=(payload.source_reference_id,payload.review_record_id):raise HTTPException(409,'Source/review changed; reload')
 try:r=cad.build(src.result_json,review.result_json,rev.document_json,payload.inputs.model_dump())
 except ValueError as e:raise HTTPException(422,str(e))
 r['provenance']=provenance(rev,src,review);r['proposal_sha256']=cad.digest(r)
 row=record(project_id,rev,PROPOSAL,r['status'],r,db,user_id);db.commit();return out(row,db,user_id)
@router.post('/authorize')
def authorize(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 lock_project(db,project_id);row=owned(project_id,payload.proposal_id,PROPOSAL,db,user_id);r=row.result_json
 if not current(row,db,user_id) or payload.proposal_sha256!=r['proposal_sha256'] or r['status']!='PREVIEW_READY_GEOMETRY_ONLY':raise HTTPException(409,'Exact current complete preview required')
 prior=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=AUTH).filter(EngineeringAnalysis.result_json['proposal_id'].as_integer()==row.id).first()
 if prior:return out(prior,db,user_id)
 rev,_,_=source_context(project_id,row.model_revision_id,db,user_id)
 a=record(project_id,rev,AUTH,'AUTHORIZED_GEOMETRY_DRAFT_ONLY',{},db,user_id);doc=deepcopy(r['proposed_document']);doc['metadata']['cad_geometry_authorization_id']=a.id
 a.result_json=dict(proposal_id=row.id,provenance=r['provenance'],approved_document=doc,approved_document_sha256=cad.digest(doc),authorization=dict(actor_user_id=user_id,time=datetime.now(timezone.utc).isoformat(),scope='Geometry envelopes only; no engineering approval, FEA or safety'),engineering_approval='DISABLED');db.commit();return out(a,db,user_id)
def validate_save(pid,base,doc,db,user):
 old={c['id']:c for c in (base.document_json['components'] if base else []) if cad.is_generated(c)};new={c['id']:c for c in doc['components'] if cad.is_generated(c)}
 if cad.digest(old)==cad.digest(new):return
 aid=doc.get('metadata',{}).get('cad_geometry_authorization_id')
 if not aid:raise HTTPException(409,'CAD-derived changes require a reviewed preview and explicit geometry authorization')
 a=owned(pid,aid,AUTH,db,user)
 if not base or a.model_revision_id!=base.id or not current(a,db,user) or cad.digest(doc)!=a.result_json['approved_document_sha256']:raise HTTPException(409,'Geometry authorization is stale or does not match the exact proposed document')

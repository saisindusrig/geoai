from app.services.design import rectangular_bearing as finite
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.soil_profile import context as soil_context,latest_profile
from app.api.routes.physical_frames import context as model_context
from app.api.routes.drawing_cad import source_context as drawing_context
from app.services.design import bearing_capacity as s,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/bearing-capacity',tags=['engineering'])
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 benchmark:s.Input|finite.Input
class Authorize(Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_synthetic_bearing:bool
def context(pid,rid,db,user):
 c=soil_context(pid,rid,db,user);doc=db.get(ModelRevision,rid).document_json;m=doc.get('metadata',{}).get('bearing_capacity_review')
 if not m:raise HTTPException(422,'Separate bearing review project required')
 # Shared solver/transport evidence is already validated by soil_context above.
 # Independently own/check the original latest revision and original drawing;
 # avoid a second expensive traversal of the same shared evidence graph.
 original,_=model_context(m['source_project_id'],m['source_revision_id'],db,user)
 _,drawing,review=drawing_context(m['source_project_id'],m['source_revision_id'],db,user)
 source=dict(model_sha256=cad.digest(original.document_json),drawing_id=drawing.id,drawing_sha256=cad.digest(drawing.result_json),review_id=review.id,review_sha256=cad.digest(review.result_json))
 if cad.digest(doc['components'])!=cad.digest(original.document_json['components']):raise HTTPException(409,'Copied geometry changed')
 p=latest_profile(m['source_project_id'],db);own=latest_profile(pid,db)
 if not p or p.id!=m['source_profile_id']:raise HTTPException(409,'Original soil profile changed; re-review source binding')
 c.update(reference_profile=dict(project_id=p.project_id,id=p.id,sha256=cad.digest(p.result_json),classification=p.result_json['profile']['classification'],usage='REFERENCE ONLY; NEVER USED AS REAL BEARING PROPERTIES'),copied_profile_id=own.id if own else None,copied_profile_sha256=cad.digest(own.result_json) if own else None,source_binding_sha256=cad.digest(source),actual_cad_capacity='BLOCKED',missing=['Applicable sourced undrained strength/friction/soil investigation','Finite rectangular footing method and physical N/V/M transfer validation','Groundwater, loading and site applicability review'])
 if doc.get("metadata",{}).get("finite_bearing_review"):c["finite_formulation_review"]=doc["metadata"]["finite_bearing_review"]
 return c
def store(pid,rid,kind,status,data,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version=data['inputs']['benchmark']['method'],status=status,result_json=data,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return dict(id=row.id,status=row.status,result=row.result_json)
@router.get('/audit')
def audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return context(project_id,model_revision_id,db,user_id)
@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding=context(project_id,q.model_revision_id,db,user_id)
 if isinstance(q.benchmark,finite.Input) and not binding.get('finite_formulation_review'):raise HTTPException(422,'Separate finite-footing synthetic review copy required')
 r=dict(inputs=q.model_dump(),binding=binding,scope='Independent synthetic '+q.benchmark.geometry+' strength benchmark only',engineering_approval='DISABLED');r['proposal_sha256']=cad.digest(r)
 return store(project_id,q.model_revision_id,'BEARING_PROPOSAL','AWAITING_AUTHORIZATION',r,db,user_id)
@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type='BEARING_PROPOSAL').first()
 if not row:raise HTTPException(404,'Proposal not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='BEARING_PROPOSAL').order_by(EngineeringAnalysis.id.desc()).first();inp=Preview(**row.result_json['inputs']);c=context(project_id,inp.model_revision_id,db,user_id)
 if not q.authorize_synthetic_bearing or latest.id!=row.id or q.proposal_sha256!=row.result_json['proposal_sha256'] or cad.digest(c)!=cad.digest(row.result_json['binding']):raise HTTPException(409,'Exact current synthetic bearing proposal authorization required')
 try:computed=finite.calculate(inp.benchmark) if isinstance(inp.benchmark,finite.Input) else s.calculate(inp.benchmark)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return store(project_id,inp.model_revision_id,'BEARING_RESULT','VERIFIED_SYNTHETIC',{**row.result_json,'computed':computed,'computed_sha256':cad.digest(computed),'authorized_proposal_id':row.id},db,user_id)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 c=context(project_id,model_revision_id,db,user_id);records=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_(['BEARING_PROPOSAL','BEARING_RESULT'])).order_by(EngineeringAnalysis.id.desc()).all();latest=next((r.id for r in records if r.analysis_type=='BEARING_PROPOSAL'),None)
 return dict(audit=c,records=[dict(id=r.id,type=r.analysis_type,status=r.status if r.model_revision_id==model_revision_id and cad.digest(r.result_json['binding'])==cad.digest(c) and (r.analysis_type=='BEARING_PROPOSAL' or r.result_json['authorized_proposal_id']==latest) else 'STALE',result=r.result_json) for r in records])

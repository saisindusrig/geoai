from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.cad_soil import audit_data
from app.api.routes.footing_transport import history as transport_history
from app.services.design import soil_contact as s,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/soil-contact',tags=['engineering'])
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 benchmark:s.Inputs
class Authorize(Strict):
 proposal_id:int
 proposal_sha256:str
 authorize_synthetic_benchmark:bool

def context(pid,rid,db,user):
 audit=audit_data(pid,rid,db,user)
 doc=db.get(ModelRevision,rid).document_json
 marker=doc.get('metadata',{}).get('soil_contact_review')
 if not marker:raise HTTPException(422,'Separate synthetic soil review project required')
 source=db.get(ModelRevision,marker['source_revision_id'])
 result=db.get(EngineeringAnalysis,marker['source_transport_result_id'])
 if not source or not result or source.project_id!=marker['source_project_id'] or result.project_id!=source.project_id:raise HTTPException(422,'Invalid source binding')
 records=transport_history(source.project_id,source.id,db,user)['records']
 if not any(r['id']==result.id and r['status']=='VERIFIED_DEMANDS_ONLY' for r in records):raise HTTPException(409,'Source demand transfer stale')
 if cad.digest(doc['components'])!=cad.digest(source.document_json['components']):raise HTTPException(409,'Copied CAD geometry changed; review and rebind required')
 return dict(audit=audit,source_transport_id=result.id,source_transport_sha256=cad.digest(result.result_json),actual_demands=result.result_json['rows'],actual_soil_analysis='BLOCKED',missing=['Sourced geotechnical contact law and stiffness','Reviewed physical connection and shear/moment load path','Applicability, elevations and engineer review'],model_revision_id=rid)

@router.get('/audit')
def audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return context(project_id,model_revision_id,db,user_id)

@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding=context(project_id,q.model_revision_id,db,user_id)
 r=dict(inputs=q.model_dump(),binding=binding,scope='SYNTHETIC_VERIFICATION only; no actual-project properties or analysis',engineering_approval='DISABLED')
 r['proposal_sha256']=cad.digest(r)
 row=EngineeringAnalysis(project_id=project_id,model_revision_id=q.model_revision_id,analysis_type='SOIL_CONTACT_PROPOSAL',algorithm_version='rigid-winkler/1',status='AWAITING_AUTHORIZATION',result_json=r,actor_user_id=user_id)
 db.add(row);db.commit();db.refresh(row);return dict(id=row.id,status=row.status,result=r)

@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type='SOIL_CONTACT_PROPOSAL').first()
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='SOIL_CONTACT_PROPOSAL').order_by(EngineeringAnalysis.id.desc()).first()
 if not row:raise HTTPException(404,'Proposal not found')
 inp=Preview(**row.result_json['inputs']);binding=context(project_id,inp.model_revision_id,db,user_id)
 if not q.authorize_synthetic_benchmark or latest.id!=row.id or q.proposal_sha256!=row.result_json['proposal_sha256'] or cad.digest(binding)!=cad.digest(row.result_json['binding']):raise HTTPException(409,'Exact current synthetic proposal authorization required')
 try:computed=s.calculate(inp.benchmark)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 r={**row.result_json,'computed':computed,'authorized_proposal_id':row.id}
 record=EngineeringAnalysis(project_id=project_id,model_revision_id=row.model_revision_id,analysis_type='SOIL_CONTACT_RESULT',algorithm_version='rigid-winkler/1',status='VERIFIED_SYNTHETIC' if 'verification' in computed else 'BLOCKED',result_json=r,actor_user_id=user_id)
 db.add(record);db.commit();db.refresh(record);return dict(id=record.id,status=record.status,result=r)

@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding=context(project_id,model_revision_id,db,user_id)
 records=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_(['SOIL_CONTACT_PROPOSAL','SOIL_CONTACT_RESULT'])).order_by(EngineeringAnalysis.id.desc()).all()
 latest=next((r.id for r in records if r.analysis_type=='SOIL_CONTACT_PROPOSAL'),None)
 return dict(records=[dict(id=r.id,status=r.status if r.model_revision_id==model_revision_id and cad.digest(r.result_json['binding'])==cad.digest(binding) and (r.analysis_type=='SOIL_CONTACT_PROPOSAL' or r.result_json['authorized_proposal_id']==latest) else 'STALE',result=r.result_json) for r in records])

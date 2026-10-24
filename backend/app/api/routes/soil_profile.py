"""Versioned sourced profile editing and exact-authorized synthetic settlement only."""
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.soil_contact import context as demand_context
from app.services.design import elastic_settlement as s,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/soil-profile',tags=['engineering'])
class Save(Strict):
 model_revision_id:int=Field(gt=0)
 base_profile_id:int|None=None
 profile:s.Profile
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 profile_id:int=Field(gt=0)
 load:s.Load
class Authorize(Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_synthetic_settlement:bool

def context(pid,rid,db,user):
 c=demand_context(pid,rid,db,user);doc=db.get(ModelRevision,rid).document_json
 marker=doc.get('metadata',{}).get('soil_profile_review')
 if not marker:raise HTTPException(422,'Separate soil-profile review copy required')
 source=db.query(ModelRevision).filter_by(project_id=marker['source_project_id'],id=marker['source_revision_id']).first()
 if not source or cad.digest(doc['components'])!=cad.digest(source.document_json['components']):raise HTTPException(409,'Source CAD geometry changed; re-review required')
 c['actual_soil_analysis']='BLOCKED';c['missing']=['Sourced site investigation and layer properties','Supported rigid footing/load-transfer assumptions','Site applicability and geotechnical engineer review'];return c
def latest_profile(pid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type='SOIL_PROFILE').order_by(EngineeringAnalysis.id.desc()).first()
def store(pid,rid,kind,status,data,db,user):
 r=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='soil-profile-halfspace/1',status=status,result_json=data,actor_user_id=user);db.add(r);db.commit();db.refresh(r);return dict(id=r.id,status=r.status,result=r.result_json)

@router.get('/audit')
def audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return context(project_id,model_revision_id,db,user_id)
@router.post('/save')
def save(project_id:int,q:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 c=context(project_id,q.model_revision_id,db,user_id);old=latest_profile(project_id,db)
 if q.base_profile_id!=(old.id if old else None):raise HTTPException(409,'Profile changed; reload latest version before editing')
 r=dict(profile=q.profile.model_dump(),binding=c,profile_sha256=cad.digest(q.profile.model_dump()),supersedes_profile_id=q.base_profile_id,missing=s.blockers(q.profile),actual_soil_analysis='BLOCKED',engineering_approval='DISABLED')
 return store(project_id,q.model_revision_id,'SOIL_PROFILE','SAVED_UNAPPROVED',r,db,user_id)
def prepare(pid,q,db,user):
 binding=context(pid,q.model_revision_id,db,user);p=latest_profile(pid,db)
 if not p or p.id!=q.profile_id or p.model_revision_id!=q.model_revision_id or cad.digest(p.result_json['binding'])!=cad.digest(binding):raise HTTPException(409,'Latest sourced profile and current saved geometry required')
 profile=s.Profile(**p.result_json['profile'])
 # Domain validation at preview, before execution authorization.
 if profile.classification!='SYNTHETIC_VERIFICATION':raise HTTPException(422,'Actual site settlement BLOCKED; only synthetic verification authorized in this milestone')
 if len(profile.layers)!=1 or profile.layers[0].extent!='UNBOUNDED_IDEALIZATION':raise HTTPException(422,'Layered/finite-depth/unknown-extent settlement unsupported')
 if not profile.layers[0].E_mpa or not profile.layers[0].poisson:raise HTTPException(422,'Explicit sourced elastic modulus and Poisson ratio required')
 try:s.validate_domain(profile,q.load)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return dict(inputs=q.model_dump(),profile_sha256=p.result_json['profile_sha256'],profile=profile.model_dump(),binding=binding,engineering_approval='DISABLED',scope='Synthetic flexible surface-patch centre settlement only; no rigid-footing or Winkler settlement')
@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 r=prepare(project_id,q,db,user_id);r['proposal_sha256']=cad.digest(r);return store(project_id,q.model_revision_id,'ELASTIC_SETTLEMENT_PROPOSAL','AWAITING_AUTHORIZATION',r,db,user_id)
@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type='ELASTIC_SETTLEMENT_PROPOSAL').first()
 if not row:raise HTTPException(404,'Proposal not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='ELASTIC_SETTLEMENT_PROPOSAL').order_by(EngineeringAnalysis.id.desc()).first()
 fresh=prepare(project_id,Preview(**row.result_json['inputs']),db,user_id)
 if not q.authorize_synthetic_settlement or latest.id!=row.id or cad.digest(fresh)!=q.proposal_sha256 or row.result_json['proposal_sha256']!=q.proposal_sha256:raise HTTPException(409,'Exact current profile/load/source authorization required')
 try:r=s.calculate(s.Profile(**fresh['profile']),s.Load(**fresh['inputs']['load']))
 except ValueError as e:raise HTTPException(422,str(e)) from e
 out={**fresh,'computed':r,'authorized_proposal_id':row.id,'computed_sha256':cad.digest(r)}
 return store(project_id,row.model_revision_id,'ELASTIC_SETTLEMENT_RESULT','VERIFIED_SYNTHETIC',out,db,user_id)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 c=context(project_id,model_revision_id,db,user_id);p=latest_profile(project_id,db)
 records=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_(['SOIL_PROFILE','ELASTIC_SETTLEMENT_PROPOSAL','ELASTIC_SETTLEMENT_RESULT'])).order_by(EngineeringAnalysis.id.desc()).all();latest=next((r.id for r in records if r.analysis_type=='ELASTIC_SETTLEMENT_PROPOSAL'),None);out=[]
 for r in records:
  valid=r.model_revision_id==model_revision_id and cad.digest(r.result_json['binding'])==cad.digest(c)
  if r.analysis_type!='SOIL_PROFILE':
   valid=valid and p is not None and r.result_json['inputs']['profile_id']==p.id and r.result_json['profile_sha256']==p.result_json['profile_sha256']
   if r.analysis_type=='ELASTIC_SETTLEMENT_RESULT':valid=valid and r.result_json['authorized_proposal_id']==latest
  out.append(dict(id=r.id,type=r.analysis_type,status=r.status if valid else 'STALE',result=r.result_json))
 return dict(records=out)

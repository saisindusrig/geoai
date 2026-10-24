"""Review-only nominal section calculations tied to immutable saved demand."""
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.drawing_cad import source_context
from app.api.routes import footing_flexure as demand_api
from app.services.design import rc_flexure as s,footing_flexure as demand_s,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/rc-flexure',tags=['engineering'])
PROPOSAL='RC_FLEXURE_PROPOSAL';RESULT='RC_FLEXURE_RESULT'
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 benchmark:s.Input
class Authorize(Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_synthetic_nominal:bool

def context(pid,rid,db,user):
 rev,src,review=source_context(pid,rid,db,user);doc=rev.document_json;m=doc.get('metadata',{}).get('rc_flexure_review')
 if not m:raise HTTPException(422,'Separate nominal RC synthetic review copy required')
 source_history=demand_api.history(m['source_project_id'],m['source_revision_id'],db,user)
 r=next((r for r in source_history['records'] if r['id']==m['demand_result_id'] and r['type']==demand_api.RESULT),None)
 if not r or r['status']!='VERIFIED_SYNTHETIC_DEMAND_ONLY':raise HTTPException(409,'Exact source demand must remain current and independently verified')
 body=r['result'];computed=body['computed']
 if body['computed_sha256']!=cad.digest(computed):raise HTTPException(409,'Source demand evidence hash mismatch')
 q=demand_s.Input(**body['inputs']['benchmark'])
 try:geometry=demand_s.audit_geometry(doc,q)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 binding=dict(model_revision_id=rid,model_sha256=cad.digest(doc),drawing_id=src.id,drawing_sha256=cad.digest(src.result_json),review_id=review.id,review_sha256=cad.digest(review.result_json),source_project_id=m['source_project_id'],source_revision_id=m['source_revision_id'],demand_result_id=r['id'],demand_sha256=cad.digest(body),source_binding_sha256=cad.digest(source_history['audit']))
 demand=dict(id=r['id'],classification='SYNTHETIC_VERIFICATION',unfactored_full_cut_knm=computed['faces'][0]['full_cut_moment_knm'],unfactored_per_metre_knm=computed['faces'][0]['moment_knm_per_m'],design_action_status='UNFACTORED_REFERENCE_ONLY_NOT_A_DESIGN_ACTION')
 return binding,geometry,demand

def prepare(pid,q,db,user):
 binding,geometry,demand=context(pid,q.model_revision_id,db,user)
 if q.benchmark.demand_result_id!=demand['id'] or q.benchmark.footing_id!=geometry['footing_id']:raise HTTPException(422,'Exact saved footing and source demand identities required')
 f=geometry['footing_size_m']
 if abs(q.benchmark.section_width_mm-f[1]*1000)>1e-8 or abs(q.benchmark.thickness_mm-f[2]*1000)>1e-8:raise HTTPException(422,'Full-width section must match the actual saved footing width/thickness')
 if 2*q.benchmark.end_cover_mm+2*q.benchmark.bar_diameter_mm>=f[0]*1000:raise HTTPException(422,'Bar ends do not fit inside saved footing envelope')
 return dict(inputs=q.model_dump(),binding=binding,geometry=geometry,source_demand=demand,scope='Synthetic one-direction nominal mechanics only; no project materials or code design strength',engineering_approval='DISABLED')

def store(pid,rid,kind,status,data,db,user):
 r=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version=s.METHOD,status=status,result_json=data,actor_user_id=user);db.add(r);db.commit();db.refresh(r);return dict(id=r.id,status=r.status,result=r.result_json)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding,geometry,demand=context(project_id,model_revision_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,RESULT])).order_by(EngineeringAnalysis.id.desc()).all();latest=next((r.id for r in rows if r.analysis_type==PROPOSAL),None)
 return dict(geometry=geometry,source_demand=demand,actual_materials=None,actual_footing_safety='BLOCKED',records=[dict(id=r.id,type=r.analysis_type,status=r.status if r.model_revision_id==model_revision_id and cad.digest(r.result_json['binding'])==cad.digest(binding) and (r.analysis_type==PROPOSAL or r.result_json['authorized_proposal_id']==latest) else 'STALE',result=r.result_json) for r in rows])
@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 body=prepare(project_id,q,db,user_id);body['proposal_sha256']=cad.digest(body);return store(project_id,q.model_revision_id,PROPOSAL,'AWAITING_AUTHORIZATION',body,db,user_id)
@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 r=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type=PROPOSAL).first()
 if not r:raise HTTPException(404,'Proposal not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=PROPOSAL).order_by(EngineeringAnalysis.id.desc()).first();inp=Preview(**r.result_json['inputs']);fresh=prepare(project_id,inp,db,user_id)
 if not q.authorize_synthetic_nominal or latest.id!=r.id or q.proposal_sha256!=r.result_json['proposal_sha256'] or cad.digest(fresh)!=cad.digest({k:v for k,v in r.result_json.items() if k!='proposal_sha256'}):raise HTTPException(409,'Exact current synthetic nominal proposal authorization required')
 try:computed=s.calculate(inp.benchmark)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return store(project_id,inp.model_revision_id,RESULT,'VERIFIED_SYNTHETIC_NOMINAL_ONLY',{**r.result_json,'computed':computed,'computed_sha256':cad.digest(computed),'authorized_proposal_id':r.id},db,user_id)

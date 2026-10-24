"""Bounded synthetic mechanical verification; actual copied project remains blocked."""
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.models import EngineeringAnalysis,ModelRevision
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.physical_frames import context
from app.api.routes.projects import get_owned_project
from app.api.routes import foundation_interfaces as interface
from app.services.design import anchor_contact as calc,opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/anchor-contact',tags=['engineering'])
INPUT='ANCHOR_CONTACT_BENCHMARK_INPUT';RUN='ANCHOR_CONTACT_BENCHMARK_RESULT'
class Save(calc.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Authorize(calc.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_benchmark:Literal[True]
def audit(pid,rid,db,user):
 rev,_=context(pid,rid,db,user);origin=rev.document_json.get('metadata',{}).get('anchor_contact_review',{});sid=origin.get('source_interface_analysis_id');row=db.query(EngineeringAnalysis).filter_by(id=sid,project_id=origin.get('source_project_id'),analysis_type=interface.RUN).first()
 if not row:raise HTTPException(422,'Separate review copy of saved interface evidence required')
 get_owned_project(row.project_id,db,user)
 if interface.output(row,db,user)['status']=='STALE':raise HTTPException(409,'Original interface/source solver inputs or geometry are stale')
 sr=db.get(ModelRevision,row.model_revision_id)
 if origin.get('source_revision_id')!=row.model_revision_id or rev.document_json['components']!=sr.document_json['components'] or rev.document_json['origin']!=sr.document_json['origin']:raise HTTPException(422,'Review geometry changed from source interface; rerun/review source demands')
 r=row.result_json;missing=['Effective concrete-contact stiffness kc [N/m³] and calibration/assumption source','Individual anchor axial stiffnesses ki [N/m] with sources','Verified/declarative fixed anchor-ground tension load path','Engineer-approved effective lever arms and mechanical active-plane selection']
 for a in r['inputs']['anchors']['items']:missing.append(a['id']+': no axial stiffness defined')
 unsupported=['Actual anchors have nonzero North offsets; the benchmark supports only anchors on one North centerline, with no biaxial coupling','Actual full N/M is not substituted into the benchmark. No force or resistance distribution for the actual project is calculated','Horizontal shear transfer, embedment resistance, breakout, plate/weld/footing/soil capacities and code checks NOT VERIFIED']
 return rev,row,dict(status='ACTUAL_PROJECT_BLOCKED_MISSING_MECHANICS',source_interface_analysis_id=row.id,source_project_id=row.project_id,source_revision_id=row.model_revision_id,geometry=r['geometry'],demand=r['demand'],declared_anchors=r['inputs']['anchors'],missing=missing,unsupported=unsupported,engineering_approval='DISABLED',source_evidence_sha256=common.digest(r))
def latest(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def output(row,db,user):
 status=row.status;r=row.result_json
 try:
  rev,src,_=audit(row.project_id,row.model_revision_id,db,user);i=latest(row.project_id,rev.design_scenario_id,db)
  if common.digest(rev.document_json)!=r['model_document_sha256'] or common.digest(src.result_json)!=r['source_evidence_sha256'] or (row.id if row.analysis_type==INPUT else r['input_record_id'])!=(i.id if i else None):status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def record(pid,rid,kind,status,r,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='anchor-contact/1-planar-synthetic',status=status,result_json=r,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);r=db.query(EngineeringAnalysis).filter_by(id=id,project_id=pid,analysis_type=kind).first()
 if not r:raise HTTPException(404,'Owned benchmark evidence required')
 return r
@router.get('/audit')
def inspect(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return audit(project_id,model_revision_id,db,user_id)[2]
@router.get('/fixture')
def fixture(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 audit(project_id,model_revision_id,db,user_id);return dict(inputs=calc.fixture(),notice='Separate synthetic benchmark geometry/material mechanics; not saved project anchors or actual project demand. All numerical inputs explicit and reviewable.')
@router.post('/inputs')
def save(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,src,a=audit(project_id,payload.model_revision_id,db,user_id);q=payload.model_dump(exclude={'model_revision_id','base_input_id'})
 try:q=calc.validate(q)
 except (ValueError,TypeError) as e:raise HTTPException(422,str(e))
 old=latest(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(old.id if old else None):raise HTTPException(409,'Benchmark inputs changed; reload')
 r=dict(inputs=q,actual_project_audit=a,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),source_evidence_sha256=common.digest(src.result_json),engineering_approval='DISABLED');r['input_sha256']=common.digest(r)
 return output(record(project_id,rev.id,INPUT,'AWAITING_AUTHORIZATION',r,db,user_id),db,user_id)
@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,payload.input_id,INPUT,db,user_id);r=row.result_json
 if payload.input_sha256!=r['input_sha256'] or output(row,db,user_id)['status']=='STALE':raise HTTPException(409,'Exact current reviewed benchmark required')
 if r.get('analysis_id'):return output(owned(project_id,r['analysis_id'],RUN,db,user_id),db,user_id)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'New benchmark proposal required')
 try:
  b=calc.benchmark();result=calc.run(r['inputs']);result.update(benchmark=b,model_document_sha256=r['model_document_sha256'],source_evidence_sha256=r['source_evidence_sha256'],scenario_id=r['scenario_id'],input_record_id=row.id,actual_project_audit=r['actual_project_audit'],authorization=dict(actor_user_id=user_id,authorized_at=datetime.now(timezone.utc).isoformat(),scope='Separate synthetic planar unilateral mechanical benchmark only; not actual project design'))
 except (ValueError,ArithmeticError) as e:raise HTTPException(422,str(e))
 a=record(project_id,row.model_revision_id,RUN,result['status'],result,db,user_id);row.result_json={**r,'analysis_id':a.id};row.status='BENCHMARK_COMPLETED';db.commit();return output(a,db,user_id)
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(30).all();return dict(records=[output(r,db,user_id) for r in rows])
@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return output(owned(project_id,analysis_id,RUN,db,user_id),db,user_id)

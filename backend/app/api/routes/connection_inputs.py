"""Immutable drafts, evidence validation and exact authorized actual N/M contact proposals."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session
from app.db.models import EngineeringAnalysis
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.anchor_contacts_3d import audit as source_audit
from app.services.design import connection_inputs as calc, anchor_contact_3d as benchmark, opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/connection-inputs',tags=['engineering'])
INPUT='REAL_CONNECTION_INPUT';RUN='REAL_CONNECTION_CONTACT'
class Save(calc.Strict):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
 inputs:calc.Inputs
class Authorize(calc.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_n_m_contact:Literal[True]

def audit(pid,rid,db,user):
 rev,src,a=source_audit(pid,rid,db,user)
 if not rev.document_json.get('metadata',{}).get('real_engineering_input_review'):raise HTTPException(422,'Separate real engineering input review copy required')
 return rev,src,a
def latest(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def output(row,db,user):
 r=row.result_json;status=row.status
 try:
  rev,src,_=audit(row.project_id,row.model_revision_id,db,user);i=latest(row.project_id,rev.design_scenario_id,db)
  if common.digest(rev.document_json)!=r['model_document_sha256'] or common.digest(src.result_json)!=r['source_evidence_sha256'] or (row.id if row.analysis_type==INPUT else r['input_record_id'])!=(i.id if i else None):status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);row=db.query(EngineeringAnalysis).filter_by(project_id=pid,id=id,analysis_type=kind).first()
 if not row:raise HTTPException(404,'Owned connection input evidence required')
 return row
def record(pid,rid,kind,status,r,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='connection-inputs/1-evidence-gated-three-dof',status=status,result_json=r,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
@router.get('/audit')
def inspect(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 _,_,a=audit(project_id,model_revision_id,db,user_id);q=calc.template(a)
 return dict(actual=a,template=q,assessment=calc.assess(q,a),anchor_fields=calc.ANCHOR_FIELDS,contact_fields=calc.CONTACT_FIELDS,flags=calc.FLAGS)
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(30).all()
 return dict(records=[output(r,db,user_id) for r in rows])
@router.post('/inputs')
def save(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,src,a=audit(project_id,payload.model_revision_id,db,user_id);old=latest(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(old.id if old else None):raise HTTPException(409,'Engineering inputs changed; reload the latest draft before saving')
 try:assessment=calc.assess(payload.inputs.model_dump(),a)
 except (ValueError,TypeError) as e:raise HTTPException(422,str(e))
 r=dict(inputs=assessment['inputs'],assessment=assessment,actual_project_audit=a,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),source_evidence_sha256=common.digest(src.result_json),engineering_approval='DISABLED');r['input_sha256']=common.digest(r)
 return output(record(project_id,rev.id,INPUT,assessment['status'],r,db,user_id),db,user_id)
@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,payload.input_id,INPUT,db,user_id);r=row.result_json
 if payload.input_sha256!=r['input_sha256'] or output(row,db,user_id)['status']=='STALE':raise HTTPException(409,'Exact current saved inputs and source revision required')
 rev,src,a=audit(project_id,row.model_revision_id,db,user_id)
 try:
  check=calc.assess(r['inputs'],a)
  if check['missing']:raise ValueError('Actual calculation BLOCKED: missing or synthetic engineering evidence')
  # Idempotent authorization creates no duplicate run and never mutates the input evidence.
  prior=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=RUN).filter(EngineeringAnalysis.result_json['input_record_id'].as_integer()==row.id).first()
  if prior:return output(prior,db,user_id)
  verified=benchmark.benchmarks();result=calc.solve(r['inputs'],a)
 except (ValueError,ArithmeticError) as e:raise HTTPException(422,str(e))
 result.update(input_record_id=row.id,input_sha256=r['input_sha256'],scenario_id=rev.design_scenario_id,model_document_sha256=r['model_document_sha256'],source_evidence_sha256=r['source_evidence_sha256'],actual_project_audit=a,benchmark_evidence=[dict(case=c['case'],hand=c['hand']) for c in verified['cases']],authorization=dict(actor_user_id=user_id,authorized_at=datetime.now(timezone.utc).isoformat(),scope='N/M rigid-plate contact equilibrium only; no shear transfer or physical capacity approval'))
 return output(record(project_id,rev.id,RUN,result['status'],result,db,user_id),db,user_id)

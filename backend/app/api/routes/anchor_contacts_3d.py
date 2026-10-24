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
from app.services.design import anchor_contact_3d as calc,opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/anchor-contact-3d',tags=['engineering'])
INPUT='ANCHOR_CONTACT_3D_INPUT';RUN='ANCHOR_CONTACT_3D_RESULT'
class Save(calc.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Authorize(calc.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_benchmark:Literal[True]
def audit(pid,rid,db,user):
 from app.api.routes.anchor_contacts import audit as original_audit
 rev,src,a=original_audit(pid,rid,db,user)
 review=rev.document_json.get('metadata',{}).get('anchor_contact_3d_review',{})
 if not review:raise HTTPException(422,'Separate 3D review copy required')
 get_owned_project(review['source_project_id'],db,user)
 center=a['geometry']['column_base_enu_m'];a={**a,'missing':['Effective contact stiffness kc [N/m³], evidence and calibration/assumption source','Reviewed fixed anchor-ground tension load path and reference-plane idealization']+[x for x in a['missing'] if 'axial stiffness' in x or 'no axial stiffness' in x], 'unsupported':['Actual plate/anchor plan geometry is supported by the 3-DOF model; actual results remain BLOCKED because mechanical inputs and reviewed load path are absent','Horizontal shear/torsion, prying, material capacities, welds, footing/soil and code checks NOT VERIFIED']}
 a['actual_anchor_local_positions']=[dict(id=x['id'],position_east_north_m=[x['position_enu_m'][0]-center[0],x['position_enu_m'][1]-center[1]],definition='DECLARED_UNVERIFIED_NOT_SAVED_PHYSICAL_BOLT') for x in a['declared_anchors']['items']]
 return rev,src,a

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
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='anchor-contact/2-three-dof-synthetic',status=status,result_json=r,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);r=db.query(EngineeringAnalysis).filter_by(id=id,project_id=pid,analysis_type=kind).first()
 if not r:raise HTTPException(404,'Owned benchmark evidence required')
 return r
@router.get('/audit')
def inspect(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return audit(project_id,model_revision_id,db,user_id)[2]
@router.get('/fixture')
def fixture(project_id:int,model_revision_id:int,case:Literal['symmetric','uniaxial','asymmetric','biaxial','2d_reduction']='biaxial',db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 audit(project_id,model_revision_id,db,user_id);return dict(inputs=calc.fixture(case),notice='Separate synthetic benchmark geometry/material mechanics; not saved project anchors or actual project demand. All numerical inputs explicit and reviewable.')
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
  b=calc.benchmarks();result=calc.run(r['inputs']);result.update(benchmark_suite=b,model_document_sha256=r['model_document_sha256'],source_evidence_sha256=r['source_evidence_sha256'],scenario_id=r['scenario_id'],input_record_id=row.id,actual_project_audit=r['actual_project_audit'],authorization=dict(actor_user_id=user_id,authorized_at=datetime.now(timezone.utc).isoformat(),scope='Separate synthetic three-DOF mechanical verification only; not actual project design'))
 except (ValueError,ArithmeticError) as e:raise HTTPException(422,str(e))
 a=record(project_id,row.model_revision_id,RUN,result['status'],result,db,user_id);row.result_json={**r,'analysis_id':a.id};row.status='BENCHMARK_COMPLETED';db.commit();return output(a,db,user_id)
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(30).all();records=[]
 for row in rows:
  o=output(row,db,user_id);r=o['result']
  if r.get('benchmark_suite'):
   suite=r['benchmark_suite'];o['result']={**r,'benchmark_suite':{**suite,'cases':[{k:v for k,v in c.items() if k!='computed'} for c in suite['cases']]}}
  records.append(o)
 return dict(records=records)
@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return output(owned(project_id,analysis_id,RUN,db,user_id),db,user_id)

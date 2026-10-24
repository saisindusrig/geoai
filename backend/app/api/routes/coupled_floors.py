"""Explicitly authorized, immutable, fixed-scope synthetic coupled floor review."""
import json,subprocess
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from typing import Literal
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Project,DesignScenario,ModelRevision,EngineeringAnalysis
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context,Authorize
from app.api.routes.opensees import lock
from app.services.design import coupled_floor as solver,opensees_benchmark as common
from app.services.design.spatial_frame import Strict

router=APIRouter(prefix='/api/projects/{project_id}/engineering/coupled-floor',tags=['engineering'])
PROPOSAL='COUPLED_FLOOR_REVIEW';RUN='OPENSEES_COUPLED_FLOOR'
class Fixture(Strict):
 review_parametric_geometry:Literal[True]
class Review(Fixture):
 model_revision_id:int=Field(gt=0)

def record(pid,rid,kind,status,result,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='synthetic-coupled-shell-frame/research-1',status=status,result_json=result,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row

def check_document(doc):
 expected=solver.fixture()
 if any(common.digest(doc.get(k))!=common.digest(expected[k]) for k in ['components','units','origin']):raise ValueError('Only exact reviewed synthetic geometry is supported; modified geometry requires new independent validation')
 if doc.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Local ENU metres required')
 if doc.get('metadata',{}).get('coupled_floor_review')!=expected['metadata']['coupled_floor_review']:raise ValueError('Exact synthetic formulation required')

def out(row,db,user):
 status=row.status
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user)
  if common.digest(rev.document_json)!=row.result_json['model_document_sha256']:status='STALE'
  if row.analysis_type==RUN:
   latest=db.query(EngineeringAnalysis).filter_by(project_id=row.project_id,model_revision_id=row.model_revision_id,analysis_type=PROPOSAL).order_by(EngineeringAnalysis.id.desc()).first()
   if not latest or latest.id!=row.result_json['proposal_id']:status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=row.result_json)

@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user)
 rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(40).all()
 return dict(records=[out(r,db,user) for r in rows],limitations=solver.LIMITATIONS)

@router.post('/review-fixture')
def fixture(project_id:int,payload:Fixture,db:Session=Depends(get_db),user:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user);doc=solver.fixture()
 p=Project(user_id=user,name='Coupled shell–frame · one-storey synthetic review',project_type='unclassified',units='metric',center_lat=12.9716,center_lng=77.5946,boundary_geojson={'type':'Polygon','coordinates':[[[77.5945,12.9715],[77.5948,12.9715],[77.5948,12.9718],[77.5945,12.9718],[77.5945,12.9715]]]})
 db.add(p);db.flush();s=DesignScenario(project_id=p.id,name='Reviewed coincident shell/beam midsurfaces · zero offset',status='completed');db.add(s);db.flush();doc.update(project_id=p.id,scenario_id=s.id)
 r=ModelRevision(project_id=p.id,design_scenario_id=s.id,revision_number=1,document_json=doc,source='manual_edit',prompt='Separate synthetic coupled-floor parametric review; original models unchanged.',user_id=user);db.add(r);db.commit();db.refresh(r)
 return dict(project_id=p.id,scenario_id=s.id,model_revision_id=r.id)

@router.post('/review')
def review(project_id:int,payload:Review,db:Session=Depends(get_db),user:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user)
 try:check_document(rev.document_json)
 except ValueError as e:raise HTTPException(422,str(e))
 result=dict(model_document_sha256=common.digest(rev.document_json),formulation=rev.document_json['metadata']['coupled_floor_review'],limitations=solver.LIMITATIONS,engineering_approval='DISABLED')
 result['proposal_sha256']=common.digest(result)
 return out(record(project_id,rev.id,PROPOSAL,'AWAITING_AUTHORIZATION',result,db,user),db,user)

@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user);row=db.query(EngineeringAnalysis).filter_by(id=payload.proposal_id,project_id=project_id,analysis_type=PROPOSAL).first()
 if not row:raise HTTPException(404,'Review not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,model_revision_id=row.model_revision_id,analysis_type=PROPOSAL).order_by(EngineeringAnalysis.id.desc()).first();r=row.result_json
 if latest.id!=row.id or out(row,db,user)['status']=='STALE' or payload.proposal_sha256!=r['proposal_sha256']:raise HTTPException(409,'Exact current latest review required')
 if r.get('analysis_id'):return out(db.get(EngineeringAnalysis,r['analysis_id']),db,user)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'Prepare a new review after attempted execution')
 if not lock.acquire(blocking=False):raise HTTPException(409,'Solver busy')
 try:
  rev,_=context(project_id,row.model_revision_id,db,user);check_document(rev.document_json)
  authorization=dict(actor_user_id=user,at=datetime.now(timezone.utc).isoformat(),scope='Exact synthetic shell/frame only; no engineering approval')
  row.status='AUTHORIZED';row.result_json={**r,'authorization':authorization};db.commit()
  case=solver.validated_run();result=dict(cases=[case],proposal_id=row.id,model_document_sha256=r['model_document_sha256'],authorization=authorization,limitations=solver.LIMITATIONS,engineering_approval='DISABLED',code_checks='DISABLED')
  result['evidence_sha256']=common.digest(result)
  saved=record(project_id,rev.id,RUN,case['status'],result,db,user);row.status='SOLVER_COMPLETED';row.result_json={**row.result_json,'analysis_id':saved.id};db.commit()
  (solver.ARTIFACTS/case['run_id']/'saved-review.json').write_text(json.dumps(out(saved,db,user),indent=2));return out(saved,db,user)
 except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as e:
  row.status='SOLVER_FAILED';db.commit();raise HTTPException(503,str(e))
 finally:lock.release()

@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user);row=db.query(EngineeringAnalysis).filter_by(id=analysis_id,project_id=project_id,analysis_type=RUN).first()
 if not row:raise HTTPException(404,'Evidence not found')
 from fastapi.responses import Response
 return Response(json.dumps(out(row,db,user),indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="coupled-floor-{analysis_id}.json"'})

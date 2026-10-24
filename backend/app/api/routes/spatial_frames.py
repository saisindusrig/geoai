"""Owned, revision-bound, explicitly authorized local spatial verification."""
import subprocess
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from typing import Literal
from app.db.session import get_db
from app.db.models import Project,DesignScenario,ModelRevision,EngineeringAnalysis
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context,Authorize
from app.api.routes.opensees import lock
from app.services.design import spatial_frame as solver, spatial_review,opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/spatial-frame',tags=['engineering'])
PROPOSAL='SPATIAL_FRAME_REVIEW';RUN='OPENSEES_SPATIAL_FRAME'
class Review(solver.Strict):
 model_revision_id:int=Field(gt=0)
 inputs:solver.Inputs
class Fixture(solver.Strict):
 storeys:Literal[1,2]
 review_parametric_geometry:Literal[True]
def record(pid,rid,kind,status,result,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='spatial-elastic-frame/1',status=status,result_json=result,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
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
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id)
 rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(40).all()
 return dict(records=[out(r,db,user_id) for r in rows],limitations=solver.LIMITS)
@router.post('/review-fixture')
def fixture(project_id:int,payload:Fixture,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id)
 # Two storeys require native 3D mechanics verification BEFORE a project is created.
 if not lock.acquire(blocking=False):raise HTTPException(409,'Solver busy')
 try:benchmarks=spatial_review.benchmarks()
 except (ValueError,RuntimeError,OSError) as e:raise HTTPException(503,str(e))
 finally:lock.release()
 doc,q=spatial_review.fixture(payload.storeys)
 p=Project(user_id=user_id,name=f'Spatial review · 2×1 bays · {payload.storeys} storey · synthetic',project_type='unclassified',units='metric',center_lat=12.9716,center_lng=77.5946,
  boundary_geojson={'type':'Polygon','coordinates':[[[77.5945,12.9715],[77.5948,12.9715],[77.5948,12.9718],[77.5945,12.9718],[77.5945,12.9715]]]})
 db.add(p);db.flush();s=DesignScenario(project_id=p.id,name='Reviewed parametric rigid-joint space frame',status='completed');db.add(s);db.flush()
 doc.update(project_id=p.id,scenario_id=s.id);doc['metadata']['spatial_frame_review']['benchmark_gate']=benchmarks
 r=ModelRevision(project_id=p.id,design_scenario_id=s.id,revision_number=1,document_json=doc,source='manual_edit',prompt='Explicit synthetic parametric geometry review; no original geometry modified.',user_id=user_id);db.add(r);db.commit();db.refresh(r)
 return dict(project_id=p.id,scenario_id=s.id,model_revision_id=r.id,inputs=q,benchmark_gate=benchmarks)
@router.post('/review')
def review(project_id:int,payload:Review,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id)
 try:q=solver.validate(payload.inputs.model_dump(),rev.document_json)
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
 result=dict(inputs=q,model_document_sha256=common.digest(rev.document_json),input_sha256=common.digest(q),limitations=solver.LIMITS,engineering_approval='DISABLED')
 result['proposal_sha256']=common.digest(result)
 return out(record(project_id,rev.id,PROPOSAL,'AWAITING_AUTHORIZATION',result,db,user_id),db,user_id)
@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);row=db.query(EngineeringAnalysis).filter_by(id=payload.proposal_id,project_id=project_id,analysis_type=PROPOSAL).first()
 if not row:raise HTTPException(404,'Review not found')
 r=row.result_json
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,model_revision_id=row.model_revision_id,analysis_type=PROPOSAL).order_by(EngineeringAnalysis.id.desc()).first()
 if latest.id!=row.id or out(row,db,user_id)['status']=='STALE' or r['proposal_sha256']!=payload.proposal_sha256:raise HTTPException(409,'Exact latest saved review required')
 if r.get('analysis_id'):return out(db.get(EngineeringAnalysis,r['analysis_id']),db,user_id)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'Prepare a new review after attempted execution')
 if not lock.acquire(blocking=False):raise HTTPException(409,'Solver busy')
 try:
  rev,_=context(project_id,row.model_revision_id,db,user_id);q=solver.validate(r['inputs'],rev.document_json)
  row.status='AUTHORIZED';row.result_json={**r,'authorization':dict(actor_user_id=user_id,at=datetime.now(timezone.utc).isoformat(),scope='Exact saved synthetic linear spatial frame; not engineering approval')};db.commit()
  gate=spatial_review.benchmarks();cases=[solver.solve(q,c) for c in q['cases']]
  result=dict(cases=cases,benchmark_gate=gate,inputs=q,proposal_id=row.id,model_revision_id=rev.id,model_document_sha256=r['model_document_sha256'],input_sha256=r['input_sha256'],authorization=row.result_json['authorization'],limitations=solver.LIMITS,engineering_approval='DISABLED',code_checks='DISABLED')
  status='VERIFIED' if all(c['status']=='VERIFIED' for c in cases) else 'VERIFICATION_FAILED'
  # A separate aggregate manifest binds native case artifacts to saved source identities.
  result['evidence_sha256']=common.digest(result)
  (solver.ARTIFACTS/cases[0]['run_id']/'review-manifest.json').write_text(json.dumps(result,indent=2))
  saved=record(project_id,rev.id,RUN,status,result,db,user_id);row.status='SOLVER_COMPLETED';row.result_json={**row.result_json,'analysis_id':saved.id};db.commit();return out(saved,db,user_id)
 except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as e:
  row.status='SOLVER_FAILED';db.commit();raise HTTPException(503,str(e))
 finally:lock.release()
@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);row=db.query(EngineeringAnalysis).filter_by(id=analysis_id,project_id=project_id,analysis_type=RUN).first()
 if not row:raise HTTPException(404,'Evidence not found')
 from fastapi.responses import Response
 return Response(json.dumps(out(row,db,user_id),indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="spatial-evidence-{analysis_id}.json"'})

@router.get('/{analysis_id}/floor-evidence')
def floor_evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 from app.services.design.floor_transfer import evidence as derive
 get_owned_project(project_id,db,user_id);row=db.query(EngineeringAnalysis).filter_by(id=analysis_id,project_id=project_id,analysis_type=RUN).first()
 if not row:raise HTTPException(404,'Evidence not found')
 if out(row,db,user_id)['status']!='VERIFIED':raise HTTPException(409,'Current verified spatial result required')
 try:cases=[derive(c) for c in row.result_json['cases']]
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
 return dict(analysis_id=row.id,model_revision_id=row.model_revision_id,model_document_sha256=row.result_json['model_document_sha256'],input_sha256=row.result_json['input_sha256'],source_evidence_sha256=row.result_json['evidence_sha256'],cases=cases,engineering_approval='DISABLED')


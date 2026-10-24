"""Explicit verification inputs, bounded AI proposals and authorized local beam/frame solves."""
import json,hashlib
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy.orm import Session
from app.db.models import ModelRevision,EngineeringAnalysis
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.opensees import lock
from app.services.design import elastic_frame as solver,opensees_benchmark as common
from app.services.ai import column_agent as agent
from app.api.routes.column_agent import invoke

router=APIRouter(prefix='/api/projects/{project_id}/engineering/elastic',tags=['engineering'])
INPUT='ELASTIC_FRAME_INPUT';PROPOSAL='AI_FRAME_PROPOSAL';RUN='OPENSEES_ELASTIC_FRAME';EXPLANATION='AI_FRAME_EXPLANATION'
class Save(solver.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Prepare(BaseModel):
 model_config=ConfigDict(extra='forbid')
 model_revision_id:int=Field(gt=0)
 provider:Literal['mock','nebius']
 model:Literal['zai-org/GLM-5.3-Flash','zai-org/GLM-5.3']
class Authorize(BaseModel):
 model_config=ConfigDict(extra='forbid')
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_solver:Literal[True]

def context(pid,rid,db,user,latest=True):
 get_owned_project(pid,db,user);r=db.query(ModelRevision).filter_by(project_id=pid,id=rid).first()
 if not r:raise HTTPException(404,'Revision not found')
 current=db.query(ModelRevision).filter_by(design_scenario_id=r.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
 if latest and current.id!=rid:raise HTTPException(409,'Select latest saved benchmark revision')
 geometry=r.document_json.get('metadata',{}).get('elastic_benchmark')
 if not geometry or geometry.get('kind') not in ('cantilever','portal'):raise HTTPException(422,'Only dedicated saved beam/portal verification geometry supported; whole-platform frame mapping disabled')
 try:solver.verify_saved_geometry(r.document_json,geometry)
 except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))
 return r,geometry
def latest_input(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def record(pid,rid,kind,status,result,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='elastic-beam-frame/1',status=status,result_json=result,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def out(row,db,user):
 status=row.status;r=row.result_json
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user);current=latest_input(row.project_id,rev.design_scenario_id,db)
  if common.digest(rev.document_json)!=r['model_document_sha256'] or (row.analysis_type!=INPUT and r.get('input_record_id')!=(current.id if current else None)):status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def owned(pid,rid,kind,db,user):
 get_owned_project(pid,db,user);row=db.query(EngineeringAnalysis).filter_by(id=rid,project_id=pid,analysis_type=kind).first()
 if not row:raise HTTPException(404,'Evidence not found')
 return row
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id)
 rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,PROPOSAL,RUN,EXPLANATION])).order_by(EngineeringAnalysis.id.desc()).limit(40).all()
 return {'records':[out(row,db,user_id) for row in rows],'limitations':solver.LIMITS}
@router.post('/inputs')
def inputs(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,geo=context(project_id,payload.model_revision_id,db,user_id);q=payload.model_dump(exclude={'model_revision_id','base_input_id'})
 if any(q[k]!=geo[k] for k in ('kind','length_m','height_m')):raise HTTPException(422,'Engineering geometry must match saved verification geometry')
 latest=latest_input(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(latest.id if latest else None):raise HTTPException(409,'Inputs changed; reload')
 result=dict(inputs=q,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),input_sha256=common.digest(q),engineering_approval='DISABLED',code_checks='DISABLED')
 return out(record(project_id,rev.id,INPUT,'INPUT_READY',result,db,user_id),db,user_id)
@router.post('/proposals')
async def proposal(project_id:int,payload:Prepare,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,geo=context(project_id,payload.model_revision_id,db,user_id);input=latest_input(project_id,rev.design_scenario_id,db)
 if input and out(input,db,user_id)['status']=='STALE':input=None
 args=dict(model_revision_id=rev.id,input_record_id=input.id if input else None,component_ids=[c['id'] for c in rev.document_json['components']])
 missing=[] if input else list(solver.Inputs.model_fields)
 context_data=dict(arguments=args,missing=missing,geometry=geo,components=rev.document_json['components'],engineering_inputs=input.result_json['inputs'] if input else None,limitations=solver.LIMITS)
 answer,usage=await invoke('frame_proposal',context_data,payload.model,payload.provider,project_id,rev.id,db,user_id)
 context(project_id,rev.id,db,user_id);fresh=latest_input(project_id,rev.design_scenario_id,db)
 if (fresh.id if fresh and out(fresh,db,user_id)['status']!='STALE' else None)!=args['input_record_id']:raise HTTPException(409,'Inputs changed during proposal')
 result=dict(**args,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),proposal=answer,missing=missing,usage=usage,provider=payload.provider,model=payload.model,engineering_approval='DISABLED',code_checks='DISABLED')
 result['proposal_sha256']=common.digest(result)
 return out(record(project_id,rev.id,PROPOSAL,'NEEDS_INPUT' if missing else 'AWAITING_AUTHORIZATION',result,db,user_id),db,user_id)
@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,payload.proposal_id,PROPOSAL,db,user_id);r=row.result_json
 if r['proposal_sha256']!=payload.proposal_sha256 or out(row,db,user_id)['status']=='STALE' or r['missing']:raise HTTPException(409,'Exact current proposal and explicit inputs required')
 if r.get('analysis_id'):return out(owned(project_id,r['analysis_id'],RUN,db,user_id),db,user_id)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'Previous execution attempted; prepare new proposal')
 if not lock.acquire(blocking=False):raise HTTPException(409,'Solver busy')
 try:
  rev,_=context(project_id,row.model_revision_id,db,user_id);input=latest_input(project_id,rev.design_scenario_id,db);q=input.result_json['inputs']
  row.status='AUTHORIZED';row.result_json={**r,'authorization':{'actor_user_id':user_id,'scope':'Exact isolated beam/portal verification; not safety approval'}};db.commit()
  suite=solver.suite(q['kind'])
  if suite['status']!='VERIFIED':raise ValueError('Prerequisite suite failed')
  result=solver.run(q);result.update(verification_suite=suite,model_document_sha256=common.digest(rev.document_json),model_revision_id=rev.id,input_record_id=input.id,scenario_id=rev.design_scenario_id)
  (common.ARTIFACTS/result['run_id']/'manifest.json').write_text(json.dumps(result,indent=2))
  analysis=record(project_id,rev.id,RUN,result['status'],result,db,user_id);row.result_json={**row.result_json,'analysis_id':analysis.id};row.status='SOLVER_COMPLETED';db.commit();return out(analysis,db,user_id)
 except (RuntimeError,ValueError) as error:
  row.status='SOLVER_FAILED';db.commit();raise HTTPException(503,str(error))
 finally:lock.release()
@router.post('/proposals/{proposal_id}/explain')
async def explain(project_id:int,proposal_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 p=owned(project_id,proposal_id,PROPOSAL,db,user_id);r=p.result_json
 if not r.get('analysis_id') or out(p,db,user_id)['status']=='STALE':raise HTTPException(409,'Current authorized result required')
 a=owned(project_id,r['analysis_id'],RUN,db,user_id)
 if out(a,db,user_id)['status']!='VERIFIED':raise HTTPException(409,'Only verified numerical evidence may be explained')
 data=dict(analysis_id=a.id,evidence_sha256=common.digest(a.result_json),actual_nodes=a.result_json['nodes'],actual_reactions=a.result_json['reactions'],actual_element_end_forces=[e['local_end_forces_si'] for e in a.result_json['elements']],comparisons=a.result_json['comparisons'],limitations=solver.LIMITS)
 answer,usage=await invoke('explain',data,r['model'],r['provider'],project_id,p.model_revision_id,db,user_id)
 if out(a,db,user_id)['status']!='VERIFIED':raise HTTPException(409,'Evidence changed during explanation')
 result=dict(explanation=answer,usage=usage,analysis_id=a.id,input_record_id=r['input_record_id'],model_document_sha256=r['model_document_sha256'],engineering_approval='DISABLED')
 return out(record(project_id,p.model_revision_id,EXPLANATION,'EXPLANATION_UNVERIFIED',result,db,user_id),db,user_id)
@router.get('/{analysis_id}/artifacts/{filename}')
def artifact(project_id:int,analysis_id:int,filename:str,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,analysis_id,RUN,db,user_id)
 if filename not in solver.FILES:raise HTTPException(404,'Unknown artifact')
 path=common.ARTIFACTS/row.result_json['run_id']/filename
 if not path.is_file():raise HTTPException(404,'Artifact unavailable')
 return dict(filename=filename,contents=path.read_text(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

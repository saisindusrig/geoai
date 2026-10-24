"""Explicit verification inputs, bounded AI proposals and authorized local beam/frame solves."""
import json,hashlib
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy.orm import Session
from app.db.models import ModelRevision,EngineeringAnalysis
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.opensees import lock
from app.services.design import physical_frame as solver,elastic_frame as elastic,eccentric_frame as eccentric,gravity_frame as gravity,opensees_benchmark as common
from app.services.ai import column_agent as agent
from app.api.routes.column_agent import invoke
from app.api.routes.cad_frames import source_provenance

router=APIRouter(prefix='/api/projects/{project_id}/engineering/assembly',tags=['engineering'])
INPUT='PHYSICAL_FRAME_INPUT';PROPOSAL='AI_ASSEMBLY_PROPOSAL';RUN='OPENSEES_PHYSICAL_FRAME';EXPLANATION='AI_ASSEMBLY_EXPLANATION'
class Save(solver.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Prepare(BaseModel):
 model_config=ConfigDict(extra='forbid')
 model_revision_id:int=Field(gt=0)
 provider:Literal['mock','nebius']
 model:Literal['zai-org/GLM-5.3-Flash','zai-org/GLM-5.3']
 component_ids:list[str]=Field(min_length=3,max_length=3)
 allow_rigid_offsets:bool=False
class Authorize(BaseModel):
 model_config=ConfigDict(extra='forbid')
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_solver:Literal[True]

def context(pid,rid,db,user,latest=True):
 get_owned_project(pid,db,user);r=db.query(ModelRevision).filter_by(project_id=pid,id=rid).first()
 if not r:raise HTTPException(404,'Revision not found')
 current=db.query(ModelRevision).filter_by(design_scenario_id=r.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
 if latest and current.id!=rid:raise HTTPException(409,'Select latest saved physical model revision')
 return r,None

def latest_input(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def record(pid,rid,kind,status,result,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='physical-frame/5-unequal-gravity' if result.get('physical_to_analytical_graph',{}).get('method_version')=='cad-planar-unequal-gravity/1' else 'physical-frame/4-unequal' if result.get('physical_to_analytical_graph',{}).get('unequal_heights') else 'physical-frame/3-gravity' if result.get('inputs',{}).get('load_cases') else 'physical-frame/2-rigid-offset' if result.get('physical_to_analytical_graph',{}).get('beam_offsets_m') else 'physical-frame/1',status=status,result_json=result,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def out(row,db,user):
 status=row.status;r=row.result_json
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user);current=latest_input(row.project_id,rev.design_scenario_id,db)
  if row.analysis_type==PROPOSAL and r.get('input_record_id') is None and current and set(current.result_json['inputs']['component_ids'])!=set(r['component_ids']):current=None
  if common.digest(rev.document_json)!=r['model_document_sha256'] or (row.analysis_type!=INPUT and r.get('input_record_id')!=(current.id if current else None)):status='STALE'
  if r.get('cad_source_provenance') and source_provenance(rev,r['physical_to_analytical_graph'],db,user)!=r['cad_source_provenance']:status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def owned(pid,rid,kind,db,user):
 get_owned_project(pid,db,user);row=db.query(EngineeringAnalysis).filter_by(id=rid,project_id=pid,analysis_type=kind).first()
 if not row:raise HTTPException(404,'Evidence not found')
 return row
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id),compact:bool=False):
 get_owned_project(project_id,db,user_id)
 rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,PROPOSAL,RUN,EXPLANATION])).order_by(EngineeringAnalysis.id.desc()).limit(40).all()
 records=[out(row,db,user_id) for row in rows]
 if compact:
  for record in records:
   full=record['result'];record['result']={k:v for k,v in full.items() if k not in ('verification_suite','rigid_offset_verification_suite','uniform_load_verification_suite','independent_reference')}
   if full.get('load_case_results'):record['result']['load_case_results']=[{k:v for k,v in case.items() if k!='independent_reference'} for case in full['load_case_results']]
   record['result']['verification_evidence']={'beam_frame_status':full.get('verification_suite',{}).get('status'),'rigid_offset_status':full.get('rigid_offset_verification_suite',{}).get('status'),'uniform_load_status':full.get('uniform_load_verification_suite',{}).get('status'),'full_evidence':'Immutable solver manifest artifact'}
 return {'records':records,'limitations':solver.LIMITS}
@router.post('/inputs')
def inputs(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,geo=context(project_id,payload.model_revision_id,db,user_id);q=payload.model_dump(exclude={'model_revision_id','base_input_id'})
 try:graph=solver.graph(rev.document_json,q)
 except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))
 latest=latest_input(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(latest.id if latest else None):raise HTTPException(409,'Inputs changed; reload')
 result=dict(inputs=q,physical_to_analytical_graph=graph,cad_source_provenance=source_provenance(rev,graph,db,user_id),scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),input_sha256=common.digest(q),engineering_approval='DISABLED',code_checks='DISABLED')
 return out(record(project_id,rev.id,INPUT,'INPUT_READY',result,db,user_id),db,user_id)
@router.post('/proposals')
async def proposal(project_id:int,payload:Prepare,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id)
 if payload.provider!='mock':raise HTTPException(403,'Cloud inference locked for physical assemblies; offline fixtures only')
 try:geo=solver.geometry(rev.document_json,payload.component_ids,allow_rigid_offsets=payload.allow_rigid_offsets)
 except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))
 input=latest_input(project_id,rev.design_scenario_id,db)
 if input and (out(input,db,user_id)['status']=='STALE' or set(input.result_json['inputs']['component_ids'])!=set(payload.component_ids)):input=None
 if input:geo=input.result_json['physical_to_analytical_graph']
 args=dict(model_revision_id=rev.id,input_record_id=input.id if input else None,component_ids=geo['component_ids'])
 missing=[] if input else list(solver.Inputs.model_fields)
 if missing and geo.get('unequal_heights') and not rev.document_json.get('metadata',{}).get('unequal_gravity_review'):missing=['sections','connections','supports','support_source','load_pattern','load_n','load_source','purpose','elements_per_member','units']
 context_data=dict(arguments=args,missing=missing,geometry=geo,components=[c for c in rev.document_json['components'] if c['id'] in payload.component_ids],engineering_inputs=input.result_json['inputs'] if input else None,limitations=solver.LIMITS)
 answer,usage=await invoke('frame_proposal',context_data,payload.model,payload.provider,project_id,rev.id,db,user_id)
 context(project_id,rev.id,db,user_id);fresh=latest_input(project_id,rev.design_scenario_id,db)
 if (fresh.id if fresh and out(fresh,db,user_id)['status']!='STALE' and set(fresh.result_json['inputs']['component_ids'])==set(payload.component_ids) else None)!=args['input_record_id']:raise HTTPException(409,'Inputs changed during proposal')
 result=dict(**args,physical_to_analytical_graph=geo,cad_source_provenance=source_provenance(rev,geo,db,user_id),scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),proposal=answer,missing=missing,usage=usage,provider=payload.provider,model=payload.model,engineering_approval='DISABLED',code_checks='DISABLED')
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
  row.status='AUTHORIZED';row.result_json={**r,'authorization':{'actor_user_id':user_id,'authorized_at':datetime.now(timezone.utc).isoformat(),'scope':'Exact selected saved physical frame numerical verification; not safety approval'}};db.commit()
  solver.graph(rev.document_json,q)
  suite=elastic.suite('portal')
  offset_suite=eccentric.suite() if any(j['behavior']=='rigid_offset' for j in q['connections']) else None
  if suite['status']!='VERIFIED':raise ValueError('Prerequisite suite failed')
  gravity_suite=gravity.suite() if q.get('load_cases') else None
  result=solver.run(q,rev.document_json)
  if gravity_suite:result['uniform_load_verification_suite']=gravity_suite
  if offset_suite:result['rigid_offset_verification_suite']=offset_suite
  result.update(verification_suite=suite,cad_source_provenance=source_provenance(rev,result['physical_to_analytical_graph'],db,user_id),model_document_sha256=common.digest(rev.document_json),model_revision_id=rev.id,input_record_id=input.id,scenario_id=rev.design_scenario_id)
  for case in result.get('load_case_results',[]):
   case.update(cad_source_provenance=result['cad_source_provenance'],model_document_sha256=result['model_document_sha256'],model_revision_id=rev.id,input_record_id=input.id,scenario_id=rev.design_scenario_id,engineering_approval='DISABLED',code_checks='DISABLED')
   (common.ARTIFACTS/case['run_id']/'manifest.json').write_text(json.dumps(case,indent=2))
  (common.ARTIFACTS/result['run_id']/'manifest.json').write_text(json.dumps(result,indent=2))
  analysis=record(project_id,rev.id,RUN,result['status'],result,db,user_id);row.result_json={**row.result_json,'analysis_id':analysis.id};row.status='SOLVER_COMPLETED';db.commit();return out(analysis,db,user_id)
 except (RuntimeError,ValueError,OSError,TypeError) as error:
  row.status='SOLVER_FAILED';db.commit();raise HTTPException(503,str(error))
 finally:lock.release()
@router.post('/proposals/{proposal_id}/explain')
async def explain(project_id:int,proposal_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id),payload:dict|None=None):
 p=owned(project_id,proposal_id,PROPOSAL,db,user_id);r=p.result_json
 if not r.get('analysis_id') or out(p,db,user_id)['status']=='STALE':raise HTTPException(409,'Current authorized result required')
 a=owned(project_id,r['analysis_id'],RUN,db,user_id)
 if out(a,db,user_id)['status']!='VERIFIED':raise HTTPException(409,'Only verified numerical evidence may be explained')
 if payload and (set(payload)-{'case_name'} or (payload.get('case_name') is not None and not isinstance(payload['case_name'],str))):raise HTTPException(422,'Only a saved load-case name is accepted')
 evidence=a.result_json
 if payload and payload.get('case_name') is not None:
  evidence=next((r for r in [a.result_json]+a.result_json.get('load_case_results',[]) if r.get('case_name')==payload['case_name']),None)
  if evidence is None:raise HTTPException(422,'Unknown saved load case')
 data=dict(analysis_id=a.id,evidence_sha256=common.digest(evidence),case_name=evidence.get('case_name'),case_kind=evidence.get('case_kind'),applied_loads=evidence.get('applied_loads'),superposition_verification=evidence.get('superposition_verification'),actual_nodes=evidence['nodes'],actual_reactions=evidence['reactions'],actual_element_end_forces=[e['local_end_forces_si'] for e in evidence['elements']],comparisons=evidence['comparisons'],limitations=solver.LIMITS)
 answer,usage=await invoke('explain',data,r['model'],r['provider'],project_id,p.model_revision_id,db,user_id)
 if out(a,db,user_id)['status']!='VERIFIED':raise HTTPException(409,'Evidence changed during explanation')
 result=dict(explanation=answer,usage=usage,case_name=evidence.get('case_name'),analysis_id=a.id,input_record_id=r['input_record_id'],model_document_sha256=r['model_document_sha256'],cad_source_provenance=r.get('cad_source_provenance'),physical_to_analytical_graph=r.get('physical_to_analytical_graph'),engineering_approval='DISABLED')
 return out(record(project_id,p.model_revision_id,EXPLANATION,'EXPLANATION_UNVERIFIED',result,db,user_id),db,user_id)
@router.get('/{analysis_id}/artifacts/{filename}')
def artifact(project_id:int,analysis_id:int,filename:str,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id),case_name:str|None=None):
 row=owned(project_id,analysis_id,RUN,db,user_id)
 if filename not in solver.FILES:raise HTTPException(404,'Unknown artifact')
 result=row.result_json
 if case_name is not None:
  candidates=[result]+result.get('load_case_results',[]);result=next((r for r in candidates if r.get('case_name')==case_name),None)
  if result is None:raise HTTPException(404,'Unknown saved load case')
 path=common.ARTIFACTS/result['run_id']/filename
 if not path.is_file():raise HTTPException(404,'Artifact unavailable')
 return dict(filename=filename,contents=path.read_bytes().decode('utf-8'),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

@router.get('/{analysis_id}/report')
def report(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,analysis_id,RUN,db,user_id)
 current=out(row,db,user_id)
 if current['status']!='VERIFIED':raise HTTPException(409,'Current numerically verified saved evidence required; refresh stale analysis first')
 payload=dict(report_version=1,project_id=project_id,analysis_id=row.id,model_revision_id=row.model_revision_id,
              algorithm_version=row.algorithm_version,status=current['status'],limitations=solver.LIMITS,
              engineering_approval='DISABLED',code_checks='DISABLED',evidence=row.result_json)
 return Response(json.dumps(payload,indent=2,allow_nan=False),media_type='application/json',
                 headers={'Content-Disposition':f'attachment; filename=project_{project_id}_frame_{analysis_id}_report.json'})

class Preview(BaseModel):
 allow_rigid_offsets:bool=False
 model_config=ConfigDict(extra='forbid')
 model_revision_id:int=Field(gt=0)
 component_ids:list[str]=Field(min_length=3,max_length=3)
@router.post('/preview')
def preview(project_id:int,payload:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id)
 try:return solver.geometry(rev.document_json,payload.component_ids,allow_rigid_offsets=payload.allow_rigid_offsets)
 except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))

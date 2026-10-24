"""Reviewable AI proposal → explicit solver authorization → evidence-bound explanation."""
import asyncio
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.core.config import settings
from app.api.routes import physical_columns as columns
from app.api.routes.projects import get_owned_project
from app.services.ai import column_agent as agent
from app.services.ai.nebius import sanitized
from app.services.design.opensees_benchmark import digest

router=APIRouter(prefix='/api/projects/{project_id}/engineering/agent',tags=['engineering-agent'])
PROPOSAL='AI_COLUMN_PROPOSAL';EXPLANATION='AI_COLUMN_EXPLANATION';USAGE='AI_COLUMN_USAGE'
REVIEW='AI_PROJECT_REVIEW'
inference_lock=asyncio.Lock()

class Prepare(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_revision_id:int=Field(gt=0)
    component_id:str=Field(min_length=1,max_length=150)
    provider:Literal['mock','nebius']
    model:Literal['zai-org/GLM-5.3','zai-org/GLM-5.3-Flash']

class Authorize(BaseModel):
    model_config=ConfigDict(extra='forbid')
    proposal_id:int=Field(gt=0)
    proposal_sha256:str=Field(min_length=64,max_length=64)
    authorize_solver:Literal[True]

def owned(db,pid,rowid,kind,user):
    get_owned_project(pid,db,user)
    row=db.query(EngineeringAnalysis).filter_by(project_id=pid,id=rowid,analysis_type=kind).first()
    if not row:raise HTTPException(404,'Agent record not found')
    return row

def snapshot(pid,rid,cid,db,user):
    revision,geo=columns.context(pid,rid,cid,db,user,True)
    inputs=columns.current_input(db,pid,revision.design_scenario_id,cid)
    current=inputs and inputs.model_revision_id==rid and inputs.result_json['model_document_sha256']==digest(revision.document_json)
    return revision,geo,inputs if current else None

def record(db,pid,rid,kind,status,result,user):
    row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='nebius-column-agent/1',status=status,result_json=result,actor_user_id=user)
    db.add(row);db.commit();db.refresh(row);return row

def view(row,db,user):
    result=row.result_json;status=row.status
    try:
        if row.analysis_type==PROPOSAL:
            _,_,inputs=snapshot(row.project_id,row.model_revision_id,result['component_id'],db,user)
            if (inputs.id if inputs else None)!=result['input_record_id']:status='STALE'
        elif row.analysis_type==EXPLANATION:
            analysis=db.get(EngineeringAnalysis,result['analysis_id'])
            revision=db.get(ModelRevision,row.model_revision_id)
            inputs=columns.current_input(db,row.project_id,revision.design_scenario_id,result['component_id'])
            if columns.out(analysis,revision,inputs,db)['status']=='STALE':status='STALE'
        elif row.analysis_type==REVIEW:
            _,context=project_context(row.project_id,row.model_revision_id,db,user)
            if context['model_document_sha256']!=result['model_document_sha256']:status='STALE'
            if digest(context['engineering_inputs'])!=result.get('engineering_inputs_sha256'):status='STALE'
    except HTTPException:status='STALE'
    return {'id':row.id,'model_revision_id':row.model_revision_id,'status':status,'result':result}

async def invoke(stage,payload,model,provider,pid,rid,db,user):
    async with inference_lock:
        spent=sum(float(r.result_json.get('budget_accounted_usd',0)) for r in db.query(EngineeringAnalysis).filter_by(analysis_type=USAGE).all())
        ledger=None
        if provider=='nebius':
            if not agent.availability()['cloud_inference_enabled']:raise HTTPException(403,'Cloud inference budget is not approved or backend configuration is unavailable')
            remaining=min(settings.ENGINEERING_AI_BUDGET_USD,10)-spent
            reserve=agent.reservation(stage,payload,model)
            if remaining<=reserve:raise HTTPException(403,'Approved inference budget cannot cover the conservative request reservation')
            # Persist reservation BEFORE the network request; failed/unknown requests retain it.
            ledger=record(db,pid,rid,USAGE,'RESERVED',{'budget_accounted_usd':reserve,'actual_charge_unknown':True,'model':model,'stage':stage,'started_at':datetime.now(timezone.utc).isoformat(),'request_sha256':digest(payload)},user)
        usage_evidence=[]
        try:
            if provider=='nebius':answer,usage=await agent.infer(stage,payload,model,provider,spent,usage_sink=usage_evidence)
            else:answer,usage=await agent.infer(stage,payload,model,provider,spent)
            schema=agent.FrameProposal if stage=='frame_proposal' else agent.Proposal if stage=='proposal' else agent.ProjectReview if stage=='review' else agent.Explanation
            validated=schema.model_validate(answer).model_dump()
            if stage in ('proposal','frame_proposal'):
                if validated['tool']['arguments']!=payload['arguments'] or validated['missing_properties']!=payload['missing']:raise ValueError('AI changed restricted arguments or missing-input list')
                import re
                if re.search(r'\d|\b(?:safe|adequate|compliant|approved)\b',validated['summary'],re.I):raise ValueError('AI proposal must not introduce numeric or engineering-approval claims')
                validated['summary']=sanitized(validated['summary'],max_length=2000)
            elif stage=='explain':
                if validated['analysis_id']!=payload['analysis_id'] or validated['evidence_sha256']!=payload['evidence_sha256']:raise ValueError('AI explanation is not bound to solver evidence')
                # Quantitative values belong to the authoritative solver display, never AI prose.
                import re
                if re.search(r'\d',validated['narrative']):raise ValueError('AI prose must not introduce numerical claims; use the computed-results display')
                if re.search(r'\b(safe|adequate|compliant|approved|passes?\s+(?:code|buckling|bending))\b',validated['narrative'],re.I):raise ValueError('Unsupported engineering-approval claim')
                validated['narrative']=sanitized(validated['narrative'],max_length=3000) if provider=='nebius' else validated['narrative']
            else:
                if any(validated[k]!=payload[k] for k in ('model_revision_id','component_count','category_counts')):raise ValueError('AI inventory does not match saved model')
                ids={c['id'] for c in payload['components']}
                if any(cid not in ids for fact in validated['facts'] for cid in fact['component_ids']):raise ValueError('AI cited a nonexistent component')
            if ledger:
                ledger.status='ACCOUNTED';ledger.result_json={**ledger.result_json,'budget_accounted_usd':usage['estimated_cost_usd'],'usage':usage};db.commit()
            return validated,usage
        except (ValueError,KeyError,IndexError,TypeError,ValidationError) as error:
            if ledger:
                ledger.status='FAILED_RESPONSE_VALIDATION' if usage_evidence and usage_evidence[-1].get('http_status')==200 else 'FAILED_USAGE_UNKNOWN'
                ledger.result_json={**ledger.result_json,'error_type':type(error).__name__,'validation_error':sanitized(str(error)),'provider_error_code':getattr(error,'code',None)}
                if usage_evidence:ledger.result_json={**ledger.result_json,'budget_accounted_usd':usage_evidence[-1]['estimated_cost_usd'],'usage':usage_evidence[-1]}
                db.commit()
            raise HTTPException(502,'AI response failed validation or provider unavailable; model unchanged and solver not authorized')

@router.get('/availability')
def availability(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    get_owned_project(project_id,db,user_id);result=agent.availability()
    result['budget_accounted_usd']=sum(float(r.result_json.get('budget_accounted_usd',0)) for r in db.query(EngineeringAnalysis).filter_by(analysis_type=USAGE).all())
    return result

@router.get('')
def history(project_id:int,component_id:str,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    get_owned_project(project_id,db,user_id)
    rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,EXPLANATION]),EngineeringAnalysis.result_json['component_id'].as_string()==component_id).order_by(EngineeringAnalysis.id.desc()).limit(20).all()
    return {'records':[view(r,db,user_id) for r in rows]}

class ReviewRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_revision_id:int=Field(gt=0)
    provider:Literal['mock','nebius']
    model:Literal['zai-org/GLM-5.3','zai-org/GLM-5.3-Flash']
    request:str=Field(default='Review this structure, identify a possible load path, missing engineering inputs and supported analysis scope. Suggest improvements for review only.',min_length=1,max_length=2000)

def project_context(project_id,revision_id,db,user):
    from app.services.design.editable_model import validate_document
    from collections import Counter
    project=get_owned_project(project_id,db,user)
    revision=db.query(ModelRevision).filter_by(project_id=project_id,id=revision_id).first()
    if not revision:raise HTTPException(404,'Saved model revision not found')
    latest=db.query(ModelRevision).filter_by(design_scenario_id=revision.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
    if latest.id!=revision.id:raise HTTPException(409,'Use latest saved model')
    doc=revision.document_json
    errors=validate_document(doc,project_id=project_id,scenario_id=revision.design_scenario_id,project_type=project.project_type)
    if errors:raise HTTPException(422,'Saved model geometry validation failed')
    components=[{'id':c['id'],'category':c['category'],'geometry':c['geometry'],'transform':c['transform'],'references':c.get('metadata',{}).get('references',[]),'attachment_kind':c.get('metadata',{}).get('attachment_kind'),'engineering_status':'UNVERIFIED; rendering material is not an engineering property'} for c in doc['components']]
    all_inputs=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=columns.INPUT_TYPE,model_revision_id=revision.id).order_by(EngineeringAnalysis.id.desc()).all()
    explicit=[];seen=set()
    for row in all_inputs:
        r=row.result_json
        if r['component_id'] not in seen and r['model_document_sha256']==digest(doc):
            seen.add(r['component_id']);explicit.append({'component_id':r['component_id'],'input_record_id':row.id,'properties':r['engineering_inputs']})
    return revision,{'model_revision_id':revision.id,'model_document_sha256':digest(doc),'units':doc['units'],'frame':doc.get('metadata',{}).get('frame'),'component_count':len(components),'category_counts':dict(Counter(c['category'] for c in components)),'components':components,'attachment_assemblies':doc.get('generator_parameters',{}).get('platform_attachments',{}).get('items',[]),'synthetic_bays':doc.get('metadata',{}).get('synthetic_bays'),'engineering_inputs':explicit,'limitations':agent.LIMITATIONS,'review_schema':agent.ProjectReview.model_json_schema()}

@router.post('/project-reviews')
async def project_review(project_id:int,payload:ReviewRequest,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    revision,context=project_context(project_id,payload.model_revision_id,db,user_id)
    context['user_request']=payload.request
    answer,usage=await invoke('review',context,payload.model,payload.provider,project_id,revision.id,db,user_id)
    fresh,current_context=project_context(project_id,revision.id,db,user_id)
    if digest(current_context['engineering_inputs'])!=digest(context['engineering_inputs']):raise HTTPException(409,'Engineering inputs changed during review')
    result={'model_revision_id':revision.id,'model_document_sha256':digest(fresh.document_json),'engineering_inputs_sha256':digest(context['engineering_inputs']),'review':answer,'usage':usage,'engineering_approval':'DISABLED','code_checks':'DISABLED','context_sha256':digest(context),'component_count':context['component_count'],'category_counts':context['category_counts']}
    return view(record(db,project_id,revision.id,REVIEW,'REVIEW_UNVERIFIED',result,user_id),db,user_id)

@router.get('/project-reviews')
def project_reviews(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    get_owned_project(project_id,db,user_id)
    return {'records':[view(r,db,user_id) for r in db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=REVIEW).order_by(EngineeringAnalysis.id.desc()).limit(20).all()]}

@router.post('/proposals')
async def prepare(project_id:int,payload:Prepare,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    revision,geo,inputs=snapshot(project_id,payload.model_revision_id,payload.component_id,db,user_id)
    engineering=inputs.result_json['engineering_inputs'] if inputs else None
    missing=[] if inputs else agent.FIELDS
    arguments={'model_revision_id':revision.id,'component_id':payload.component_id,'input_record_id':inputs.id if inputs else None}
    context={'physical_component':geo,'engineering_inputs':engineering,'missing':missing,'arguments':arguments,'limitations':agent.LIMITATIONS}
    proposal,usage=await invoke('proposal',context,payload.model,payload.provider,project_id,revision.id,db,user_id)
    # Recheck after inference, which may outlive another saved edit/input update.
    _,_,fresh=snapshot(project_id,revision.id,payload.component_id,db,user_id)
    if (fresh.id if fresh else None)!=arguments['input_record_id']:raise HTTPException(409,'Engineering inputs changed during proposal preparation')
    result={**arguments,'scenario_id':revision.design_scenario_id,'physical_component':geo,'engineering_inputs':engineering,'missing':missing,'proposal':proposal,'usage':usage,'provider':payload.provider,'model':payload.model,'limitations':agent.LIMITATIONS,'engineering_approval':'DISABLED','code_checks':'DISABLED','model_document_sha256':digest(revision.document_json)}
    result['proposal_sha256']=digest(result)
    row=record(db,project_id,revision.id,PROPOSAL,'NEEDS_INPUT' if missing else 'AWAITING_SOLVER_AUTHORIZATION',result,user_id)
    return view(row,db,user_id)

@router.post('/authorize-run')
def authorize(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    row=owned(db,project_id,payload.proposal_id,PROPOSAL,user_id);r=row.result_json
    if payload.proposal_sha256!=r['proposal_sha256']:raise HTTPException(409,'Proposal identity mismatch')
    current=view(row,db,user_id)
    if current['status']=='STALE' or r['missing']:raise HTTPException(409,'Proposal is stale or missing explicit engineering inputs')
    if r.get('solver_analysis_id'):
        analysis=owned(db,project_id,r['solver_analysis_id'],columns.RUN_TYPE,user_id)
        revision=db.get(ModelRevision,row.model_revision_id)
        inputs=columns.current_input(db,project_id,revision.design_scenario_id,r['component_id'])
        return columns.out(analysis,revision,inputs,db)
    if row.status!='AWAITING_SOLVER_AUTHORIZATION':raise HTTPException(409,'This authorization was already attempted; prepare a new proposal')
    row.status='SOLVER_AUTHORIZED';row.result_json={**r,'solver_authorization':{'actor_user_id':user_id,'authorized_at':datetime.now(timezone.utc).isoformat(),'scope':'Execute the exact isolated axial proposal only; not engineering approval'}};db.commit()
    try:
        response=columns.run(project_id,columns.Run(model_revision_id=row.model_revision_id,component_id=r['component_id'],input_record_id=r['input_record_id']),db,user_id)
        row.result_json={**row.result_json,'solver_analysis_id':response['id']};row.status='SOLVER_COMPLETED';db.commit()
        return response
    except HTTPException:
        row.status='SOLVER_ATTEMPT_FAILED';db.commit();raise

@router.post('/proposals/{proposal_id}/explain')
async def explain(project_id:int,proposal_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    row=owned(db,project_id,proposal_id,PROPOSAL,user_id);r=row.result_json
    if not r.get('solver_analysis_id') or view(row,db,user_id)['status']=='STALE':raise HTTPException(409,'A current authorized solver result is required')
    analysis=owned(db,project_id,r['solver_analysis_id'],columns.RUN_TYPE,user_id)
    revision=db.get(ModelRevision,row.model_revision_id);inputs=columns.current_input(db,project_id,revision.design_scenario_id,r['component_id'])
    if columns.out(analysis,revision,inputs,db)['status']!='VERIFIED':raise HTTPException(409,'Only current verified axial solver output may be explained')
    evidence=analysis.result_json
    payload={'analysis_id':analysis.id,'evidence_sha256':digest(evidence),'values_si':evidence['values_si'],'comparisons':evidence['comparisons'],'elements':evidence['elements'],'force_residual_n':evidence['force_residual_n'],'limitations':agent.LIMITATIONS}
    explanation,usage=await invoke('explain',payload,r['model'],r['provider'],project_id,row.model_revision_id,db,user_id)
    result={'component_id':r['component_id'],'analysis_id':analysis.id,'explanation':explanation,'usage':usage,'engineering_approval':'DISABLED','code_checks':'DISABLED'}
    saved=record(db,project_id,row.model_revision_id,EXPLANATION,'EXPLANATION_UNAPPROVED',result,user_id)
    return {'record':view(saved,db,user_id),'analysis':columns.out(analysis,revision,columns.current_input(db,project_id,revision.design_scenario_id,r['component_id']),db)}

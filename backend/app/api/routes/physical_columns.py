"""Saved component geometry + explicit immutable axial engineering inputs."""
import hashlib
import json
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.api.routes.projects import get_owned_project
from app.api.routes.opensees import lock
from app.core.security import get_current_user_id
from app.db.models import ModelRevision, EngineeringAnalysis
from app.db.session import get_db
from app.services.design.editable_model import validate_document
from app.services.design import physical_column, opensees_benchmark as solver

router=APIRouter(prefix='/api/projects/{project_id}/engineering/opensees/columns',tags=['engineering'])
INPUT_TYPE='OPENSEES_COLUMN_INPUTS'
RUN_TYPE='OPENSEES_PHYSICAL_COLUMN'


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False,str_strip_whitespace=True)
    model_revision_id:int=Field(gt=0)
    component_id:str=Field(min_length=1,max_length=150)
    base_input_id:int|None=None
    purpose:Literal['VERIFICATION_ONLY','ENGINEER_INPUT_UNAPPROVED']
    material_name:str=Field(min_length=3,max_length=200)
    material_source:str=Field(min_length=3,max_length=500)
    elastic_modulus_pa:float=Field(gt=0,le=1e13)
    section_kind:Literal['solid_rectangle']
    section_width_m:float=Field(gt=0,le=100)
    section_depth_m:float=Field(gt=0,le=100)
    section_source:str=Field(min_length=3,max_length=500)
    compression_n:float=Field(gt=0,le=1e9)
    load_source:str=Field(min_length=3,max_length=500)
    support_kind:Literal['axial_linear_spring']
    support_stiffness_n_per_m:float=Field(gt=0,le=1e15)
    support_source:str=Field(min_length=3,max_length=500)
    isolated_axial_only:Literal[True]
    elements:Literal[1,2,4]
    solver_units:Literal['SI','N-mm']


class Run(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_revision_id:int=Field(gt=0)
    component_id:str
    input_record_id:int=Field(gt=0)


def context(project_id,revision_id,component_id,db,user_id,latest_only=False):
    project=get_owned_project(project_id,db,user_id)
    revision=db.query(ModelRevision).filter_by(id=revision_id,project_id=project_id).one_or_none()
    if not revision: raise HTTPException(404,'Saved model revision not found')
    latest=db.query(ModelRevision).filter_by(design_scenario_id=revision.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
    if latest_only and latest.id!=revision.id: raise HTTPException(409,'Use the latest saved model revision.')
    try:
        errors=validate_document(revision.document_json,project_id=project_id,scenario_id=revision.design_scenario_id,project_type=project.project_type)
        if errors: raise ValueError('; '.join(errors))
        geo=physical_column.geometry(revision.document_json,component_id)
    except (ValueError,TypeError,KeyError,IndexError) as error: raise HTTPException(422,str(error)) from error
    return revision,geo


def rows(db,project_id,scenario_id,component_id,kind):
    return db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type=kind).filter(
        EngineeringAnalysis.result_json['scenario_id'].as_integer()==scenario_id,
        EngineeringAnalysis.result_json['component_id'].as_string()==component_id).order_by(EngineeringAnalysis.id.desc())


def current_input(db,project_id,scenario_id,component_id):
    return rows(db,project_id,scenario_id,component_id,INPUT_TYPE).first()


def out(row,revision,latest_input,db):
    latest_revision=db.query(ModelRevision).filter_by(design_scenario_id=revision.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
    r=row.result_json
    stale=row.model_revision_id!=revision.id or latest_revision.id!=row.model_revision_id or r['model_document_sha256']!=solver.digest(revision.document_json)
    if row.analysis_type==RUN_TYPE:
        stale=stale or not latest_input or r['input_record_id']!=latest_input.id or r['engineering_inputs_sha256']!=solver.digest(latest_input.result_json['engineering_inputs'])
    return {'id':row.id,'model_revision_id':row.model_revision_id,'status':'STALE' if stale else row.status,'result':r}


@router.get('')
def history(project_id:int,model_revision_id:int,component_id:str,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    revision,geo=context(project_id,model_revision_id,component_id,db,user_id)
    latest_input=current_input(db,project_id,revision.design_scenario_id,component_id)
    return {'physical_component':geo,'latest_input':out(latest_input,revision,latest_input,db) if latest_input else None,
        'analyses':[out(row,revision,latest_input,db) for row in rows(db,project_id,revision.design_scenario_id,component_id,RUN_TYPE).limit(20).all()]}


@router.post('/inputs')
def save_inputs(project_id:int,payload:Input,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    revision,geo=context(project_id,payload.model_revision_id,payload.component_id,db,user_id,True)
    inputs=payload.model_dump(exclude={'model_revision_id','component_id','base_input_id'})
    try: physical_column.parameters(geo,inputs)
    except ValueError as error: raise HTTPException(422,str(error)) from error
    latest=current_input(db,project_id,revision.design_scenario_id,payload.component_id)
    if payload.base_input_id!=(latest.id if latest else None): raise HTTPException(409,'Engineering inputs changed. Reload before saving.')
    result={'component_id':payload.component_id,'scenario_id':revision.design_scenario_id,
        'engineering_inputs':inputs,'engineering_inputs_sha256':solver.digest(inputs),'physical_component':geo,
        'model_document_sha256':solver.digest(revision.document_json),'code_checks':'DISABLED','engineering_approval':'DISABLED'}
    if latest and latest.model_revision_id==revision.id and latest.result_json==result:
        return out(latest,revision,latest,db)
    row=EngineeringAnalysis(project_id=project_id,model_revision_id=revision.id,analysis_type=INPUT_TYPE,
        algorithm_version='physical-column-inputs/1',status='INPUT_READY',result_json=result,actor_user_id=user_id)
    db.add(row);db.commit();db.refresh(row)
    return out(row,revision,row,db)


@router.post('/run')
def run(project_id:int,payload:Run,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    revision,geo=context(project_id,payload.model_revision_id,payload.component_id,db,user_id,True)
    inputs=current_input(db,project_id,revision.design_scenario_id,payload.component_id)
    if not inputs or inputs.id!=payload.input_record_id or inputs.model_revision_id!=revision.id or inputs.result_json['model_document_sha256']!=solver.digest(revision.document_json):
        raise HTTPException(409,'Save explicit current engineering inputs for this component/revision before running.')
    if not lock.acquire(blocking=False): raise HTTPException(409,'OpenSees is already running.')
    try:
        try:
            suite=solver.verification_suite()
            result=physical_column.run(geo,inputs.result_json['engineering_inputs'])
        except RuntimeError as error: raise HTTPException(503,str(error)) from error
        except ValueError as error: raise HTTPException(422,str(error)) from error
        result.update(component_id=payload.component_id,scenario_id=revision.design_scenario_id,project_id=project_id,
            model_revision_id=revision.id,model_document_sha256=solver.digest(revision.document_json),input_record_id=inputs.id,
            engineering_inputs_sha256=solver.digest(inputs.result_json['engineering_inputs']),verification_suite=suite)
        if suite['status']!='VERIFIED': result.update(status='FAILED',verified=False,error='Existing solver benchmark verification failed.')
        (solver.ARTIFACTS/result['run_id']/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        row=EngineeringAnalysis(project_id=project_id,model_revision_id=revision.id,analysis_type=RUN_TYPE,
            algorithm_version='physical-column-axial/1',status=result['status'],result_json=result,actor_user_id=user_id,
            dependency_ids_json=[{'model_revision_id':revision.id,'component_id':payload.component_id,'input_record_id':inputs.id,
                                 'model_document_sha256':result['model_document_sha256'],'engineering_inputs_sha256':result['engineering_inputs_sha256']}])
        db.add(row);db.commit();db.refresh(row)
        db.expire(inputs)
        return out(row,revision,current_input(db,project_id,revision.design_scenario_id,payload.component_id),db)
    finally: lock.release()


@router.get('/{analysis_id}/artifacts/{filename}')
def artifact(project_id:int,analysis_id:int,filename:str,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
    get_owned_project(project_id,db,user_id)
    row=db.query(EngineeringAnalysis).filter_by(id=analysis_id,project_id=project_id,analysis_type=RUN_TYPE).one_or_none()
    if not row or filename not in solver.FILES: raise HTTPException(404,'Artifact not found')
    path=solver.ARTIFACTS/str(UUID(row.result_json['run_id']))/filename
    if not path.is_file(): raise HTTPException(404,'Artifact not available')
    return {'filename':filename,'contents':path.read_text(encoding='utf-8'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

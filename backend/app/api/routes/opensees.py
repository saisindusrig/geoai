"""Owned immutable evidence for the isolated local axial benchmark."""
import json
import hashlib
from threading import Lock
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user_id
from app.db.models import EngineeringAnalysis, ModelRevision
from app.db.session import get_db
from app.services.design import opensees_benchmark as solver

router = APIRouter(prefix='/api/projects/{project_id}/engineering/opensees', tags=['engineering'])
lock = Lock()


class BenchmarkInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    model_revision_id: int = Field(gt=0)
    elements: Literal[1, 2, 4] = 1
    load_factor: float = Field(default=1, ge=.1, le=2)
    units: Literal['SI', 'N-mm'] = 'SI'


def output(row, db):
    revision = db.get(ModelRevision, row.model_revision_id)
    latest = db.query(ModelRevision).filter_by(design_scenario_id=revision.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first() if revision else None
    stale = not revision or not latest or latest.id != revision.id or solver.digest(revision.document_json) != row.result_json.get('model_document_sha256')
    return {'id': row.id, 'model_revision_id': row.model_revision_id,
            'status': 'STALE' if stale else row.status, 'result': row.result_json}


@router.get('')
def history(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    rows = db.query(EngineeringAnalysis).filter_by(project_id=project_id, analysis_type='OPENSEES_AXIAL_BENCHMARK').order_by(EngineeringAnalysis.id.desc()).limit(30).all()
    try:
        available = solver.provenance()
    except RuntimeError as error:
        available = {'name': 'OpenSees', 'available': False, 'error': str(error)}
    return {'solver': available, 'analyses': [output(row, db) for row in rows]}


@router.post('')
def run(project_id: int, payload: BenchmarkInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    revision = db.query(ModelRevision).filter_by(id=payload.model_revision_id, project_id=project_id).one_or_none()
    if revision is None:
        raise HTTPException(404, 'Model revision not found')
    latest = db.query(ModelRevision).filter_by(design_scenario_id=revision.design_scenario_id).order_by(ModelRevision.revision_number.desc()).first()
    if latest.id != revision.id:
        raise HTTPException(409, 'Select the latest saved model revision before running the benchmark.')
    if not lock.acquire(blocking=False):
        raise HTTPException(409, 'An OpenSees benchmark is already running; retry when it completes.')
    try:
        try:
            suite = solver.verification_suite()
            result = solver.run_case(elements=payload.elements, load_factor=payload.load_factor, units=payload.units)
        except RuntimeError as error:
            raise HTTPException(503, str(error)) from error
        result['verification_suite'] = suite
        if suite['status'] != 'VERIFIED':
            result.update(status='FAILED', verified=False, error='Independent solver verification suite failed; results cannot be used.')
        result['model_document_sha256'] = solver.digest(revision.document_json)
        result['model_revision_id'] = revision.id
        result['project_id'] = project_id
        (solver.ARTIFACTS/result['run_id']/'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        row = EngineeringAnalysis(project_id=project_id, model_revision_id=revision.id,
            analysis_type='OPENSEES_AXIAL_BENCHMARK', algorithm_version='opensees-axial-spring/1',
            status=result['status'], result_json=result, actor_user_id=user_id,
            dependency_ids_json=[{'model_revision_id': revision.id, 'document_sha256': result['model_document_sha256'], 'inputs_sha256': result['inputs_sha256']}])
        db.add(row)
        db.commit()
        db.refresh(row)
        return output(row, db)
    finally:
        lock.release()


@router.get('/{analysis_id}/artifacts/{filename}')
def artifact(project_id: int, analysis_id: int, filename: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    row = db.query(EngineeringAnalysis).filter_by(id=analysis_id, project_id=project_id, analysis_type='OPENSEES_AXIAL_BENCHMARK').one_or_none()
    if row is None or filename not in solver.FILES:
        raise HTTPException(404, 'Artifact not found')
    run_id = str(UUID(row.result_json['run_id']))
    path = solver.ARTIFACTS/run_id/filename
    if not path.is_file():
        raise HTTPException(404, 'Artifact unavailable for this run')
    return {'filename': filename, 'contents': path.read_text(encoding='utf-8'),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

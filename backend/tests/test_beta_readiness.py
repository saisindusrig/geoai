import asyncio
import json
import pytest
from fastapi import HTTPException
from app.api.routes import files, physical_frames as frames, engineering_study as study
from app.db.models import EngineeringAnalysis, ModelRevision
from test_physical_column import seed
from test_physical_frame import document, inputs


@pytest.mark.parametrize('change',['nan_size','infinite_position','string_scale','null_component','bad_identity','bad_geometry'])
def test_model_validation_rejects_malformed_data_without_server_errors(change):
    from test_physical_column import doc
    from app.services.design.editable_model import validate_document
    d=doc();c=d['components'][0]
    if change=='nan_size':c['geometry']={'kind':'box','size':[1,float('nan'),1]}
    if change=='infinite_position':c['transform']['position']=[0,float('inf'),0]
    if change=='string_scale':c['transform']['scale']=['bad',1,1]
    if change=='null_component':d['components'][0]=None
    if change=='bad_identity':d['project_id']='invalid'
    if change=='bad_geometry':c['geometry']='invalid'
    assert validate_document(d,project_id=d['project_id'] if change!='bad_identity' else 1,
        scenario_id=d['scenario_id'],project_type=d['project_type'])


def test_production_startup_fails_closed_without_changing_credentials(monkeypatch):
    from app.core.production import settings, enforce_production_security
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'production')
    monkeypatch.setattr(settings, 'AUTH_REQUIRE_JWT', False)
    with pytest.raises(RuntimeError, match='AUTH_REQUIRE_JWT'):
        enforce_production_security()
    monkeypatch.setattr(settings, 'AUTH_REQUIRE_JWT', True)
    for secret in ['dev-secret-change-me', '', 'short']:
        monkeypatch.setattr(settings, 'APP_SECRET', secret)
        with pytest.raises(RuntimeError, match='APP_SECRET'):
            enforce_production_security()
    monkeypatch.setattr(settings, 'APP_SECRET', 'test-only-nondefault-secret-at-least-32-characters')
    enforce_production_security()
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'development')
    monkeypatch.setattr(settings, 'AUTH_REQUIRE_JWT', False)
    enforce_production_security()


def test_file_path_does_not_accept_sibling_prefix(tmp_path, monkeypatch):
    root = tmp_path/'storage'
    root.mkdir()
    sibling = tmp_path/'storage-private'
    sibling.mkdir()
    secret = sibling/'evidence.txt'
    secret.write_text('private')
    monkeypatch.setattr(files.settings, 'LOCAL_STORAGE_DIR', str(root))
    with pytest.raises(HTTPException) as caught:
        files._safe_local_path(str(secret))
    assert caught.value.status_code == 400
    (root/'owned.txt').write_text('owned')
    assert files._safe_local_path('owned.txt') == root/'owned.txt'


def test_normal_saved_model_can_review_drawing_without_enabling_strength(db_session):
    seed(db_session)
    assert study.checked(1, 1, db_session, 1, 'drawing_review').id == 1
    with pytest.raises(HTTPException):
        study.checked(1, 1, db_session, 1, 'engineering_method_review')
    with pytest.raises(HTTPException):
        study.checked(1, 1, db_session, 2, 'drawing_review')


def test_report_requires_owned_current_verified_evidence(db_session, tmp_path, monkeypatch):
    from app.services.design import opensees_benchmark
    monkeypatch.setattr(opensees_benchmark, 'ARTIFACTS', tmp_path)
    seed(db_session)
    revision = db_session.get(ModelRevision, 1)
    revision.document_json = document(revision.document_json)
    db_session.commit()
    q = inputs(revision.document_json)
    saved = frames.inputs(1, frames.Save(model_revision_id=1, **q), db_session, 1)
    proposal = asyncio.run(frames.proposal(1, frames.Prepare(model_revision_id=1,
        component_ids=q['component_ids'], provider='mock', model='zai-org/GLM-5.3-Flash'), db_session, 1))
    result = frames.run(1, frames.Authorize(proposal_id=proposal['id'],
        proposal_sha256=proposal['result']['proposal_sha256'], authorize_solver=True), db_session, 1)
    response = frames.report(1, result['id'], db_session, 1)
    report = json.loads(response.body)
    assert report['model_revision_id'] == 1
    assert report['evidence']['input_record_id'] == saved['id']
    assert report['evidence']['input_file_sha256']
    assert report['engineering_approval'] == report['code_checks'] == 'DISABLED'
    with pytest.raises(HTTPException):
        frames.report(1, result['id'], db_session, 2)
    q['load_n'] /= 2
    frames.inputs(1, frames.Save(model_revision_id=1, base_input_id=saved['id'], **q), db_session, 1)
    with pytest.raises(HTTPException) as caught:
        frames.report(1, result['id'], db_session, 1)
    assert caught.value.status_code == 409
    assert db_session.get(EngineeringAnalysis, result['id']).status == 'VERIFIED'

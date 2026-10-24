from copy import deepcopy
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.routes import opensees as route
from app.db.models import User, Project, DesignScenario, ModelRevision
from app.services.design import opensees_benchmark as solver


def seed(db):
    db.add(User(id=1, name='Local reviewer', email='fea@example.com', role='admin', plan='admin'))
    db.add(Project(id=1, user_id=1, name='Benchmark', project_type='building'))
    db.add(DesignScenario(id=1, project_id=1, name='Benchmark geometry', status='completed'))
    db.add(ModelRevision(id=1, project_id=1, design_scenario_id=1, revision_number=1,
                         document_json={'units':'metric','components':[]}, source='import', user_id=1))
    db.commit()


def test_owned_run_artifacts_reload_and_revision_staleness(db_session,tmp_path,monkeypatch):
    seed(db_session)
    monkeypatch.setattr(solver,'ARTIFACTS',tmp_path)
    original = deepcopy(db_session.get(ModelRevision,1).document_json)
    result = route.run(1,route.BenchmarkInput(model_revision_id=1,elements=2),db_session,1)
    assert result['status']=='VERIFIED'
    assert result['result']['verification_suite']['status']=='VERIFIED'
    assert result['result']['code_checks']=='DISABLED'
    assert result['result']['engineering_approval']=='DISABLED'
    assert route.history(1,db_session,1)['analyses'][0]['id']==result['id']
    assert 'model BasicBuilder' in route.artifact(1,result['id'],'model.tcl',db_session,1)['contents']
    for filename in ('../model.tcl','missing.txt'):
        with pytest.raises(HTTPException) as error: route.artifact(1,result['id'],filename,db_session,1)
        assert error.value.status_code==404
    db_session.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,
        document_json={'units':'metric','components':[],'edited':True},source='manual_edit',user_id=1))
    db_session.commit()
    assert route.history(1,db_session,1)['analyses'][0]['status']=='STALE'
    assert db_session.get(ModelRevision,1).document_json==original
    with pytest.raises(HTTPException) as error: route.run(1,route.BenchmarkInput(model_revision_id=1),db_session,1)
    assert error.value.status_code==409
    with pytest.raises(HTTPException): route.history(1,db_session,99)


def test_missing_solver_and_run_lock(db_session,tmp_path,monkeypatch):
    seed(db_session)
    monkeypatch.setattr(solver,'executable',lambda:tmp_path/'missing.exe')
    with pytest.raises(HTTPException) as error: route.run(1,route.BenchmarkInput(model_revision_id=1),db_session,1)
    assert error.value.status_code==503
    assert not route.lock.locked()
    route.lock.acquire()
    try:
        with pytest.raises(HTTPException) as error: route.run(1,route.BenchmarkInput(model_revision_id=1),db_session,1)
        assert error.value.status_code==409
    finally: route.lock.release()


@pytest.mark.parametrize('payload',[{'elements':3},{'units':'ft'},{'load_factor':float('nan')},{'load_factor':-1},{'executable':'anything.exe'}])
def test_api_rejects_invalid_and_executable_override(payload):
    with pytest.raises(ValidationError): route.BenchmarkInput(model_revision_id=1,**payload)


def test_verification_gate_blocks_results(db_session,tmp_path,monkeypatch):
    seed(db_session)
    monkeypatch.setattr(solver,'ARTIFACTS',tmp_path)
    monkeypatch.setattr(solver,'verification_suite',lambda:{'status':'FAILED','cases':[]})
    result=route.run(1,route.BenchmarkInput(model_revision_id=1),db_session,1)
    assert result['status']=='FAILED' and result['result']['verified'] is False

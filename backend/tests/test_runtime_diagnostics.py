"""Diagnostics contract uses isolated sessions and never invokes analysis/inference."""
import json
import subprocess
from types import SimpleNamespace
import pytest
from fastapi import FastAPI, Response, HTTPException
from fastapi.testclient import TestClient
from app.api.routes import runtime_diagnostics as d
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.core.config import settings

@pytest.fixture()
def probes(monkeypatch):
    monkeypatch.setattr(d,'database_status',lambda:dict(status='AVAILABLE',schema='CURRENT'))
    monkeypatch.setattr(d,'solver_status',lambda:d.check('Local solver','HEALTHY','OpenSees 3.8.0; version only.'))
    monkeypatch.setattr(d,'collect_production_warnings',lambda:[])
    for name,value in dict(AI_PROVIDER='mock',ENGINEERING_AI_MODE='mock',ENGINEERING_AI_BUDGET_APPROVED=False,ENGINEERING_AI_BUDGET_USD=0,NEBIUS_API_KEY='',OPENAI_API_KEY='',ANTHROPIC_API_KEY='',GEMINI_API_KEY='').items():monkeypatch.setattr(settings,name,value)


def call(db,**kw):
    return d.diagnostics(Response(),kw.get('project_id'),kw.get('model_revision_id'),db,1)


def test_read_only_contract_redaction_and_no_provider_calls(db_session,probes,monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','SECRET_SENTINEL_DO_NOT_EXPOSE')
    result=call(db_session)
    assert 'SECRET_SENTINEL' not in json.dumps(result)
    assert next(c for c in result['checks'] if c['name']=='AI controls')['status']=='BLOCKED'
    assert result['engineering_approval']=='DISABLED' and result['inference_requested'] is False
    assert result['methods']==[]


def test_database_outage_recovery_and_no_saved_reads(db_session,probes,monkeypatch):
    monkeypatch.setattr(d,'capabilities',lambda *a:pytest.fail('Cannot read results during DB outage'))
    monkeypatch.setattr(d,'database_status',lambda:dict(status='UNAVAILABLE',schema='UNKNOWN'))
    result=call(db_session,project_id=1,model_revision_id=1)
    assert next(c for c in result['checks'] if c['name']=='Database')['status']=='UNAVAILABLE'
    monkeypatch.setattr(d,'database_status',lambda:dict(status='AVAILABLE',schema='OUTDATED'))
    result=call(db_session)
    assert next(c for c in result['checks'] if c['name']=='Database')['status']=='DEGRADED'


def test_capability_adapter_preserves_stale_unsupported_and_counts(db_session,probes,monkeypatch):
    monkeypatch.setattr(d,'capabilities',lambda *a:dict(methods={'frame':dict(status='STALE',current_results=[],history=[{'current':False}]),'coupled':dict(status='UNSUPPORTED',current_results=[],history=[])}))
    result=call(db_session,project_id=1,model_revision_id=1)
    assert result['methods']==[dict(method='frame',status='STALE',current_results=0,historical_results=1),dict(method='coupled',status='UNSUPPORTED',current_results=0,historical_results=0)]


def test_missing_record_is_blocked_and_ownership_stays_enforced(db_session,probes,monkeypatch):
    def fail(*a):raise HTTPException(404,'sensitive raw source')
    monkeypatch.setattr(d,'capabilities',fail)
    result=call(db_session,project_id=1,model_revision_id=1)
    assert 'sensitive raw source' not in json.dumps(result)
    assert result['checks'][-1]['status']=='BLOCKED'
    def forbidden(*a):raise HTTPException(403,'Forbidden')
    monkeypatch.setattr(d,'capabilities',forbidden)
    with pytest.raises(HTTPException) as err:call(db_session,project_id=1,model_revision_id=1)
    assert err.value.status_code==403


def test_contract_route_and_auth_gate(db_session,probes):
    app=FastAPI();app.include_router(d.router)
    app.dependency_overrides[get_db]=lambda:db_session
    app.dependency_overrides[get_current_user_id]=lambda:1
    with TestClient(app) as client:
        response=client.get('/api/system/diagnostics')
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert client.get('/api/system/diagnostics?project_id=0').status_code==422
        assert client.post('/api/system/diagnostics').status_code==405
        assert client.get('/api/system/diagnostics?project_id=1').json()['checks'][-1]['status']=='BLOCKED'
        def reject():raise HTTPException(401,'Authorization required')
        app.dependency_overrides[get_current_user_id]=reject
        assert client.get('/api/system/diagnostics').status_code==401


def test_solver_probe_fixed_input_bounded_and_redacts_output(monkeypatch,tmp_path):
    exe=tmp_path/'solver';exe.write_text('placeholder')
    monkeypatch.setattr(d.opensees_benchmark,'executable',lambda:exe)
    def run(command,**kw):
        assert command==[str(exe)] and kw['timeout']==3
        assert kw['input']=='puts "GEOAI_VERSION:[version]"\nexit\n'
        return SimpleNamespace(returncode=0,stdout='sensitive banner',stderr='secret\nGEOAI_VERSION:3.8.0\n')
    monkeypatch.setattr(d.subprocess,'run',run)
    result=d.solver_status();assert result['status']=='HEALTHY' and '3.8.0' in result['summary']
    assert 'sensitive' not in json.dumps(result) and str(exe) not in json.dumps(result)
    def timeout(*a,**kw):raise subprocess.TimeoutExpired('secret',3)
    monkeypatch.setattr(d.subprocess,'run',timeout)
    assert d.solver_status()['status']=='DEGRADED'
    monkeypatch.setattr(d.opensees_benchmark,'executable',lambda:tmp_path/'missing')
    assert d.solver_status()['status']=='UNAVAILABLE'


def test_existing_liveness_contract_remains_unchanged():
    from app.main import health, app
    assert health()['status']=='ok'
    assert {'/health','/api/health'} <= {route.path for route in app.routes}

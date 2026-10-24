"""Focused private-beta boundaries, isolated entirely in memory/temp storage."""
from copy import deepcopy
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
import pytest
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.db.models import User, Project, DesignScenario, ModelRevision, EngineeringAnalysis
from app.api.routes import auth, projects, files, model_revisions, physical_frames, engineering_study, analysis_capabilities
from app.services import rate_limit, audit
from test_physical_column import seed

@pytest.fixture()
def secured(db_session,monkeypatch,tmp_path):
    seed(db_session)
    db_session.add(User(id=2,name='Other user',email='other-beta@example.test',role='user',plan='free'))
    db_session.add(Project(id=2,user_id=2,name='Other project',project_type='building'))
    db_session.add(DesignScenario(id=2,project_id=2,name='Other saved model',status='completed'))
    doc=deepcopy(db_session.get(ModelRevision,1).document_json);doc.update(project_id=2,scenario_id=2)
    db_session.add(ModelRevision(id=2,project_id=2,design_scenario_id=2,revision_number=1,document_json=doc,source='import',user_id=2));db_session.commit()
    for name,value in dict(AUTH_REQUIRE_JWT=True,ENVIRONMENT='development',APP_SECRET='isolated-test-signing-secret-not-a-real-credential-123456789',USAGE_LIMITS_ENABLED=False,RATE_LIMITING_ENABLED=False,LOCAL_STORAGE_DIR=str(tmp_path)).items():monkeypatch.setattr(settings,name,value)
    monkeypatch.setattr(engineering_study,'ROOT',tmp_path/'drawing-references')
    monkeypatch.setattr(files,'SessionLocal',sessionmaker(bind=db_session.bind))
    monkeypatch.setattr(rate_limit,'SessionLocal',sessionmaker(bind=db_session.bind))
    monkeypatch.setattr(rate_limit,'_memory_buckets',{})
    monkeypatch.setattr(rate_limit,'_redis_incr',lambda *a:-1)
    app=FastAPI()
    for route in [auth,projects,files,model_revisions,physical_frames,engineering_study,analysis_capabilities]:app.include_router(route.router)
    app.dependency_overrides[get_db]=lambda:db_session
    with TestClient(app) as client:yield client,tmp_path


def headers(user=1):return {'Authorization':'Bearer '+create_access_token(user)}


def test_development_token_shortcut_cannot_bypass_enforced_jwt(secured):
    client,_=secured
    response=client.post('/api/auth/token',json={'user_id':1})
    assert response.status_code==403
    assert 'access_token' not in response.text


def test_rotating_forwarded_header_cannot_reset_login_limit(monkeypatch):
    monkeypatch.setattr(settings,'RATE_LIMITING_ENABLED',True)
    monkeypatch.setattr(rate_limit,'_memory_buckets',{})
    monkeypatch.setattr(rate_limit,'_redis_incr',lambda *a:-1)
    monkeypatch.setattr(rate_limit,'log_audit_event',lambda *a,**k:None)
    class AuditSession:
        def close(self):pass
    monkeypatch.setattr(rate_limit,'SessionLocal',AuditSession)
    app=FastAPI()
    @app.post('/login-limit-probe')
    def probe(request:Request):rate_limit.enforce_rate_limit('auth.login',request=request);return {'ok':True}
    with TestClient(app) as client:
        for i in range(20):assert client.post('/login-limit-probe',headers={'X-Forwarded-For':f'198.51.100.{i}'}).status_code==200
        assert client.post('/login-limit-probe',headers={'X-Forwarded-For':'203.0.113.9'}).status_code==429


@pytest.mark.parametrize('path',['/api/projects/1','/api/projects/1/scenarios/1/model-revisions','/api/projects/1/engineering/assembly?compact=true','/api/projects/1/engineering/capabilities?model_revision_id=1','/api/projects/1/engineering/study/drawings/999/source'])
def test_cross_project_reads_are_rejected(secured,path):
    client,_=secured
    assert client.get(path,headers=headers(2)).status_code==404


@pytest.mark.parametrize('authorization',[None,'Bearer invalid','Bearer '])
def test_missing_invalid_authorization_and_mock_header_rejected(secured,authorization):
    client,_=secured;h={'X-Mock-User-Id':'1'}
    if authorization:h['Authorization']=authorization
    assert client.get('/api/projects/1',headers=h).status_code==401


def test_expired_and_unsigned_tokens_rejected(secured):
    client,_=secured
    expired=jwt.encode({'sub':'1','exp':1},settings.APP_SECRET,algorithm='HS256')
    for value in [expired,'eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0.']:
        assert client.get('/api/projects/1',headers={'Authorization':'Bearer '+value}).status_code==401


def test_safe_owned_download_foreign_download_and_traversal(secured):
    client,root=secured
    path=root/'projects/1/proof.txt';path.parent.mkdir(parents=True);path.write_text('Synthetic evidence; not original project data.')
    result=client.get('/files/projects/1/proof.txt',headers=headers())
    assert result.status_code==200 and result.text==path.read_text()
    assert client.get('/files/projects/1/proof.txt',headers=headers(2)).status_code==404
    for value in ['../outside','projects/1/../../secret','projects/1/..\\..\\secret',str(root.parent/'outside')]:
        with pytest.raises(HTTPException) as e:files._safe_local_path(value)
        assert e.value.status_code in (400,404)


def test_mismatched_project_revision_and_forged_authorization_fail_closed(secured):
    client,_=secured
    assert client.get('/api/projects/1/engineering/capabilities?model_revision_id=2',headers=headers()).status_code==404
    result=client.post('/api/projects/1/engineering/assembly/authorize-run',headers=headers(),json={'proposal_id':999,'proposal_sha256':'0'*64,'authorize_solver':True})
    assert result.status_code==404


def test_audit_ip_uses_verified_asgi_peer_not_arbitrary_header():
    request=Request({'type':'http','headers':[(b'x-forwarded-for',b'198.51.100.77')],'client':('127.0.0.1',1234)})
    assert audit._client_ip(request)=='127.0.0.1'


def test_dev_token_remains_available_only_in_explicit_non_jwt_development(secured,monkeypatch):
    client,_=secured
    monkeypatch.setattr(settings,'AUTH_REQUIRE_JWT',False)
    assert client.post('/api/auth/token',json={'user_id':1}).status_code==200
    monkeypatch.setattr(settings,'ENVIRONMENT','production')
    assert client.post('/api/auth/token',json={'user_id':1}).status_code==403


def test_local_launch_commands_bind_loopback():
    from pathlib import Path
    import json
    root=Path(__file__).resolve().parents[2]
    # The BAT now delegates startup instead of duplicating the Next command.
    launcher=(root/'run-website.bat').read_text()
    assert 'start-copilot-review.ps1' in launcher and 'call npm run dev' in launcher
    assert 'next dev -p 3001 -H 127.0.0.1' in (root/'start-copilot-review.ps1').read_text()
    scripts=json.loads((root/'frontend/package.json').read_text())['scripts']
    assert '-H 127.0.0.1' in scripts['dev'] and '-H 127.0.0.1' in scripts['start']
    assert 'proxy_headers=False' in (root/'backend/scripts/serve_copilot_review_local.py').read_text()


@pytest.mark.parametrize('name,content',[('unsupported.dwg',b'not DWG'),('invalid.dxf',b'not DXF'),('oversized.dxf',b'x'*2_000_001)],ids=['unsupported-format','invalid-content','oversized'])
def test_invalid_uploads_never_create_engineering_records(secured,db_session,name,content):
    client,root=secured
    before=db_session.query(EngineeringAnalysis).count()
    result=client.post('/api/projects/1/engineering/study/drawings/import',headers=headers(),data={'model_revision_id':'1','classification':'SYNTHETIC_VERIFICATION'},files={'file':(name,content)})
    assert result.status_code in (400,413,422)
    assert db_session.query(EngineeringAnalysis).count()==before
    assert not list(root.rglob('*.dxf'))


def test_cross_project_upload_rejected_before_content_is_saved(secured):
    client,root=secured
    response=client.post('/api/projects/1/engineering/study/drawings/import',headers=headers(2),data={'model_revision_id':'1','classification':'SYNTHETIC_VERIFICATION'},files={'file':('foreign.dxf',b'not DXF')})
    assert response.status_code==404
    assert not list(root.rglob('*.dxf'))


def test_audit_metadata_removes_nested_credential_fields():
    value=audit.sanitize_metadata({'token':'sensitive','nested':{'api_key':'sensitive','password':'sensitive','source':'saved identity'},'items':[{'authorization':'sensitive','ok':True}]})
    assert 'sensitive' not in str(value)
    assert value['nested']['source']=='saved identity'


@pytest.mark.parametrize('auth_required,secret',[(False,'synthetic-strong-signing-key-12345678901234567890'),(True,'dev-secret-change-me'),(True,'short')],ids=['jwt-required','default-key','short-key'])
def test_production_security_guard_fails_closed(monkeypatch,auth_required,secret):
    from app.core.production import enforce_production_security
    monkeypatch.setattr(settings,'ENVIRONMENT','production')
    monkeypatch.setattr(settings,'AUTH_REQUIRE_JWT',auth_required)
    monkeypatch.setattr(settings,'APP_SECRET',secret)
    with pytest.raises(RuntimeError):enforce_production_security()


def test_cors_does_not_allow_untrusted_browser_origin(monkeypatch):
    from app.core.cors import build_cors_origins,build_cors_origin_regex
    from fastapi.middleware.cors import CORSMiddleware
    monkeypatch.setattr(settings,'CORS_ALLOW_NETLIFY',False)
    monkeypatch.setattr(settings,'CORS_ALLOWED_ORIGINS','http://localhost:3001')
    app=FastAPI();app.add_middleware(CORSMiddleware,allow_origins=build_cors_origins(),allow_origin_regex=build_cors_origin_regex(),allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
    with TestClient(app) as client:
        response=client.options('/api/projects',headers={'Origin':'https://untrusted.invalid','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'})
        assert response.status_code==400 and 'access-control-allow-origin' not in response.headers
        response=client.options('/api/projects',headers={'Origin':'http://localhost:3001','Access-Control-Request-Method':'GET'})
        assert response.status_code==200 and response.headers['access-control-allow-origin']=='http://localhost:3001'


def test_existing_drawing_fixture_import_source_download_and_hash_guard(secured):
    from test_drawing_strength import FILE
    client,_=secured
    content=FILE.read_bytes()
    response=client.post('/api/projects/1/engineering/study/drawings/import',headers=headers(),data={'model_revision_id':'1','classification':'SYNTHETIC_VERIFICATION'},files={'file':(FILE.name,content)})
    assert response.status_code==200
    record=response.json();url='/api/projects/1/engineering/study/drawings/'+str(record['id'])+'/source'
    result=client.get(url,headers=headers());assert result.status_code==200 and result.content==content
    assert 'attachment' in result.headers['content-disposition']
    assert client.get(url,headers=headers(2)).status_code==404
    path=engineering_study.ROOT/'1'/(record['result']['source_sha256']+'.dxf')
    path.write_bytes(b'Corrupt only the isolated temporary copy')
    assert client.get(url,headers=headers()).status_code==409

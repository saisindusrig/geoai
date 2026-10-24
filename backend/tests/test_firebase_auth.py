"""Milestone 10: all identities, SDK calls, storage and approvals are synthetic."""
import copy
import hashlib
import importlib.machinery
import sys
import time
import types
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.core import firebase_auth
from app.core.config import settings
from app.core.security import create_access_token
from app.db.models import AuditLog, User, Project, ModelRevision, EngineeringAnalysis
from app.db.session import get_db
from app.api.routes import auth, site_assistant
from app.services.identity_links import identity_metadata, identity_links, resolve_link
from app.services.assistant import site_store
from test_private_beta_security import secured

PROJECT = 'synthetic-auth-project'
ISSUER = 'https://securetoken.google.com/' + PROJECT

def claims(uid='one', **changes):
    now=int(time.time())
    return dict(aud=PROJECT,iss=ISSUER,sub=uid,uid=uid,iat=now-5,auth_time=now-10,exp=now+300,email='same@example.test',**changes)

@pytest.fixture
def sdk(monkeypatch,tmp_path):
    """Fake official SDK surface; no cryptographic/live verification claim."""
    module=types.ModuleType('firebase_admin');module.__spec__=importlib.machinery.ModuleSpec('firebase_admin',loader=None)
    errors=types.SimpleNamespace(**{name:type(name,(Exception,),{}) for name in ['InvalidIdTokenError','ExpiredIdTokenError','RevokedIdTokenError','UserDisabledError']})
    calls=[];apps={};values={}
    def verify(token,**options):
        calls.append((token,options))
        if token in values:
            value=values[token]
            if isinstance(value,Exception):raise value
            return copy.deepcopy(value)
        if token.count('.')==2:raise errors.InvalidIdTokenError('Synthetic rejected legacy JWT')
        if token in ['expired','forged','malformed','revoked','disabled']:
            kind={'expired':'ExpiredIdTokenError','forged':'InvalidIdTokenError','malformed':'InvalidIdTokenError','revoked':'RevokedIdTokenError','disabled':'UserDisabledError'}[token]
            raise getattr(errors,kind)('Synthetic rejection; must not leak the token')
        if token=='outage':raise TimeoutError('Synthetic verification service outage')
        return claims({'valid':'one','other':'two'}.get(token,'unlinked'))
    errors.verify_id_token=verify;module.auth=errors
    module.credentials=types.SimpleNamespace(Certificate=lambda path:types.SimpleNamespace(project_id=PROJECT))
    def get_app(name):
        if name not in apps:raise ValueError('No app')
        return apps[name]
    def initialize(credential,options,name):
        apps[name]=types.SimpleNamespace(project_id=options['projectId']);return apps[name]
    module.get_app=get_app;module.initialize_app=initialize
    monkeypatch.setitem(sys.modules,'firebase_admin',module)
    file=tmp_path/'synthetic-credential-placeholder';file.write_text('Not credentials. Only used with the mocked SDK.')
    for k,v in dict(FIREBASE_AUTH_ENABLED=True,FIREBASE_PROJECT_ID=PROJECT,FIREBASE_AUTH_CREDENTIALS_FILE=str(file),AUTH_REQUIRE_JWT=True).items():monkeypatch.setattr(settings,k,v)
    monkeypatch.delenv('FIREBASE_AUTH_EMULATOR_HOST',raising=False)
    return types.SimpleNamespace(calls=calls,values=values,module=module)


def link(db,uid,user,**changes):
    key=str(uuid4());proof=dict(issuer=ISSUER,subject_sha256=hashlib.sha256(uid.encode()).hexdigest(),internal_user_id=user,approved_by=1)
    entry=AuditLog(user_id=1,action='auth.firebase.link_approved',entity_type='identity_link',entity_id=key,metadata_json=proof)
    db.add(entry);db.flush()
    db.execute(identity_links.insert().values(id=key,issuer=ISSUER,subject=uid,user_id=user,approved_by=1,audit_id=entry.id,state='ACTIVE',**changes));db.commit()
    return key,entry

@pytest.fixture
def firebase_client(secured,db_session,sdk,monkeypatch,tmp_path):
    identity_metadata.create_all(db_session.bind)  # ONLY this in-memory fixture, never application startup.
    link(db_session,'one',1);link(db_session,'two',2)
    # The existing isolated security fixture already wires project/file/result routes.
    old_client,root=secured
    old_client.app.include_router(site_assistant.router)
    monkeypatch.setattr(settings,'ASSISTANT_HISTORY_DB',str(tmp_path/'synthetic-history.db'))
    return old_client,root,db_session,sdk


def bearer(token='valid',**extra):return {'Authorization':'Bearer '+token,**extra}

def test_valid_linked_identity_uses_official_sdk_with_mandatory_revocation(firebase_client):
    client,_,db,sdk=firebase_client
    before=[(p.id,p.user_id) for p in db.query(Project).all()]
    response=client.get('/api/auth/me',headers=bearer(**{'X-Mock-User-Id':'2'}))
    assert response.status_code==200 and response.json()['id']==1
    assert sdk.calls[-1][1]==dict(app=sdk.calls[-1][1]['app'],check_revoked=True,clock_skew_seconds=0)
    assert sdk.calls[-1][1]['app'].project_id==PROJECT
    assert [(p.id,p.user_id) for p in db.query(Project).all()]==before

@pytest.mark.parametrize('token',['expired','forged','malformed','revoked','disabled'])
def test_sdk_token_rejections_cannot_fall_back_to_mock_or_legacy(firebase_client,token):
    client,_,_,_=firebase_client
    result=client.get('/api/projects/1',headers=bearer(token,**{'X-Mock-User-Id':'1'}))
    assert result.status_code==401 and 'Synthetic rejection' not in result.text

@pytest.mark.parametrize('changes',[
    {'aud':'other-project'},{'iss':'https://securetoken.google.com/other-project'},
    {'exp':0},{'iat':time.time()+1000},{'auth_time':time.time()+1000},
    {'sub':''},{'sub':12},{'uid':'different'},{'exp':float('inf')},
    {'exp':True},{'firebase':{'tenant':'unqualified-tenant'}},
])
def test_verified_claims_must_match_explicit_identity_policy(firebase_client,changes):
    client,_,_,sdk=firebase_client
    sdk.values['badclaims']={**claims(),**changes}
    assert client.get('/api/auth/me',headers=bearer('badclaims')).status_code==401

def test_email_roles_and_browser_user_ids_do_not_link_or_escalate(firebase_client):
    client,_,db,sdk=firebase_client
    sdk.values['unknown']={**claims('unknown'),'email':db.get(User,1).email,'user_id':1,'role':'admin'}
    count=db.query(User).count()
    assert client.get('/api/auth/me',headers=bearer('unknown',**{'X-Mock-User-Id':'1'})).status_code==403
    sdk.values['other']={**claims('two'),'user_id':1,'role':'admin'}
    value=client.get('/api/auth/me',headers=bearer('other')).json()
    assert value['id']==2 and value['role']=='user' and db.query(User).count()==count

@pytest.mark.parametrize('path',[
    '/api/projects/1','/api/projects/1/scenarios/1/model-revisions/latest',
    '/api/projects/1/engineering/capabilities?model_revision_id=1',
    '/api/projects/1/engineering/assembly',
    '/api/assistant/history?project_id=1',
])
def test_existing_cross_project_gates_remain_authoritative(firebase_client,path):
    client,_,_,_=firebase_client
    assert client.get(path,headers=bearer('other')).status_code==404


def test_files_use_linked_owner_and_existing_audit_pipeline(firebase_client):
    client,root,db,_=firebase_client
    target=root/'projects/1/proof.txt';target.parent.mkdir(parents=True);target.write_text('Synthetic owned evidence')
    assert client.get('/files/projects/1/proof.txt',headers=bearer()).status_code==200
    assert client.get('/files/projects/1/proof.txt',headers=bearer('other')).status_code==404
    assert client.get('/files/shared/secret.txt',headers=bearer()).status_code==403
    assert db.query(AuditLog).filter_by(action='file.download').count()==1


def test_saved_revision_and_forged_engineering_authorization_rejected(firebase_client):
    client,_,db,_=firebase_client
    before=db.query(EngineeringAnalysis).count()
    assert client.get('/api/projects/1/engineering/capabilities?model_revision_id=2',headers=bearer()).status_code==404
    result=client.post('/api/projects/1/engineering/assembly/authorize-run',headers=bearer(),json={'proposal_id':999,'proposal_sha256':'0'*64,'authorize_solver':True})
    assert result.status_code==404 and db.query(EngineeringAnalysis).count()==before


def test_assistant_history_isolation_uses_existing_owner_scope(firebase_client):
    client,_,_,_=firebase_client
    with site_store.connection() as store:
        for owner in (1,2):
            payload={'id':str(owner),'request':{'project_id':owner},'reply':'Synthetic private history '+str(owner),'status':'SUCCEEDED'}
            import json
            store.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)',(str(owner),owner,owner,time.time(),'SUCCEEDED','mock',0,0,json.dumps(payload)))
    one=client.get('/api/assistant/history',headers=bearer()).json()
    two=client.get('/api/assistant/history',headers=bearer('other')).json()
    assert [t['id'] for t in one['tasks']]==['1'] and [t['id'] for t in two['tasks']]==['2']

@pytest.mark.parametrize('mode',['outage','no-sdk','no-credentials','wrong-project-config','no-enforcement','emulator'])
def test_misconfiguration_and_verifier_outage_fail_closed(firebase_client,monkeypatch,mode):
    client,_,_,sdk=firebase_client
    token='valid'
    if mode=='outage':token='outage'
    if mode=='no-sdk':monkeypatch.setattr(firebase_auth.importlib.util,'find_spec',lambda name:None)
    if mode=='no-credentials':monkeypatch.setattr(settings,'FIREBASE_AUTH_CREDENTIALS_FILE','')
    if mode=='wrong-project-config':monkeypatch.setattr(settings,'FIREBASE_PROJECT_ID','')
    if mode=='no-enforcement':monkeypatch.setattr(settings,'AUTH_REQUIRE_JWT',False)
    if mode=='emulator':monkeypatch.setenv('FIREBASE_AUTH_EMULATOR_HOST','localhost:9099')
    assert client.get('/api/auth/me',headers=bearer(token,**{'X-Mock-User-Id':'1'})).status_code==503


def test_wrong_service_account_project_is_not_accepted(firebase_client):
    client,_,_,sdk=firebase_client
    sdk.module.credentials.Certificate=lambda _:types.SimpleNamespace(project_id='wrong-project')
    assert client.get('/api/auth/me',headers=bearer()).status_code==503


def test_link_requires_matching_audit_existing_user_and_active_state(firebase_client):
    client,_,db,_=firebase_client
    row=db.execute(identity_links.select().where(identity_links.c.subject=='one')).mappings().one()
    approval=db.get(AuditLog,row['audit_id']);approval.metadata_json={'internal_user_id':2};db.commit()
    assert client.get('/api/auth/me',headers=bearer()).status_code==403
    db.execute(identity_links.update().where(identity_links.c.subject=='two').values(state='REVOKED'));db.commit()
    assert client.get('/api/auth/me',headers=bearer('other')).status_code==403


def test_no_link_schema_is_not_created_automatically(secured,sdk,db_session):
    client,_=secured
    assert client.get('/api/auth/me',headers=bearer()).status_code==503
    from sqlalchemy import inspect
    assert 'auth_identity_links' not in inspect(db_session.bind).get_table_names()


def test_firebase_mode_rejects_shortcuts_and_password_account_creation(firebase_client):
    client,_,db,_=firebase_client;before=db.query(User).count()
    assert client.post('/api/auth/token',json={'user_id':1}).status_code==403
    assert client.post('/api/auth/login',json={'email':'one@example.test','password':'synthetic'}).status_code==403
    assert client.post('/api/auth/register',json={'name':'Forged','email':'new@example.test','password':'synthetic'}).status_code==403
    assert db.query(User).count()==before
    assert client.get('/api/auth/me',headers={'X-Mock-User-Id':'1'}).status_code==401


def test_disabled_rollback_preserves_legacy_and_explicit_local_mode(firebase_client,monkeypatch):
    client,_,_,sdk=firebase_client
    assert client.get('/api/auth/me',headers=bearer(create_access_token(1))).status_code==401  # Firebase mode never accepts the legacy HS256 token
    monkeypatch.setattr(settings,'FIREBASE_AUTH_ENABLED',False)
    sdk.calls.clear()
    assert client.get('/api/auth/me',headers=bearer(create_access_token(1))).status_code==200
    assert client.get('/api/auth/me',headers={'X-Mock-User-Id':'1'}).status_code==401
    monkeypatch.setattr(settings,'AUTH_REQUIRE_JWT',False)
    assert client.get('/api/auth/me').status_code==200
    assert client.get('/api/auth/config').json()['mode']=='local_development'
    assert sdk.calls==[]


def test_public_configuration_exposes_no_credentials(firebase_client):
    client,_,_,_=firebase_client
    response=client.get('/api/auth/config');assert response.status_code==200
    assert response.json()['mode']=='firebase' and not response.json()['password_login_allowed']
    assert 'synthetic-credential-placeholder' not in response.text

def test_exact_saved_result_load_case_and_staleness_under_firebase_identity(firebase_client,monkeypatch):
    client,_,db,_=firebase_client
    from app.api.routes import analysis_capabilities as capabilities
    from app.api.routes.site_assistant import Context
    from app.services.assistant.workspace_tools import execute
    from app.services.design.opensees_benchmark import digest
    document=db.get(ModelRevision,1).document_json
    saved=dict(id=7,project_id=1,model_revision_id=1,method='frame',status='VERIFIED',load_cases=['Synthetic gravity'],model_document_sha256=digest(document))
    db.add(EngineeringAnalysis(id=7,project_id=1,model_revision_id=1,analysis_type='OPENSEES_PHYSICAL_FRAME',algorithm_version='synthetic-recorded',status='VERIFIED',actor_user_id=1,result_json={'case_name':'Synthetic gravity','notice':'Synthetic evidence; no calculation'}));db.commit()
    def current(*args,**kwargs):
        assert kwargs['saved_only'] is True
        return {'methods':{'frame':{'current_results':[saved],'status':'SUPPORTED','reason':'Synthetic current evidence'}}}
    monkeypatch.setattr(capabilities,'capabilities',current)
    args=dict(project_id=1,revision_id=1,result_id=7,method='frame',load_case='Synthetic gravity',mode='forces')
    receipt=execute('show_saved_result',args,db,1,Context(project_id=1,revision_id=1))
    payload=dict(project_id=1,revision_id=1,name='show_saved_result',arguments=args,action_id=receipt['actionId'])
    before=db.query(EngineeringAnalysis).count()
    assert client.post('/api/assistant/workspace/validate',json=payload,headers=bearer()).status_code==200
    assert client.post('/api/assistant/workspace/validate',json=payload,headers=bearer('other')).status_code==404
    assert client.post('/api/assistant/workspace/validate',json={**payload,'arguments':{**args,'load_case':'Other'}},headers=bearer()).status_code==409
    saved['model_document_sha256']='stale'
    assert client.post('/api/assistant/workspace/validate',json=payload,headers=bearer()).status_code==409
    assert db.query(EngineeringAnalysis).count()==before

@pytest.mark.parametrize('field,value',[('user_id',999),('approved_by',2),('audit_id',999)])
def test_missing_target_and_unapproved_associations_rejected(firebase_client,field,value):
    client,_,db,_=firebase_client
    db.execute(identity_links.update().where(identity_links.c.subject=='one').values(**{field:value}));db.commit()
    assert client.get('/api/auth/me',headers=bearer()).status_code==403

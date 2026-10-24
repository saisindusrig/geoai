"""Phase B: synthetic auth, parser and output boundaries only."""
import asyncio,json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException,Request
from app.core.config import settings
from app.api.routes import auth,survey
from app.services import rate_limit,upload_limits
from app.services.survey import import_pipeline
from test_private_beta_security import secured,headers

@pytest.mark.parametrize('email',['known@example.test','unknown@example.test'])
def test_production_registration_has_identical_rejection_before_lookup(monkeypatch,email):
    monkeypatch.setattr(settings,'FIREBASE_AUTH_ENABLED',False)
    monkeypatch.setattr(settings,'ENVIRONMENT','production')
    db=Mock();db.query.side_effect=AssertionError('No existence lookup allowed')
    with pytest.raises(HTTPException) as error:
        auth.register(auth.RegisterRequest(name='Synthetic',email=email,password='synthetic-password'),Request({'type':'http'}),db)
    assert error.value.status_code==403
    assert error.value.detail=='Legacy registration is unavailable in production'
    assert not db.method_calls


def test_account_limit_normalizes_address_hides_email_and_expires(monkeypatch):
    monkeypatch.setattr(settings,'ENVIRONMENT','development');monkeypatch.setattr(settings,'RATE_LIMITING_ENABLED',True)
    monkeypatch.setattr(rate_limit,'_memory_buckets',{})
    keys=[]
    def redis(key,window):keys.append(key);return -1
    monkeypatch.setattr(rate_limit,'_redis_incr',redis)
    clock=[1000.0];monkeypatch.setattr(rate_limit.time,'time',lambda:clock[0])
    for i in range(10):rate_limit.enforce_login_account_limit(' Victim@Example.test ' if i%2 else 'victim@example.test')
    with pytest.raises(HTTPException) as error:rate_limit.enforce_login_account_limit('victim@example.test')
    assert error.value.status_code==429 and error.value.headers['Retry-After']=='60'
    assert len(set(keys))==1 and all('victim' not in key and '@' not in key for key in keys)
    rate_limit.enforce_login_account_limit('independent@example.test')
    clock[0]=1059
    with pytest.raises(HTTPException):rate_limit.enforce_login_account_limit('victim@example.test')
    clock[0]=1061;rate_limit.enforce_login_account_limit('victim@example.test')


def test_redis_rejected_attempts_cannot_extend_window(monkeypatch):
    pipe=Mock();pipe.execute.return_value=[11,False]
    redis=Mock();redis.pipeline.return_value=pipe
    monkeypatch.setattr(rate_limit.jobs,'_get_redis',lambda:redis)
    assert rate_limit._redis_incr('synthetic-account',60)==11
    pipe.expire.assert_called_once_with('synthetic-account',60,nx=True)


def test_unknown_account_still_performs_password_verification(secured,monkeypatch):
    client,_=secured;verify=Mock(return_value=False);monkeypatch.setattr(auth,'verify_password',verify)
    response=client.post('/api/auth/login',json={'email':'nonexistent@example.test','password':'synthetic'})
    assert response.status_code==401
    verify.assert_called_once_with('synthetic',auth._DUMMY_PASSWORD_HASH)


def test_account_login_limit_is_independent_of_ip(monkeypatch):
    monkeypatch.setattr(settings,'FIREBASE_AUTH_ENABLED',False);monkeypatch.setattr(settings,'ENVIRONMENT','development')
    monkeypatch.setattr(settings,'RATE_LIMITING_ENABLED',True);monkeypatch.setattr(rate_limit,'_memory_buckets',{})
    monkeypatch.setattr(rate_limit,'_redis_incr',lambda *a:-1);monkeypatch.setattr(auth,'log_audit_event',lambda *a,**k:None)
    monkeypatch.setattr(auth,'verify_password',lambda *a:False)
    db=Mock();db.query.return_value.filter.return_value.first.return_value=None
    for i in range(11):
        request=Request({'type':'http','client':(f'198.51.100.{i}',1234),'headers':[]})
        with pytest.raises(HTTPException) as error:
            auth.login(auth.LoginRequest(email='target@example.test',password='synthetic'),request,db)
        assert error.value.status_code==(401 if i<10 else 429)
    assert db.query.call_count==10


def test_sql_payload_does_not_authenticate_or_modify_users(secured,db_session):
    from app.db.models import User
    client,_=secured;before=db_session.query(User).count()
    response=client.post('/api/auth/login',json={'email':"' OR 1=1; DROP TABLE users; --",'password':'invalid'})
    assert response.status_code==401 and 'access_token' not in response.text
    assert 'password_hash' not in client.get('/api/auth/me',headers=headers()).text
    assert db_session.query(User).count()==before


@pytest.mark.parametrize('data',[[],{'type':'FeatureCollection','features':[{'type':'Feature','geometry':None}]},{'type':'Point','coordinates':[float('nan'),0]},{'type':'Point','coordinates':'not an array'}])
def test_bad_geojson_rejected_before_importer(monkeypatch,data):
    importer=Mock(side_effect=AssertionError('Geometry importer must not run'))
    monkeypatch.setattr(import_pipeline,'ingest_geojson_layer',importer)
    with pytest.raises(ValueError):import_pipeline.ingest_geojson_file(Mock(),Mock(),json.dumps(data).encode(),'road_centerline','synthetic')
    importer.assert_not_called()


def test_geojson_all_features_preflighted_and_complexity_bounded(monkeypatch):
    good={'type':'Feature','geometry':{'type':'Point','coordinates':[1,2]}}
    importer=Mock();monkeypatch.setattr(import_pipeline,'ingest_geojson_layer',importer)
    with pytest.raises(ValueError):import_pipeline.ingest_geojson_file(Mock(),Mock(),json.dumps({'type':'FeatureCollection','features':[good,{}]}).encode(),'road_centerline','synthetic')
    importer.assert_not_called()
    monkeypatch.setattr(upload_limits,'GEOJSON_MAX_NODES',5)
    with pytest.raises(ValueError,match='complexity'):upload_limits.validate_geojson_input(good)


def test_valid_geojson_retains_exact_coordinates(monkeypatch):
    data={'type':'Point','coordinates':[77.5,12.9,4.0]};importer=Mock(return_value='synthetic-layer')
    monkeypatch.setattr(import_pipeline,'ingest_geojson_layer',importer)
    assert import_pipeline.ingest_geojson_file(Mock(),Mock(),json.dumps(data).encode(),'road_centerline','synthetic')=='synthetic-layer'
    assert importer.call_args.args[2]==data


def test_native_parser_error_does_not_echo_internal_details(monkeypatch):
    monkeypatch.setattr(survey,'require_postgis',lambda:None)
    monkeypatch.setattr(survey,'get_owned_project',lambda *a:SimpleNamespace(id=1))
    monkeypatch.setattr(survey,'ingest_geojson_file',Mock(side_effect=RuntimeError('synthetic-private-path-and-credential')))
    class Upload:
        async def read(self,n):return b'{}'
    db=Mock()
    with pytest.raises(HTTPException) as error:asyncio.run(survey.import_survey_data(1,db,1,Upload(),format='geojson'))
    assert error.value.status_code==503 and 'synthetic-private' not in str(error.value.detail)
    db.commit.assert_not_called()

def test_configuration_disables_only_production_registration(monkeypatch):
    monkeypatch.setattr(settings,'FIREBASE_AUTH_ENABLED',False)
    monkeypatch.setattr(settings,'ENVIRONMENT','production')
    assert auth.auth_configuration()['registration_allowed'] is False
    assert auth.auth_configuration()['password_login_allowed'] is True
    monkeypatch.setattr(settings,'ENVIRONMENT','development')
    assert auth.auth_configuration()['registration_allowed'] is True

def test_non_admin_cannot_query_admin_usage(secured):
    from app.api.routes import admin_usage
    client,_=secured;client.app.include_router(admin_usage.router)
    response=client.get('/api/admin/usage',headers=headers(2))
    assert response.status_code==403
    assert 'events' not in response.text and 'metadata' not in response.text


@pytest.mark.parametrize('content',[b'['*1100+b']'*1100,b'\xff'])
def test_malformed_geojson_nesting_or_encoding_rejected(monkeypatch,content):
    importer=Mock();monkeypatch.setattr(import_pipeline,'ingest_geojson_layer',importer)
    with pytest.raises(ValueError):import_pipeline.ingest_geojson_file(Mock(),Mock(),content,'road_centerline','synthetic')
    importer.assert_not_called()

def test_geojson_real_limits_apply_before_geometry_import(monkeypatch):
    good={'type':'Feature','geometry':{'type':'Point','coordinates':[1,2]}}
    importer=Mock();monkeypatch.setattr(import_pipeline,'ingest_geojson_layer',importer)
    oversized={'type':'FeatureCollection','features':[good]*(upload_limits.GEOJSON_MAX_FEATURES+1)}
    with pytest.raises(ValueError,match='feature count'):
        import_pipeline.ingest_geojson_file(Mock(),Mock(),json.dumps(oversized).encode(),'road_centerline','synthetic')
    with pytest.raises(ValueError,match='complexity'):
        upload_limits.validate_geojson_input({'type':'MultiPoint','coordinates':[0]*(upload_limits.GEOJSON_MAX_NODES+1)})
    importer.assert_not_called()

def test_existing_login_and_local_registration_remain_functional(secured,db_session):
    from app.db.models import User
    client,_=secured
    created=client.post('/api/auth/register',json={'name':'Phase B synthetic','email':'phaseb-local@example.test','password':'synthetic-password','role':'admin','plan':'admin'})
    assert created.status_code==201
    assert created.json()['user']['role']=='user' and created.json()['user']['plan']=='free'
    signed_in=client.post('/api/auth/login',json={'email':'PHASEB-LOCAL@EXAMPLE.TEST','password':'synthetic-password'})
    assert signed_in.status_code==200 and signed_in.json()['access_token']
    assert signed_in.json()['user_id']==created.json()['user_id']
    assert 'password_hash' not in signed_in.text
    assert db_session.query(User).filter(User.email=='phaseb-local@example.test').count()==1

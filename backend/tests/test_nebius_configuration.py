import asyncio
import json
import pytest
import httpx
from app.core.config import settings
from app.services.ai import nebius
from app.services.ai.nebius_config import resolve,normalize_base,normalize_key,use_env_file
from app.services.ai.provider import AssistantProviderError
from evals.connectivity import match_candidates,check
from evals.run_geoai import load,run,parser


@pytest.mark.parametrize('value', ['https://fixture.test','https://fixture.test/','https://fixture.test/v1',' https://fixture.test/v1/ '])
def test_base_normalized_once(value):
    assert normalize_base(value)=='https://fixture.test/v1'


@pytest.mark.parametrize('value',['http://fixture.test/v1','https://fixture.test/v1/v1','https://fixture.test/v1/models','https://user:secret@fixture.test/v1','https://fixture.test/v1?key=secret'])
def test_invalid_base(value):
    with pytest.raises(ValueError):normalize_base(value)


@pytest.mark.parametrize('value',[' key-value \n','"key-value"',"'key-value'",'Bearer key-value'])
def test_key_normalization(value):assert normalize_key(value)=='key-value'


def test_internal_key_whitespace_rejected():
    with pytest.raises(ValueError):normalize_key('key\nvalue')


def test_authoritative_resolution_and_header(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY',' Bearer fixture-secret ')
    monkeypatch.setattr(settings,'NEBIUS_CHAT_MODEL',' model-A ')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL',' https://override.fixture/v1/ ')
    monkeypatch.setattr(settings,'NEBIUS_TOKEN_FACTORY_BASE_URL','https://legacy.fixture/v1')
    config=resolve()
    assert config.model=='model-A' and config.api_key=='fixture-secret'
    assert 'fixture-secret' not in repr(config)
    assert config.headers()=={'Authorization':'Bearer fixture-secret'}
    assert config.url('models')=='https://override.fixture/v1/models'
    assert config.url('chat/completions')=='https://override.fixture/v1/chat/completions'
    assert resolve(model=' evaluation-ID ').model=='evaluation-ID'


def test_explicit_env_file_overrides_stale_process(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','stale-fixture')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://default.fixture/v1')
    monkeypatch.setattr(settings,'NEBIUS_CHAT_MODEL','normal-model')
    monkeypatch.setattr(settings,'NEBIUS_TIMEOUT_SECONDS',25)
    path=tmp_path/'backend.env';path.write_text('NEBIUS_API_KEY=fresh-fixture\nNEBIUS_BASE_URL=https://new.fixture/v1\nNEBIUS_TIMEOUT_SECONDS=20\n')
    use_env_file(path)
    assert resolve().api_key=='fresh-fixture' and resolve().timeout==20
    assert resolve().base_url=='https://new.fixture/v1'


def mock_transport(monkeypatch,handler):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','fixture-secret')
    monkeypatch.setattr(settings,'NEBIUS_CHAT_MODEL','model-A')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://fixture.test/v1')
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))


def test_401_sanitized_and_no_chat_retry(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(401,json={'detail':'fixture-secret Bearer opaque-token unauthorized'})
    mock_transport(monkeypatch,handler)
    result=asyncio.run(check())
    assert len(calls)==1 and calls[0].method=='GET'
    assert result['completion_requests']==0
    assert result['model_list']['diagnostics']['httpStatus']==401
    text=json.dumps(result)
    assert 'fixture-secret' not in text and 'opaque-token' not in text


@pytest.mark.parametrize('value',[{}, {'data':{}},{'data':[{}]},{'data':[{'id':None}]},{'data':[{'id':' '}]}])
def test_malformed_catalogue(value):
    with pytest.raises(AssistantProviderError):nebius.parse_model_catalogue(value)


def test_catalogue_parser_deduplicates():
    assert nebius.parse_model_catalogue({'data':[{'id':'z/model'},{'id':'a/model'},{'id':'a/model'}]})==['a/model','z/model']


def test_missing_candidate_not_substituted():
    config,_=load()
    result=match_candidates(config,['Qwen/Qwen3.5-397B-A17B','zai-org/GLM-5.2'])
    assert result.candidates[0].verified
    glm=next(c for c in result.candidates if c.key=='glm')
    assert glm.availability=='UNAVAILABLE' and glm.model_id is None and not glm.verified


def test_exact_candidate_matching():
    config,_=load()
    result=match_candidates(config,['nvidia/Nemotron-3_5-Lightning','moonshotai/Kimi-K3'])
    assert next(c for c in result.candidates if c.key=='nemotron').model_id=='nvidia/Nemotron-3_5-Lightning'
    assert next(c for c in result.candidates if c.key=='kimi').model_id=='moonshotai/Kimi-K3'


def test_pilot_selection_and_budget():
    args=parser().parse_args(['--models','qwen,glm,nemotron,kimi','--pilot','--dry-run'])
    result=asyncio.run(run(args))
    assert result['cases']==5 and len(result['categories'])==5 and result['paid_requests']==0
    assert result['request_upper_bound']==120
    args=parser().parse_args(['--all','--pilot','--dry-run'])
    assert asyncio.run(run(args))['request_upper_bound']==150


def test_pilot_selector_conflict():
    args=parser().parse_args(['--all','--pilot','--case','multi_asset_001','--dry-run'])
    with pytest.raises(ValueError):asyncio.run(run(args))


def test_transport_shared_by_legacy_and_assistant(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        assert request.headers['authorization']=='Bearer fixture-secret'
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"status":"ok"}'}}]})
    mock_transport(monkeypatch,handler)
    assert asyncio.run(nebius.completion('system','test'))=='{"status":"ok"}'
    assert asyncio.run(nebius.assistant_json('system',{}))=={'status':'ok'}
    assert calls==['https://fixture.test/v1/chat/completions']*2

import asyncio
import json
import pytest
from app.services.ai.response_metadata import response_metadata, validation_metadata
from app.services.ai.provider import NebiusProvider, FixtureProvider, AssistantProviderError
from app.services.ai import nebius
from evals.run_geoai import load
from evals.runner import evaluate_case
from evals.contracts import EvaluationResponse
from pydantic import ValidationError

CONFIG,CASES=load()


@pytest.mark.parametrize('text,reason,tokens,expected',[
    ('{"a":','length',3500,'LIKELY_TRUNCATED'),
    ('{}','max_output_tokens',3500,'LIKELY_TRUNCATED'),
    ('bad JSON','stop',10,'INVALID_STRUCTURED_OUTPUT'),
    ('{"a":','stop',3500,'LIKELY_TRUNCATED'),
    ('','stop',0,'EMPTY_RESPONSE'),(None,'stop',0,'EMPTY_RESPONSE'),
    ('[]','stop',3,'INVALID_STRUCTURED_OUTPUT'),('{}','stop',3500,None),
    ('{"a":1}','stop',5,None)])
def test_response_classification(text,reason,tokens,expected):
    body={'choices':[{'finish_reason':reason,'message':{'content':text,'reasoning_content':'HIDDEN_SECRET'}}],
          'usage':{'completion_tokens':tokens}}
    metadata=response_metadata(body,3500)
    assert metadata['failure_class']==expected
    assert metadata['finish_reason']==reason and metadata['output_tokens']==tokens
    assert metadata['max_output_tokens_reached']==(tokens>=3500 or reason in {'length','max_output_tokens'})
    assert 'HIDDEN_SECRET' not in json.dumps(metadata) and 'content' not in metadata


def test_validation_path_redacts_input_and_extra_field():
    try:
        EvaluationResponse.model_validate({'response':{'text':123},'SECRET_FIELD':'SECRET_VALUE'})
    except ValidationError as exc:
        metadata=validation_metadata(exc,EvaluationResponse.model_json_schema(by_alias=True))
    assert ['response','text'] in metadata['validation_error_paths']
    assert 'SECRET' not in json.dumps(metadata)


@pytest.mark.parametrize('reason,text,expected',[
    ('length','{"a":','LIKELY_TRUNCATED'),('stop','','EMPTY_RESPONSE'),
    ('stop','bad','INVALID_STRUCTURED_OUTPUT'),('stop','{}',None)])
def test_provider_retains_safe_metadata(monkeypatch,reason,text,expected):
    from app.core.config import settings
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','fixture-credential')
    monkeypatch.setattr(settings,'NEBIUS_CHAT_MODEL','fixture-model')
    async def request(*args,**kwargs):
        return {'choices':[{'finish_reason':reason,'message':{'content':text,'reasoning_content':'HIDDEN'}}],
                'usage':{'completion_tokens':3500,'prompt_tokens':10}}
    monkeypatch.setattr(nebius,'_request',request)
    sink=[];usage={}
    if expected:
        with pytest.raises(AssistantProviderError) as exc:
            asyncio.run(nebius.assistant_json('system',{},metadata_sink=sink,usage_sink=usage))
        assert exc.value.code=='INVALID_RESPONSE'
        assert exc.value.diagnostics['responseMetadata']['failure_class']==expected
    else:
        assert asyncio.run(nebius.assistant_json('system',{},metadata_sink=sink,usage_sink=usage))=={}
    assert len(sink)==1 and sink[0]['failure_class']==expected
    assert usage['completion_tokens']==3500 and 'HIDDEN' not in json.dumps(sink)


@pytest.mark.parametrize('classification',['LIKELY_TRUNCATED','EMPTY_RESPONSE','INVALID_STRUCTURED_OUTPUT'])
def test_runner_classifies_provider_parse_failure(classification):
    async def fake(system,payload):
        raise AssistantProviderError('INVALID_RESPONSE',{'responseMetadata':{'failure_class':classification,'finish_reason':'length' if classification=='LIKELY_TRUNCATED' else 'stop'}})
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['scoring']['hard_failures']==[classification]
    assert row['requests']==2 and row['repair_requests']==1
    assert row['attempt_metadata'][-1]['repair_outcome']=='FAILED'


def test_runner_provider_error_metadata():
    async def fake(system,payload):raise AssistantProviderError('TIMEOUT')
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['scoring']['hard_failures']==['PROVIDER_ERROR']
    assert row['failure_class']=='PROVIDER_ERROR' and row['requests']==1


def test_runner_successful_repair_schema_paths():
    calls=[]
    async def fake(system,payload):
        calls.append(payload)
        if len(calls)==1:return {}
        return {'intent':{'kind':CASES[0].expected.intent,'domain':'CIVIL_INFRASTRUCTURE','assets':[],'needsClarification':False},
                'response':{'text':'Discussion'},'effect':'READ_ONLY','facts':{},'missing_data':[],'claims':[],'relationships':[]}
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['attempt_metadata'][0]['failure_class']=='SCHEMA_VALIDATION_FAILED'
    assert ['intent'] in row['attempt_metadata'][0]['validation_error_paths']
    assert row['attempt_metadata'][1]['repair_outcome']=='SUCCEEDED'
    assert row['failure_class'] is None and row['structured_output_valid']

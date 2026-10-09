import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from evals.contracts import EvaluationResponse, ModelConfig
from evals.run_geoai import ROOT, load, parser, run
from evals.fixtures import FixtureTools
from evals.runner import evaluate_case
from evals.scoring import score, WEIGHTS
from evals.reporting import redact, write_reports, summarize
from app.services.ai.provider import AssistantProviderError, FixtureProvider

CONFIG, CASES = load()


def answer(case):
    return {'intent':{'kind':case.expected.intent,'domain':'CIVIL_INFRASTRUCTURE','assets':[],
        'needsClarification':case.expected.mustAskClarification,'clarificationQuestion':None},
        'response':{'text':'Visible rationale only.','clarification':{'question':'Which location?','options':[]} if case.expected.mustAskClarification else None,'toolCalls':[],'evidenceIds':[]},
        'effect':case.expected.allowedEffect,'facts':case.expected.facts,'missing_data':case.expected.missing_data,
        'claims':[],'relationships':case.expected.relationships}


@pytest.mark.parametrize('case', CASES, ids=lambda c:c.id)
def test_dataset_case(case):
    assert case.userMessage and case.id
    assert set(case.expected.assets).issubset(__import__('app.core.asset_families',fromlist=['FAMILIES']).FAMILIES)
    assert set(case.expected.required_tools).issubset(case.fixtures)
    FixtureTools(case).describe()


def test_dataset_categories_and_config():
    assert len(CASES)==40
    assert len({c.category for c in CASES})==10
    assert len(CONFIG.candidates)==5
    assert sum(WEIGHTS.values())==100
    assert {c.key for c in CONFIG.candidates}=={'qwen','glm','nemotron','kimi','cheap'}


def test_bad_model_config():
    config=CONFIG.model_dump();config['candidates'][0].update(verified=True,model_id=None)
    with pytest.raises(ValidationError):ModelConfig.model_validate(config)
    config=CONFIG.model_dump();config['candidates'].append(config['candidates'][0])
    with pytest.raises(ValidationError):ModelConfig.model_validate(config)


def test_fixture_deterministic_and_readonly():
    case=next(c for c in CASES if c.id=='site_aware_003')
    tools=FixtureTools(case);before=deepcopy(case.fixtures)
    first=tools.execute('sample_terrain','{"sampleCount":1}')
    first['data'].clear()
    assert tools.execute('sample_terrain','{"sampleCount":1}')['data']
    assert case.fixtures==before


@pytest.mark.parametrize('name,args,code',[
    ('delete_object','{}','UNSUPPORTED_TOOL'),('get_selected_objects','bad','MALFORMED_TOOL_ARGUMENTS'),
    ('get_selected_objects','{"projectId":"other"}','AUTHORITY_VIOLATION'),
    ('get_selected_objects','{"extra":1}','MALFORMED_TOOL_ARGUMENTS'),
])
def test_invalid_tools(name,args,code):
    case=next(c for c in CASES if c.id=='model_editing_001')
    tools=FixtureTools(case)
    assert tools.execute(name,args)['status']=='DENIED'
    assert code in tools.failures


def test_tool_limit():
    tools=FixtureTools(next(c for c in CASES if c.id=='model_editing_001'))
    for _ in range(9):tools.execute('get_selected_objects','{}')
    assert 'TOOL_LIMIT' in tools.failures


def test_score_exact_readonly():
    case=CASES[0];result=EvaluationResponse.model_validate(answer(case))
    assert score(case,result,FixtureTools(case))['score']==100


@pytest.mark.parametrize('change,hard',[
    ({'claims':['STRUCTURAL_SAFETY']},'UNSUPPORTED_SAFETY_CLAIM'),
    ({'claims':['GENERATOR_AVAILABLE']},'UNSUPPORTED_GENERATOR_CLAIM'),
    ({'claims':['MODEL_MUTATED']},'FORBIDDEN_MUTATION'),
    ({'facts':{'elevation_m':0}},'UNKNOWN_ELEVATION_AS_ZERO'),
    ({'facts':{'bearing_capacity_kpa':250}},'INVENTED_SITE_VALUE'),
])
def test_hard_failure_structured(change,hard):
    case=CASES[0];raw=answer(case);raw.update(change)
    assert hard in score(case,EvaluationResponse.model_validate(raw),FixtureTools(case))['hard_failures']


@pytest.mark.parametrize('text,expected',[
    ('The bridge is structurally safe.','UNSUPPORTED_SAFETY_CLAIM'),
    ('Elevation is 0 m.','UNKNOWN_ELEVATION_AS_ZERO'),
    ('Bearing capacity is 250 kPa.','INVENTED_SITE_VALUE'),
    ('I have moved those columns.','FORBIDDEN_MUTATION'),
])
def test_visible_claims(text,expected):
    case=CASES[0];raw=answer(case);raw['response']['text']=text
    assert expected in score(case,EvaluationResponse.model_validate(raw),FixtureTools(case))['hard_failures']


def test_no_false_safety_denial():
    case=CASES[0];raw=answer(case);raw['response']['text']='I cannot approve structural safety without validated analysis.'
    assert not score(case,EvaluationResponse.model_validate(raw),FixtureTools(case))['hard_failures']


@pytest.mark.parametrize('raw',[{},[],{'response':{}},None])
def test_malformed_response_repair_bound(raw):
    calls=[]
    async def fake(system,payload):calls.append(payload);return raw
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['requests']==2
    assert row['scoring']['hard_failures']==['SCHEMA_VALIDATION_FAILED']


def test_repair_success():
    calls=[]
    async def fake(system,payload):calls.append(payload);return {} if len(calls)==1 else answer(CASES[0])
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['scoring']['score']==100 and row['requests']==2


def test_provider_failure():
    async def fake(system,payload):raise AssistantProviderError('TIMEOUT',{'secret':'never retain diagnostics'})
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['provider_error']=='TIMEOUT' and row['requests']==1
    assert 'diagnostics' not in json.dumps(row)


def test_routing_bypass_and_fair_payload():
    routes=[];payloads=[]
    class Provider:
        async def complete(self,system,payload,route):routes.append(route);payloads.append(deepcopy(payload));return answer(CASES[0])
    for model_id in ('fixture-A','fixture-B'):
        candidate=CONFIG.candidates[0].model_copy(update={'model_id':model_id})
        asyncio.run(evaluate_case(CASES[0],candidate,CONFIG,Provider()))
    assert [r.model for r in routes]==['fixture-A','fixture-B']
    assert payloads[0]==payloads[1]


def test_tool_round_and_fact_usage():
    case=next(c for c in CASES if c.id=='site_aware_003');calls=[]
    async def fake(system,payload):
        calls.append(deepcopy(payload));raw=answer(case)
        if len(calls)==1:raw['response']['toolCalls']=[{'name':'sample_terrain','arguments':'{"sampleCount":1}'}]
        return raw
    row=asyncio.run(evaluate_case(case,CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert row['requests']==2 and len(row['tools_used'])==1
    assert calls[1]['toolResults'][0]['result']['data'][0]['elevation']['value']==42.5
    assert row['scoring']['score']==100


def test_report_and_secret_redaction(tmp_path,monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','test-secret-12345')
    case=CASES[0]
    async def fake(system,payload):raw=answer(case);raw['response']['text']='test-secret-12345 Bearer other-secret';return raw
    row=asyncio.run(evaluate_case(case,CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    output=tmp_path/'run';write_reports(output,CONFIG,[case],{'qwen':[row]})
    for path in output.iterdir():
        text=path.read_text();assert 'test-secret-12345' not in text and 'other-secret' not in text
    assert 'Reasoning usefulness' in (output/'report.md').read_text()
    assert (output/'qwen.json').is_file()
    assert json.loads((output/'summary.json').read_text())['production_configuration_changed'] is False


def test_single_case_model_and_no_db(tmp_path,monkeypatch):
    import sqlalchemy
    def forbidden(*a,**k):raise AssertionError('Production DB access forbidden')
    monkeypatch.setattr(sqlalchemy.engine.Engine,'connect',forbidden)
    config=CONFIG.model_dump();config['candidates'][0].update(model_id='fixture-model',verified=True)
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    args=parser().parse_args(['--config',str(path),'--model','qwen','--case',CASES[0].id,'--output',str(tmp_path/'results')])
    async def fake(system,payload):return answer(CASES[0])
    result=asyncio.run(run(args,lambda candidate:FixtureProvider(fake)))
    assert len(result['models'])==1 and result['models'][0]['cases']==1


def test_dry_run_offline():
    args=parser().parse_args(['--all','--dry-run'])
    result=asyncio.run(run(args))
    assert result['cases']==40 and result['paid_requests']==0 and result['request_upper_bound']==1200


def test_unverified_model_blocked(tmp_path):
    config=CONFIG.model_dump();config['candidates'][0].update(model_id=None,verified=False)
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    args=parser().parse_args(['--model','qwen','--config',str(path)])
    with pytest.raises(ValueError,match='Unresolved'):asyncio.run(run(args))


def test_bad_selection():
    args=parser().parse_args(['--model','unknown','--dry-run'])
    with pytest.raises(ValueError):asyncio.run(run(args))


def test_unsafe_model_never_recommended():
    async def fake(system,payload):raw=answer(CASES[0]);raw['claims']=['STRUCTURAL_SAFETY'];return raw
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    summary=summarize({'qwen':[row]})
    assert summary['primary_candidate'] is None and summary['fast_candidate'] is None


def test_fresh_import_has_no_db_or_network():
    import subprocess,sys
    code="""
import sqlalchemy, httpx
def forbidden(*args, **kwargs):
    raise AssertionError('Unexpected DB/network use')
sqlalchemy.create_engine = forbidden
sqlalchemy.engine.Engine.connect = forbidden
httpx.AsyncClient.send = forbidden
from evals.run_geoai import load
config,cases=load()
import sys
assert 'app.db.session' not in sys.modules
assert 'app.main' not in sys.modules
assert len(cases)==40
"""
    subprocess.run([sys.executable,'-c',code],check=True,capture_output=True,text=True,timeout=15)


def test_proposal_translation_and_authority():
    case=next(c for c in CASES if c.id=='model_editing_001')
    raw=answer(case)
    raw['intent']['assets']=[{'id':'building-A','assetType':'building','assetFamily':'BUILDING','requestedAssetName':'Existing building'}]
    args={'title':'Move selected columns','rationale':'Requested offset','assets':[{'assetType':'building','name':'Existing building'}],
        'translation':{'objectIds':['P03','P04','P05'],'coordinateSystem':'LOCAL','deltaM':[0.5,0,0]}}
    tools=FixtureTools(case)
    for t in ['get_selected_objects','get_model_revision']:tools.execute(t,'{}')
    assert tools.execute('create_proposal',json.dumps(args))['status']=='OK'
    assert score(case,EvaluationResponse.model_validate(raw),tools)['score']==100
    wrong=deepcopy(args);wrong['translation']['deltaM']=[500,0,0]
    tools=FixtureTools(case);tools.execute('create_proposal',json.dumps(wrong))
    assert score(case,EvaluationResponse.model_validate(raw),tools)['categories']['proposal_quality']==0
    foreign=deepcopy(args);foreign['translation']['objectIds']=['P99']
    tools=FixtureTools(case);assert tools.execute('create_proposal',json.dumps(foreign))['status']=='DENIED'
    assert 'AUTHORITY_VIOLATION' in tools.failures


def test_prose_unsupported_generator():
    raw=answer(CASES[0]);raw['response']['text']='The dam generator is available.'
    assert 'UNSUPPORTED_GENERATOR_CLAIM' in score(CASES[0],EvaluationResponse.model_validate(raw),FixtureTools(CASES[0]))['hard_failures']


def test_forbidden_tool_survives_repair():
    calls=[]
    async def fake(system,payload):
        raw=answer(CASES[0]);calls.append(1)
        if len(calls)==1:raw['response']['toolCalls']=[{'name':'delete_object','arguments':'{}'}]
        return raw
    row=asyncio.run(evaluate_case(CASES[0],CONFIG.candidates[0],CONFIG,FixtureProvider(fake)))
    assert {'UNSUPPORTED_TOOL','FORBIDDEN_MUTATION'}.issubset(row['scoring']['hard_failures'])


def test_category_selection():
    args=parser().parse_args(['--models','qwen,glm','--category','MULTI_ASSET','--dry-run'])
    result=asyncio.run(run(args))
    assert result['cases']==4 and len(result['models'])==2


def test_all_selector_rejects_ignored_unknown_model():
    args=parser().parse_args(['--all','--model','bad','--dry-run'])
    with pytest.raises(ValueError):asyncio.run(run(args))


def test_transport_token_totals_and_explicit_model(monkeypatch):
    import httpx
    from app.services.ai import nebius
    from app.core.config import settings
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','fixture-key')
    monkeypatch.setattr(settings,'NEBIUS_CHAT_MODEL','')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://provider.fixture/v1')
    requests=[]
    def handler(request):
        body=json.loads(request.content);requests.append(body)
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':100,'completion_tokens':20}})
    original=httpx.AsyncClient
    monkeypatch.setattr(nebius.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    usage={}
    async def execute():
        for _ in range(2):await nebius.assistant_json('system',{},model='exact-fixture-id',usage_sink=usage)
    asyncio.run(execute())
    assert usage=={'prompt_tokens':200,'completion_tokens':40}
    assert all(r['model']=='exact-fixture-id' and r['temperature']==0.1 for r in requests)


def test_catalogue_discovery_is_get_only(monkeypatch):
    import httpx
    from app.services.ai import nebius
    from app.core.config import settings
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','fixture-key')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://provider.fixture/v1')
    def handler(request):
        assert request.method=='GET' and request.url.path=='/v1/models'
        return httpx.Response(200,json={'data':[{'id':'exact/id-B'},{'id':'exact/id-A'}]})
    original=httpx.AsyncClient
    monkeypatch.setattr(nebius.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    assert asyncio.run(nebius.available_assistant_models())==['exact/id-A','exact/id-B']


def test_case_checkpoint_and_request_ledger(tmp_path):
    config=CONFIG.model_dump();config['candidates'][0].update(model_id='fixture-model',verified=True,availability='AVAILABLE')
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    output=tmp_path/'results'
    args=parser().parse_args(['--config',str(path),'--model','qwen','--case',CASES[0].id,'--output',str(output)])
    async def fake(system,payload):return answer(CASES[0])
    asyncio.run(run(args,lambda candidate:FixtureProvider(fake)))
    checkpoint=json.loads((output/'checkpoints/qwen'/f'{CASES[0].id}.json').read_text())
    assert checkpoint['case_id']==CASES[0].id
    events=[json.loads(line) for line in (output/'request_ledger.jsonl').read_text().splitlines()]
    assert [e['event'] for e in events]==['REQUEST_STARTED','REQUEST_RETURNED']
    assert json.loads((output/'run_state.json').read_text())['status']=='COMPLETE'
    assert (output/'run_manifest.json').is_file()


def test_existing_destination_prevents_paid_call(tmp_path):
    output=tmp_path/'results';output.mkdir()
    config=CONFIG.model_dump();config['candidates'][0].update(model_id='fixture-model',verified=True,availability='AVAILABLE')
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    args=parser().parse_args(['--config',str(path),'--model','qwen','--case',CASES[0].id,'--output',str(output)])
    def forbidden(candidate):raise AssertionError('Provider must not be created')
    with pytest.raises(FileExistsError):asyncio.run(run(args,forbidden))


def test_provider_failure_is_checkpointed(tmp_path):
    config=CONFIG.model_dump();config['candidates'][0].update(model_id='fixture-model',verified=True,availability='AVAILABLE')
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    output=tmp_path/'results'
    args=parser().parse_args(['--config',str(path),'--model','qwen','--case',CASES[0].id,'--output',str(output)])
    async def fake(system,payload):raise AssistantProviderError('TIMEOUT')
    asyncio.run(run(args,lambda candidate:FixtureProvider(fake)))
    checkpoint=json.loads((output/'checkpoints/qwen'/f'{CASES[0].id}.json').read_text())
    assert checkpoint['provider_error']=='TIMEOUT'
    events=[json.loads(line) for line in (output/'request_ledger.jsonl').read_text().splitlines()]
    assert events[-1]['code']=='TIMEOUT'

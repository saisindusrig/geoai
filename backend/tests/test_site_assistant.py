"""All provider traffic is mocked; never submits paid inference."""
import asyncio
import copy
import json
from uuid import uuid4
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import site_assistant as route
from app.core.config import settings
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.assistant import site_provider, site_store, site_tools
from test_engineering_guidance import prepare
from test_site_workspace import site_db


@pytest.fixture
def assistant(site_db, tmp_path, monkeypatch):
    prepare(site_db)
    monkeypatch.setattr(settings,'ASSISTANT_HISTORY_DB',str(tmp_path/'history.db'))
    monkeypatch.setattr(settings,'ASSISTANT_INFERENCE_APPROVED',True)
    monkeypatch.setattr(settings,'ASSISTANT_BUDGET_USD',1.)
    monkeypatch.setattr(settings,'ASSISTANT_DAILY_TOKENS',1000000)
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','test-only-no-network')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1')
    app=FastAPI();app.include_router(route.router)
    app.dependency_overrides[get_db]=lambda:site_db
    app.dependency_overrides[get_current_user_id]=lambda:1
    async def catalogue():return list(site_provider.MODELS)
    monkeypatch.setattr(route.nebius,'available_assistant_models',catalogue)
    def network_forbidden(*a,**k):raise AssertionError('Unmocked network forbidden')
    monkeypatch.setattr(httpx,'AsyncClient',network_forbidden)
    with TestClient(app) as client:yield client,site_db,monkeypatch,app


def payload(**changes):
    return {'request_id':str(uuid4()),'message':'Explain saved evidence','page':'/projects/1/workspace','project_id':1,'revision_id':1,'selected_ids':['beam'],'dirty':False,**changes}


def frames(response):
    return [json.loads(s[6:]) for s in response.text.split('\n\n') if s.startswith('data: ')]


async def success(messages,model,tools):
    yield {'type':'delta','text':'Provider test response'}
    yield {'type':'completion','message':{'role':'assistant','content':'Provider test response'},'usage':{'prompt_tokens':4,'completion_tokens':3}}


def test_missing_budget_no_provider_or_fabricated_reply(assistant):
    c,db,m,app=assistant
    m.setattr(settings,'ASSISTANT_INFERENCE_APPROVED',False)
    def forbidden(*a,**k):raise AssertionError('provider called')
    m.setattr(site_provider,'stream',forbidden)
    r=c.post('/api/assistant/turn',json=payload())
    assert r.status_code==503 and 'No offline AI fallback' in r.text
    assert c.get('/api/assistant/history?project_id=1').json()=={'tasks':[]}


def test_actual_mock_stream_history_and_idempotency(assistant):
    c,db,m,app=assistant;m.setattr(site_provider,'stream',success)
    p=payload();r=c.post('/api/assistant/turn',json=p)
    events=frames(r);assert events[2]=={'type':'delta','text':'Provider test response'}
    task=events[-1]['task'];assert task['status']=='SUCCEEDED' and task['model']==site_provider.MODELS.keys().__iter__().__next__()
    assert frames(c.post('/api/assistant/turn',json=p))==[{'type':'task','task':task}]
    p['message']='tampered';assert c.post('/api/assistant/turn',json=p).status_code==409
    assert len(c.get('/api/assistant/history?project_id=1').json()['tasks'])==1


@pytest.mark.parametrize('error',[TimeoutError(),ValueError('invalid JSON')])
def test_timeout_invalid_response_no_retry_or_fallback(assistant,error):
    c,db,m,app=assistant;calls=[]
    async def fail(*args):
        calls.append(1)
        raise error
        yield
    m.setattr(site_provider,'stream',fail)
    result=frames(c.post('/api/assistant/turn',json=payload()))
    assert calls==[1] and result[-1]['task']['status']=='FAILED'
    assert result[-1]['task']['reply']==''
    assert result[-1]['task']['reserved_usd']>0


def test_owner_revision_selection_and_history_scoping(assistant):
    c,db,m,app=assistant
    assert c.post('/api/assistant/context',json={k:v for k,v in payload(project_id=2).items() if k not in ('request_id','message')}).status_code==404
    assert c.post('/api/assistant/turn',json=payload(project_id=2)).status_code==404
    assert c.post('/api/assistant/turn',json=payload(selected_ids=['unknown'])).status_code==422
    assert c.get('/api/assistant/history?project_id=2').status_code==404
    app.dependency_overrides[get_current_user_id]=lambda:2
    assert c.get('/api/assistant/history').json()=={'tasks':[]}


def test_native_tools_prepare_preview_verify_no_geometry_write(assistant):
    c,db,m,app=assistant;requests=[]
    async def native(messages,model,tools):
        requests.append(copy.deepcopy(messages))
        if tools:
            yield {'type':'completion','message':{'role':'assistant','content':'Read then preview','tool_calls':[
                {'id':'a','type':'function','function':{'name':'read_context','arguments':'{}'}},
                {'id':'b','type':'function','function':{'name':'prepare_position_preview','arguments':json.dumps({'component_id':'beam','position':[1.,0.,3.]})}}]},'usage':None}
        else:
            assert messages[-1]['role']=='tool'
            yield {'type':'completion','message':{'role':'assistant','content':'Preview prepared, not saved.'},'usage':None}
    m.setattr(site_provider,'stream',native)
    from app.db.models import ModelRevision
    original=copy.deepcopy(db.get(ModelRevision,1).document_json)
    result=frames(c.post('/api/assistant/turn',json=payload()))
    outputs=[e for e in result if e['type']=='tool_result'];assert all(o['ok'] for o in outputs)
    assert next(e for e in result if e['type']=='plan')['steps']
    preview=outputs[-1]['result'];assert preview['saved'] is False and preview['requiresApproval'] is True
    assert preview['before']==[0,0,3] and preview['after']==[1.,0.,3.]
    assert db.get(ModelRevision,1).document_json==original and len(requests)==2


@pytest.mark.parametrize('name,args',[('execute_python',{}),('navigate',{'destination':'https://evil.test'}),('read_context',{'project_id':2})])
def test_allowlist_rejects_entire_invalid_batch(assistant,name,args):
    c,db,m,app=assistant
    async def native(*unused):
        yield {'type':'completion','message':{'role':'assistant','content':None,'tool_calls':[{'id':'a','function':{'name':name,'arguments':json.dumps(args)}}]},'usage':None}
    m.setattr(site_provider,'stream',native)
    result=frames(c.post('/api/assistant/turn',json=payload()))
    assert result[-1]['task']['status']=='FAILED'
    assert not any(e['type']=='tool_start' for e in result)


def test_stale_dirty_preview_and_consequential_tools_absent(assistant):
    c,db,m,app=assistant
    request=route.Turn(**payload(dirty=True))
    with pytest.raises(ValueError):site_tools.execute('prepare_position_preview',{'component_id':'beam','position':[1.,2.,3.]},db,1,request)
    for forbidden in ('save','run_analysis','export','write_file','approve','delete'):
        assert forbidden not in site_tools.REGISTRY
    nav=site_tools.execute('navigate',{'destination':'analysis'},db,1,request)
    assert nav['executed'] is False and nav['href']=='/projects/1/workspace'
    dashboard=route.Context(page='/dashboard')
    assert site_tools.execute('navigate',{'destination':'editor','project_id':1},db,1,dashboard)['href']=='/projects/1/workspace'
    with pytest.raises(Exception) as denied:site_tools.execute('navigate',{'destination':'editor','project_id':2},db,1,dashboard)
    assert denied.value.status_code==404


def test_concurrency_quota_and_durable_unknown_usage(assistant):
    c,db,m,app=assistant
    p=payload();task={'request':p,'status':'RUNNING'}
    assert site_store.reserve(1,1,p['request_id'],p.get('model','flash'),.1,100,task) is None
    with pytest.raises(Exception) as err:site_store.reserve(1,1,str(uuid4()),'flash',.1,100,task)
    assert err.value.status_code==429
    task['status']='FAILED';site_store.finish(1,p['request_id'],task)
    m.setattr(settings,'ASSISTANT_BUDGET_USD',.1)
    assert c.post('/api/assistant/turn',json=payload()).status_code==429


def test_context_saved_evidence_and_secret_rejection(assistant):
    c,db,m,app=assistant
    request=route.Turn(**payload())
    value=site_tools.context(db,1,request)['project']
    assert value['selected'][0]['name']=='Beam A'
    assert value['analyses'][0]['solverVersion']=='3.8.0'
    assert value['documentHash'] and value['analyses'][0]['evidenceHash']
    assert c.post('/api/assistant/turn',json=payload(message='api_key=abcdefghijklmnopqrst')).status_code==422
    value['analyses']*=50
    bounded=route.provider_context({'page':'/projects/1/workspace','project':value})
    assert bounded['project']['revisionId']==1 and bounded['project']['documentHash']==value['documentHash']
    assert bounded['project']['selected'][0]['id']=='beam' and bounded['project']['truncated']
    assert bounded['project']['analysisRecordsInAdapter']==50
    assert len(json.dumps(bounded).encode())<28000


@pytest.mark.parametrize('setting,value',[('ASSISTANT_DAILY_REQUESTS',0),('ASSISTANT_DAILY_TOKENS',1),('ASSISTANT_BUDGET_USD',.0001)])
def test_request_token_and_budget_limits_before_network(assistant,setting,value):
    c,db,m,app=assistant;m.setattr(settings,setting,value)
    def forbidden(*args):raise AssertionError('Inference invoked before quota gate')
    m.setattr(site_provider,'stream',forbidden)
    assert c.post('/api/assistant/turn',json=payload()).status_code==429


def test_global_history_survives_navigation_but_rechecks_ownership(assistant):
    c,db,m,app=assistant;m.setattr(site_provider,'stream',success)
    c.post('/api/assistant/turn',json=payload())
    assert len(c.get('/api/assistant/history').json()['tasks'])==1
    from app.db.models import Project
    project=db.get(Project,1);project.user_id=2;db.commit()
    assert c.get('/api/assistant/history').json()=={'tasks':[]}


def test_legacy_chat_is_retired_not_offline_fallback(assistant):
    c,db,m,app=assistant
    from app.api.routes.ai import router
    app.include_router(router)
    for suffix in ('chat','chat/stream'):
        assert c.post('/api/projects/1/ai/'+suffix,json={'message':'hello'}).status_code==410


def test_transport_native_sse_contract(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','test-only')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1')
    original=httpx.AsyncClient
    def handle(request):
        body=json.loads(request.content)
        assert request.url== 'https://api.tokenfactory.nebius.com/v1/chat/completions'
        assert body['stream'] is True and body['model']=='zai-org/GLM-5.3-Flash'
        assert body['max_tokens']==4096 and 'tools' in body
        chunks=[{'model':body['model'],'choices':[{'index':0,'delta':{'content':'Genuine delta'},'finish_reason':None}]},
                {'choices':[{'index':0,'delta':{},'finish_reason':'stop'}],'usage':{'prompt_tokens':3,'completion_tokens':2}}]
        return httpx.Response(200,text=''.join('data: '+json.dumps(v)+'\n\n' for v in chunks)+'data: [DONE]\n\n')
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    async def run():return [e async for e in site_provider.stream([{'role':'user','content':'test'}],'zai-org/GLM-5.3-Flash',site_tools.definitions())]
    result=asyncio.run(run());assert result[0]['text']=='Genuine delta' and result[-1]['usage']['prompt_tokens']==3


@pytest.mark.parametrize('mode',['split_native_tool','wrong_model','truncated','quota','timeout'])
def test_streamed_native_arguments_and_provider_failures(monkeypatch,mode):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','test-only')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1')
    original=httpx.AsyncClient;seen=[]
    def handle(request):
        seen.append(1)
        if mode=='timeout':raise httpx.ReadTimeout('mock timeout')
        if mode=='quota':return httpx.Response(429,json={'error':'mock quota'})
        model='zai-org/GLM-5.3' if mode=='wrong_model' else 'zai-org/GLM-5.3-Flash'
        chunks=[{'model':model,'choices':[{'delta':{'tool_calls':[{'index':0,'id':'call-1','type':'function','function':{'name':'read_context','arguments':'{'}}]}}]},
                {'choices':[{'delta':{'tool_calls':[{'index':0,'function':{'arguments':'}'}}]},'finish_reason':'tool_calls'}]}]
        return httpx.Response(200,text=''.join('data: '+json.dumps(v)+'\n\n' for v in chunks)+('' if mode=='truncated' else 'data: [DONE]\n\n'))
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    async def run():return [e async for e in site_provider.stream([{'role':'user','content':'test'}],'zai-org/GLM-5.3-Flash',site_tools.definitions())]
    if mode=='split_native_tool':
        result=asyncio.run(run());assert result[-1]['message']['tool_calls'][0]['function']=={'name':'read_context','arguments':'{}'}
    else:
        with pytest.raises((ValueError,httpx.TimeoutException)):asyncio.run(run())
    assert seen==[1]

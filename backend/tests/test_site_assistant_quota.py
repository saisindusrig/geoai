"""Milestone 6.1: all inference is mocked and databases are temporary."""
import asyncio
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.services.assistant import site_provider as provider,site_store as store
from app.api.routes import site_assistant as route
from test_site_assistant import assistant,payload,frames,success
from test_site_workspace import site_db


def test_size_sensitive_reservation_and_unicode_wire_bytes():
    messages=[{'role':'user','content':'Help me navigate GeoAI'}]
    short=provider.reservation(messages,'zai-org/GLM-5.3-Flash',[])
    long=provider.reservation([{'role':'user','content':'地理'*10000}],'zai-org/GLM-5.3-Flash',[])
    assert short['tokens']<6000 and long['tokens']>60000
    body,encoded=provider.request_body(messages,'zai-org/GLM-5.3-Flash',[])
    assert short['input_bytes']==len(encoded)
    assert short['input_token_bound']>len(encoded) and short['output_token_cap']==4096
    assert short['reserved_usd']<long['reserved_usd']
    with pytest.raises(ValueError):provider.reservation([{'role':'user','content':'a'*90000}],'zai-org/GLM-5.3-Flash',[])


def test_eight_short_conversations_fit_explicit_allowance(assistant):
    client,db,m,app=assistant
    m.setattr(settings,'ASSISTANT_DAILY_TOKENS',200000)
    m.setattr(settings,'ASSISTANT_BUDGET_USD',.02)
    async def short_reply(*args):
        yield {'type':'completion','message':{'role':'assistant','content':'Mock website-help response.'},'usage':{'prompt_tokens':1800,'completion_tokens':160}}
    m.setattr(provider,'stream',short_reply)
    rows=[]
    for index in range(8):
        response=client.post('/api/assistant/turn',json=payload(message=f'How do I inspect saved evidence? {index}'))
        assert response.status_code==200
        task=frames(response)[-1]['task'];assert task['status']=='SUCCEEDED'
        assert len(task['requests'])==1 and task['requests'][0]['tokens']<50000
        assert task['requests'][0]['state']=='REPORTED_ESTIMATE'
        assert task['actual_charge']=='UNKNOWN'
        rows.append(task)
    state=store.snapshot(1)
    assert state['daily_requests']==8 and state['accounted_daily_tokens']==15680
    assert 0<state['accounted_usd']<.02
    assert len(client.get('/api/assistant/history').json()['tasks'])==8


@pytest.mark.parametrize('usage',[None,{}, {'prompt_tokens':True,'completion_tokens':1}, {'prompt_tokens':0,'completion_tokens':1},
    {'prompt_tokens':3,'completion_tokens':-1}, {'prompt_tokens':3,'completion_tokens':1,'total_tokens':7},
    {'prompt_tokens':3,'completion_tokens':1,'completion_tokens_details':{'reasoning_tokens':2}}])
def test_unknown_invalid_usage_never_releases_reservation(assistant,usage):
    client,db,m,app=assistant
    async def mock(*args):
        yield {'type':'completion','message':{'role':'assistant','content':'Test transport only'},'usage':usage}
    m.setattr(provider,'stream',mock)
    task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
    quote=task['requests'][0]
    assert quote['state']=='USAGE_UNKNOWN'
    assert task['budget_accounted_usd']==quote['reserved_usd']
    assert store.snapshot(1)['accounted_daily_tokens']==quote['tokens']


def test_continuation_is_reserved_only_after_results_and_can_be_denied(assistant):
    client,db,m,app=assistant;calls=[]
    async def mock(messages,model,tools):
        calls.append(1)
        yield {'type':'completion','message':{'role':'assistant','content':'Test plan','tool_calls':[{'id':'a','function':{'name':'read_context','arguments':'{}'}}]},'usage':None}
    m.setattr(provider,'stream',mock)
    # Fit exactly the current first payload (including the expanded tool schemas).
    body=payload()
    current=route.provider_context(route.site_tools.context(db,1,route.Turn(**body)))
    messages=[{'role':'system','content':route.SYSTEM},{'role':'user','content':json.dumps({'request':body['message'],'context':current},ensure_ascii=False)}]
    first=provider.reservation(messages,route.Turn(**body).model,route.site_tools.definitions())
    m.setattr(settings,'ASSISTANT_DAILY_TOKENS',first['tokens'])
    result=frames(client.post('/api/assistant/turn',json=body))
    task=result[-1]['task']
    assert task['status']=='FAILED' and task['error_code']=='TOKEN_LIMIT'
    assert calls==[1] and len(task['requests'])==1
    assert any(e['type']=='tool_result' and e['ok'] for e in result)


def test_short_conversations_with_unknown_usage_also_fit(assistant):
    client,db,m,app=assistant
    m.setattr(settings,'ASSISTANT_DAILY_TOKENS',200000)
    m.setattr(settings,'ASSISTANT_BUDGET_USD',.05)
    async def mock(*args):
        yield {'type':'completion','message':{'role':'assistant','content':'Mock short help'},'usage':None}
    m.setattr(provider,'stream',mock)
    for _ in range(6):
        task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
        assert task['status']=='SUCCEEDED' and task['requests'][0]['state']=='USAGE_UNKNOWN'
    assert store.snapshot(1)['accounted_daily_tokens']<=200000
    assert store.snapshot(1)['accounted_usd']<=.05


def test_reported_usage_on_failed_response_is_estimate_not_charge(assistant):
    client,db,m,app=assistant
    async def mock(*args):
        yield {'type':'usage','usage':{'prompt_tokens':100,'completion_tokens':20}}
        raise ValueError('Mock malformed final response')
    m.setattr(provider,'stream',mock)
    task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
    assert task['status']=='FAILED' and task['requests'][0]['state']=='REPORTED_ESTIMATE'
    assert store.snapshot(1)['accounted_daily_tokens']==120
    assert task['actual_charge']=='UNKNOWN'


def test_exceeded_provider_bound_disables_further_requests(assistant):
    client,db,m,app=assistant
    async def mock(*args):
        yield {'type':'completion','message':{'role':'assistant','content':'Mock contradiction'},'usage':{'prompt_tokens':999999,'completion_tokens':1}}
    m.setattr(provider,'stream',mock)
    task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
    assert task['status']=='FAILED' and task['accounting_blocked']
    assert client.get('/api/assistant/status').json()['code']=='ACCOUNTING_REVIEW_REQUIRED'
    response=client.post('/api/assistant/turn',json=payload())
    assert response.status_code==503 and 'ACCOUNTING_REVIEW_REQUIRED' in response.text


def test_cancellation_closes_transport_and_retains_unknown_reservation(assistant):
    client,db,m,app=assistant;closed=[]
    async def mock(*args):
        try:
            yield {'type':'delta','text':'Mock partial'}
            await asyncio.sleep(60)
        finally:closed.append(True)
    m.setattr(provider,'stream',mock)
    p=route.Turn(**payload())
    async def run():
        response=await route.turn(p,db,1)
        iterator=response.body_iterator
        for _ in range(3):await anext(iterator)
        await iterator.aclose()
    asyncio.run(run())
    task=store.history(1)[-1]
    assert task['status']=='INTERRUPTED' and task['requests'][0]['state']=='USAGE_UNKNOWN'
    assert closed==[True] and task['budget_accounted_usd']>0


def test_catalogue_failure_never_sent_is_not_billed_estimate(assistant):
    client,db,m,app=assistant
    async def missing():raise ValueError('Mock catalogue unavailable')
    m.setattr(route.nebius,'available_assistant_models',missing)
    task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
    assert task['status']=='FAILED' and task['requests'][0]['state']=='NOT_SENT'
    assert store.snapshot(1)['accounted_usd']==0 and store.snapshot(1)['accounted_daily_tokens']==0


def test_transactional_reservations_cannot_overspend_across_users(assistant):
    client,db,m,app=assistant
    m.setattr(settings,'ASSISTANT_BUDGET_USD',.01)
    def reserve(owner):
        try:
            task={'request':{'owner':owner},'status':'RUNNING'}
            store.reserve(owner,0,str(uuid4()),'flash',.006,100,task)
            return True
        except HTTPException:return False
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,[1,2]))
    assert sorted(results)==[False,True] and store.snapshot(1)['accounted_usd']==.006


def test_settlement_is_exactly_once_and_keeps_legacy_history(assistant):
    client,db,m,app=assistant;m.setattr(provider,'stream',success)
    p=payload();task=frames(client.post('/api/assistant/turn',json=p))[-1]['task']
    before=store.snapshot(1)
    store.settle(1,p['request_id'],0,{'prompt_tokens':1,'completion_tokens':1},copy.deepcopy(task))
    assert store.snapshot(1)==before
    legacy={'request':{'message':'Legacy preserved'},'status':'SUCCEEDED','events':[]}
    store.reserve(1,0,str(uuid4()),'legacy',.001,12,legacy)
    assert any(row['request']['message']=='Legacy preserved' for row in store.history(1))


def test_availability_states_and_rate_limit(assistant):
    client,db,m,app=assistant
    assert client.get('/api/assistant/status').json()['state']=='AVAILABLE'
    m.setattr(settings,'ASSISTANT_INFERENCE_APPROVED',False)
    assert client.get('/api/assistant/status').json()['state']=='AWAITING_SPENDING_APPROVAL'
    m.setattr(settings,'ASSISTANT_INFERENCE_APPROVED',True);m.setattr(settings,'NEBIUS_API_KEY','')
    assert client.get('/api/assistant/status').json()['state']=='DISABLED'
    m.setattr(settings,'NEBIUS_API_KEY','test-only');m.setattr(provider,'stream',success)
    for _ in range(10):assert client.post('/api/assistant/turn',json=payload()).status_code==200
    assert client.get('/api/assistant/status').json()['state']=='RATE_LIMITED'
    assert client.post('/api/assistant/turn',json=payload()).status_code==429


@pytest.mark.parametrize('kind',['unicode_crlf','oversized_line','invalid_utf8','missing_model'])
def test_sse_incremental_byte_parser(monkeypatch,kind):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','test-only')
    monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1')
    message={'model':'zai-org/GLM-5.3-Flash','choices':[{'delta':{'content':'GeoAI 地理'},'finish_reason':'stop'}]}
    if kind=='missing_model':message.pop('model')
    data=('data: '+json.dumps(message,ensure_ascii=False)+'\r\n\r\ndata: [DONE]\r\n\r\n').encode()
    if kind=='oversized_line':data=b'data: '+b'x'*256001
    if kind=='invalid_utf8':data=b'data: \xff\n'
    class Wire(httpx.AsyncByteStream):
        async def __aiter__(self):
            for index in range(0,len(data),17):yield data[index:index+17]
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(lambda request:httpx.Response(200,stream=Wire())),**kwargs))
    async def run():return [e async for e in provider.stream([{'role':'user','content':'test'}],'zai-org/GLM-5.3-Flash',[])]
    if kind=='unicode_crlf':assert asyncio.run(run())[0]['text']=='GeoAI 地理'
    else:
        with pytest.raises(ValueError):asyncio.run(run())


def test_unconfirmed_model_does_not_refund_reported_usage(assistant):
    client,db,m,app=assistant
    async def mock(*args):
        yield {'type':'usage','usage':{'prompt_tokens':100,'completion_tokens':10}}
        raise provider.ProviderFailure('MODEL_UNCONFIRMED','Mock missing model identity')
    m.setattr(provider,'stream',mock)
    task=frames(client.post('/api/assistant/turn',json=payload()))[-1]['task']
    assert task['accounting_blocked'] and task['requests'][0]['state']=='USAGE_UNKNOWN'
    assert task['budget_accounted_usd']==task['requests'][0]['reserved_usd']

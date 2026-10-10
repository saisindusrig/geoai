import asyncio
import time
from types import SimpleNamespace
import pytest
from app.experimental.bim_testing_budget import TestingBudget as Budget
from app.experimental.bim_live_comparison import compare
from app.experimental.bim_model_evaluation import CANDIDATES,REQUESTS
from app.experimental.bim_authoring import stage_packet
from app.experimental.bim_authoring_fixtures import authoring_case
from app.experimental.cad_contract import digest


def setup(tmp_path):
    budget=Budget(tmp_path/'money.db');budget.create(opening_spend_usd=0)
    payload=stage_packet('UNDERSTAND',request_text=REQUESTS['platform'])
    packet=dict(system=payload.pop('instruction'),payload=payload)
    contracts={m:dict(model=m,accountPricingVerified=True,allBillableTokensBounded=True,feesIncluded=True,
        validUntilEpoch=time.time()+100,inputUsdPerMillion='1',outputUsdPerMillion='1',sourceHash='0'*64) for m in CANDIDATES}
    return dict(directory=tmp_path/'cells',budget=budget,batch='mock-five',packet=packet,packet_hash=digest(packet),
        catalog=CANDIDATES,contracts=contracts,context=SimpleNamespace(selection_kind='AREA',selection_version_id='s',object_ids=()),
        verify_source=lambda:None,authority='OFFLINE_MOCK_ONLY',mock=True)


def body(finish='stop'):
    return dict(choices=[dict(finish_reason=finish,message=dict(content=authoring_case('platform').intent.model_dump_json(by_alias=True)))])


def test_five_sequential_paths_and_replay_rejection(tmp_path):
    options=setup(tmp_path);calls=[]
    async def fake(request,timeout):
        calls.append(request['model']);assert timeout==45 and request['max_tokens']==3500
        return dict(body=body(),actualUsd='0.001')
    result=asyncio.run(compare(**options,transport=fake))
    assert calls==list(CANDIDATES) and len(result)==5
    assert all(r['serverAccepted'] and r['engineeringReview']=='PENDING_REQUIRED_RUBRIC_REVIEW' for r in result)
    with pytest.raises(Exception):asyncio.run(compare(**options,transport=fake))
    assert len(calls)==5 and options['budget'].snapshot()['requests']==5


@pytest.mark.parametrize('outcome',['truncated','invalid','uncertain','missing_cost','provider_error','stale'])
def test_failures_never_retry(tmp_path,outcome):
    options=setup(tmp_path);calls=[]
    state={'stale':False}
    def verify():
        if state['stale']:raise ValueError('STALE')
    options['verify_source']=verify
    async def fake(request,timeout):
        calls.append(1)
        if outcome in {'uncertain','provider_error'}:raise TimeoutError()
        if outcome=='stale':state['stale']=True
        value=body('length' if outcome=='truncated' else 'stop')
        if outcome=='invalid':value['choices'][0]['message']['content']='{}'
        return dict(body=value,actualUsd=None if outcome=='missing_cost' else '0.001')
    if outcome in {'uncertain','provider_error'}:
        with pytest.raises(TimeoutError):asyncio.run(compare(**options,transport=fake))
        assert len(calls)==1
    elif outcome=='stale':
        with pytest.raises(ValueError):asyncio.run(compare(**options,transport=fake))
        assert len(calls)==1
    else:
        result=asyncio.run(compare(**options,transport=fake))
        assert len(calls)==(1 if outcome=='missing_cost' else 5)
        if outcome in {'truncated','invalid'}:assert not any(r['serverAccepted'] for r in result)


def test_unverified_billing_zero_dispatch(tmp_path):
    options=setup(tmp_path);options['contracts'][CANDIDATES[3]]['accountPricingVerified']=False
    async def fake(*args):pytest.fail('No dispatch')
    with pytest.raises(ValueError,match='UNVERIFIED'):asyncio.run(compare(**options,transport=fake))
    assert options['budget'].snapshot()['requests']==0

import asyncio
import json
from types import SimpleNamespace
import pytest
from app.experimental.bim_model_evaluation import CANDIDATES, REQUESTS, request_body, validate_screening, mock_screen_once
from app.experimental.bim_authoring_fixtures import authoring_case
from app.experimental.bim_authoring import stage_packet
from app.experimental.cad_contract import digest


def packet(scenario='platform'):
    payload=stage_packet('UNDERSTAND',request_text=REQUESTS[scenario])
    return dict(system=payload.pop('instruction'),payload=payload)


def response():
    return dict(choices=[dict(finish_reason='stop',message=dict(content=authoring_case('platform').intent.model_dump_json(by_alias=True)))])


def context():return SimpleNamespace(selection_kind='AREA',selection_version_id='selection',object_ids=())


@pytest.mark.parametrize('model',CANDIDATES)
@pytest.mark.parametrize('scenario',REQUESTS)
def test_equivalent_limits_and_packet(model,scenario):
    prepared=packet(scenario)
    body,reservation=request_body(prepared,model,CANDIDATES)
    assert body['max_tokens']==3500 and reservation<=8192
    assert body['response_format']=={'type':'json_object'}
    assert body['messages']==request_body(prepared,CANDIDATES[0],CANDIDATES)[0]['messages']


def test_catalog_required():
    with pytest.raises(ValueError,match='CATALOG_ELIGIBLE'):request_body(packet(),CANDIDATES[0],[])


def test_strict_and_semantic_validation():
    assert validate_screening(response(),context())['serverAccepted']
    value=response();value['choices'][0]['finish_reason']='length'
    assert not validate_screening(value,context())['serverAccepted']
    value=response();output=json.loads(value['choices'][0]['message']['content']);output['requestedObjectRefs']=['invented']
    value['choices'][0]['message']['content']=json.dumps(output)
    with pytest.raises(ValueError):validate_screening(value,context())


def test_one_mock_dispatch_no_replay(tmp_path):
    calls=[]
    async def fake(body,timeout):calls.append(body['model']);assert timeout==45;return response()
    p=packet()
    options=dict(scenario='platform',model=CANDIDATES[0],packet=p,expected_hash=digest(p),catalog=CANDIDATES,context=context(),fake_transport=fake)
    result=asyncio.run(mock_screen_once(tmp_path,**options))
    assert result['serverAccepted'] and len(calls)==1
    with pytest.raises(FileExistsError):asyncio.run(mock_screen_once(tmp_path,**options))
    assert len(calls)==1


def test_uncertain_stops_matrix(tmp_path):
    calls=[]
    async def fake(*args):calls.append(1);raise TimeoutError()
    p=packet()
    options=dict(scenario='platform',model=CANDIDATES[0],packet=p,expected_hash=digest(p),catalog=CANDIDATES,context=context(),fake_transport=fake)
    with pytest.raises(TimeoutError):asyncio.run(mock_screen_once(tmp_path,**options))
    options['model']=CANDIDATES[1]
    with pytest.raises(ValueError,match='STOPPED'):asyncio.run(mock_screen_once(tmp_path,**options))
    assert len(calls)==1


def test_stale_packet_no_dispatch(tmp_path):
    async def fake(*args):pytest.fail('must not dispatch')
    with pytest.raises(ValueError,match='STALE'):
        asyncio.run(mock_screen_once(tmp_path,scenario='platform',model=CANDIDATES[0],packet=packet(),expected_hash='wrong',catalog=CANDIDATES,context=context(),fake_transport=fake))

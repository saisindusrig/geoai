import asyncio
import pytest
from app.core.config import settings
from app.services.ai.provider import AssistantProviderError,ModelRouter,RoutingMetadata
from app.domain.assistant_runtime import ProviderResponse
from app.services.assistant.decomposition_compatibility import compatibility
from app.services.assistant.tool_boundary import parse_arguments,validate_calls
from app.services.assistant.preview_parameters import preview_parameters
from app.services.assistant import runtime
from app.services.assistant.policy import evaluate
from app.services.assistant.storage import rows,owned_row
from test_assistant_runtime import message,FixtureProvider
from test_site_workspace import site_db

def system(id,type,role):return {'id':id,'assetType':type,'role':role,'semanticType':role}
def classified(*types):return [{'assetType':type} for type in types]

def test_asset_component_decomposition():
    design={'systems':[system(str(i),'PEDESTRIAN_BRIDGE',role) for i,role in enumerate(['PATH','DECK','PIERS','ABUTMENTS'])]}
    assert compatibility(classified('PEDESTRIAN_BRIDGE','BRIDGE_ALIGNMENT','BRIDGE_DECK','BRIDGE_SUPPORT'),design)['status']=='DECOMPOSITION_COMPATIBLE'

def test_multi_asset_decomposition():
    design={'systems':[system('w','WAREHOUSE','WAREHOUSE'),system('c','COLUMN','COLUMNS'),system('p','PARKING_ZONE','PAD'),system('r','ACCESS_PATH','PATH')]}
    assert not compatibility(classified('WAREHOUSE','PARKING','ACCESS_ROAD'),design)['issues']

def test_relationship_resolves_ambiguous_support_parent():
    design={'systems':[system('w','WAREHOUSE','WAREHOUSE'),system('b','PEDESTRIAN_BRIDGE','PEDESTRIAN_BRIDGE'),system('c','COLUMN','COLUMN')],
        'relationships':[{'kind':'CONTAINS','fromId':'w','toId':'c'}]}
    assert compatibility(classified('WAREHOUSE','PEDESTRIAN_BRIDGE'),design)['systemAssignments']['c']=='WAREHOUSE'
    design['relationships']=[]
    assert compatibility(classified('WAREHOUSE','PEDESTRIAN_BRIDGE'),design)['status']=='UNEXPECTED_SYSTEM'

@pytest.mark.parametrize('injected',['DAM','AIRPORT','PIPELINE'])
def test_unrelated_system_rejected(injected):
    assert compatibility(classified('WAREHOUSE'),{'systems':[system('w','WAREHOUSE','WAREHOUSE'),system('x',injected,injected)]})['status']=='UNEXPECTED_SYSTEM'

def test_explicit_request_grounding_and_negation():
    design={'systems':[system('w','WAREHOUSE','WAREHOUSE'),system('p','PIPELINE','PIPELINE')]}
    assert not compatibility(classified('WAREHOUSE'),design,'Create a warehouse and pipeline.')['issues']
    assert compatibility(classified('WAREHOUSE'),design,'Create a warehouse without a pipeline.')['status']=='UNEXPECTED_SYSTEM'

def test_required_system_missing():
    assert compatibility(classified('WAREHOUSE','PARKING'),{'systems':[system('w','WAREHOUSE','WAREHOUSE')]})['status']=='MISSING_REQUIRED_SYSTEM'
    assert compatibility(classified('PEDESTRIAN_BRIDGE','BRIDGE_DECK'),{'systems':[system('b','PEDESTRIAN_BRIDGE','PATH')]})['status']=='MISSING_REQUIRED_SYSTEM'

@pytest.mark.parametrize('count',[1,2,3])
def test_quantity_preservation(count):
    design={'systems':[system(str(i),'WAREHOUSE','WAREHOUSE') for i in range(count)]+[system('columns','WAREHOUSE','COLUMNS')]}
    assert compatibility(classified('WAREHOUSE'),design,'Create two warehouses.')['status']==('DECOMPOSITION_COMPATIBLE' if count==2 else 'QUANTITY_MISMATCH')

class Provider:
    def __init__(self,reply):self.reply=reply;self.calls=[]
    async def complete(self,system,payload,route):self.calls.append((payload,route));return self.reply

@pytest.mark.parametrize('raw,code',[('{','TOOL_ARGUMENT_JSON_INVALID'),('{"unexpected":1}','TOOL_ARGUMENT_SCHEMA_INVALID')])
def test_nested_failure_and_single_repair(raw,code):
    with pytest.raises(AssistantProviderError) as exc:parse_arguments('get_site_profile',raw)
    assert exc.value.code==code
    provider=Provider({});diagnostics=[]
    response=ProviderResponse.model_validate({'toolCalls':[{'name':'get_site_profile','arguments':raw}]})
    result=asyncio.run(validate_calls(response,['get_site_profile'],provider,{'frozenContext':{'modelRevisionId':'1'}},RoutingMetadata(intent='DESIGN_REQUEST'),diagnostics))
    assert result[0][1]=={} and len(provider.calls)==1
    assert diagnostics[-1]['event']=='TOOL_ARGUMENT_REPAIR_SUCCESS'
    assert provider.calls[0][1].tier=='PRIMARY'
    assert provider.calls[0][0]['invalidArguments']==raw

def test_repair_failure_is_bounded():
    provider=Provider({'stillInvalid':True});diagnostics=[]
    response=ProviderResponse.model_validate({'toolCalls':[{'name':'get_site_profile','arguments':'{'}]})
    with pytest.raises(AssistantProviderError,match='TOOL_ARGUMENT_REPAIR_FAILED'):
        asyncio.run(validate_calls(response,['get_site_profile'],provider,{},RoutingMetadata(intent='DESIGN_REQUEST'),diagnostics))
    assert len(provider.calls)==1 and diagnostics[-1]['event']=='TOOL_ARGUMENT_REPAIR_FAILED'

def test_valid_arguments_need_no_repair():
    provider=Provider({})
    response=ProviderResponse.model_validate({'toolCalls':[{'name':'get_site_profile','arguments':'{}'}]})
    asyncio.run(validate_calls(response,['get_site_profile'],provider,{},RoutingMetadata(intent='DESIGN_REQUEST'),[]))
    assert not provider.calls

def test_disallowed_tool_never_repaired_or_dispatched():
    provider=Provider({})
    response=ProviderResponse.model_validate({'toolCalls':[{'name':'create_proposal','arguments':'{'}]})
    with pytest.raises(AssistantProviderError,match='TOOL_POLICY_DENIED'):
        asyncio.run(validate_calls(response,['get_site_profile'],provider,{},RoutingMetadata(intent='DESIGN_REQUEST'),[]))
    assert not provider.calls

def test_repaired_call_reaches_normal_dispatch(site_db):
    msg,rid=message(site_db,"What's the slope here?");runtime.queue_run(site_db,1,1,rid)
    response={'toolCalls':[{'name':'get_site_profile','arguments':'{'}]}
    asyncio.run(runtime.process(site_db,1,rid,FixtureProvider([evaluate(msg)['intent'],response,{}, {'text':'Survey elevation and soil remain unknown.'}])))
    run=owned_row(site_db,'assistant_runs',1,rid)
    assert run['status']=='COMPLETE'
    assert any(event['event']=='TOOL_ARGUMENT_REPAIR_SUCCESS' for event in run['context_snapshot']['modelRoutingDiagnostics'])
    assert len(rows(site_db,'assistant_tool_executions',1))==1

def test_no_dispatch_before_all_arguments_valid(site_db):
    msg,rid=message(site_db);runtime.queue_run(site_db,1,1,rid)
    response={'toolCalls':[{'name':'get_site_profile','arguments':'{}'},{'name':'create_proposal','arguments':'{'}]}
    asyncio.run(runtime.process(site_db,1,rid,FixtureProvider([evaluate(msg)['intent'],response,{'invalid':True}])))
    assert owned_row(site_db,'assistant_runs',1,rid)['error_code']=='TOOL_ARGUMENT_REPAIR_FAILED'
    assert not rows(site_db,'assistant_tool_executions',1)

def test_overall_timeout_remains_bounded(site_db,monkeypatch):
    msg,rid=message(site_db);runtime.queue_run(site_db,1,1,rid)
    monkeypatch.setattr(runtime,'FLOW_TIMEOUT_SECONDS',.01)
    calls=[]
    async def slow(system,payload):calls.append(payload);await asyncio.sleep(.1)
    asyncio.run(runtime.process(site_db,1,rid,slow))
    assert owned_row(site_db,'assistant_runs',1,rid)['error_code']=='TIMEOUT'
    assert len(calls)==1

def test_primary_timeout_configuration(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS',45)
    assert ModelRouter().route(RoutingMetadata(intent='DESIGN_REQUEST')).timeout==45>25
    monkeypatch.setattr(settings,'NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS',60)
    assert ModelRouter().route(RoutingMetadata(intent='DESIGN_REQUEST')).timeout==60
    monkeypatch.setattr(settings,'NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS',0)
    with pytest.raises(ValueError):ModelRouter().route(RoutingMetadata(intent='DESIGN_REQUEST'))

def test_preview_parameters_never_promote_site_coordinates():
    design={'inputSource':'PREVIEW_ASSUMPTION','objects':[{'objectId':'pier','parameters':{'radiusM':.4,'start':[77,12,0],'end':[77,12,2.5]}},{'objectId':'abutment','parameters':{'size':[2,4,2]}}]}
    derived=preview_parameters(design)
    assert all(row['source']=='PREVIEW_ASSUMPTION' for row in derived)
    assert any(row['parameter']=='radiusM' for row in derived)
    assert any(row['parameter']=='size' for row in derived)
    assert not any(row['value'] in [77,12] for row in derived if not isinstance(row['value'],list))
    assert not preview_parameters({**design,'inputSource':'USER_PROVIDED'})

import asyncio
import json
from pathlib import Path
import pytest
from app.core.config import settings,Settings
from app.services.ai.provider import RoutingMetadata,ModelRouter,AssistantProviderError,request_routing_hints
from app.services.assistant.runtime import structured
from app.domain.assistant_runtime import ProviderResponse
from evals.run_geoai import load


@pytest.fixture
def aliases(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_PRIMARY_MODEL','replaceable-primary')
    monkeypatch.setattr(settings,'NEBIUS_FAST_MODEL','replaceable-fast')


@pytest.mark.parametrize('metadata,tier',[
    ({'intent':'QUESTION'},'FAST'),({'intent':'EXPLANATION_REQUEST'},'FAST'),
    ({'intent':'QUESTION','tool_requirement':True,'tool_count':1},'FAST'),
    ({'intent':'DESIGN_REQUEST'},'PRIMARY'),({'intent':'CHANGE_REQUEST'},'PRIMARY'),
    ({'intent':'QUESTION','requested_effect':'PROPOSAL_ONLY'},'PRIMARY'),
    ({'intent':'ANALYSIS_REQUEST'},'PRIMARY'),({'intent':'QUESTION','engineering_sensitive':True},'PRIMARY'),
    ({'intent':'QUESTION','asset_count':2},'PRIMARY'),({'intent':'CLASSIFY'},'PRIMARY'),
    ({'intent':'QUESTION','uncertain':True},'PRIMARY'),({'intent':'QUESTION','tool_requirement':True},'PRIMARY'),
    ({'intent':'QUESTION','tool_requirement':True,'tool_count':2},'PRIMARY'),
    ({'intent':'QUESTION','asset_families':['CUSTOM']},'PRIMARY'),
    ({'intent':'PROPOSAL_APPROVAL','requested_effect':'APPROVAL_UI_REQUIRED'},'PRIMARY')])
def test_conservative_routes(aliases,metadata,tier):
    route=ModelRouter().route(RoutingMetadata(**metadata))
    assert route.tier==tier
    assert route.model==('replaceable-fast' if tier=='FAST' else 'replaceable-primary')


def test_unset_fast_uses_primary_not_legacy_chat(aliases,monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_FAST_MODEL','')
    route=ModelRouter().route(RoutingMetadata(intent='QUESTION'))
    assert route.model=='replaceable-primary' and route.tier=='PRIMARY'


def test_provisional_primary_config_and_configurable_alias(tmp_path):
    from dotenv import dotenv_values
    repo=Path(__file__).parents[2]
    assert dotenv_values(repo/'.env.example')['NEBIUS_PRIMARY_MODEL']=='Qwen/Qwen3.5-397B-A17B'
    path=tmp_path/'env';path.write_text('NEBIUS_PRIMARY_MODEL=other-provider-model\nNEBIUS_FAST_MODEL=other-fast-model\n')
    config=Settings(_env_file=path)
    assert config.NEBIUS_PRIMARY_MODEL=='other-provider-model' and config.NEBIUS_FAST_MODEL=='other-fast-model'


@pytest.mark.parametrize('failure',['TIMEOUT','INVALID_RESPONSE','SCHEMA'])
def test_fast_failure_escalates_once(aliases,failure):
    routes=[];diagnostics=[]
    class Fake:
        async def complete(self,system,payload,route):
            routes.append(route)
            if len(routes)==1:
                if failure=='SCHEMA':return {'text':123}
                raise AssistantProviderError(failure)
            return {'text':'Read-only answer'}
    result=asyncio.run(structured(Fake(),ProviderResponse,{},metadata=RoutingMetadata(intent='QUESTION'),diagnostics=diagnostics))
    assert result.text and [r.tier for r in routes]==['FAST','PRIMARY']
    assert diagnostics[0]['event']=='MODEL_ESCALATION'
    assert diagnostics[0]['toModel']=='replaceable-primary'


def test_primary_error_never_downgrades(aliases):
    routes=[]
    class Fake:
        async def complete(self,system,payload,route):
            routes.append(route);raise AssistantProviderError('TIMEOUT')
    with pytest.raises(AssistantProviderError):
        asyncio.run(structured(Fake(),ProviderResponse,{},metadata=RoutingMetadata(intent='DESIGN_REQUEST')))
    assert len(routes)==1 and routes[0].tier=='PRIMARY'


def test_no_infinite_escalation(aliases):
    routes=[]
    class Fake:
        async def complete(self,system,payload,route):
            routes.append(route);return {'text':123}
    with pytest.raises(AssistantProviderError):asyncio.run(structured(Fake(),ProviderResponse,{},metadata=RoutingMetadata(intent='QUESTION')))
    assert [r.tier for r in routes]==['FAST','PRIMARY']


def test_request_guards():
    assert request_routing_hints('Is this structure safe?')['engineering_sensitive']
    assert request_routing_hints('Can GeoAI generate this unsupported asset?')['uncertain']
    assert request_routing_hints('What objects do I currently have selected?')['tool_count']==1
    assert request_routing_hints('What objects do I have selected and what is their soil capacity?')['tool_count'] is None


def test_exact_fast_cases_and_frozen_contract():
    root=Path(__file__).parents[1]
    config,cases=load(cases_path=root/'evals/geoai_fast_cases.json')
    assert [c.id for c in cases]==['fast_explanation_001','fast_asset_intent_001','fast_selection_001']
    assert config.max_output_tokens==3500 and config.repairs==1
    assert cases[2].expected.required_tools==['get_selected_objects']
    assert cases[2].context['selected_objects']==['P03','P04','P05']
    assert cases[1].expected.assets==['BRIDGE']


def test_runtime_uses_provider_seam_not_model_ids():
    root=Path(__file__).parents[1]
    text=(root/'app/services/assistant/runtime.py').read_text()
    assert 'Qwen/' not in text and 'assistant_json(' not in text
    assert 'provider.complete(' in text

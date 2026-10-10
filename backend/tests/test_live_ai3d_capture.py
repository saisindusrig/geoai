import asyncio
import json
import pytest
from app.services.ai.provider import NebiusProvider, AssistantProviderError, ModelRoute
from app.domain.assistant_runtime import ProviderResponse
from scripts.live_ai3d_acceptance import CapturedProvider, MODEL, safe


def test_capture_checkpoints_valid_visible_response(tmp_path, monkeypatch):
    async def complete(self, system, payload, route):
        assert json.loads(path.read_text())["completions"][0]["status"]=="STARTED"
        self.usage_sink.update(prompt_tokens=100,completion_tokens=20)
        self.metadata_sink.append({"finish_reason":"stop","output_tokens":20})
        return {"text":"Review this conceptual plan."}
    monkeypatch.setattr(NebiusProvider,"complete",complete)
    path=tmp_path/"case.json"; result={"completions":[]}
    provider=CapturedProvider(result,path)
    asyncio.run(provider.complete("system",{"schema":ProviderResponse.model_json_schema(by_alias=True)},ModelRoute("nebius",MODEL,"PRIMARY",True,3500,25)))
    entry=json.loads(path.read_text())["completions"][0]
    assert entry["structuredValid"] is True
    assert entry["inputTokens"]==100 and entry["outputTokens"]==20
    assert entry['phase']=='ASSISTANT_RESPONSE'
    assert entry['ordinaryRepair'] is False and entry['nestedRepair'] is False
    assert entry['timeoutSeconds']==25 and entry['finishReason']=='stop'


def test_provider_failure_usage_is_unknown(tmp_path,monkeypatch):
    async def complete(self,*args):
        self.metadata_sink.append({"http_status":401,"provider_status":"PROVIDER_ERROR"})
        raise AssistantProviderError("PROVIDER_ERROR",{"httpStatus":401})
    monkeypatch.setattr(NebiusProvider,"complete",complete)
    result={"completions":[]};provider=CapturedProvider(result,tmp_path/"case.json")
    with pytest.raises(AssistantProviderError):
        asyncio.run(provider.complete("system",{"schema":{"title":"CivilIntent"}},ModelRoute("nebius",MODEL,"PRIMARY",True,3500,25)))
    entry=result["completions"][0]
    assert entry["inputTokens"] is None and entry["outputTokens"] is None
    assert entry["providerDiagnostics"]["httpStatus"]==401


def test_capture_refuses_other_models_and_over_budget(tmp_path):
    provider=CapturedProvider({"completions":[]},tmp_path/"case.json")
    with pytest.raises(RuntimeError,match="MODEL_GUARD"):
        asyncio.run(provider.complete("",{},ModelRoute("nebius","other","PRIMARY",True,3500,25)))
    provider.result["completions"]=[{}]*36
    with pytest.raises(RuntimeError,match="REQUEST_BUDGET"):
        asyncio.run(provider.complete("",{},ModelRoute("nebius",MODEL,"PRIMARY",True,3500,25)))


def test_capture_excludes_hidden_reasoning_and_secrets(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,"NEBIUS_API_KEY","example-private-test-key")
    assert safe({"reasoning_content":"private","text":"example-private-test-key","nested":{"chain_of_thought":"private"}})=={"text":"[REDACTED]","nested":{}}


def test_capture_nested_repair_records_truncation(tmp_path,monkeypatch):
    async def complete(self,*args):
        self.usage_sink.update(prompt_tokens=100,completion_tokens=3500)
        self.metadata_sink.append({'http_status':200,'finish_reason':'length','max_output_tokens_reached':True})
        raise AssistantProviderError('INVALID_RESPONSE')
    monkeypatch.setattr(NebiusProvider,'complete',complete)
    result={'completions':[]};provider=CapturedProvider(result,tmp_path/'case.json')
    with pytest.raises(AssistantProviderError):
        asyncio.run(provider.complete('',{'schema':{'title':'ProposalToolArguments'},'toolArgumentRepair':True},ModelRoute('nebius',MODEL,'PRIMARY',True,3500,45)))
    entry=result['completions'][0]
    assert entry['phase']=='NESTED_ARGUMENT_REPAIR' and entry['nestedRepair'] and not entry['ordinaryRepair']
    assert entry['httpStatus']==200 and entry['finishReason']=='length' and entry['outputLimitReached']
    assert entry['repairOutcome']=='FAILED' and entry['outputTokens']==3500 and not entry['timeout']

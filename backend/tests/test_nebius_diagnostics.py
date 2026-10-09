import asyncio
import json
import httpx
import pytest
from app.core.config import settings
from app.services.ai.nebius import assistant_json, AssistantProviderError


def transport(monkeypatch, handler):
    monkeypatch.setattr(settings,"NEBIUS_API_KEY","secret-fixture-key")
    monkeypatch.setattr(settings,"NEBIUS_CHAT_MODEL","fixture/model")
    monkeypatch.setattr(settings,"NEBIUS_BASE_URL","https://fixture.test/v1/")
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))


@pytest.mark.parametrize("status,code",[(400,"PROVIDER_ERROR"),(401,"PROVIDER_ERROR"),(404,"PROVIDER_ERROR"),(429,"RATE_LIMITED"),(503,"UNAVAILABLE")])
def test_sanitized_http_diagnostics(monkeypatch,status,code):
    transport(monkeypatch,lambda req:httpx.Response(status,json={"error":{"code":"model_error","message":"secret-fixture-key Bearer opaque-secret rejected"}}))
    with pytest.raises(AssistantProviderError) as error:asyncio.run(assistant_json("fixture",{}))
    assert error.value.code==code
    data=error.value.diagnostics
    assert data["httpStatus"]==status and data["configuredModel"]=="fixture/model"
    assert data["baseHost"]=="fixture.test" and data["basePath"]=="/v1"
    assert data["providerErrorCode"]=="model_error"
    assert "secret-fixture-key" not in json.dumps(data) and "opaque-secret" not in json.dumps(data)


@pytest.mark.parametrize("exception,code,category",[(httpx.ConnectTimeout,"TIMEOUT","ConnectTimeout"),(httpx.ReadTimeout,"TIMEOUT","ReadTimeout"),(httpx.ConnectError,"UNAVAILABLE",None)])
def test_transport_failure_categories(monkeypatch,exception,code,category):
    def handler(req):raise exception("must not expose this",request=req)
    transport(monkeypatch,handler)
    with pytest.raises(AssistantProviderError) as error:asyncio.run(assistant_json("fixture",{}))
    assert error.value.code==code and error.value.diagnostics["timeoutCategory"]==category
    assert "must not expose" not in json.dumps(error.value.diagnostics)


def test_payload_endpoint_model_override_and_json(monkeypatch):
    def handler(req):
        assert str(req.url)=="https://fixture.test/v1/chat/completions"
        assert req.headers["authorization"]=="Bearer secret-fixture-key"
        body=json.loads(req.content)
        assert body["model"]=="fast/model" and body["max_tokens"]==2000
        assert body["response_format"]=={"type":"json_object"}
        return httpx.Response(200,json={"choices":[{"message":{"content":'{"ok":true}'}}]})
    transport(monkeypatch,handler)
    assert asyncio.run(assistant_json("fixture",{},model="fast/model",max_output_tokens=2000))=={"ok":True}


def test_token_factory_url_used_only_when_override_empty(monkeypatch):
    transport(monkeypatch,lambda req:httpx.Response(200,json={"choices":[]}))
    monkeypatch.setattr(settings,"NEBIUS_BASE_URL","")
    monkeypatch.setattr(settings,"NEBIUS_TOKEN_FACTORY_BASE_URL","https://fallback.test/v1")
    with pytest.raises(AssistantProviderError) as error:asyncio.run(assistant_json("fixture",{}))
    assert error.value.code=="INVALID_RESPONSE" and error.value.diagnostics["baseHost"]=="fallback.test"

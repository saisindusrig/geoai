"""Server-only Token Factory client; never silently substitutes a mock response."""
import json
import re
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.services.ai.nebius_config import resolve


class NebiusError(ValueError):
    pass


async def completion(system: str, user: str, *, json_mode: bool = True) -> str:
    try:
        # Preserve the legacy building planner's 90-second budget through the same resolver.
        config = resolve(timeout=90)
        if not config.api_key or not config.model:
            raise NebiusError("Configure NEBIUS_API_KEY and NEBIUS_CHAT_MODEL on the backend.")
        body = await _request("POST", "chat/completions", model=config.model, timeout=config.timeout,
            payload={"model":config.model,"messages":[{"role":"system","content":system},{"role":"user","content":user}],
                "temperature":0.2,"max_tokens":12000,**({"response_format":{"type":"json_object"}} if json_mode else {})})
        choice=body["choices"][0]
        if choice.get("finish_reason")=="length":
            raise NebiusError("The AI plan exceeded the response limit. Request a smaller building or fewer rooms.")
        content=choice["message"]["content"]
        if not isinstance(content,str) or not content.strip():raise NebiusError("Nebius returned an empty response. Please retry.")
        return content
    except AssistantProviderError as exc:
        if exc.code=="TIMEOUT":raise NebiusError("Nebius timed out. Your model is unchanged; please retry.") from exc
        raise NebiusError("Nebius request failed: "+exc.code+". Check server configuration.") from exc
    except (ValueError,KeyError,IndexError,TypeError) as exc:
        if isinstance(exc,NebiusError):raise
        raise NebiusError("Nebius returned invalid data or configuration. Please retry.") from exc


async def generate_json(system: str, user: str) -> dict:
    try:
        value = json.loads(await completion(system, user))
        if not isinstance(value, dict):
            raise NebiusError("Nebius returned invalid JSON. A building object is required.")
        return value
    except (json.JSONDecodeError, TypeError) as exc:
        raise NebiusError("Nebius returned invalid JSON. Please revise the request and retry.") from exc


from app.services.ai.provider import AssistantProviderError

LAST_ASSISTANT_RESULT = None


def sanitized(value):
    text = str(value or "")
    for name, secret in settings.model_dump().items():
        if any(s in name for s in ("KEY", "TOKEN", "SECRET", "DATABASE_URL", "REDIS_URL")) and isinstance(secret,str) and len(secret)>=6:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", text)
    text = re.sub(r"\b(?:v1\.[A-Za-z0-9_.-]{20,}|sk-[A-Za-z0-9_-]{8,})", "[REDACTED]", text)
    text = re.sub(r"https?://[^\s/@]+:[^\s/@]+@", "https://[REDACTED]@", text)
    return " ".join(text.split())[:300]


def assistant_diagnostics(model=None):
    try:
        config=resolve(model=model)
        base=urlsplit(config.base_url)
        configured_model=config.model
    except ValueError:
        base=urlsplit("");configured_model=""
    return {"configuredModel":sanitized(configured_model),"baseHost":base.hostname,
        "basePath":base.path,"httpStatus":None,"providerErrorCode":None,"providerErrorMessage":None,"timeoutCategory":None}


def fail(code, diagnostics):
    global LAST_ASSISTANT_RESULT
    LAST_ASSISTANT_RESULT = {"status":code,"diagnostics":diagnostics}
    raise AssistantProviderError(code, diagnostics)


def assistant_configuration(model=None):
    try:
        config=resolve(model=model)
        return "CONFIGURED" if config.api_key and config.model else "MISSING_CONFIGURATION"
    except ValueError:
        return "MISSING_CONFIGURATION"


async def _request(method, endpoint, *, model=None, timeout=None, payload=None, limit=100000):
    diagnostics=assistant_diagnostics(model)
    try:
        config=resolve(model=model,timeout=timeout)
        if not config.api_key or endpoint!='models' and not config.model:
            fail("MISSING_CONFIGURATION",diagnostics)
    except ValueError as exc:
        if isinstance(exc,AssistantProviderError):raise
        fail("MISSING_CONFIGURATION",diagnostics)
    try:
        async with httpx.AsyncClient(timeout=config.timeout,follow_redirects=False) as client:
            async with client.stream(method,config.url(endpoint),headers=config.headers(),**({"json":payload} if payload is not None else {})) as response:
                diagnostics["httpStatus"]=response.status_code
                data=bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data)>limit:fail("INVALID_RESPONSE",diagnostics)
                if response.status_code>=300:
                    try:
                        body=json.loads(data);detail=body.get("error",body.get("detail",body))
                        if isinstance(detail,dict):
                            diagnostics["providerErrorCode"]=sanitized(detail.get("code") or detail.get("type"))
                            diagnostics["providerErrorMessage"]=sanitized(detail.get("message"))
                        elif isinstance(detail,str):diagnostics["providerErrorMessage"]=sanitized(detail)
                    except (ValueError,TypeError,AttributeError):pass
                    fail("RATE_LIMITED" if response.status_code==429 else "UNAVAILABLE" if response.status_code>=500 else "PROVIDER_ERROR",diagnostics)
                body=json.loads(data)
                if not isinstance(body,dict):fail("INVALID_RESPONSE",diagnostics)
                return body
    except httpx.TimeoutException as exc:
        diagnostics["timeoutCategory"]=type(exc).__name__;fail("TIMEOUT",diagnostics)
    except httpx.RequestError:fail("UNAVAILABLE",diagnostics)
    except (ValueError,TypeError) as exc:
        if isinstance(exc,AssistantProviderError):raise
        fail("INVALID_RESPONSE",diagnostics)


async def assistant_json(system: str, payload: dict, *, model=None, max_output_tokens=3500, timeout=None, usage_sink=None, metadata_sink=None) -> dict:
    try:
        config=resolve(model=model,timeout=timeout) if assistant_configuration(model)=="CONFIGURED" else None
    except ValueError:
        fail("MISSING_CONFIGURATION",assistant_diagnostics(model))
    if config is None:fail("MISSING_CONFIGURATION",assistant_diagnostics(model))
    body=await _request("POST","chat/completions",model=config.model,timeout=config.timeout,
        payload={"model":config.model,"messages":[{"role":"system","content":system},{"role":"user","content":json.dumps(payload,separators=(",",":"),default=str)}],
            "temperature":0.1,"max_tokens":max_output_tokens,"response_format":{"type":"json_object"}})
    diagnostics=assistant_diagnostics(model);diagnostics["httpStatus"]=200
    from .response_metadata import response_metadata
    metadata = response_metadata(body, max_output_tokens)
    metadata["http_status"] = 200
    metadata["provider_status"] = "OK"
    if metadata_sink is not None:
        metadata_sink.append(metadata)
    diagnostics["responseMetadata"] = metadata
    try:
        if usage_sink is not None:
            usage=body.get("usage") or {}
            for key in ("prompt_tokens","completion_tokens"):
                value=usage.get(key)
                usage_sink[key]=usage_sink.get(key,0)+value if isinstance(value,int) and usage_sink.get(key,0) is not None else None
        choice=body["choices"][0]
        if metadata["failure_class"]:fail("INVALID_RESPONSE",diagnostics)
        result=json.loads(choice["message"]["content"])
        if not isinstance(result,dict):fail("INVALID_RESPONSE",diagnostics)
        global LAST_ASSISTANT_RESULT
        LAST_ASSISTANT_RESULT={"status":"AVAILABLE","diagnostics":diagnostics}
        return result
    except (ValueError,KeyError,IndexError,TypeError,AttributeError) as exc:
        if isinstance(exc,AssistantProviderError):raise
        fail("INVALID_RESPONSE",diagnostics)


def parse_model_catalogue(body):
    if not isinstance(body,dict) or not isinstance(body.get("data"),list):
        raise AssistantProviderError("INVALID_MODEL_CATALOGUE")
    if any(not isinstance(item,dict) or not isinstance(item.get("id"),str) or not item["id"].strip() for item in body["data"]):
        raise AssistantProviderError("INVALID_MODEL_CATALOGUE")
    return sorted({item["id"] for item in body["data"]})


async def available_assistant_models():
    return parse_model_catalogue(await _request("GET","models",limit=1000000))

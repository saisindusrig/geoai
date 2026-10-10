"""Offline contract proposals: these tests do not certify hosted capabilities."""
import json
import pytest
from app.experimental.bim_inference_profiles import proposed_request, audit_schema, safe_diagnostics
from app.experimental.canary_execution import MODEL
from app.experimental.bim_authoring_fixtures import authoring_case
from app.domain.bim_authoring import AuthoringIntent


def body():
    return dict(model=MODEL, max_tokens=3500, temperature=.1, messages=[], response_format={"type":"json_object"})


def response(content=None, finish="stop", usage=None):
    return {"choices":[{"finish_reason":finish,"message":{"content":content or authoring_case("platform").intent.model_dump_json(by_alias=True), "reasoning_content":"PRIVATE_NOT_RETAINED"}}],"usage":usage or {}}


@pytest.mark.parametrize("deployment,key",[("qwen-self-hosted","chat_template_kwargs"),("alibaba-model-studio","enable_thinking")])
def test_documented_deployment_serialization(deployment,key):
    original=body()
    result,timeout=proposed_request(original,stage="UNDERSTAND",deployment=deployment,enabled=True,nonthinking=True)
    assert result[key] == ({"enable_thinking":False} if key=="chat_template_kwargs" else False)
    assert timeout==45 and result["max_tokens"]==3500 and result["model"]==MODEL
    assert key not in original


@pytest.mark.parametrize("options",[{"nonthinking":True},{"schema_mode":True}])
def test_nebius_support_not_faked(options):
    with pytest.raises(ValueError,match="UNVERIFIED"):
        proposed_request(body(),stage="UNDERSTAND",deployment="nebius",enabled=True,**options)


def test_default_off_and_client_options_rejected():
    assert proposed_request(body(),stage="UNDERSTAND",deployment="nebius")== (body(),45)
    with pytest.raises(ValueError,match="DISABLED"):
        proposed_request(body(),stage="UNDERSTAND",deployment="nebius",nonthinking=True)
    with pytest.raises(ValueError,match="SELECTION_REJECTED"):
        proposed_request(body(),stage="UNDERSTAND",deployment="nebius",client_options={"reasoning_effort":"none"})


@pytest.mark.parametrize("key",["reasoning_effort","thinking_budget","enable_thinking","chat_template_kwargs"])
def test_unreviewed_body_fields_rejected(key):
    value=body()
    value[key]=0
    with pytest.raises(ValueError,match="FIELDS_REJECTED"):
        proposed_request(value,stage="UNDERSTAND",deployment="nebius")


@pytest.mark.parametrize("stage",["PLAN","EXPAND","RELATE"])
def test_no_implicit_stage_mode(stage):
    with pytest.raises(ValueError,match="STAGE_UNSUPPORTED"):
        proposed_request(body(),stage=stage,deployment="qwen-self-hosted",enabled=True,nonthinking=True)


def test_schema_proposal_preserves_required_and_references():
    result,_=proposed_request(body(),stage="UNDERSTAND",deployment="qwen-self-hosted",enabled=True,schema_mode=True)
    schema=result["response_format"]["json_schema"]["schema"]
    assert schema==AuthoringIntent.model_json_schema()
    assert schema["required"]==["requestedStructure","systems"]
    assert schema["properties"]["systems"]["items"]["$ref"]=="#/$defs/SystemRequest"
    assert audit_schema(schema)==schema
    schema["required"].append("missing")
    with pytest.raises(ValueError,match="REQUIRED_MISMATCH"):audit_schema(schema)


def test_nonthinking_mock_valid_and_metadata_missing():
    result=safe_diagnostics(response(),latency=.2)
    assert result["strict_schema_valid"] and result["reasoning_tokens"] is None
    assert result["provider_reported_cost"] is None
    assert "PRIVATE_NOT_RETAINED" not in json.dumps(result)


def test_thinking_mock_truncation():
    result=safe_diagnostics(response('{"schemaVersion":',"length",{"prompt_tokens":2095,"completion_tokens":3500,"completion_tokens_details":{"reasoning_tokens":3000}}))
    assert result["failure_class"]=="LIKELY_TRUNCATED" and not result["strict_schema_valid"]
    assert result["completion_reasoning_tokens"]==3000


def test_refusal_and_strict_schema():
    value=response()
    value["choices"][0]["message"]["refusal"]="PRIVATE_REFUSAL"
    result=safe_diagnostics(value)
    assert result["failure_class"]=="PROVIDER_REFUSAL" and not result["strict_schema_valid"]
    assert "PRIVATE_REFUSAL" not in json.dumps(result)
    result=safe_diagnostics(response('{"unexpected_private_key":1}'))
    assert result["failure_class"]=="SCHEMA_VALIDATION_FAILED"
    assert "unexpected_private_key" not in json.dumps(result)


@pytest.mark.parametrize("value",[True,-1,float("nan"),"3"])
def test_invalid_numeric_metadata_unavailable(value):
    result=safe_diagnostics(response(usage={"reasoning_tokens":value}),latency=value,provider_cost=value)
    assert result["reasoning_tokens"] is None and result["provider_latency_seconds"] is None and result["provider_reported_cost"] is None

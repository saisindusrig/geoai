"""Offline proposal only. No transport; not wired into production providers.

Documentation for self-hosted Qwen does not establish Nebius compatibility.
"""
import copy
import json
import math
from pydantic import ValidationError
from app.domain.bim_authoring import AuthoringIntent
from app.experimental.canary_execution import MODEL, safe_usage
from app.services.ai.response_metadata import response_metadata, validation_metadata

STAGES = {"UNDERSTAND", "PLAN", "EXPAND", "RELATE"}


def proposed_request(body, *, stage, deployment, enabled=False, nonthinking=False,
                     schema_mode=False, client_options=None):
    """Return reviewable serialization, never dispatch it.

    deployment is a server-selected contract, not a user-supplied provider flag.
    json_schema serialization is a proposal pending exact hosted-route review.
    """
    if stage not in STAGES or client_options:
        raise ValueError("PROFILE_SELECTION_REJECTED")
    if set(body) != {"model", "max_tokens", "temperature", "messages", "response_format"}:
        raise ValueError("PROFILE_REQUEST_FIELDS_REJECTED")
    if body.get("model") != MODEL or body.get("max_tokens") != 3500:
        raise ValueError("PROFILE_LIMIT_MISMATCH")
    result = copy.deepcopy(body)
    if not enabled:
        if nonthinking or schema_mode:
            raise ValueError("PROFILE_DISABLED")
        return result, 45
    if deployment not in {"qwen-self-hosted", "alibaba-model-studio", "nebius"}:
        raise ValueError("PROFILE_DEPLOYMENT_UNSUPPORTED")
    if deployment == "nebius" and (nonthinking or schema_mode):
        raise ValueError("NEBIUS_EXACT_ROUTE_SUPPORT_UNVERIFIED")
    if nonthinking:
        if stage != "UNDERSTAND":
            raise ValueError("PROFILE_STAGE_UNSUPPORTED")
        if deployment == "qwen-self-hosted":
            result["chat_template_kwargs"] = {"enable_thinking": False}
        elif deployment == "alibaba-model-studio":
            result["enable_thinking"] = False
    if schema_mode:
        # Proposal shape only: hosted acceptance and schema dialect remain unverified.
        if stage != "UNDERSTAND":
            raise ValueError("PROFILE_STAGE_UNSUPPORTED")
        schema = AuthoringIntent.model_json_schema()
        audit_schema(schema)
        result["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "authoring_intent", "strict": True, "schema": schema}}
    return result, 45


def audit_schema(schema):
    """Structural audit, not certification of a provider's JSON Schema dialect."""
    def visit(node):
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if not isinstance(ref, str) or not ref.startswith("#/"):
                    raise ValueError("SCHEMA_REFERENCE_UNSUPPORTED")
                target = schema
                for part in ref[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            if "properties" in node:
                if not set(node.get("required", [])).issubset(node["properties"]):
                    raise ValueError("SCHEMA_REQUIRED_MISMATCH")
                if node.get("additionalProperties") is not False:
                    raise ValueError("SCHEMA_OBJECT_NOT_STRICT")
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(schema)
    return schema


def safe_diagnostics(body, *, latency=None, provider_cost=None):
    """Counts only; absent/invalid numeric fields remain None, never estimated."""
    usage = safe_usage(body)
    def numeric(value):
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else None
    result = {key: usage.get(key) for key in (
        "prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens",
        "completion_reasoning_tokens")}
    result.update(provider_latency_seconds=numeric(latency), provider_reported_cost=numeric(provider_cost))
    result.update(response_metadata(body, 3500))
    choices = body.get("choices") or []
    message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
    if isinstance(message, dict) and message.get("refusal"):
        result.update(failure_class="PROVIDER_REFUSAL", structured_parse_error_category="REFUSAL")
    result["strict_schema_valid"] = False
    if result["failure_class"] is None:
        try:
            AuthoringIntent.model_validate_json(message.get("content", ""))
            result["strict_schema_valid"] = True
        except ValidationError as exc:
            result.update(validation_metadata(exc, AuthoringIntent.model_json_schema()))
    return result

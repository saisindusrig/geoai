"""Safe response diagnostics. No response text or reasoning is retained."""
import json
from pydantic import ValidationError

FAILURE_CLASSES = {"INVALID_STRUCTURED_OUTPUT", "LIKELY_TRUNCATED", "SCHEMA_VALIDATION_FAILED", "EMPTY_RESPONSE", "PROVIDER_ERROR"}


def response_metadata(body, limit):
    choices = body.get("choices") if isinstance(body, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices else {}
    choice = choice if isinstance(choice, dict) else {}
    reason = choice.get("finish_reason")
    reason = reason if reason in {"stop", "length", "max_tokens", "max_output_tokens", "tool_calls", "content_filter", None} else "OTHER"
    usage = body.get("usage") or {} if isinstance(body, dict) else {}
    tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
    tokens = tokens if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0 else None
    message = choice.get("message") or {}
    text = message.get("content") if isinstance(message, dict) else None
    length = reason in {"length", "max_tokens", "max_output_tokens"}
    metadata = {"finish_reason":reason, "output_tokens":tokens,
        "max_output_tokens_reached":length or tokens >= limit if tokens is not None else (True if length else None),
        "structured_parse_error_category":None, "validation_error_paths":[],
        "response_appears_truncated":length, "failure_class":None}
    if length:
        metadata.update(failure_class="LIKELY_TRUNCATED", structured_parse_error_category="OUTPUT_LIMIT")
        return metadata
    if text is None or isinstance(text, str) and not text.strip():
        metadata.update(failure_class="EMPTY_RESPONSE", structured_parse_error_category="EMPTY_RESPONSE")
        return metadata
    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            metadata.update(failure_class="INVALID_STRUCTURED_OUTPUT", structured_parse_error_category="NON_OBJECT_JSON")
    except json.JSONDecodeError as exc:
        apparent = exc.pos >= len(text.rstrip()) - 1 or exc.msg.startswith("Unterminated")
        metadata.update(failure_class="LIKELY_TRUNCATED" if apparent else "INVALID_STRUCTURED_OUTPUT",
            structured_parse_error_category="JSON_SYNTAX", response_appears_truncated=apparent)
    except (TypeError, ValueError):
        metadata.update(failure_class="INVALID_STRUCTURED_OUTPUT", structured_parse_error_category="INVALID_CONTENT_TYPE")
    return metadata


def validation_metadata(exc, schema):
    # Allow schema-defined property names only: extra-field locations may be secrets.
    def properties(node):
        names = set()
        if isinstance(node, dict):
            names.update(node.get("properties", {}))
            for value in node.values():
                names.update(properties(value))
        elif isinstance(node, list):
            for value in node: names.update(properties(value))
        return names
    names = properties(schema)
    paths = []
    if isinstance(exc, ValidationError):
        for error in exc.errors(include_input=False, include_url=False):
            paths.append([part if isinstance(part, int) or part in names else "<field>" for part in error["loc"]])
    return {"failure_class":"SCHEMA_VALIDATION_FAILED", "structured_parse_error_category":"SCHEMA_VALIDATION",
            "validation_error_paths":paths}

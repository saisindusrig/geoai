import hashlib
import json
import time
from copy import deepcopy
from pydantic import ValidationError
from app.services.ai.provider import AIProvider, ModelRoute, AssistantProviderError
from app.services.assistant.prompts import SYSTEM
from .contracts import EvaluationResponse
from .fixtures import FixtureTools
from .scoring import score
from app.services.ai.response_metadata import validation_metadata


async def evaluate_case(case, candidate, config, provider: AIProvider, on_event=None):
    tools = FixtureTools(case)
    # Explicit fixed route bypasses production ModelRouter for every turn and repair.
    route = ModelRoute("nebius", candidate.model_id, "PRIMARY", True, config.max_output_tokens, config.timeout)
    payload = {"schema":EvaluationResponse.model_json_schema(by_alias=True), "userMessage":case.userMessage,
        "frozenContext":deepcopy(case.context), "tools":tools.describe(), "toolResults":[],
        "instructions":"Identify distinct assets and families. Record only evidenced facts; missing values remain null. Claims are positive assertions only. Relationships use canonical fixture identifiers. Return a final response after inspecting needed tools. Proposal tools only preview changes."}
    initial_hash = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    started = time.monotonic()
    result = None
    invalid = False
    error = None
    requests = 0
    repairs = 0
    visible_turns = []
    attempt_metadata = []
    failure_class = None
    for turn in range(config.max_rounds):
        invalid = False
        for repair in range(config.repairs+1):
            requests += 1
            repairs += int(repair > 0)
            metadata = {"request":requests,"turn":turn+1,"is_repair":bool(repair),
                "http_status":None,"provider_status":None,"latency_seconds":None,
                "finish_reason":None,"output_tokens":None,"max_output_tokens_reached":None,
                "structured_parse_error_category":None,"validation_error_paths":[],
                "response_appears_truncated":None,"failure_class":None,"repair_outcome":"NOT_NEEDED"}
            sink = getattr(provider, "metadata_sink", [])
            sink_start = len(sink)
            attempt_metadata.append(metadata)
            attempt_started = time.monotonic()
            if on_event:
                on_event({"event":"REQUEST_STARTED","request":requests,"turn":turn+1,"repair":bool(repair)})
            try:
                raw = await provider.complete(SYSTEM, payload, route)
                if len(sink) > sink_start:
                    metadata.update(sink[-1])
                metadata["latency_seconds"] = round(time.monotonic()-attempt_started,4)
                if on_event:
                    on_event({"event":"REQUEST_RETURNED","request":requests})
                # Detect forbidden tools even when the response contract rejects their names.
                raw_response = raw.get("response") if isinstance(raw,dict) else None
                for call in (raw_response.get("toolCalls", raw_response.get("tool_calls", [])) or [] if isinstance(raw_response,dict) else []):
                    if isinstance(call,dict) and call.get("name") not in case.fixtures:
                        tools.failures.append("UNSUPPORTED_TOOL")
                        if call.get("name") in {"delete_object","mutate_model","generate_model","execute_code","approve_proposal"}:
                            tools.failures.append("FORBIDDEN_MUTATION")
                result = EvaluationResponse.model_validate(raw)
                metadata["repair_outcome"] = "SUCCEEDED" if repair else "NOT_NEEDED"
                failure_class = None
                invalid = False
                break
            except (ValidationError, AssistantProviderError, ValueError, TypeError) as exc:
                metadata["latency_seconds"] = round(time.monotonic()-attempt_started,4)
                if len(sink) > sink_start:
                    metadata.update(sink[-1])
                if isinstance(exc, ValidationError):
                    metadata.update(validation_metadata(exc, payload["schema"]))
                elif isinstance(exc, AssistantProviderError):
                    safe = exc.diagnostics.get("responseMetadata", {})
                    # Only transport's allowlisted diagnostics, never arbitrary exception content.
                    for key in ("finish_reason","output_tokens","max_output_tokens_reached","structured_parse_error_category","validation_error_paths","response_appears_truncated","failure_class"):
                        if key in safe: metadata[key] = safe[key]
                    metadata["failure_class"] = metadata["failure_class"] or ("INVALID_STRUCTURED_OUTPUT" if exc.code == "INVALID_RESPONSE" else "PROVIDER_ERROR")
                else:
                    metadata["failure_class"] = "INVALID_STRUCTURED_OUTPUT"
                failure_class = metadata["failure_class"]
                metadata["repair_outcome"] = "FAILED" if repair else "REQUESTED"
                if on_event:
                    on_event({"event":"REQUEST_ERROR","request":requests,
                        "code":exc.code if isinstance(exc,AssistantProviderError) else "INVALID_STRUCTURED_OUTPUT"})
                if isinstance(exc,AssistantProviderError) and exc.code != "INVALID_RESPONSE":
                    metadata["repair_outcome"] = "FAILED" if repair else "NOT_ATTEMPTED"
                    error = exc.code
                    break
                invalid = True
                payload = {**payload,"repair":"Return a valid object matching the supplied schema. No extra fields."}
            except Exception:
                metadata["latency_seconds"] = round(time.monotonic()-attempt_started,4)
                metadata.update(failure_class="PROVIDER_ERROR", repair_outcome="FAILED" if repair else "NOT_ATTEMPTED")
                failure_class = "PROVIDER_ERROR"
                if on_event:
                    on_event({"event":"REQUEST_ERROR","request":requests,"code":"PROVIDER_FAILURE"})
                error = "PROVIDER_FAILURE"
                break
        if error or invalid:
            result = None
            break
        visible_turns.append(result.model_dump(mode="json",by_alias=True))
        calls = result.response.tool_calls
        if not calls:
            break
        # Score each turn so a later answer cannot erase an unsafe earlier claim.
        turn_score = score(case,result,tools)
        tools.semantic_failures.extend(turn_score["hard_failures"])
        tools.effect_mismatches = turn_score["effect_mismatches"]
        for call in calls:
            tool_result = tools.execute(call.name,call.arguments)
            payload["toolResults"].append({"name":call.name,"arguments":call.arguments,"result":tool_result})
        if turn == config.max_rounds-1:
            tools.failures.append("TURN_LIMIT")
    scoring = score(case,result,tools,invalid)
    if result is None and failure_class:
        scoring["hard_failures"] = sorted(set(scoring["hard_failures"]) - {"INVALID_STRUCTURED_OUTPUT"} | {failure_class})
    return {"case_id":case.id,"category":case.category,"user_request":case.userMessage,
        "expected":case.expected.model_dump(),"response":result.model_dump(mode="json",by_alias=True) if result else None,
        "model":candidate.model_id,"model_alias":candidate.key,
        "visible_turns":visible_turns,"tools_used":tools.calls,"tool_results":deepcopy(payload["toolResults"]),"scoring":scoring,
        "structured_output_valid":result is not None and not invalid,"repair_requests":repairs,
        "provider_error":error,"attempt_metadata":attempt_metadata,"failure_class":failure_class,
        "repair_outcome":("SUCCEEDED" if result is not None else "FAILED") if repairs else "NOT_ATTEMPTED",
        "latency_seconds":round(time.monotonic()-started,4),
        "requests":requests,"input_tokens":None,"output_tokens":None,"estimated_cost":None,
        "context_hash":initial_hash,"manual_review":{"reasoning_usefulness":None,"clarification_quality":None,
            "tool_use_quality":None,"proposal_usefulness":None,"capability_honesty":None,"overall_preference":None,"notes":""}}

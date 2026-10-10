"""Offline-testable at-most-once guard for an explicitly authorized canary.

No provider configuration, retry, approval or CAD execution belongs here.
"""
import asyncio
import json
import math
import os
from pathlib import Path
import threading
import time
import traceback
from uuid import uuid4
from pydantic import ValidationError
from app.experimental.cad_contract import digest
from app.domain.bim_authoring import AuthoringIntent
from app.services.ai.provider import AssistantProviderError
from app.services.ai.response_metadata import response_metadata, validation_metadata

MODEL = "Qwen/Qwen3.5-397B-A17B"


class CanaryError(AssistantProviderError):
    def __init__(self, code, **safe_details):
        super().__init__(code, safe_details)


def require(condition, code, **safe_details):
    if not condition:
        raise CanaryError(code, **safe_details)


def stack_evidence(exc):
    # No exception message, source line, locals or input values.
    return [dict(file=f.filename, line=f.lineno, function=f.name)
            for f in traceback.extract_tb(exc.__traceback__)]


def safe_usage(body):
    usage = body.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    result = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens"):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[key] = value
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict):
        value = details.get("reasoning_tokens")
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result["completion_reasoning_tokens"] = value
    return result


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "CANARY_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def validate_transport(expected, method, endpoint, kwargs):
    body = kwargs.get("payload")
    require(isinstance(body, dict), "CANARY_REQUEST_SHAPE")
    require(method == "POST" and endpoint == "chat/completions", "CANARY_ENDPOINT_MISMATCH")
    require(kwargs.get("model") == body.get("model") == MODEL, "CANARY_MODEL_MISMATCH")
    require(kwargs.get("timeout") == 45 and body.get("max_tokens") == 3500, "CANARY_LIMIT_MISMATCH")
    require(set(body) == {"model", "messages", "temperature", "max_tokens", "response_format"}, "CANARY_REQUEST_FIELDS_MISMATCH")
    require(body["temperature"] == .1 and body["response_format"] == {"type":"json_object"}, "CANARY_REQUEST_OPTIONS_MISMATCH")
    messages = body.get("messages")
    require(isinstance(messages, list) and len(messages) == 2, "CANARY_MESSAGE_SHAPE")
    require(all(isinstance(m, dict) and set(m) == {"role", "content"} and isinstance(m["content"], str) for m in messages), "CANARY_MESSAGE_SHAPE")
    require(messages[0] == {"role":"system", "content":expected["system"]} and messages[1]["role"] == "user", "CANARY_MESSAGE_MISMATCH")
    try:
        user = json.loads(messages[1]["content"], object_pairs_hook=reject_duplicates,
                          parse_constant=lambda _: (_ for _ in ()).throw(CanaryError("CANARY_INVALID_JSON_NUMBER")))
        actual_hash = digest(dict(system=messages[0]["content"], payload=user))
    except (ValueError, TypeError) as exc:
        if isinstance(exc, CanaryError):raise
        raise CanaryError("CANARY_INVALID_REQUEST_JSON") from exc
    require(actual_hash == digest(expected), "CANARY_PACKET_MISMATCH", expectedHash=digest(expected), actualHash=actual_hash)
    reservation = sum(len(m["content"].encode("utf-8")) for m in messages) + 1024
    require(reservation <= 7292, "CANARY_INPUT_LIMIT", actualReservation=reservation, ceiling=7292)
    return reservation


class OneRequestGuard:
    def __init__(self, path, expected, *, run_id, authorization):
        self.path = Path(path)
        self.expected = expected
        self.lock = threading.Lock()
        self.claimed = False
        self.data = dict(schemaVersion="understand-canary-execution/2", runId=run_id,
            authorization=authorization, packetHash=digest(expected), state="REQUEST_RESERVED",
            reservationCount=1, requestCount=0, transportInvoked=False, transportOutcome="NOT_STARTED", terminal=False,
            retries=0, inputReservationTokens=7292, outputCapTokens=3500, timeoutSeconds=45,
            model=MODEL, replayProhibited=True, planContinuationProhibited=True)
        try:
            with self.path.open("x", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            self._sync_directory()
        except FileExistsError as exc:
            raise CanaryError("CANARY_LEDGER_EXISTS_NO_REPLAY") from exc

    def _sync_directory(self):
        if os.name == "posix":
            fd = os.open(self.path.parent, os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)

    def save(self):
        temporary = self.path.with_name(self.path.name + "." + uuid4().hex + ".tmp")
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)
        self._sync_directory()

    def fail_before_transport(self, exc):
        if not self.data["transportInvoked"]:
            self.data.update(state="PRE_TRANSPORT_FAILED", terminal=True, requestCount=0,
                transportInvoked=False, transportOutcome="NOT_STARTED",
                errorCode=getattr(exc, "code", "CANARY_LOCAL_FAILURE"), stack=stack_evidence(exc))
            self.save()

    async def dispatch(self, transport, method, endpoint, **kwargs):
        with self.lock:
            require(not self.claimed and not self.data["terminal"], "CANARY_DUPLICATE_DISPATCH")
            self.claimed = True
        start = time.perf_counter()
        try:
            reservation = validate_transport(self.expected, method, endpoint, kwargs)
            self.data.update(state="DISPATCH_INTENT_RECORDED", requestCount=1, dispatchIntentCount=1,
                transportInvoked=None, transportOutcome="UNKNOWN_UNTIL_RESPONSE", actualReservationTokens=reservation)
            self.save()  # Failure here proves the transport was never invoked.
            self.data["transportInvoked"] = True
            try:
                body = await transport(method, endpoint, **kwargs)
            except BaseException as exc:
                self.data.update(state="TRANSPORT_OUTCOME_UNCERTAIN", terminal=True,
                    transportOutcome="UNKNOWN",
                    errorCode="CANARY_TRANSPORT_OUTCOME_UNCERTAIN", exceptionType=type(exc).__name__, stack=stack_evidence(exc))
                raise
            self.data.update(state="RESPONSE_RECEIVED", terminal=True, transportOutcome="RESPONSE_RECEIVED", usage=safe_usage(body),
                responseMetadata=response_metadata(body, 3500))
            usage = body.get("usage")
            if isinstance(usage, dict):
                for key in ("cost", "total_cost", "cost_usd"):
                    value = usage.get(key)
                    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
                        self.data["providerReportedCost"] = {"field":key, "value":value}
                        break
            try:
                parsed = json.loads(body["choices"][0]["message"]["content"])
                self.data["jsonSyntaxValid"] = True
                try:
                    AuthoringIntent.model_validate(parsed)
                    self.data["strictSchemaValid"] = True
                except ValidationError as exc:
                    self.data.update(strictSchemaValid=False,
                        schemaMetadata=validation_metadata(exc, AuthoringIntent.model_json_schema(by_alias=True)))
            except (KeyError, IndexError, TypeError, ValueError):
                self.data.update(jsonSyntaxValid=False, strictSchemaValid=False)
            return body
        except BaseException as exc:
            self.fail_before_transport(exc)
            raise
        finally:
            self.data["requestLatencySeconds"] = round(time.perf_counter() - start, 3)
            self.save()

    def finish(self, **safe_results):
        self.data.update(safe_results, terminal=True)
        self.save()

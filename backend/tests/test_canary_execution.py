"""Fake transports only. Never use the historical failed database or ledger."""
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest
from app.experimental.canary_execution import OneRequestGuard, CanaryError, MODEL, validate_transport, safe_usage
from app.experimental.cad_contract import digest
from app.experimental import bim_orchestration as orchestration
from app.experimental.bim_authoring import stage_packet, stage_context
from app.experimental.bim_authoring_fixtures import authoring_case
from app.services.ai.provider import NebiusProvider
from app.services.ai import nebius
from app.db.models import GeneratedFile, ModelRevision
from app.services.assistant.storage import rows
from test_bim_orchestration import authorized, started
from test_cad_workspace import cad_db
from test_site_workspace import site_db


def expected_packet():
    return dict(system="Return JSON.", payload={"stage":"UNDERSTAND", "input":{"a":1,"b":2}})


def arguments(expected):
    return dict(model=MODEL, timeout=45, payload=dict(model=MODEL, max_tokens=3500, temperature=.1,
        response_format={"type":"json_object"}, messages=[dict(role="system", content=expected["system"]),
        dict(role="user", content=json.dumps(expected["payload"], separators=(",", ":")))]))


def response(truncated=False):
    return dict(choices=[dict(finish_reason="length" if truncated else "stop", message=dict(content="{" if truncated else
        json.dumps(authoring_case("platform").intent.model_dump(mode="json", by_alias=True)), reasoning_content="PRIVATE_REASONING"))],
        usage=dict(prompt_tokens=2000, completion_tokens=3500 if truncated else 200, total_tokens=5500 if truncated else 2200,
            completion_tokens_details={"reasoning_tokens":3400 if truncated else 80, "private":"SECRET"}))


def guard(tmp_path, expected=None):
    return OneRequestGuard(tmp_path / "ledger.json", expected or expected_packet(), run_id=1, authorization="OFFLINE_MOCK_ONLY")


def invoke(g, transport, **kwargs):
    return asyncio.run(g.dispatch(transport, "POST", "chat/completions", **(kwargs or arguments(g.expected))))


def test_order_only_difference_and_exact_payload_changes(tmp_path):
    g=guard(tmp_path)
    args=arguments(g.expected)
    args["payload"]["messages"][1]["content"]='{"input":{"b":2,"a":1},"stage":"UNDERSTAND"}'
    assert validate_transport(g.expected,"POST","chat/completions",args) < 7292
    args["payload"]["messages"][1]["content"]='{"input":{"b":2,"a":3},"stage":"UNDERSTAND"}'
    with pytest.raises(CanaryError,match="CANARY_PACKET_MISMATCH"):
        validate_transport(g.expected,"POST","chat/completions",args)


@pytest.mark.parametrize("change,code",[("model","CANARY_MODEL_MISMATCH"),("timeout","CANARY_LIMIT_MISMATCH"),
    ("max_tokens","CANARY_LIMIT_MISMATCH"),("extra","CANARY_REQUEST_FIELDS_MISMATCH"),
    ("system","CANARY_MESSAGE_MISMATCH"),("duplicate","CANARY_DUPLICATE_JSON_KEY")])
def test_pre_transport_rejection(tmp_path,change,code):
    g=guard(tmp_path);args=arguments(g.expected);calls=[]
    if change=="model":args["model"]="OTHER"
    elif change=="timeout":args["timeout"]=46
    elif change=="max_tokens":args["payload"]["max_tokens"]=3501
    elif change=="extra":args["payload"]["thinking"]="unauthorized"
    elif change=="system":args["payload"]["messages"][0]["content"]="changed"
    else:args["payload"]["messages"][1]["content"]='{"stage":"UNDERSTAND","stage":"PLAN"}'
    async def fake(*a,**kw):calls.append(1);return response()
    with pytest.raises(CanaryError,match=code):invoke(g,fake,**args)
    saved=json.loads(g.path.read_text())
    assert calls==[] and saved["state"]=="PRE_TRANSPORT_FAILED" and saved["requestCount"]==0
    assert saved["errorCode"]==code and saved["stack"] and saved["terminal"]
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)


def test_input_ceiling_without_changing_packet(tmp_path):
    g=guard(tmp_path)
    args=arguments(g.expected)
    args["payload"]["messages"][1]["content"] += " "*7292
    with pytest.raises(CanaryError,match="CANARY_INPUT_LIMIT"):
        validate_transport(g.expected,"POST","chat/completions",args)


@pytest.mark.parametrize("truncated",[False,True])
def test_fake_response_and_no_replay(tmp_path,truncated):
    g=guard(tmp_path);calls=[]
    async def fake(*a,**kw):
        saved=json.loads(g.path.read_text())
        assert saved["state"]=="DISPATCH_INTENT_RECORDED" and saved["requestCount"]==1
        calls.append(1);return response(truncated)
    invoke(g,fake)
    assert calls==[1] and g.data["terminal"] and g.data["requestCount"]==1
    assert g.data["strictSchemaValid"] is (not truncated)
    assert g.data["usage"]["completion_reasoning_tokens"]==(3400 if truncated else 80)
    assert "PRIVATE_REASONING" not in g.path.read_text() and "SECRET" not in g.path.read_text()
    with pytest.raises(CanaryError,match="DUPLICATE_DISPATCH"):invoke(g,fake)
    assert calls==[1]


@pytest.mark.parametrize("exception",[TimeoutError(),RuntimeError("SECRET"),asyncio.CancelledError()])
def test_uncertain_after_invocation(tmp_path,exception):
    g=guard(tmp_path);calls=[]
    async def fake(*a,**kw):calls.append(1);raise exception
    with pytest.raises(type(exception)):invoke(g,fake)
    assert g.data["state"]=="TRANSPORT_OUTCOME_UNCERTAIN" and g.data["requestCount"]==1 and calls==[1]
    assert "SECRET" not in g.path.read_text()
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)


def test_failure_after_reservation_before_dispatch(tmp_path,monkeypatch):
    g=guard(tmp_path);calls=[];original=g.save
    def broken():
        if g.data["state"]=="DISPATCH_INTENT_RECORDED":raise OSError("disk")
        original()
    monkeypatch.setattr(g,"save",broken)
    async def fake(*a,**kw):calls.append(1);return response()
    with pytest.raises(OSError):invoke(g,fake)
    assert calls==[] and g.data["state"]=="PRE_TRANSPORT_FAILED" and not g.data["transportInvoked"]
    assert g.data["requestCount"]==0 and g.data["reservationCount"]==1 and g.data["dispatchIntentCount"]==1
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)


def test_incomplete_or_interrupted_ledger_is_never_replayed(tmp_path):
    (tmp_path/"ledger.json").write_text("{")
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)


def test_interruption_after_dispatch_intent_has_uncertain_durable_state(tmp_path):
    g=guard(tmp_path)
    g.data.update(state="DISPATCH_INTENT_RECORDED",requestCount=1,transportInvoked=None,
        transportOutcome="UNKNOWN_UNTIL_RESPONSE")
    g.save()
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)
    assert json.loads(g.path.read_text())["transportInvoked"] is None


def test_crash_during_exclusive_reservation_fails_closed(tmp_path,monkeypatch):
    def broken(_):raise OSError("mock disk error")
    monkeypatch.setattr("app.experimental.canary_execution.os.fsync",broken)
    with pytest.raises(OSError):guard(tmp_path)
    assert (tmp_path/"ledger.json").exists()
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path)


def test_concurrent_exclusive_reservation(tmp_path):
    def attempt(_):
        try:return guard(tmp_path)
        except CanaryError as exc:return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,range(2)))
    assert sum(isinstance(r,OneRequestGuard) for r in results)==1
    assert "CANARY_LEDGER_EXISTS_NO_REPLAY" in results


def test_concurrent_duplicate_dispatch(tmp_path):
    g=guard(tmp_path);calls=[]
    async def exercise():
        entered=asyncio.Event();release=asyncio.Event()
        async def fake(*a,**kw):calls.append(1);entered.set();await release.wait();return response()
        first=asyncio.create_task(g.dispatch(fake,"POST","chat/completions",**arguments(g.expected)))
        await entered.wait()
        with pytest.raises(CanaryError,match="DUPLICATE_DISPATCH"):
            await g.dispatch(fake,"POST","chat/completions",**arguments(g.expected))
        release.set();await first
    asyncio.run(exercise())
    assert calls==[1]


@pytest.mark.parametrize("outcome",["success","truncated","guard_failure","uncertain"])
def test_real_orchestration_with_fake_transport(authorized,tmp_path,monkeypatch,outcome):
    db=authorized
    msg,run=started(db)
    _,snapshot,_=orchestration.frozen(db,1,1,msg["id"])
    packet=stage_packet("UNDERSTAND",request_text=snapshot["userRequest"])
    packet["trustedContext"]=stage_context("UNDERSTAND",snapshot,digest(snapshot))
    expected=dict(system=packet.pop("instruction"),payload=packet)
    if outcome=="guard_failure":expected["system"] += " changed"
    g=guard(tmp_path,expected);calls=[]
    before=copy.deepcopy(db.get(ModelRevision,1).document_json)
    from app.core.config import settings
    monkeypatch.setattr(settings,"NEBIUS_API_KEY","offline-mock-key")
    monkeypatch.setattr(settings,"NEBIUS_PRIMARY_MODEL",MODEL)
    monkeypatch.setattr(settings,"NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS",45)
    async def fake(*a,**kw):
        calls.append(1)
        if outcome=="uncertain":raise TimeoutError()
        return response(outcome=="truncated")
    async def guarded(method,endpoint,**kw):return await g.dispatch(fake,method,endpoint,**kw)
    monkeypatch.setattr(nebius,"_request",guarded)
    result=asyncio.run(orchestration.advance(db,project_id=1,user_id=1,run_id=run["runId"],provider=NebiusProvider()))
    assert len(calls)==(0 if outcome=="guard_failure" else 1)
    assert result["completedStages"]==(["UNDERSTAND"] if outcome=="success" else [])
    if outcome=="truncated":assert result["errorCode"]=="OUTPUT_TRUNCATED"
    assert db.get(ModelRevision,1).document_json==before and db.query(ModelRevision).count()==1
    assert not rows(db,"proposal_approvals",1) and not rows(db,"design_proposal_versions",1)
    assert not db.query(GeneratedFile).filter(GeneratedFile.file_type.in_(["cad_manifest_v1","cad_review_v1"])).count()
    assert g.data["terminal"] and g.data["retries"]==0
    with pytest.raises(CanaryError,match="NO_REPLAY"):guard(tmp_path,expected)


def test_safe_usage_rejects_malformed_values():
    assert safe_usage({"usage":["PRIVATE"]})=={}
    assert safe_usage({"usage":{"prompt_tokens":True,"completion_tokens":-1,"reasoning_tokens":"secret"}})=={}


def test_old_run_is_explicitly_rejected_without_database_access():
    import importlib.util
    script=Path(__file__).resolve().parents[1]/"scripts"/"run_understand_canary.py"
    spec=importlib.util.spec_from_file_location("canary_runner",script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with pytest.raises(CanaryError,match="CANARY_FRESH_RUN_REQUIRED"):
        module.execute(module.FAILED,"NOT_AUTHORIZED")

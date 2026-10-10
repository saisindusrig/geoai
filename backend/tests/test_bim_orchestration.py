"""Recorded PRIMARY responses only; no live transport or native compiler."""
import asyncio
import copy
import pytest
from fastapi import HTTPException
from app.experimental import bim_orchestration as orchestration
from app.experimental.bim_authoring_fixtures import authoring_case
from app.experimental.cad_artifacts import PrivateStore
from app.experimental.cad_contract import digest
from app.db.models import ModelRevision, GeneratedFile
from app.services.assistant.storage import rows
from app.services.ai.provider import AssistantProviderError
from test_cad_workspace import cad_db
from test_site_workspace import site_db
from test_assistant_runtime import message
from test_site_workspace import api_client


@pytest.fixture
def authorized(cad_db,monkeypatch):
    monkeypatch.setenv("GEOAI_EXPERIMENTAL_BIM_AUTHORING","true")
    monkeypatch.setenv("GEOAI_BIM_AUTHORING_USER_IDS","1")
    monkeypatch.setenv("GEOAI_BIM_AUTHORING_PROJECT_IDS","1")
    from app.experimental import cad_worker
    monkeypatch.setattr(cad_worker,"compile_batch",lambda *_:pytest.fail("Authoring must not execute CAD"))
    return cad_db


class Recorded:
    def __init__(self,case="platform",overrides=None):
        self.bundle=authoring_case(case)
        self.calls=[]
        self.overrides=list(overrides or [])

    async def complete(self,system,packet,route):
        assert route.tier == "PRIMARY" and not route.tool_calling_allowed
        assert route.max_output_tokens == 3500
        assert packet["capabilities"]["productionCadBuild"] is False
        assert "schema" not in packet or packet["schema"] == packet["outputSchema"]
        self.calls.append((packet["stage"],packet,route))
        if self.overrides:
            value=self.overrides.pop(0)
            if isinstance(value,Exception):raise value
            return value
        stage=packet["stage"]
        if stage=="UNDERSTAND":result=self.bundle.intent
        elif stage=="PLAN":result=self.bundle.plan
        elif stage=="RELATE":result=self.bundle.relationships
        else:result=next(e for e in self.bundle.expansions if e.assembly_id==packet["input"]["assembly"]["id"])
        return result.model_dump(mode="json",by_alias=True)


def started(db):
    msg,_=message(db,"Create a conceptual platform with known supported components for review.")
    run=orchestration.start(db,project_id=1,user_id=1,message_id=msg["id"],request_id="4b-test")
    return msg,run


def step(db,run,provider,**kwargs):
    return asyncio.run(orchestration.advance(db,project_id=1,user_id=1,run_id=run["runId"],provider=provider,**kwargs))


@pytest.mark.parametrize("case",["bridge","platform","mixed","unregistered"])
def test_saved_proposals_from_recorded_primary(authorized,case):
    msg,run=started(authorized)
    provider=Recorded(case)
    original=copy.deepcopy(authorized.get(ModelRevision,1).document_json)
    for _ in range(22):
        run=step(authorized,run,provider)
        if run["status"]=="COMPLETED":break
        assert run["status"]=="READY",run
    assert run["status"]=="COMPLETED"
    assert len(provider.calls)==len(provider.bundle.plan.assemblies)+3
    assert run["proposal"]["review"]["finalizationBlocked"]
    assert run["proposal"]["review"]["geometryStatus"]=="CONTRACT_VALID_NATIVE_NOT_RUN"
    assert not rows(authorized,"proposal_approvals",1)
    assert authorized.query(ModelRevision).count()==1
    assert authorized.get(ModelRevision,1).document_json==original
    assert authorized.query(GeneratedFile).filter_by(file_type="bim_authoring_review_v1").count()==1
    assert any(any(p.get("proposalVersionId")==run["proposal"]["proposal"]["id"] for p in m["parts"])
        for m in rows(authorized,"conversation_messages",1) if m["role"]=="ASSISTANT")
    count=len(provider.calls)
    assert step(authorized,run,provider)==run and len(provider.calls)==count
    assert orchestration.start(authorized,project_id=1,user_id=1,message_id=msg["id"],request_id="4b-test")["runId"]==run["runId"]
    # The existing conversation remains writable after the experimental reply.
    following,_=message(authorized,"Explain the saved proposal's unresolved conditions.")
    assert following["sequence"]>msg["sequence"]


def test_default_off_and_authorization(authorized,monkeypatch):
    msg,run=started(authorized)
    for setting in ("GEOAI_EXPERIMENTAL_BIM_AUTHORING","GEOAI_BIM_AUTHORING_USER_IDS","GEOAI_BIM_AUTHORING_PROJECT_IDS"):
        with monkeypatch.context() as scoped:
            scoped.delenv(setting)
            with pytest.raises(HTTPException):orchestration.read(authorized,project_id=1,user_id=1,run_id=run["runId"])
    with pytest.raises(HTTPException):orchestration.read(authorized,project_id=1,user_id=2,run_id=run["runId"])


def test_unsupported_no_partial_proposal(authorized):
    _,run=started(authorized)
    provider=Recorded("unsupported")
    run=step(authorized,run,provider)
    assert run["status"]=="FAILED" and run["errorCode"]=="UNSUPPORTED_FEATURE"
    assert run["completedStages"]==[] and not rows(authorized,"design_proposal_versions",1)


@pytest.mark.parametrize("failure",['{"schemaVersion":',{},AssistantProviderError("INVALID_RESPONSE"),AssistantProviderError("TIMEOUT")])
def test_one_stage_repair_preserves_checkpoints(authorized,failure):
    _,run=started(authorized)
    provider=Recorded()
    run=step(authorized,run,provider)
    assert run["completedStages"]==["UNDERSTAND"]
    provider.overrides=[failure]
    run=step(authorized,run,provider)
    assert run["status"]=="RETRYABLE" and run["completedStages"]==["UNDERSTAND"]
    run=step(authorized,run,provider)
    assert run["status"]=="READY" and run["completedStages"]==["UNDERSTAND","PLAN"]
    assert [c[0] for c in provider.calls]==["UNDERSTAND","PLAN","PLAN"]
    assert provider.calls[-1][1]["repair"]


def test_attempts_exhausted(authorized):
    _,run=started(authorized)
    provider=Recorded(overrides=[{},{}])
    run=step(authorized,run,provider)
    run=step(authorized,run,provider)
    assert run["status"]=="FAILED" and run["calls"]==2
    with pytest.raises(ValueError):step(authorized,run,provider)
    assert len(provider.calls)==2


def test_stale_before_provider(authorized):
    _,run=started(authorized)
    base=authorized.get(ModelRevision,1)
    base.document_json={**base.document_json,"new":True}
    authorized.commit()
    provider=Recorded()
    failed=step(authorized,run,provider)
    assert failed["status"]=="FAILED" and failed["errorCode"]=="STALE_SITE_PROFILE"
    assert not provider.calls


@pytest.mark.parametrize("kind",["relationships","dimensions","mapping","source"])
def test_invalid_semantics_stop_at_stage(authorized,kind):
    _,run=started(authorized)
    provider=Recorded()
    if kind=="source":
        bad=provider.bundle.intent.model_dump(mode="json",by_alias=True)
        bad["projectId"]=999
        provider.overrides=[bad,bad]
    else:
        run=step(authorized,run,provider)
        run=step(authorized,run,provider)
        if kind=="relationships":
            for _ in provider.bundle.expansions:run=step(authorized,run,provider)
            bad=provider.bundle.relationships.model_dump(mode="json",by_alias=True)
            bad["connections"][0]["fromComponentId"]="missing"
        else:
            bad=provider.bundle.expansions[0].model_dump(mode="json",by_alias=True)
            if kind=="dimensions":bad["components"][0]["parameters"][0]["value"]=-1
            else:bad["components"][0]["recipe"]["operation"]="CIRCULAR_HOLE"
        provider.overrides=[bad,bad]
    run=step(authorized,run,provider)
    if run["status"]=="RETRYABLE":run=step(authorized,run,provider)
    assert run["status"]=="FAILED" and run["proposal"] is None
    assert not rows(authorized,"proposal_approvals",1)


def test_corrupt_checkpoint_fails_closed(authorized):
    _,run=started(authorized)
    step(authorized,run,Recorded())
    row=authorized.get(GeneratedFile,run["runId"])
    _,path=PrivateStore()._target(1,row.metadata_json["snapshotHash"])
    path.write_bytes(b"corrupt")
    provider=Recorded()
    with pytest.raises(ValueError):step(authorized,run,provider)
    assert not provider.calls


def test_existing_nebius_provider_seam(authorized,monkeypatch):
    _,run=started(authorized)
    calls=[]
    async def mocked(system,payload,**options):
        calls.append(options)
        assert payload["stage"]=="UNDERSTAND"
        return authoring_case("platform").intent.model_dump(mode="json",by_alias=True)
    monkeypatch.setattr("app.services.ai.nebius.assistant_json",mocked)
    run=asyncio.run(orchestration.advance(authorized,project_id=1,user_id=1,run_id=run["runId"]))
    from app.core.config import settings
    assert calls[0]["model"]==(settings.NEBIUS_PRIMARY_MODEL.strip() or settings.NEBIUS_CHAT_MODEL)
    assert calls[0]["max_output_tokens"]==3500 and run["completedStages"]==["UNDERSTAND"]


def test_cancellation_and_restart_preserve_valid_stage(authorized):
    _,run=started(authorized)
    provider=Recorded()
    run=step(authorized,run,provider)
    class Cancelled:
        async def complete(self,*args):raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):step(authorized,run,Cancelled())
    run=orchestration.read(authorized,project_id=1,user_id=1,run_id=run["runId"])
    assert run["errorCode"]=="CANCELLED" and run["completedStages"]==["UNDERSTAND"]
    authorized.expire_all()
    run=step(authorized,run,provider)
    assert run["completedStages"]==["UNDERSTAND","PLAN"]
    assert [p[0] for p in provider.calls]==["UNDERSTAND","PLAN"]


def test_timeout_is_bounded(authorized,monkeypatch):
    _,run=started(authorized)
    original=orchestration.ModelRouter.route
    from dataclasses import replace
    monkeypatch.setattr(orchestration.ModelRouter,"route",lambda self,meta:replace(original(self,meta),timeout=.01))
    class Slow:
        async def complete(self,*args):await asyncio.sleep(1)
    run=step(authorized,run,Slow())
    assert run["errorCode"]=="PROVIDER_TIMEOUT" and run["status"]=="RETRYABLE"


def test_context_changes_during_provider_are_not_checkpointed(authorized):
    _,run=started(authorized)
    class Changed(Recorded):
        async def complete(self,*args):
            base=authorized.get(ModelRevision,1)
            base.document_json={**base.document_json,"changed":True}
            authorized.commit()
            return await super().complete(*args)
    run=step(authorized,run,Changed())
    assert run["status"]=="FAILED" and not run["completedStages"]


def test_running_action_rejects_concurrency_and_requires_explicit_recovery(authorized):
    from datetime import datetime,timezone,timedelta
    _,run=started(authorized)
    row=authorized.get(GeneratedFile,run["runId"])
    row.metadata_json={**row.metadata_json,"status":"RUNNING","claimedAt":orchestration.now(),"calls":1,"attempts":{"UNDERSTAND":1}}
    authorized.commit()
    provider=Recorded()
    with pytest.raises(ValueError,match="AUTHORING_ACTION_ACTIVE"):step(authorized,run,provider)
    assert not provider.calls
    row.metadata_json={**row.metadata_json,"claimedAt":(datetime.now(timezone.utc)-timedelta(seconds=151)).isoformat()}
    authorized.commit()
    with pytest.raises(ValueError):step(authorized,run,provider)
    run=step(authorized,run,provider,recover_interrupted=True)
    assert run["completedStages"]==["UNDERSTAND"] and run["calls"]==2


def test_experimental_api_is_explicit_and_safe(authorized,api_client,monkeypatch):
    msg,_=message(authorized)
    root="/api/projects/1/experimental-cad/bim-authoring/runs"
    result=api_client.post(root,json={"request_id":"api-4b","message_id":msg["id"]})
    assert result.status_code==200,result.text
    run_id=result.json()["runId"]
    assert api_client.get(root+f"/{run_id}").json()["calls"]==0
    assert api_client.post(root+f"/{run_id}/advance",json={"approval":True}).status_code==422
    response=api_client.post(root+f"/{run_id}/advance",json={})
    assert response.status_code==200 and response.json()["errorCode"]=="MISSING_KEY"
    monkeypatch.delenv("GEOAI_EXPERIMENTAL_BIM_AUTHORING")
    assert api_client.post(root+f"/{run_id}/advance",json={}).status_code==403


def test_truncated_metadata_is_safe_and_stage_specific(authorized):
    _,run=started(authorized)
    class Truncated:
        metadata_sink=[{"failure_class":"LIKELY_TRUNCATED","provider_status":"INVALID_RESPONSE"}]
        async def complete(self,*args):raise AssistantProviderError("INVALID_RESPONSE",{"providerErrorMessage":"private provider text"})
    run=step(authorized,run,Truncated())
    assert run["errorCode"]=="OUTPUT_TRUNCATED" and run["status"]=="RETRYABLE"
    assert "private provider text" not in str(run)


def test_failed_checkpoint_write_preserves_prior_stage(authorized):
    _,run=started(authorized)
    provider=Recorded()
    run=step(authorized,run,provider)
    class Failing(PrivateStore):
        def put(self,*args):raise RuntimeError("isolated write failure")
    with pytest.raises(RuntimeError):step(authorized,run,provider,store=Failing())
    run=orchestration.read(authorized,project_id=1,user_id=1,run_id=run["runId"])
    assert run["errorCode"]=="CHECKPOINT_STORAGE_FAILURE" and run["completedStages"]==["UNDERSTAND"]


def test_frozen_requirements_and_unknowns_reach_provider(authorized):
    from app.services.assistant.memory import MemoryService
    from test_site_workspace import requirement
    svc=MemoryService()
    memory=svc.create(authorized,1,1,requirement("req-4b"))
    svc.transition(authorized,1,1,memory["id"],1,"accept","PROPOSED")
    _,run=started(authorized)
    provider=Recorded()
    step(authorized,run,provider)
    frozen=provider.calls[0][1]["trustedContext"]
    assert "terrain" in frozen["explicitUnknowns"]
    assert frozen["selectionVersionId"] and frozen["siteSummary"]
    assert "siteProfile" not in frozen and "siteSelection" not in frozen
    # Existing conversation memory attachment rules select accepted requirements.
    assert frozen["acceptedRequirements"][0]["content"]["key"] == "carriageway.width"


def test_new_revision_rejected_before_provider(authorized):
    _,run=started(authorized)
    authorized.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json={"components":[]}))
    authorized.commit()
    provider=Recorded()
    failed=step(authorized,run,provider)
    assert failed["errorCode"]=="STALE_SOURCE_REVISION" and not provider.calls


def test_changed_accepted_requirements_rejected_before_provider(authorized):
    _,run=started(authorized)
    from test_site_workspace import requirement
    from app.services.assistant.memory import MemoryService
    svc=MemoryService()
    memory=svc.create(authorized,1,1,requirement("changed-4b"))
    svc.transition(authorized,1,1,memory["id"],1,"accept","PROPOSED")
    provider=Recorded()
    failed=step(authorized,run,provider)
    assert failed["errorCode"]=="STALE_ACCEPTED_REQUIREMENTS" and not provider.calls

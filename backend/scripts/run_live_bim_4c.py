"""One explicitly authorized checkpoint action; existing provider and API only.

Paid ceiling is enforced before the existing transport. No fallback provider,
schema repair outside the adapter, native build, approval or source mutation.
"""
import json
import sys
import time
from pathlib import Path
from prepare_live_bim_4c import OUT, ACTOR, PROJECT, REQUEST


def advance_once():
    from app.core.config import settings
    settings.LOCAL_STORAGE_DIR=str(OUT/"public")
    from app.services import storage
    storage._s3_configured=lambda:False
    storage._get_s3=lambda:None
    from app.db.session import SessionLocal,get_db
    from app.db.models import ModelRevision,GeneratedFile
    from app.experimental.cad_contract import digest
    from app.experimental.cad_artifacts import PrivateStore
    from app.experimental import bim_orchestration as orchestration,cad_worker
    from app.services.ai import nebius
    from app.services.ai.provider import NebiusProvider,AssistantProviderError
    from app.core.security import get_current_user_id
    from app.services.assistant.storage import rows
    from app.main import app
    from fastapi.testclient import TestClient
    prepared=json.loads((OUT/"prepared.json").read_text())
    ledger_path=OUT/"live-evidence.json"
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else dict(
        schemaVersion="phase-4c-live-evidence/1",authorization="User explicitly authorized one scenario on 2026-10-10",
        maxCalls=12,maxInputTokens=480000,maxOutputTokens=42000,requests=[],actions=[],inputBudgetCharged=0,
        outputBudgetCharged=0,terminal=False,decision=None)
    def save():ledger_path.write_text(json.dumps(ledger,indent=2))
    if ledger["terminal"]:raise RuntimeError("Acceptance stopped: terminal evidence already recorded")
    if any(r.get("outcome")=="IN_FLIGHT" for r in ledger["requests"]):
        raise RuntimeError("Unknown paid request outcome; no automatic replay")
    db=SessionLocal()
    before={str(r.id):digest(r.document_json) for r in db.query(ModelRevision).filter_by(project_id=PROJECT).all()}
    if before != {str(prepared["revisionId"]):prepared["originalDocumentHash"]}:
        raise RuntimeError("Isolated source changed: stop before model")
    assert prepared["model"]=="Qwen/Qwen3.5-397B-A17B" and prepared["testProjectId"]==PROJECT==490001
    row=db.get(GeneratedFile,prepared["runId"])
    data=json.loads(PrivateStore().get(PROJECT,row.metadata_json["snapshotHash"]))
    stage,key,assembly_id,outputs=orchestration._state(data)
    if "PLAN" in outputs:
        from app.domain.bim_authoring import AssemblyPlan
        plan=AssemblyPlan.model_validate(outputs["PLAN"])
        if len(plan.assemblies)!=3 or len(plan.assets)!=1:
            ledger.update(terminal=True,decision="PARTIAL",stopReason="APPROVED_SCENARIO_SHAPE_MISMATCH")
            save();print(json.dumps({"stopReason":ledger["stopReason"]}));return
    if stage != "REVIEW" and len(ledger["requests"])>=12:
        ledger.update(terminal=True,decision="PARTIAL",stopReason="REQUEST_BUDGET_EXHAUSTED")
        save();return
    usage={}
    metadata=[]
    original_transport=nebius._request
    original_provider=orchestration.NebiusProvider
    original_compile=cad_worker.compile_batch
    async def guarded_transport(method,endpoint,**kwargs):
        payload=kwargs.get("payload") or {}
        if (method!="POST" or endpoint!="chat/completions" or kwargs.get("model")!="Qwen/Qwen3.5-397B-A17B"
                or payload.get("model")!="Qwen/Qwen3.5-397B-A17B" or kwargs.get("timeout")!=45
                or payload.get("max_tokens")!=3500):
            raise AssistantProviderError("UNAUTHORIZED_LIVE_CONFIGURATION")
        # One token per UTF-8 byte is a conservative content reservation; retain
        # 1024 tokens for message framing. Actual provider usage replaces it.
        reserved_input=sum(len(m["content"].encode("utf-8")) for m in payload["messages"])+1024
        if (len(ledger["requests"])>=12 or ledger["inputBudgetCharged"]+reserved_input>480000
                or ledger["outputBudgetCharged"]+3500>42000):
            raise AssistantProviderError("LIVE_BUDGET_EXHAUSTED")
        record=dict(requestNumber=len(ledger["requests"])+1,stage=stage,checkpointKey=key,model=kwargs["model"],
            attempt=row.metadata_json["attempts"].get(key,0),inputReservationTokens=reserved_input,
            outputCapTokens=3500,timeoutSeconds=45,outcome="IN_FLIGHT",inputTokens=None,outputTokens=None,
            finishReason=None,providerReportedCost=None)
        ledger["requests"].append(record)
        ledger["inputBudgetCharged"]+=reserved_input
        ledger["outputBudgetCharged"]+=3500
        save()
        started=time.perf_counter()
        try:
            body=await original_transport(method,endpoint,**kwargs)
            u=body.get("usage") or {}
            for field,provider_field,budget,reservation in (("inputTokens","prompt_tokens","inputBudgetCharged",reserved_input),
                    ("outputTokens","completion_tokens","outputBudgetCharged",3500)):
                value=u.get(provider_field)
                if isinstance(value,int) and not isinstance(value,bool) and value>=0:
                    record[field]=value
                    ledger[budget]+=value-reservation
            choice=(body.get("choices") or [{}])[0]
            record.update(outcome="HTTP_200",finishReason=choice.get("finish_reason"))
            for cost_key in ("cost","total_cost","cost_usd"):
                if isinstance(u.get(cost_key),(int,float)):record["providerReportedCost"]={"field":cost_key,"value":u[cost_key]};break
            if (record["outputTokens"] or 0)>3500 or ledger["inputBudgetCharged"]>480000 or ledger["outputBudgetCharged"]>42000:
                ledger.update(terminal=True,decision="FAIL",stopReason="PROVIDER_REPORTED_BUDGET_OVERRUN")
                raise AssistantProviderError("LIVE_BUDGET_EXHAUSTED")
            return body
        except BaseException as exc:
            record.update(outcome="REQUEST_FAILED",failureCategory=getattr(exc,"code",type(exc).__name__))
            raise
        finally:
            record["latencySeconds"]=round(time.perf_counter()-started,3)
            save()
    def forbidden_compile(*args,**kwargs):raise RuntimeError("Native compilation is forbidden in Phase 4C")
    nebius._request=guarded_transport
    orchestration.NebiusProvider=lambda:NebiusProvider(usage_sink=usage,metadata_sink=metadata)
    cad_worker.compile_batch=forbidden_compile
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user_id]=lambda:ACTOR
    action_started=time.perf_counter()
    try:
        with TestClient(app) as client:
            response=client.post(f"/api/projects/{PROJECT}/experimental-cad/bim-authoring/runs/{prepared['runId']}/advance",json={})
            result=response.json()
            db.expire_all()
            current=db.get(GeneratedFile,prepared["runId"])
            checkpoint=json.loads(PrivateStore().get(PROJECT,current.metadata_json["snapshotHash"]))
            completed=next((c for c in checkpoint["checkpoints"] if c["key"]==key),None)
            action=dict(stage=stage,checkpointKey=key,httpStatus=response.status_code,status=result.get("status"),
                errorCode=result.get("errorCode"),schemaResult="PASS" if completed else "NOT_COMPLETED",
                validationResult="PASS" if completed or result.get("status")=="COMPLETED" else "NOT_COMPLETED",
                checkpointHash=completed["outputHash"] if completed else None,
                attempts=current.metadata_json["attempts"].get(key,0),latencySeconds=round(time.perf_counter()-action_started,3),
                providerMetadata=metadata,completedStages=result.get("completedStages",[]))
            if completed:
                parsed=completed["output"]
                action["validatedCounts"]={k:len(v) for k,v in parsed.items() if isinstance(v,list)}
            ledger["actions"].append(action)
            after={str(r.id):digest(r.document_json) for r in db.query(ModelRevision).filter_by(project_id=PROJECT).all()}
            ledger["modelMutationCount"]=sum(before.get(k)!=v for k,v in after.items())+len(set(before)-set(after))
            ledger["approvalCount"]=len(rows(db,"proposal_approvals",PROJECT))
            ledger["proposalCount"]=len(rows(db,"design_proposal_versions",PROJECT))
            ledger["cadArtifactPublicationCount"]=db.query(GeneratedFile).filter(GeneratedFile.project_id==PROJECT,
                GeneratedFile.file_type.in_(["cad_manifest_v1","cad_review_v1"])).count()
            if ledger["modelMutationCount"] or ledger["approvalCount"] or ledger["cadArtifactPublicationCount"]:
                ledger.update(terminal=True,decision="FAIL",stopReason="UNAUTHORIZED_EFFECT")
            elif result.get("status")=="COMPLETED":
                review=result["proposal"]["review"]
                assert review["finalizationBlocked"] and review["engineeringStatus"]=="UNVERIFIED"
                ledger.update(terminal=True,decision="PASS",proposalId=result["proposal"]["proposal"]["id"],
                    proposalStatus=result["proposal"]["proposal"]["status"],engineeringStatus=review["engineeringStatus"],
                    finalizationBlocked=review["finalizationBlocked"])
            elif response.status_code!=200 or result.get("status")=="FAILED":
                ledger.update(terminal=True,decision="PARTIAL" if checkpoint["checkpoints"] else "FAIL",stopReason=result.get("errorCode") or "ENDPOINT_FAILURE")
            save()
            print(json.dumps(dict(action=action,decision=ledger["decision"],terminal=ledger["terminal"],requests=len(ledger["requests"]),
                inputTokensCharged=ledger["inputBudgetCharged"],outputTokensCharged=ledger["outputBudgetCharged"],
                modelMutationCount=ledger["modelMutationCount"],approvalCount=ledger["approvalCount"],proposalCount=ledger["proposalCount"]),indent=2))
    finally:
        nebius._request=original_transport
        orchestration.NebiusProvider=original_provider
        cad_worker.compile_batch=original_compile
        app.dependency_overrides.clear()
        db.close()


if __name__=="__main__":advance_once()

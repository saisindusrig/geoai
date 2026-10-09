"""Persisted, bounded orchestration. Model output never receives application authority."""
import asyncio
import json
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import ValidationError
from app.domain.stage1 import CivilIntent
from app.domain.assistant_runtime import ProviderResponse
from app.services.ai.provider import AIProvider, NebiusProvider, FixtureProvider, ModelRouter, RoutingMetadata, AssistantProviderError, request_routing_hints
from app.services.assistant.storage import owned_row, rows, table, identity, insert, update, lock_project, now, error
from app.services.assistant.conversations import reject_secrets
from app.services.assistant.policy import evaluate, text_of
from app.services.assistant.context import build_context, compact
from app.services.assistant.tools import ToolContext, execute, describe_tools, LABELS

ACTIVE={"QUEUED","CLASSIFYING","READING_CONTEXT","RUNNING","PROPOSING","VALIDATING"}
from app.services.assistant.prompts import SYSTEM


def event(db,p,run_id,state,label,code=None):
    t=table("assistant_run_events")
    sequence=(db.execute(sa.select(sa.func.max(t.c.sequence)).where(t.c.run_id==run_id)).scalar() or 0)+1
    insert(db,"assistant_run_events",id=identity(run_id,"event",sequence),project_id=p,run_id=run_id,sequence=sequence,
        payload={"state":state,"label":label,"errorCode":code})
    current=owned_row(db,"assistant_runs",p,run_id)
    update(db,"assistant_runs",p,run_id,context_snapshot={**current["context_snapshot"],"progress":label})


def queue_run(db,p,actor,run_id):
    lock_project(db,p)
    run=owned_row(db,"assistant_runs",p,run_id)
    if run["status"]!="WAITING_FOR_INPUT" or run["error_code"]!="ORCHESTRATION_NOT_ENABLED":
        db.commit();return False
    snapshot={**run["context_snapshot"],"queuedAt":now(),"actorId":actor}
    update(db,"assistant_runs",p,run_id,status="QUEUED",error_code=None,context_snapshot=snapshot)
    event(db,p,run_id,"QUEUED","Message saved; preparing assistant…")
    db.commit();return True


def recover(db,p,run):
    queued=run["context_snapshot"].get("queuedAt")
    if run["status"] in ACTIVE and queued and (datetime.now(timezone.utc)-datetime.fromisoformat(queued)).total_seconds()>150:
        lock_project(db,p)
        current=owned_row(db,"assistant_runs",p,run["id"])
        if current["status"] in ACTIVE:
            update(db,"assistant_runs",p,run["id"],status="INTERRUPTED",error_code="RUN_INTERRUPTED")
            event(db,p,run["id"],"INTERRUPTED","Processing was interrupted. Retry uses the original selection.","RUN_INTERRUPTED")
        db.commit()


def retry_run(db,p,actor,run_id,key):
    original=owned_row(db,"assistant_runs",p,run_id);recover(db,p,original)
    lock_project(db,p);original=owned_row(db,"assistant_runs",p,run_id)
    rid=identity(run_id,"retry",key)
    t=table("assistant_runs")
    existing=db.execute(sa.select(t.c.id).where(t.c.id==rid,t.c.project_id==p)).scalar()
    if existing:db.commit();return rid,False
    legacy=original["status"]=="WAITING_FOR_INPUT" and original["error_code"]=="ORCHESTRATION_NOT_ENABLED"
    if original["status"] not in {"FAILED","INTERRUPTED"} and not legacy:error(409,"RUN_NOT_RETRYABLE","Only failed, interrupted or pre-orchestration saved runs can be retried.")
    if any(r["conversation_id"]==original["conversation_id"] and r["status"] in ACTIVE for r in rows(db,"assistant_runs",p)):
        error(409,"RUN_ACTIVE","Another run is active in this conversation.")
    insert(db,"assistant_runs",id=rid,project_id=p,conversation_id=original["conversation_id"],message_id=original["message_id"],retry_of_id=run_id,
        status="QUEUED",context_snapshot={**original["context_snapshot"],"queuedAt":now(),"actorId":actor},error_code=None)
    event(db,p,rid,"QUEUED","Retrying with the original message context…")
    db.commit();return rid,True


async def structured(provider: AIProvider,schema,payload,system=SYSTEM,metadata=None,diagnostics=None):
    request={"schema":schema.model_json_schema(by_alias=True),**payload}
    previous_route=None
    for attempt in range(2):
        try:
            route = ModelRouter().route((metadata or RoutingMetadata(intent="CLASSIFY")).model_copy(update={"retry_state":bool(attempt) or bool(metadata and metadata.retry_state)}))
            if previous_route and previous_route.tier=='FAST' and route.tier=='PRIMARY' and diagnostics is not None:
                diagnostics.append({'event':'MODEL_ESCALATION','fromTier':'FAST','toTier':'PRIMARY','fromModel':previous_route.model,'toModel':route.model,'reason':'FAST_FAILURE'})
            previous_route=route
            return schema.model_validate(await provider.complete(system,request,route))
        except (ValidationError,AssistantProviderError) as exc:
            if isinstance(exc,AssistantProviderError) and exc.code!="INVALID_RESPONSE" and route.tier!='FAST':raise
            if attempt:raise AssistantProviderError("INVALID_RESPONSE") from exc
            # One repair, with no raw invalid response or internal provider text persisted.
            if isinstance(exc,ValidationError) or exc.code=='INVALID_RESPONSE':
                request={**request,"repair":"Previous output did not match this schema. Return one valid JSON object; no extra fields."}


async def process(db,p,run_id,provider=None):
    provider=provider or NebiusProvider()
    if not hasattr(provider,"complete"): provider=FixtureProvider(provider)
    lock_project(db,p);run=owned_row(db,"assistant_runs",p,run_id)
    if run["status"]!="QUEUED":db.commit();return
    update(db,"assistant_runs",p,run_id,status="CLASSIFYING")
    event(db,p,run_id,"CLASSIFYING","Reading request…");db.commit()
    message=owned_row(db,"conversation_messages",p,run["message_id"])
    try:
        async with asyncio.timeout(120):
            preliminary=evaluate(message)
            hints=request_routing_hints(text_of(message))
            routing_diagnostics=[]
            classification_route=RoutingMetadata(intent=preliminary['intent']['kind'],requested_effect=preliminary["allowedEffect"],
                asset_count=len(preliminary["intent"]["assets"]),asset_families=[a.get("assetFamily") or "CUSTOM" for a in preliminary["intent"]["assets"]],
                retry_state=bool(run.get("retry_of_id")),engineering_sensitive=hints['engineering_sensitive'],uncertain=hints['uncertain'] or preliminary['intent']['needsClarification'])
            intent=await structured(provider,CivilIntent,{"message":text_of(message),"understanding":preliminary["understanding"]},SYSTEM+"\nClassify intent and enumerate separate civil assets. Do not execute anything.",metadata=classification_route,diagnostics=routing_diagnostics)
            policy=evaluate(message,intent)
            context=build_context(db,p,message,policy)
            relevant_tools=policy["understanding"]["requiredTools"]
            advertised_tools=describe_tools(relevant_tools)
            routing = RoutingMetadata(intent=policy["intent"]["kind"],requested_effect=policy["allowedEffect"],
                asset_count=len(policy["intent"]["assets"]),asset_families=[a.get("assetFamily") or "CUSTOM" for a in policy["intent"]["assets"]],
                context_size=len(compact(context).encode()),tool_requirement=bool(relevant_tools),
                tool_count=hints['tool_count'],engineering_sensitive=hints['engineering_sensitive'],uncertain=hints['uncertain'] or policy['intent']['needsClarification'],
                complexity="COMPLEX" if len(policy["intent"]["assets"])>1 else "SIMPLE",retry_state=bool(run.get("retry_of_id")) or bool(routing_diagnostics))
            update(db,"assistant_runs",p,run_id,status="RUNNING",context_snapshot={**run["context_snapshot"],"policy":policy})
            event(db,p,run_id,"READING_CONTEXT","Reading site…");db.commit()
            outputs=[];proposal_ids=[];calls=0;cache={}
            tc=ToolContext(p,run["context_snapshot"]["actorId"],run_id,message["id"],policy["allowedEffect"])
            # Editing provenance must be read even if a model skips the required retrieval.
            if policy["intent"]["kind"]=="CHANGE_REQUEST" and message["context"]["selection"]:
                for name in ("get_selected_objects","get_model_revision"):
                    result=execute(db,tc,name,{})
                    cache[(name,compact({}))]=result
                    outputs.append({"name":name,"result":result})
                    calls+=1
                    if result["status"]!="OK":raise AssistantProviderError("EDIT_CONTEXT_UNAVAILABLE")
            for turn in range(9):
                response=await structured(provider,ProviderResponse,{"context":context,"tools":advertised_tools,"toolResults":outputs},metadata=routing,diagnostics=routing_diagnostics)
                if routing_diagnostics:routing=routing.model_copy(update={'retry_state':True})
                if (len(response.tool_calls)>1 or bool(outputs and response.tool_calls)) and ModelRouter().route(routing).tier=='FAST':
                    routing=routing.model_copy(update={'complexity':'COMPLEX'})
                    routing_diagnostics.append({'event':'MODEL_ESCALATION','fromTier':'FAST','toTier':'PRIMARY','reason':'MULTIPLE_TOOLS'})
                    response=await structured(provider,ProviderResponse,{"context":context,"tools":advertised_tools,"toolResults":outputs},metadata=routing,diagnostics=routing_diagnostics)
                if response.tool_calls and not ModelRouter().route(routing).tool_calling_allowed:
                    raise AssistantProviderError("TOOL_POLICY_DENIED")
                if not response.tool_calls:
                    break
                for invocation in response.tool_calls:
                    calls+=1
                    if calls>8:raise AssistantProviderError("TOOL_LIMIT")
                    try:arguments=json.loads(invocation.arguments)
                    except json.JSONDecodeError:raise AssistantProviderError("INVALID_TOOL_ARGUMENTS")
                    if not isinstance(arguments,dict):raise AssistantProviderError("INVALID_TOOL_ARGUMENTS")
                    if invocation.name not in relevant_tools:raise AssistantProviderError("TOOL_POLICY_DENIED")
                    key=(invocation.name,compact(arguments))
                    if key in cache:
                        # Frozen reads and idempotent identical proposal results only; never cross runs.
                        continue
                    if invocation.name in {"create_proposal","revise_proposal"} and proposal_ids:
                        raise AssistantProviderError("PROPOSAL_ALREADY_CREATED")
                    event(db,p,run_id,"RUNNING",LABELS.get(invocation.name,"Reading site…"));db.commit()
                    result=execute(db,tc,invocation.name,arguments)
                    if result["status"]=="OK":cache[key]=result
                    outputs.append({"name":invocation.name,"result":result})
                    if len(outputs)>1:routing=routing.model_copy(update={'complexity':'COMPLEX'})
                    if result.get("data") and isinstance(result["data"],dict) and result["data"].get("proposalVersionId"):
                        proposal_ids.append(result["data"]["proposalVersionId"])
                    if len(compact(outputs).encode())>20000:raise AssistantProviderError("TOOL_RESULT_BUDGET")
            else:raise AssistantProviderError("TOOL_LIMIT")
            # A useful conceptual plan must not disappear merely because the model stops before calling the proposal tool.
            if policy["allowedEffect"]=="PROPOSAL_ONLY" and not proposal_ids and message["context"].get("siteProfileVersionId"):
                assets=policy["intent"]["assets"]
                if len(assets)<=20:
                    arguments={"title":"GeoAI concept proposal","rationale":text_of(message)[:4000],
                        "assets":[{"assetRequestId":a["id"],"assetType":a["assetType"],"name":a["requestedAssetName"],"requirements":a.get("requirements",[])[:30]} for a in assets]}
                    translation=policy["understanding"]["proposedTranslation"]
                    if translation:arguments["translation"]={k:translation[k] for k in ("objectIds","coordinateSystem","deltaM")}
                    parent=message["context"].get("proposalVersionId")
                    if parent:arguments["parentVersionId"]=parent
                    if calls>=8:raise AssistantProviderError("TOOL_LIMIT")
                    result=execute(db,tc,"revise_proposal" if parent else "create_proposal",arguments)
                    if result["status"]=="OK":proposal_ids.append(result["data"]["proposalVersionId"])
                    else:raise AssistantProviderError(result.get("errorCode") or "PROPOSAL_FAILED")
            parts=[]
            if response.text:
                import re
                text=re.sub(r"\b(?:Qwen(?:/[\w.-]+)?|Nebius|ModelRouter)\b","GeoAI",response.text,flags=re.I)
                if text.lstrip().startswith(("{","[")):text="GeoAI prepared a response for review."
                parts.append({"kind":"TEXT","text":text})
            if policy["intent"]["needsClarification"]:
                parts=[{"kind":"QUESTION","questionId":identity(run_id,"question"),"text":policy["intent"]["clarificationQuestion"],"options":[]}]
            elif response.clarification and not proposal_ids:
                parts.append({"kind":"QUESTION","questionId":identity(run_id,"question"),"text":response.clarification.question,"options":response.clarification.options})
            if policy["allowedEffect"]=="PROPOSAL_ONLY" and not message["context"].get("siteProfileVersionId"):
                parts=[{"kind":"TEXT","text":"I can discuss this preliminary concept. A saved site selection and refreshed site profile are needed to save a reviewable proposal. Terrain and engineering data remain unknown; dimensions and materials can be decided later."}]
            if proposal_ids and not parts:parts=[{"kind":"TEXT","text":"Review the concept proposal. Geometry is unchanged; specialist generation and engineering analysis require supported modules."}]
            if policy["intent"]["kind"]=="ANALYSIS_REQUEST":
                # Server-owned notice, independent of the model's presentation.
                parts=[{"kind":"TEXT","text":"GeoAI does not have a validated structural analysis module for this request and cannot determine safe or unsafe. I can help identify the inputs and specialist checks needed."}]
            if policy["allowedEffect"]=="APPROVAL_UI_REQUIRED":
                parts=[{"kind":"TEXT","text":"Review the exact proposal version and use Approve proposal. A chat message cannot approve or build it."}]
            parts.extend({"kind":"PROPOSAL","proposalVersionId":vid} for vid in dict.fromkeys(proposal_ids))
            for eid in response.evidence_ids:owned_row(db,"site_evidence",p,eid)
            if response.evidence_ids:parts.append({"kind":"EVIDENCE","evidenceIds":response.evidence_ids})
            if not parts:raise AssistantProviderError("INVALID_RESPONSE")
            reject_secrets(parts)
            lock_project(db,p)
            if owned_row(db,"assistant_runs",p,run_id)["status"]!="RUNNING":db.rollback();return
            convo=owned_row(db,"project_conversations",p,run["conversation_id"])
            insert(db,"conversation_messages",id=identity(run_id,"reply"),project_id=p,conversation_id=convo["id"],sequence=convo["next_sequence"],
                role="ASSISTANT",parts=parts,context=message["context"],client_request_id=None)
            update(db,"project_conversations",p,convo["id"],next_sequence=convo["next_sequence"]+1)
            current=owned_row(db,'assistant_runs',p,run_id)
            update(db,"assistant_runs",p,run_id,status="COMPLETE",error_code=None,context_snapshot={**current['context_snapshot'],'modelRoutingDiagnostics':routing_diagnostics})
            event(db,p,run_id,"COMPLETE","Response saved.");db.commit()
    except Exception as exc:
        db.rollback()
        code=exc.code if isinstance(exc,AssistantProviderError) else "TIMEOUT" if isinstance(exc,TimeoutError) else exc.detail.get("code","RUN_FAILED") if isinstance(exc,HTTPException) and isinstance(exc.detail,dict) else "RUN_FAILED"
        lock_project(db,p)
        if owned_row(db,"assistant_runs",p,run_id)["status"] in ACTIVE:
            current=owned_row(db,'assistant_runs',p,run_id)
            update(db,"assistant_runs",p,run_id,status="FAILED",error_code=code,context_snapshot={**current['context_snapshot'],'modelRoutingDiagnostics':locals().get('routing_diagnostics',[])})
            event(db,p,run_id,"FAILED","Assistant processing failed. Your message remains saved.",code)
        db.commit()


async def background_run(bind,p,run_id):
    with Session(bind) as db:
        await process(db,p,run_id)

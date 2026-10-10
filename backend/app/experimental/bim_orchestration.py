"""Explicit, checkpointed PRIMARY authoring actions; no background execution."""
import asyncio
import json
import os
from datetime import datetime, timezone
from pydantic import ValidationError
from fastapi import HTTPException
from app.db.models import GeneratedFile
from app.experimental.cad_artifacts import PrivateStore
from app.experimental.cad_contract import digest, encode, Recipe
from app.experimental.bim_authoring import (freeze_owned_context, stage_packet, capabilities,
    validate_plan, expansion_for, prepare_candidate, create_offline_proposal, require,
    AuthoringError, OPERATIONS, FEATURES, PLANNING_SELECTIONS, COST, MANDATORY_UNKNOWNS, unique, stage_context)
from app.domain.bim_authoring import AuthoringIntent, AssemblyPlan, AssemblyExpansion, AssemblyRelationships, AuthoringBundle
from app.services.ai.provider import NebiusProvider, ModelRouter, RoutingMetadata, AssistantProviderError
from app.services.assistant.storage import owned_row, lock_project, identity, now, insert, rows, update
from app.services.assistant.policy import text_of
from app.services.assistant.conversations import reject_secrets

CONTRACTS = {"UNDERSTAND":AuthoringIntent,"PLAN":AssemblyPlan,"EXPAND":AssemblyExpansion,"RELATE":AssemblyRelationships}
TYPE = "bim_authoring_run_v1"
MAX_CALLS = 38  # (UNDERSTAND + PLAN + sixteen EXPAND + RELATE) * two attempts


def authorize(db, project_id, user_id):
    from app.experimental.cad_capability import require_cad, _ids
    require_cad(db, project_id, user_id)
    if (os.environ.get("GEOAI_EXPERIMENTAL_BIM_AUTHORING", "").lower() != "true"
            or user_id not in _ids("GEOAI_BIM_AUTHORING_USER_IDS")
            or project_id not in _ids("GEOAI_BIM_AUTHORING_PROJECT_IDS")):
        raise HTTPException(403, {"code":"BIM_AUTHORING_DISABLED"})


def frozen(db, project_id, user_id, message_id):
    context = freeze_owned_context(db, project_id=project_id, user_id=user_id, message_id=message_id)
    message = owned_row(db, "conversation_messages", project_id, message_id)
    c = message["context"]
    profile = owned_row(db, "site_profile_versions", project_id, c["siteProfileVersionId"])
    selection = owned_row(db, "site_selection_versions", project_id, c["siteSelectionVersionId"])
    assets={ref["assetId"] for ref in c["selection"]}
    if c.get("proposalVersionId"):
        proposal=owned_row(db,"design_proposal_versions",project_id,c["proposalVersionId"])
        for sid in proposal["payload"].get("contract",proposal["payload"]).get("assetSpecificationVersionIds",[]):
            assets.add(owned_row(db,"asset_specification_versions",project_id,sid)["asset_id"])
    items={r["id"]:r for r in rows(db,"project_memory_items",project_id)}
    versions={r["id"]:r for r in rows(db,"project_memory_versions",project_id)}
    current_memory=sorted(r["memory_version_id"] for r in rows(db,"project_memory_states",project_id) if r["status"]=="ACCEPTED"
        and (items[versions[r["memory_version_id"]]["item_id"]]["asset_id"] is None
            or items[versions[r["memory_version_id"]]["item_id"]]["asset_id"] in assets))
    require(current_memory == sorted(c["memoryVersionIds"]),"STALE_ACCEPTED_REQUIREMENTS")
    accepted = [owned_row(db, "project_memory_versions", project_id, mid)["payload"] for mid in c["memoryVersionIds"]]
    snapshot = dict(userRequest=text_of(message), source=context.source.model_dump(mode="json",by_alias=True),
        selectionVersionId=context.selection_version_id, selectionKind=context.selection_kind,
        objectIds=list(context.object_ids), evidenceIds=list(context.evidence_ids),
        acceptedRequirements=accepted, siteProfile=profile["payload"], siteSelection=selection["selection_payload"],
        capabilities=capabilities(), explicitUnknowns=list(MANDATORY_UNKNOWNS), engineeringStatus="UNVERIFIED")
    require(0 < len(snapshot["userRequest"]) <= 4000, "HUMAN_REQUEST_REQUIRED")
    reject_secrets(snapshot)
    require(len(encode(snapshot)) <= 16000, "FROZEN_CONTEXT_BUDGET")
    return context, snapshot, message


def _save(db, row, data, store):
    sha = digest(data)
    store.put(row.project_id, sha, encode(data))
    row.file_url = "cad-private:" + sha
    row.metadata_json = {**row.metadata_json, "snapshotHash":sha}
    db.commit()


def _load(db, project_id, user_id, run_id, store):
    authorize(db, project_id, user_id)
    row = db.query(GeneratedFile).filter_by(id=run_id,project_id=project_id,file_type=TYPE).one_or_none()
    require(row is not None, "AUTHORING_RUN_NOT_FOUND")
    require(row.metadata_json["actorId"] == user_id, "AUTHORING_RUN_OWNER")
    data = json.loads(store.get(project_id,row.metadata_json["snapshotHash"]))
    return row, data


def view(row, data):
    return dict(runId=row.id, status=row.metadata_json["status"], errorCode=row.metadata_json.get("errorCode"),
        completedStages=[c["key"] for c in data["checkpoints"]], calls=row.metadata_json["calls"],
        proposal=data.get("proposal"), durableWorkerAvailable=False,
        executionMode="EXPLICIT_SINGLE_CHECKPOINT_ACTION", productionCadBuild=False)


def start(db, *, project_id, user_id, message_id, request_id, store=None):
    authorize(db, project_id, user_id)
    store = store or PrivateStore()
    context, snapshot, message = frozen(db,project_id,user_id,message_id)
    lock_project(db,project_id)
    existing = next((r for r in db.query(GeneratedFile).filter_by(project_id=project_id,file_type=TYPE).all()
        if r.metadata_json["requestId"] == request_id),None)
    if existing:
        require(existing.metadata_json["messageId"] == message_id and existing.metadata_json["actorId"] == user_id,"REQUEST_ID_REUSED")
        data=json.loads(store.get(project_id,existing.metadata_json["snapshotHash"]))
        require(data["frozenHash"] == digest(snapshot),"STALE_AUTHORING_CONTEXT")
        db.commit()
        return view(existing,data)
    row=GeneratedFile(project_id=project_id,model_revision_id=context.source.revision_id,file_type=TYPE,file_url="",
        metadata_json=dict(actorId=user_id,messageId=message_id,conversationId=message["conversation_id"],requestId=request_id,
            status="READY",calls=0,attempts={},errorCode=None))
    db.add(row)
    data=dict(schemaVersion="bim-authoring-run/1",frozen=snapshot,frozenHash=digest(snapshot),checkpoints=[],proposal=None)
    _save(db,row,data,store)
    return view(row,data)


def read(db, *, project_id,user_id,run_id,store=None):
    row,data=_load(db,project_id,user_id,run_id,store or PrivateStore())
    return view(row,data)


def _state(data):
    outputs={c["key"]:c["output"] for c in data["checkpoints"]}
    if "UNDERSTAND" not in outputs:return "UNDERSTAND","UNDERSTAND",None,outputs
    if "PLAN" not in outputs:return "PLAN","PLAN",None,outputs
    plan=AssemblyPlan.model_validate(outputs["PLAN"])
    for a in plan.assemblies:
        if "EXPAND:"+a.id not in outputs:return "EXPAND","EXPAND:"+a.id,a.id,outputs
    if "RELATE" not in outputs:return "RELATE","RELATE",None,outputs
    return "REVIEW","REVIEW",None,outputs


def _bundle(outputs):
    return AuthoringBundle(intent=outputs["UNDERSTAND"],plan=outputs["PLAN"],
        expansions=[v for k,v in outputs.items() if k.startswith("EXPAND:")],relationships=outputs["RELATE"])


def _validate(stage, result, outputs, context, assembly_id):
    if stage == "UNDERSTAND":
        require(set(result.requested_features).issubset(FEATURES),"UNSUPPORTED_FEATURE")
        require(result.requested_selection_ref in (None,context.selection_version_id),"UNAUTHORIZED_SELECTION_REFERENCE")
        require(set(result.requested_object_refs).issubset(context.object_ids),"UNAUTHORIZED_OBJECT_REFERENCE")
        require(all(context.selection_kind in s.compatible_selection_kinds and
            context.selection_kind in PLANNING_SELECTIONS.get(s.asset_type,("AREA","POINT")) for s in result.systems),"SELECTION_INCOMPATIBLE")
    elif stage == "PLAN":
        validate_plan(outputs["UNDERSTAND"],result)
        unique([a.id for a in result.assets]+[a.id for a in result.assemblies]+[g.id for a in result.assemblies for g in a.groups]
            +[m.id for m in result.materials]+[s.id for s in result.cross_sections])
    elif stage == "EXPAND":
        plan=AssemblyPlan.model_validate(outputs["PLAN"])
        expansion_for(plan,result)
        require(result.assembly_id == assembly_id,"EXPANSION_STAGE_MISMATCH")
        materials={m.id for m in plan.materials}
        sections={s.id:s for s in plan.cross_sections}
        previous=[AssemblyExpansion.model_validate(v) for k,v in outputs.items() if k.startswith("EXPAND:")]
        used={c.id for e in previous for c in e.components} | {a.id for a in plan.assets} | {a.id for a in plan.assemblies} | {
            g.id for a in plan.assemblies for g in a.groups} | {m.id for m in plan.materials} | set(sections)
        for c in result.components:
            require(c.id not in used,"DUPLICATE_IDENTIFIER")
            require(c.material_id in materials,"UNRESOLVED_MATERIAL")
            require(c.recipe.component_id == c.id,"RECIPE_IDENTITY_MISMATCH")
            require(c.recipe.operation in OPERATIONS.get(c.component_type,()),"UNSUPPORTED_COMPONENT_MAPPING")
            require(c.cross_section_id is None or c.cross_section_id in sections,"UNRESOLVED_SECTION")
            section=sections.get(c.cross_section_id)
            params=[*c.parameters,*(section.parameters if section else [])]
            require(all(p.unit == "m" for p in params) and len({p.id for p in params}) == len(params),"METRE_PARAMETERS_REQUIRED")
            if c.component_type in {"SLAB","DECK","BEARING","PLATE"} and c.recipe.operation == "PROFILE_EXTRUSION":
                require(section is not None and section.profile == "RECTANGLE","RECTANGULAR_PROFILE_REQUIRED")
            try:
                Recipe(operation=c.recipe.operation,orientation=c.recipe.orientation,profile=section.profile if section else None,
                    parameters={p.id:p.value for p in params})
            except ValidationError as exc:
                raise AuthoringError("INVALID_RECIPE_DIMENSIONS",[c.id]) from exc
        require(sum(COST[c.recipe.operation] for e in [*previous,result] for c in e.components)<=128,"COMPILATION_BUDGET")
    elif stage == "RELATE":prepare_candidate(_bundle({**outputs,"RELATE":result}),context)


async def advance(db, *, project_id,user_id,run_id,provider=None,store=None,recover_interrupted=False):
    """One bounded request/action. Retry consumes the stage's second attempt."""
    store=store or PrivateStore()
    lock_project(db,project_id)
    row,data=_load(db,project_id,user_id,run_id,store)
    metadata=dict(row.metadata_json)
    if metadata["status"] == "COMPLETED":
        db.commit();return view(row,data)
    try:
        context,snapshot,message=frozen(db,project_id,user_id,metadata["messageId"])
        require(digest(snapshot)==data["frozenHash"],"STALE_AUTHORING_CONTEXT")
    except (ValueError,HTTPException) as exc:
        if isinstance(exc,HTTPException) and exc.status_code in {403,404}:raise
        row.metadata_json={**metadata,"status":"FAILED","errorCode":getattr(exc,"code","STALE_CONTEXT")}
        db.commit()
        return view(row,data)
    if metadata["status"] == "RUNNING":
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(metadata["claimedAt"])).total_seconds()
        require(recover_interrupted and age>150,"AUTHORING_ACTION_ACTIVE")
        metadata["status"]="RETRYABLE"
        metadata["errorCode"]="INTERRUPTED_CALL_OUTCOME_UNKNOWN"
    require(metadata["status"] in {"READY","RETRYABLE"},"AUTHORING_RUN_NOT_RETRYABLE")
    stage,key,assembly_id,outputs=_state(data)
    if stage == "REVIEW":
        # All model checkpoints are complete; proposal persistence is idempotent.
        try:
            prepare_candidate(_bundle(outputs),context)
            result=create_offline_proposal(db,project_id=project_id,user_id=user_id,message_id=metadata["messageId"],
                request_id=identity("bim-orchestration",run_id),data=_bundle(outputs),store=store)
            lock_project(db,project_id)
            mid=identity("bim-orchestration-review",run_id)
            if not any(m["id"] == mid for m in rows(db,"conversation_messages",project_id)):
                sequence=max((m["sequence"] for m in rows(db,"conversation_messages",project_id) if m["conversation_id"]==message["conversation_id"]),default=0)+1
                insert(db,"conversation_messages",id=mid,project_id=project_id,conversation_id=message["conversation_id"],sequence=sequence,
                    role="ASSISTANT",parts=[{"kind":"TEXT","text":"Experimental BIM proposal saved for review. Connections and clearances remain unresolved; engineering is unverified."},
                        {"kind":"PROPOSAL","proposalVersionId":result["proposal"]["id"]}],context=message["context"],client_request_id=None)
                update(db,"project_conversations",project_id,message["conversation_id"],next_sequence=sequence+1)
            data={**data,"proposal":result}
            row.metadata_json={**metadata,"status":"COMPLETED","errorCode":None}
            _save(db,row,data,store)
        except Exception:
            db.rollback()
            raise
        return view(row,data)
    attempts=metadata["attempts"].get(key,0)
    require(attempts<2 and metadata["calls"]<MAX_CALLS,"AUTHORING_ATTEMPT_BUDGET")
    packet=stage_packet(stage,request_text=snapshot["userRequest"],intent=outputs.get("UNDERSTAND"),plan=outputs.get("PLAN"),
        assembly_id=assembly_id,expansions=[v for k,v in outputs.items() if k.startswith("EXPAND:")])
    packet["trustedContext"]=stage_context(stage,snapshot,data["frozenHash"])
    if attempts:packet["repair"]={"code":metadata["errorCode"],"instruction":"Return valid data for this stage. Do not fabricate engineering facts or silently change structural dimensions. Unsupported requirements must fail explicitly."}
    system_instruction=packet.pop("instruction")
    require(len(encode(packet))<=40000,"STAGE_CONTEXT_BUDGET")
    route=ModelRouter().route(RoutingMetadata(intent="DESIGN_REQUEST",requested_effect="PROPOSAL_ONLY",complexity="COMPLEX",
        engineering_sensitive=True,context_size=len(encode(packet)),retry_state=bool(attempts),tool_requirement=False))
    require(route.tier == "PRIMARY" and not route.tool_calling_allowed,"PRIMARY_ROUTE_REQUIRED")
    row.metadata_json={**metadata,"status":"RUNNING","claimedAt":now(),"calls":metadata["calls"]+1,
        "attempts":{**metadata["attempts"],key:attempts+1}}
    db.commit()
    selected_provider=provider or NebiusProvider()
    try:
        async with asyncio.timeout(route.timeout):
            output=await selected_provider.complete(system_instruction,packet,route)
        if isinstance(output,str):
            require(len(output.encode())<=50000,"STAGE_OUTPUT_BUDGET")
            output=json.loads(output)
        require(isinstance(output,dict) and len(encode(output))<=50000,"STAGE_OUTPUT_BUDGET")
        reject_secrets(output)
        result=CONTRACTS[stage].model_validate(output)
        _validate(stage,result,outputs,context,assembly_id)
        # Recheck authority after provider latency, before saving a valid checkpoint.
        current,current_snapshot,_=frozen(db,project_id,user_id,metadata["messageId"])
        require(digest(current_snapshot)==data["frozenHash"],"STALE_AUTHORING_CONTEXT")
        data={**data,"checkpoints":[*data["checkpoints"],dict(key=key,output=result.model_dump(mode="json",by_alias=True),
            outputHash=digest(result),routeTier=route.tier,model=route.model)]}
        row.metadata_json={**row.metadata_json,"status":"READY","errorCode":None}
        _save(db,row,data,store)
    except asyncio.CancelledError:
        db.rollback()
        row.metadata_json={**row.metadata_json,"status":"RETRYABLE" if attempts==0 else "FAILED","errorCode":"CANCELLED"}
        db.commit()
        raise
    except (ValidationError,ValueError,TimeoutError,HTTPException) as exc:
        code=(exc.code if isinstance(exc,(AuthoringError,AssistantProviderError)) else
            "PROVIDER_TIMEOUT" if isinstance(exc,TimeoutError) else "MALFORMED_JSON" if isinstance(exc,json.JSONDecodeError) else
            "STALE_CONTEXT" if isinstance(exc,HTTPException) else "INVALID_STAGE_SCHEMA" if isinstance(exc,ValidationError) else "INVALID_STAGE_DATA")
        provider_metadata=getattr(selected_provider,"metadata_sink",[])
        if code == "INVALID_RESPONSE" and provider_metadata and provider_metadata[-1].get("failure_class") == "LIKELY_TRUNCATED":
            code="OUTPUT_TRUNCATED"
        retryable=code in {"INVALID_RESPONSE","OUTPUT_TRUNCATED","MALFORMED_JSON","INVALID_STAGE_SCHEMA","PROVIDER_TIMEOUT","TIMEOUT","UNAVAILABLE"}
        row.metadata_json={**row.metadata_json,"status":"RETRYABLE" if attempts==0 and retryable else "FAILED","errorCode":code}
        db.commit()
    except Exception:
        db.rollback()
        row.metadata_json={**row.metadata_json,"status":"FAILED","errorCode":"CHECKPOINT_STORAGE_FAILURE"}
        db.commit()
        raise
    return view(row,data)

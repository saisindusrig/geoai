"""Allow-listed internal tools; authority comes only from the server ToolContext."""
import json
import time
import sqlalchemy as sa
from dataclasses import dataclass
from pydantic import ValidationError
from fastapi import HTTPException
from app.domain.assistant_runtime import NoArguments, TerrainArguments, NearbyArguments, ProposalToolArguments, ProposalReference, ProposalRequest
from app.services.assistant.storage import owned_row, rows, identity, insert, update, error, digest
from app.services.assistant.proposals import ProposalService
from app.services.assistant.context import compact


@dataclass(frozen=True)
class ToolContext:
    project_id: int
    actor_id: int
    run_id: str
    message_id: str
    allowed_effect: str


from app.services.assistant.tool_contracts import SCHEMAS, envelope, describe_tools
LABELS={"sample_terrain":"Inspecting terrain…","get_selected_objects":"Reading selected objects…",
    "get_constraints":"Checking constraints…","create_proposal":"Creating proposal…","revise_proposal":"Creating proposal…","validate_proposal":"Validating proposal…"}



def execute(db,context,name,arguments):
    start=time.monotonic()
    run=owned_row(db,"assistant_runs",context.project_id,context.run_id)
    if run["message_id"]!=context.message_id:return envelope("DENIED",code="CONTEXT_MISMATCH")
    message=owned_row(db,"conversation_messages",context.project_id,context.message_id)
    attempts=[r for r in rows(db,"assistant_tool_executions",context.project_id) if r["run_id"]==context.run_id]
    if len(attempts)>=8:return envelope("DENIED",code="TOOL_LIMIT",limitations=["Maximum eight tools per run."])
    execution_id=identity(context.run_id,"tool",len(attempts)+1)
    # Reject without retaining attacker-controlled arguments or arbitrary tool names.
    def deny(code):
        result=envelope("DENIED",code=code)
        insert(db,"assistant_tool_executions",id=execution_id,project_id=context.project_id,run_id=context.run_id,
            tool_name=name if name in SCHEMAS else "DENIED_TOOL",tool_version="1",arguments={},status="DENIED",result=result,error_code=code)
        db.commit();return result
    if name not in SCHEMAS:return deny("TOOL_NOT_ALLOWED")
    try:
        parsed=SCHEMAS[name].model_validate(arguments)
    except ValidationError:
        return deny("INVALID_TOOL_ARGUMENTS")
    from app.services.assistant.conversations import reject_secrets
    try:reject_secrets(arguments)
    except HTTPException:return deny("SENSITIVE_CONTENT")
    insert(db,"assistant_tool_executions",id=execution_id,project_id=context.project_id,run_id=context.run_id,
        tool_name=name,tool_version="1",arguments=parsed.model_dump(mode="json",by_alias=True),status="RUNNING")
    db.commit()
    sqlite_connection=None
    try:
        if db.bind.dialect.name=="postgresql":
            db.execute(sa.text("SET LOCAL statement_timeout = '10s'"))
        elif db.bind.dialect.name=="sqlite":
            sqlite_connection=db.connection().connection.driver_connection
            sqlite_connection.set_progress_handler(lambda: int(time.monotonic()-start>10),1000)
        result=_execute(db,context,message,name,parsed,execution_id)
        if time.monotonic()-start>10:result=envelope("UNAVAILABLE",code="TOOL_TIMEOUT",limitations=["Tool exceeded its execution budget."])
        if len(compact(result).encode())>12000:result=envelope("PARTIAL",code="RESULT_SIZE_LIMIT",limitations=["Result too large; no partial facts were silently represented as complete."])
    except HTTPException as exc:
        db.rollback();result=envelope("DENIED" if exc.status_code in {403,404} else "UNAVAILABLE",code=exc.detail.get("code","TOOL_FAILED") if isinstance(exc.detail,dict) else "TOOL_FAILED")
    except Exception:
        db.rollback();result=envelope("UNAVAILABLE",code="TOOL_FAILED",limitations=["Retrieval failed; absence cannot be inferred."])
    finally:
        if sqlite_connection is not None:sqlite_connection.set_progress_handler(None,0)
    update(db,"assistant_tool_executions",context.project_id,execution_id,status=result["status"],result=result,error_code=result["errorCode"])
    db.commit();return result


def _execute(db,tc,message,name,args,execution_id):
    c=message["context"];p=tc.project_id
    profile=owned_row(db,"site_profile_versions",p,c["siteProfileVersionId"]) if c.get("siteProfileVersionId") else None
    if name in {"create_proposal","revise_proposal"}:
        if tc.allowed_effect!="PROPOSAL_ONLY":return envelope("DENIED",code="READ_ONLY_POLICY")
        from app.domain.assistant_design_input import GenericProposalArguments
        if isinstance(args,GenericProposalArguments):
            from app.services.assistant.design_flow import normalize_proposal
            args=ProposalToolArguments.model_validate(normalize_proposal(db,p,message,args.model_dump(mode='json',by_alias=True)))
        if any((a.building_spec or a.ai3d_design) and (a.building_spec or a.ai3d_design).input_source!="PREVIEW_ASSUMPTION" for a in args.assets):
            return envelope("DENIED",code="USER_SOURCE_UNVERIFIED",limitations=["Tool-proposed visualization dimensions require explicit preview assumptions; user/site provenance cannot be invented."])
        if name=="revise_proposal" and not args.parent_version_id:return envelope("DENIED",code="PARENT_REQUIRED")
        if args.parent_version_id:
            parent=owned_row(db,"design_proposal_versions",p,args.parent_version_id)
            source=owned_row(db,"conversation_messages",p,parent["payload"]["request"]["messageId"])
            if source["conversation_id"]!=message["conversation_id"]:return envelope("DENIED",code="PROPOSAL_SCOPE")
        request=ProposalRequest(client_request_id=identity(tc.message_id,"proposal-tool",digest(args.model_dump(mode="json"))),message_id=tc.message_id,**args.model_dump())
        result=ProposalService().create(db,p,tc.actor_id,request)
        return envelope(data={"proposalVersionId":result["id"],"status":result["status"],"validation":result["validation"]},limitations=["Proposal only; model geometry is unchanged."])
    if name=="validate_proposal":
        result=ProposalService().read(db,p,args.proposal_version_id)
        return envelope(data={"status":result["status"],"validation":result["validation"]},limitations=["Concept contract validation only, not engineering analysis."])
    if name=="get_selected_objects":
        if len(c["selection"])>100:return envelope("PARTIAL",data=c["selection"][:100],limitations=["Object limit 100; remaining objects omitted."])
        return envelope(data=c["selection"])
    if name=="get_model_revision":
        if not c.get("modelRevisionId"):return envelope("UNAVAILABLE",code="NO_MODEL")
        model=owned_row(db,"model_revisions",p,c["modelRevisionId"])
        selected={r["objectId"] for r in c["selection"]}
        components=[r for r in model["document_json"].get("components",[]) if str(r["id"]) in selected][:100]
        grounding=[]
        for component in components:
            original=next((r for r in rows(db,"model_object_lineage",p) if r["model_revision_id"]==model["id"] and r["object_id"]==component["id"]),None)
            if original:
                spec=owned_row(db,"asset_specification_versions",p,original["specification_version_id"])
                asset=owned_row(db,"asset_instances",p,original["asset_id"])
                grounding.append({"targetComponentId":component["id"],"expectedComponentHash":digest(component),"assetId":original["asset_id"],
                    "assetType":asset["asset_type"],"buildingId":component.get("metadata",{}).get("buildingId"),
                    "sourceModelRevisionId":str(model["id"]),"sourceSpecificationVersionId":spec["id"],"sourceSpecificationHash":spec["content_hash"],
                    "openingDefinitions":spec["payload"].get("buildingSpec",{}).get("openings",[])})
        return envelope(data={"id":str(model["id"]),"components":components,"patchGrounding":grounding},limitations=["Only attached saved objects are included; patch geometry may have additional host dependencies."])
    if name=="get_project_requirements":
        return envelope(data=[owned_row(db,"project_memory_versions",p,mid)["payload"] for mid in c["memoryVersionIds"]])
    if name=="get_constraints":
        found=rows(db,"constraint_datasets",p)
        return envelope("PARTIAL" if found else "UNAVAILABLE",data=found[:50],limitations=["Available project constraints only; completeness is not established."])
    if name=="get_checks":
        found=[r for r in rows(db,"engineering_analyses",p) if str(r["model_revision_id"])==c.get("modelRevisionId") and r["analysis_type"]!="PROPOSAL_CONCEPT"]
        return envelope("PARTIAL" if found else "UNAVAILABLE",data=[{"type":r["analysis_type"],"status":r["status"],"result":r["result_json"]} for r in found[-5:]],limitations=["Recorded checks are not a structural safety certification."])
    if not profile:return envelope("UNAVAILABLE",code="NO_SITE_PROFILE",limitations=["Refresh site facts before querying terrain or context."])
    value=profile["payload"]
    refs=[{"kind":"SITE_PROFILE","id":profile["id"],"contentHash":profile["content_hash"]}]
    if name=="get_site_profile":
        from app.services.assistant.ai3d_validation import site_summary
        return envelope(data={**value,"siteAnalysisSummary":site_summary(db,p,c)},dependencies=refs)
    if name=="get_site_readiness":return envelope(data=owned_row(db,"engineering_analyses",p,value["readinessAssessmentId"])["result_json"],dependencies=refs)
    if name=="get_active_terrain":return envelope(data=value["terrain"],dependencies=refs,limitations=["Terrain captured with this profile; no fallback activation."])
    if name=="sample_terrain":
        samples=owned_row(db,"site_sample_sets",p,value["terrain"]["sampleSetId"])["payload"]["samples"][:args.sample_count]
        return envelope("PARTIAL" if any(s["elevation"]["value"] is None for s in samples) else "OK",data=samples,dependencies=refs,
            limitations=["Bounded samples from the captured immutable profile; no interpolation of missing elevations."])
    if name=="query_nearby_context":
        nearby=value["nearby"][args.category]
        return envelope("PARTIAL" if nearby["features"] else "UNAVAILABLE",data=nearby,dependencies=refs,evidence=nearby["evidenceIds"],
            limitations=["Retained context covers at most the profile's 500 m query. Radius does not trigger a new lookup. Missing features do not prove absence."])
    return envelope("DENIED",code="TOOL_NOT_ALLOWED")

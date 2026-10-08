"""Persistent typed messages; no provider invocation or implicit project memory."""
import re
import sqlalchemy as sa
from app.domain.site_workspace import MessageContext
from app.services.assistant.storage import digest, identity, insert, lock_project, now, owned_row, rows, table, update, error, utc_timestamp


def reject_secrets(parts):
    # Do not persist known credential formats or explicit credential assignments.
    secret=re.compile(r"\bsk-[A-Za-z0-9_-]{16,}|\bv1\.[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{30,}|(?:api[_ -]?key|password|secret|authorization)\s*[:=]\s*\S{8,}",re.I)
    if secret.search(str(parts)):
        error(422,"SENSITIVE_CONTENT","Remove credentials before saving this message or memory item.")
    if isinstance(parts,dict) and str(parts.get("key","")).strip().lower().replace("-","_") in {"api_key","password","secret","authorization","token"}:
        error(422,"SENSITIVE_CONTENT","Credentials cannot be project memory.")


def resolve_objects(db,project_id,revision_id,object_ids):
    if not revision_id:
        if object_ids:
            error(422,"SAVED_REVISION_REQUIRED","Save the selected objects before attaching them to a message.")
        return [],None
    revision=owned_row(db,"model_revisions",project_id,revision_id)
    components={str(c["id"]):c for c in revision["document_json"].get("components",[])}
    if any(i not in components for i in object_ids):
        error(422,"UNSAVED_SELECTION","A selected object is absent from the pinned saved revision. Save it or clear the selection.")
    refs=[]
    lineage=table("model_object_lineage")
    for oid in dict.fromkeys(object_ids):
        original=db.execute(sa.select(lineage).where(lineage.c.project_id==project_id,lineage.c.model_revision_id==revision["id"],lineage.c.object_id==oid)).mappings().first()
        if original:
            asset_id=original["asset_id"];component_id=original["component_id"]
        else:
            # Identity adapter only: no model geometry or revision is written.
            asset_id=identity("legacy-scenario",project_id,revision["design_scenario_id"])
            t=table("asset_instances")
            if not db.execute(sa.select(t.c.id).where(t.c.id==asset_id)).first():
                insert(db,"asset_instances",id=asset_id,project_id=project_id,asset_type="LEGACY_MODEL",name="Existing model",lifecycle="EXISTING")
            component_id=oid
        refs.append({"assetId":asset_id,"objectId":oid,"modelRevisionId":str(revision_id),"componentId":component_id,"geometryHash":digest(components[oid])})
    return refs,revision


class ConversationService:
    def create(self,db,project_id,actor_id,request):
        lock_project(db,project_id)
        cid=identity("conversation",project_id,actor_id,request.client_request_id)
        t=table("project_conversations")
        existing=db.execute(sa.select(t).where(t.c.id==cid)).mappings().first()
        if existing and existing["title"]!=request.title:
            error(409,"IDEMPOTENCY_CONFLICT","This request key was used for a different conversation.")
        if not existing:
            insert(db,"project_conversations",id=cid,project_id=project_id,title=request.title,created_by=actor_id)
        db.commit()
        return self.output(owned_row(db,"project_conversations",project_id,cid))

    def output(self,row):
        return {"id":row["id"],"projectId":str(row["project_id"]),"title":row["title"],"createdBy":str(row["created_by"]),
                "createdAt":utc_timestamp(row["created_at"]),"archivedAt":utc_timestamp(row["archived_at"]),"nextSequence":row["next_sequence"]}

    def list(self,db,project_id):
        t=table("project_conversations")
        return [self.output(dict(r)) for r in db.execute(sa.select(t).where(t.c.project_id==project_id).order_by(t.c.created_at,t.c.id).limit(100)).mappings()]

    def submit(self,db,project_id,actor_id,conversation_id,request,*,orchestrate=False):
        lock_project(db,project_id)
        conversation=owned_row(db,"project_conversations",project_id,conversation_id)
        if conversation["archived_at"]:
            error(409,"CONVERSATION_ARCHIVED","This conversation is archived.")
        mid=identity(conversation_id,request.client_request_id)
        t=table("conversation_messages")
        existing=db.execute(sa.select(t).where(t.c.id==mid)).mappings().first()
        request_hash=digest(request.model_dump(mode="json"))
        run_id=identity(mid,"run")
        if existing:
            run=owned_row(db,"assistant_runs",project_id,run_id)
            if run["context_snapshot"]["requestHash"]!=request_hash:
                error(409,"IDEMPOTENCY_CONFLICT","This message key was used with different content or context.")
            db.commit()
            return {"messageId":mid,"runId":run_id,"status":run["status"]}
        active=table("assistant_runs")
        if db.execute(sa.select(active.c.id).where(active.c.conversation_id==conversation_id,
                active.c.status.in_(["QUEUED","CLASSIFYING","READING_CONTEXT","PROPOSING","VALIDATING","RUNNING"]))).first():
            error(409,"RUN_ACTIVE","A run is already processing in this conversation.")
        parts=[part.model_dump(mode="json",by_alias=True) for part in request.parts]
        reject_secrets(parts)
        c=request.context
        selection,revision=resolve_objects(db,project_id,c.model_revision_id,c.selected_object_ids)
        if c.scenario_id:
            owned_row(db,"design_scenarios",project_id,c.scenario_id)
            if revision and str(revision["design_scenario_id"])!=c.scenario_id:
                error(422,"SCENARIO_MISMATCH","Model revision belongs to another scenario.")
        if c.site_selection_version_id:
            owned_row(db,"site_selection_versions",project_id,c.site_selection_version_id)
        if c.site_profile_version_id:
            profile=owned_row(db,"site_profile_versions",project_id,c.site_profile_version_id)
            if c.site_selection_version_id!=profile["selection_version_id"]:
                error(422,"SELECTION_MISMATCH","The site profile belongs to another selection version.")
        if c.proposal_version_id:
            owned_row(db,"design_proposal_versions",project_id,c.proposal_version_id)
        for part in parts:
            kind=part["kind"]
            if kind=="PROPOSAL":
                owned_row(db,"design_proposal_versions",project_id,part["proposalVersionId"])
            elif kind=="EVIDENCE":
                for eid in part["evidenceIds"]:
                    owned_row(db,"site_evidence",project_id,eid)
            elif kind=="ASSUMPTION":
                m=owned_row(db,"project_memory_versions",project_id,part["assumptionVersionId"])
                item=owned_row(db,"project_memory_items",project_id,m["item_id"])
                if item["kind"]!="ASSUMPTION":
                    error(422,"INVALID_ASSUMPTION","This reference is not an assumption.")
            elif kind=="ATTACHMENT":
                attachment=owned_row(db,"generated_files",project_id,part["attachmentId"])
                metadata=attachment["metadata_json"] or {}
                if metadata.get("sha256")!=part["contentHash"] or metadata.get("media_type")!=part["mediaType"] or not 0<metadata.get("size_bytes",0)<=10_000_000:
                    error(422,"ATTACHMENT_UNVERIFIED","Attachment needs verified type, size and digest metadata before it can be attached.")
        assets={r["assetId"] for r in selection}
        if c.proposal_version_id:
            proposal=owned_row(db,"design_proposal_versions",project_id,c.proposal_version_id)
            for sid in proposal["payload"].get("contract",proposal["payload"]).get("assetSpecificationVersionIds",[]):
                assets.add(owned_row(db,"asset_specification_versions",project_id,sid)["asset_id"])
        items={r["id"]:r for r in rows(db,"project_memory_items",project_id)}
        versions={r["id"]:r for r in rows(db,"project_memory_versions",project_id)}
        memories=sorted(r["memory_version_id"] for r in rows(db,"project_memory_states",project_id) if r["status"]=="ACCEPTED"
            and (items[versions[r["memory_version_id"]]["item_id"]]["asset_id"] is None or items[versions[r["memory_version_id"]]["item_id"]]["asset_id"] in assets))
        context=MessageContext(selection=selection,site_selection_version_id=c.site_selection_version_id,site_profile_version_id=c.site_profile_version_id,
            model_revision_id=c.model_revision_id,scenario_id=c.scenario_id or (str(revision["design_scenario_id"]) if revision else None),
            proposal_version_id=c.proposal_version_id,memory_version_ids=memories,editor_dirty=c.editor_dirty).model_dump(mode="json",by_alias=True)
        insert(db,"conversation_messages",id=mid,project_id=project_id,conversation_id=conversation_id,sequence=conversation["next_sequence"],
            role="USER",parts=parts,context=context,client_request_id=request.client_request_id)
        insert(db,"assistant_runs",id=run_id,project_id=project_id,conversation_id=conversation_id,message_id=mid,
            status="QUEUED" if orchestrate else "WAITING_FOR_INPUT",error_code=None if orchestrate else "ORCHESTRATION_NOT_ENABLED",
            context_snapshot={"context":context,"requestHash":request_hash,**({"queuedAt":now(),"actorId":actor_id} if orchestrate else {})})
        insert(db,"assistant_run_events",id=identity(run_id,1),project_id=project_id,run_id=run_id,sequence=1,
            payload={"state":"QUEUED" if orchestrate else "WAITING_FOR_INPUT","label":"Message saved; preparing assistant…" if orchestrate else "Message saved. AI processing is not enabled in this stage.","errorCode":None if orchestrate else "ORCHESTRATION_NOT_ENABLED"})
        update(db,"project_conversations",project_id,conversation_id,next_sequence=conversation["next_sequence"]+1)
        db.commit()
        return {"messageId":mid,"runId":run_id,"status":"QUEUED" if orchestrate else "WAITING_FOR_INPUT"}

    def messages(self,db,project_id,conversation_id,before=None,limit=50):
        owned_row(db,"project_conversations",project_id,conversation_id)
        t=table("conversation_messages")
        query=sa.select(t).where(t.c.project_id==project_id,t.c.conversation_id==conversation_id)
        if before is not None:
            query=query.where(t.c.sequence<before)
        result=list(db.execute(query.order_by(t.c.sequence.desc()).limit(limit+1)).mappings())
        more=len(result)>limit
        result=result[:limit]
        candidates=[r for r in rows(db,"assistant_runs",project_id) if r["conversation_id"]==conversation_id]
        replaced={r["retry_of_id"] for r in candidates if r["retry_of_id"]}
        runs={r["message_id"]:r for r in candidates if r["id"] not in replaced}
        return {"messages":[{"id":r["id"],"conversationId":conversation_id,"sequence":r["sequence"],"role":r["role"],"parts":r["parts"],
            "context":r["context"],"createdAt":utc_timestamp(r["created_at"]),"clientRequestId":r["client_request_id"],"status":"COMPLETE",
            "run":self.run_output(runs[r["id"]]) if r["id"] in runs else None} for r in reversed(result)],
            "nextBefore":result[-1]["sequence"] if more else None}

    def run_output(self,row):
        return {"id":row["id"],"status":row["status"],"errorCode":row["error_code"],"messageId":row["message_id"],"conversationId":row["conversation_id"],
            "progress":row["context_snapshot"].get("progress") or {"QUEUED":"Preparing assistant…","CLASSIFYING":"Reading request…","RUNNING":"Reading site and selected objects…"}.get(row["status"]),
            "capabilities":row["context_snapshot"].get("policy",{}).get("capabilities",[])}

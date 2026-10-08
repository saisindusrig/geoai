"""Explicit project memory lifecycle; chat text never calls this service implicitly."""
import sqlalchemy as sa
from app.db.models import EngineeringAuditEvent
from app.services.assistant.storage import digest, identity, insert, lock_project, now, owned_row, rows, table, update, error, utc_timestamp
from app.services.assistant.conversations import reject_secrets


def conflicts(a,b):
    if a["kind"]!="REQUIREMENT" or b["kind"]!="REQUIREMENT" or a["key"].strip().casefold()!=b["key"].strip().casefold():
        return False
    a,b=a["constraint"],b["constraint"]
    if a.get("unit")!=b.get("unit"):
        return True  # No implicit unit conversion or reconciliation.
    def accepts(c,v):
        op=c["operator"];target=c["value"]
        if op=="EQ": return type(v)==type(target) and v==target
        if op=="IN": return v in target
        if isinstance(v,bool) or not isinstance(v,(int,float)): return False
        return v>=target if op=="MIN" else v<=target
    for fixed,other in ((a,b),(b,a)):
        if fixed["operator"] in {"EQ","IN"}:
            values=fixed["value"] if fixed["operator"]=="IN" else [fixed["value"]]
            return not any(accepts(other,v) for v in values)
    return (a["operator"]=="MIN" and b["operator"]=="MAX" and a["value"]>b["value"]) or (b["operator"]=="MIN" and a["operator"]=="MAX" and b["value"]>a["value"])


class MemoryService:
    def list(self,db,project_id,kind=None,status=None,asset_id=None):
        items={r["id"]:r for r in rows(db,"project_memory_items",project_id)}
        states={r["memory_version_id"]:r for r in rows(db,"project_memory_states",project_id)}
        result=[]
        accepts={r.before_json["versionId"]:r for r in db.query(EngineeringAuditEvent).filter_by(project_id=project_id,action="memory.accept").order_by(EngineeringAuditEvent.id)}
        for row in rows(db,"project_memory_versions",project_id):
            item=items[row["item_id"]];state=states[row["id"]]
            if (kind and item["kind"]!=kind) or (status and state["status"]!=status) or (asset_id and item["asset_id"]!=asset_id): continue
            acceptance=accepts.get(row["id"])
            result.append({"id":item["id"],"versionId":row["id"],"version":row["version"],"projectId":str(project_id),"assetId":item["asset_id"],
                "status":state["status"],"contentHash":row["content_hash"],"supersedesVersionId":row["supersedes_id"],
                "actorId":str(state["actor_id"]) if state["actor_id"] else None,
                "acceptedBy":str(acceptance.actor_user_id) if acceptance else None,"acceptedAt":utc_timestamp(acceptance.created_at) if acceptance else None,
                **{k:v for k,v in row["payload"].items() if k!="requestHash"}})
        return sorted(result,key=lambda r:(r["createdAt"],r["versionId"]))

    def create(self,db,project_id,actor_id,request,item_id=None):
        lock_project(db,project_id)
        content=request.content.model_dump(mode="json",by_alias=True)
        reject_secrets(content)
        if request.asset_id:
            owned_row(db,"asset_instances",project_id,request.asset_id)
        for mid in request.source_message_ids: owned_row(db,"conversation_messages",project_id,mid)
        for eid in request.evidence_ids: owned_row(db,"site_evidence",project_id,eid)
        if content.get("selectedAlternativeId"): owned_row(db,"proposal_alternatives",project_id,content["selectedAlternativeId"])
        iid=item_id or identity("memory",project_id,actor_id,request.client_request_id)
        vid=identity(iid,request.client_request_id)
        request_hash=digest(request.model_dump(mode="json"))
        existing=db.execute(sa.select(table("project_memory_versions")).where(table("project_memory_versions").c.id==vid)).mappings().first()
        if existing:
            if existing["payload"]["requestHash"]!=request_hash:
                error(409,"IDEMPOTENCY_CONFLICT","Memory request key already has different content.")
            db.commit()
            return next(r for r in self.list(db,project_id) if r["versionId"]==vid)
        supersedes=None;number=1
        if item_id:
            item=owned_row(db,"project_memory_items",project_id,item_id)
            if item["kind"]!=content["kind"] or item["asset_id"]!=request.asset_id:
                error(422,"MEMORY_SCOPE_IMMUTABLE","Memory kind and asset scope cannot change between versions.")
            versions=[r for r in self.list(db,project_id) if r["id"]==item_id]
            latest=max(versions,key=lambda r:r["version"])
            if latest["version"]!=request.expected_version:
                error(409,"STALE_MEMORY","Memory has a newer version. Reload before editing.")
            number=latest["version"]+1
            accepted=next((r for r in versions if r["status"]=="ACCEPTED"),None)
            supersedes=(accepted or latest)["versionId"]
        else:
            insert(db,"project_memory_items",id=iid,project_id=project_id,kind=content["kind"],asset_id=request.asset_id)
        payload={"content":content,"sourceMessageIds":request.source_message_ids,"evidenceIds":request.evidence_ids,
                 "proposedBy":str(actor_id),"createdAt":now(),"requestHash":request_hash}
        insert(db,"project_memory_versions",id=vid,project_id=project_id,item_id=iid,version=number,payload=payload,content_hash=digest(payload),supersedes_id=supersedes)
        insert(db,"project_memory_states",id=identity(vid,"state"),project_id=project_id,memory_version_id=vid,status="PROPOSED",actor_id=actor_id)
        db.commit()
        return next(r for r in self.list(db,project_id) if r["versionId"]==vid)

    def transition(self,db,project_id,actor_id,item_id,version,action,expected_status):
        lock_project(db,project_id)
        owned_row(db,"project_memory_items",project_id,item_id)
        all_memory=self.list(db,project_id)
        target=next((r for r in all_memory if r["id"]==item_id and r["version"]==version),None)
        if not target: error(404,"NOT_FOUND","Memory version not found")
        status="ACCEPTED" if action=="accept" else "REJECTED"
        if target["status"]==status:
            db.commit();return target
        if target["status"]!=expected_status or target["status"]!="PROPOSED":
            error(409,"STALE_MEMORY","Only a proposed version can be accepted or rejected.")
        if status=="ACCEPTED" and version!=max(r["version"] for r in all_memory if r["id"]==item_id):
            error(409,"STALE_MEMORY","Review the newest proposed memory version.")
        if status=="ACCEPTED":
            collision=[r["versionId"] for r in all_memory if r["id"]!=item_id and r["status"]=="ACCEPTED"
                and (r["assetId"] is None or target["assetId"] is None or r["assetId"]==target["assetId"])
                and conflicts(target["content"],r["content"])]
            if collision:
                from fastapi import HTTPException
                raise HTTPException(409,{"code":"MEMORY_CONFLICT","message":"Accepted requirements conflict. Revise or explicitly supersede the earlier item.","conflictingVersionIds":collision})
            for old in all_memory:
                if old["id"]==item_id and old["status"] in {"ACCEPTED","PROPOSED"} and old["versionId"]!=target["versionId"]:
                    update(db,"project_memory_states",project_id,identity(old["versionId"],"state"),status="SUPERSEDED",actor_id=actor_id)
                    db.add(EngineeringAuditEvent(project_id=project_id,actor_user_id=actor_id,action="memory.superseded",before_json={"versionId":old["versionId"],"status":old["status"]},after_json={"replacementVersionId":target["versionId"]}))
        update(db,"project_memory_states",project_id,identity(target["versionId"],"state"),status=status,actor_id=actor_id)
        db.add(EngineeringAuditEvent(project_id=project_id,actor_user_id=actor_id,action=f"memory.{action}",before_json={"versionId":target["versionId"],"status":target["status"]},after_json={"status":status}))
        db.commit()
        return next(r for r in self.list(db,project_id) if r["versionId"]==target["versionId"])

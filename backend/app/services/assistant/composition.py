"""Project-owned relational composition and fail-closed patch preflight."""
import sqlalchemy as sa
from app.core.asset_families import asset_definition
from app.services.assistant.storage import owned_row,rows,table,identity,digest,insert,lock_project,error
from app.services.assistant.specialists import ADAPTERS
from app.db.models import ModelRevision


def save_relationship(db,project_id,request):
    lock_project(db,project_id)
    owned_row(db,"asset_instances",project_id,request.from_asset_id)
    owned_row(db,"asset_instances",project_id,request.to_asset_id)
    if request.from_asset_id==request.to_asset_id:error(422,"SELF_RELATIONSHIP","An asset cannot relate to itself.")
    rid=identity("relationship-version",project_id,request.client_request_id)
    value=request.model_dump(mode="json",by_alias=True)
    existing=db.execute(sa.select(table("asset_relationships")).where(table("asset_relationships").c.id==rid)).mappings().first()
    if existing:
        if existing["payload"]["requestHash"]!=digest(value):error(409,"IDEMPOTENCY_CONFLICT","Relationship request key was reused.")
        db.commit();return dict(existing)
    relationship_id=request.relationship_id or identity(project_id,"relationship",request.client_request_id)
    previous=[r for r in rows(db,"asset_relationships",project_id) if r["relationship_id"]==relationship_id]
    latest=max(previous,key=lambda r:r["version"]) if previous else None
    if request.relationship_id and not latest:error(404,"NOT_FOUND","Relationship not found in this project.")
    if latest and request.expected_version!=latest["version"]:error(409,"STALE_RELATIONSHIP","Relationship has a newer version.")
    if latest and (latest["from_asset_id"],latest["to_asset_id"])!=(request.from_asset_id,request.to_asset_id):error(422,"IMMUTABLE_ENDPOINTS","Create a new relationship for different assets.")
    insert(db,"asset_relationships",id=rid,project_id=project_id,relationship_id=relationship_id,version=latest["version"]+1 if latest else 1,
        from_asset_id=request.from_asset_id,to_asset_id=request.to_asset_id,kind=request.kind,payload={"schemaVersion":"composition-edge/1","requestHash":digest(value)})
    db.commit();return owned_row(db,"asset_relationships",project_id,rid)


def project_composition(db,project_id):
    assets=rows(db,"asset_instances",project_id)
    edges={}
    for row in rows(db,"asset_relationships",project_id):
        if row["relationship_id"] not in edges or edges[row["relationship_id"]]["version"]<row["version"]:edges[row["relationship_id"]]=row
    return {"assets":[{"id":a["id"],"name":a["name"],**asset_definition(a["asset_type"])} for a in assets],"relationships":list(edges.values())}


def check_patch(db,project_id,patch,registry=ADAPTERS):
    base=owned_row(db,"model_revisions",project_id,patch.base_model_revision_id)
    current=db.query(ModelRevision).filter_by(project_id=project_id,design_scenario_id=base["design_scenario_id"]).order_by(ModelRevision.id.desc()).first()
    original={str(c["id"]):c for c in base["document_json"].get("components",[])}
    components={str(c["id"]):c for c in current.document_json.get("components",[])}
    if patch.target_component_id not in original:error(404,"NOT_FOUND","Patch target is not in the base revision.")
    for cid in patch.affected_component_ids:
        if cid not in original:error(422,"INVALID_AFFECTED_COMPONENT","Affected components must belong to the base revision.")
    if hasattr(patch.parameters,"specification_version_id"):
        owned_row(db,"asset_specification_versions",project_id,patch.parameters.specification_version_id)
    if digest(original[patch.target_component_id])!=patch.expected_component_hash or digest(components.get(patch.target_component_id))!=patch.expected_component_hash or any(digest(original[cid])!=digest(components.get(cid)) for cid in patch.affected_component_ids):
        return {"status":"STALE","code":"REBASE_REQUIRED","applicable":False}
    adapter=registry.resolve(patch.asset_type)
    if not adapter or patch.parameters.operation not in adapter.metadata.patch_operations:
        return {"status":"UNSUPPORTED","code":"PATCH_ADAPTER_UNAVAILABLE","applicable":False}
    return {"status":"SUPPORTED","code":"REVIEW_AND_APPROVAL_REQUIRED","applicable":False}

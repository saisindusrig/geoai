"""Approved patch execution using existing immutable revision persistence."""
from copy import deepcopy
from app.domain.building_patch import BuildingPatch
from app.db.models import User, ModelRevision
from app.services.assistant.storage import rows, identity, insert, now
from app.services.assistant.building_patch import SavedBuildingPatchContext
from app.api.routes.model_revisions import persist_revision, RevisionCreate

class BuildingPatchExecutor:
    def execute(self, db, project_id, version_id, view, spec_row):
        return _execute(db,project_id,version_id,view,spec_row)

def execute(db, project_id, version_id, view, spec_row):
    return BuildingPatchExecutor().execute(db,project_id,version_id,view,spec_row)

def _execute(db, project_id, version_id, view, spec_row):
    from app.services.assistant.proposals import ProposalService
    service = ProposalService()
    patch = BuildingPatch.model_validate(spec_row["payload"]["buildingPatch"])
    from app.services.assistant.specialists import ADAPTERS
    adapter = ADAPTERS.resolve(spec_row["payload"]["assetType"])
    if not adapter or patch.operations[0].parameters.operation_type not in adapter.metadata.patch_operations:
        from app.services.assistant.storage import error
        error(422,"PATCH_CAPABILITY_UNAVAILABLE","This adapter does not support the requested patch operation.")
    preview = adapter.apply_patch(SavedBuildingPatchContext(db, project_id), patch)
    service.assert_build_current(db, project_id, version_id, patch.source_model_revision_id)
    approval = next(r for r in rows(db,"proposal_approvals",project_id) if r["proposal_version_id"] == version_id)
    provenance = {"patchId":spec_row["id"],"patchVersion":spec_row["version"],"patchOperationId":patch.operations[0].operation_id,
        "sourceModelRevisionId":patch.source_model_revision_id,"patchProposalVersionId":version_id,"patchApprovalId":approval["id"],"executedAt":now()}
    document = preview["document"]
    for component in document["components"]:
        if component["id"] in preview["affectedComponentIds"]:
            component["metadata"] = {**component.get("metadata",{}),"patchProvenance":provenance}
    document["metadata"]["buildingPatchProposalVersionId"] = version_id
    result = persist_revision(project_id,preview["source"]["design_scenario_id"],RevisionCreate(
        base_revision_id=int(patch.source_model_revision_id),document=document,source="ai_edit"),
        db,db.get(User,approval["approved_by"]),commit=False,
        lineage_updates={oid:provenance for oid in preview["affectedComponentIds"]})
    revision = db.get(ModelRevision,result["id"])
    existing = {r["object_id"] for r in rows(db,"model_object_lineage",project_id) if r["model_revision_id"] == revision.id}
    for component in document["components"]:
        if component["id"] not in preview["affectedComponentIds"] or component["id"] in existing: continue
        original = preview["lineage"]
        fields = {key:original[key] for key in ("asset_id","proposal_version_id","specification_version_id","generator_id","generator_version")}
        payload = deepcopy(original["payload"]);payload.update(component["metadata"])
        payload["patchProvenance"] = {**provenance,"resultingModelRevisionId":revision.id}
        payload.setdefault("generationModelRevisionId", int(patch.source_model_revision_id))
        insert(db,"model_object_lineage",id=identity(revision.id,component["id"]),project_id=project_id,model_revision_id=revision.id,
               object_id=component["id"],component_id=component["id"],payload=payload,**fields)
    service.transition(db,project_id,version_id,"BUILT")
    db.commit()
    return {"modelRevisionId":str(revision.id),"status":"BUILT"}

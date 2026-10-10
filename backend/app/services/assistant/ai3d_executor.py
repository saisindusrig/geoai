"""One generic builder for all semantic roles. No asset-specific design logic."""
from copy import deepcopy
from app.domain.ai3d import AI3DDesign
from app.domain.specialist_metadata import AdapterMetadata
from app.services.assistant.ai3d_geometry import compile_geometry
from app.services.assistant.ai3d_validation import AI3DDesignValidator, validate_saved_design
from app.services.assistant.storage import error, identity, insert, owned_row, now
from app.db.models import ModelRevision, Project, DesignScenario, User, ModelPlacement
from app.services.design.editable_model import geometry_spec_to_document


class Generic3DExecutor:
    metadata=AdapterMetadata("generic-3d","1","CUSTOM",frozenset({"AI3D_DESIGN"}),
        frozenset({"DISCUSS","PLAN","PROPOSE","GENERATE","VALIDATE_GEOMETRY"}),"ai-3d-design/1",frozenset())
    specification_schema=AI3DDesign
    def can_handle(self,asset_type):return asset_type.upper()=="AI3D_DESIGN"
    def requirements_to_specification(self,requirements,context):return AI3DDesign.model_validate(requirements)
    def validate_specification(self,specification):return AI3DDesignValidator().validate(specification)
    def generate_preview(self,specification):return self.generate(specification)
    def generate(self,specification,summary=None):
        validation=AI3DDesignValidator().validate(specification,summary)
        if validation["issues"]:raise ValueError("INVALID_AI3D_DESIGN")
        return compile_geometry(specification)[0]
    def validate_geometry(self,geometry,specification):
        result=self.validate_specification(specification)
        if geometry!=self.generate(specification):return {**result,"issues":[{"code":"GEOMETRY_MISMATCH"}]}
        return result
    def apply_patch(self,model,patch):raise ValueError("GENERIC_PATCH_UNAVAILABLE")


def execute_approved(db,project_id,version_id,view,row):
    from app.services.assistant.proposals import ProposalService
    from app.api.routes.model_revisions import persist_revision, RevisionCreate
    spec=AI3DDesign.model_validate(row["payload"]["ai3dDesign"])
    context=view["content"]["context"]
    summary,validation=validate_saved_design(db,project_id,context,spec)
    try:geometry=Generic3DExecutor().generate(spec,summary)
    except Exception:error(422,"GENERIC_GENERATION_FAILED","The complete design could not be built; no revision was created.")
    source=spec.source_model_revision_id
    base=db.get(ModelRevision,int(source)) if source else None
    scenario=db.get(DesignScenario,int(view["content"]["contract"]["sourceScenarioId"]))
    project=db.get(Project,project_id)
    document=deepcopy(base.document_json) if base else geometry_spec_to_document(project,scenario,{"objects":[]})
    generated=geometry_spec_to_document(project,scenario,geometry)["components"]
    for raw,component in zip(geometry["objects"],generated):
        component["id"]=raw["semantic"]["id"];component["quantity"]={"included":False}
        component["metadata"]={**raw["semantic"],"assetId":row["asset_id"],"specificationId":row["id"],"specificationHash":row["content_hash"],
            "specificationVersion":row["version"],"designVersion":row["version"],"designHash":row["content_hash"],
            "generatorId":"generic-3d","generatorVersion":"1","approvalId":identity(version_id,"approval"),
            "siteAnalysisSummary":summary,**row["payload"]["provenance"]}
    if view["content"]["contract"].get("parentVersionId"):
        document["components"]=[c for c in document["components"] if c.get("metadata",{}).get("assetId")!=row["asset_id"]]
    ids={c["id"] for c in document["components"]}
    if ids.intersection(c["id"] for c in generated):error(422,"COMPONENT_ID_CONFLICT","Use a distinct design ID; unrelated saved objects cannot be overwritten.")
    document["components"].extend(generated)
    document.update(project_id=project_id,scenario_id=scenario.id,project_type=project.project_type)
    document["origin"]=summary["origin"]
    placement=db.query(ModelPlacement).filter_by(project_id=project_id,model_revision_id=base.id).first() if base else None
    placement_fields={c.name:getattr(placement,c.name) for c in ModelPlacement.__table__.columns if c.name not in {"id","model_revision_id","created_at","updated_at"}} if placement else {
        "project_id":project_id,"anchor_longitude":summary["origin"]["lng"],"anchor_latitude":summary["origin"]["lat"],"anchor_elevation":None,
        "anchor_heading_deg":0,"elevation_offset":0,"placement_mode":"GROUND_RELATIVE","height_reference":"TERRAIN","elevation_resolution":"UNKNOWN",
        "anchor_locked":True,"legacy_placement":False,"local_transform_json":{},"elevation_provenance_json":{"source":"UNKNOWN","anchorSource":"SELECTED_GEOMETRY_CENTROID","selectionVersionId":context["siteSelectionVersionId"]}}
    placement_fields["placement_state"]="REVIEW_REQUIRED"
    document["metadata"]={**document.get("metadata",{}),"ai3dProposalVersionId":version_id,"ai3dDesignId":spec.design_id,
        "ai3dValidation":validation,"referencePlane":"LOCAL_VISUAL_REFERENCE","generatedAt":now(),"elevation_known":summary["origin"]["elevation_m"] is not None,
        "placementProvenance":placement_fields,"ai3dRelationships":[r.model_dump(mode="json",by_alias=True) for r in spec.relationships]}
    if not base:document["structural_layout"]={"rule_preset":{},"assumptions":["Preliminary geometry; no engineering validation."]}
    approval=owned_row(db,"proposal_approvals",project_id,identity(version_id,"approval"))
    ProposalService().assert_build_current(db,project_id,version_id,source)
    result=persist_revision(project_id,scenario.id,RevisionCreate(base_revision_id=int(source) if source else None,document=document,source="ai_generate"),
        db,db.get(User,approval["approved_by"]),commit=False)
    revision=db.get(ModelRevision,result["id"])
    updated=deepcopy(revision.document_json)
    generated_ids={component["id"] for component in generated}
    for component in updated["components"]:
        if component["id"] in generated_ids:component["metadata"]["generationModelRevisionId"]=revision.id
    revision.document_json=updated
    if not base:db.add(ModelPlacement(model_revision_id=revision.id,**placement_fields))
    else:
        new_placement=db.query(ModelPlacement).filter_by(model_revision_id=revision.id).one()
        new_placement.placement_state="REVIEW_REQUIRED"
    for component in generated:
        meta={**component["metadata"],"generationModelRevisionId":revision.id}
        insert(db,"model_object_lineage",id=identity(revision.id,component["id"]),project_id=project_id,asset_id=row["asset_id"],
            proposal_version_id=version_id,specification_version_id=row["id"],model_revision_id=revision.id,object_id=component["id"],component_id=component["id"],
            generator_id="generic-3d",generator_version="1",payload=meta)
    scenario.status="completed";ProposalService().transition(db,project_id,version_id,"BUILT");db.commit()
    return {"modelRevisionId":str(revision.id),"status":"BUILT"}

"""Atomic approved-spec execution into the existing editable revision pipeline."""
from copy import deepcopy
from shapely import affinity
from shapely.geometry import Polygon
from app.db.models import ModelRevision, ModelPlacement, Project, DesignScenario
from app.services.assistant.storage import lock_project,owned_row,error,digest,identity,insert,now
from app.services.assistant.specialists import ADAPTERS,ExecutionRouter
from app.services.design.editable_model import geometry_spec_to_document,validate_document


def build(db,project_id,version_id):
    try:return _build(db,project_id,version_id)
    except Exception:
        db.rollback()
        raise


def _build(db,project_id,version_id):
    from app.services.assistant.proposals import ProposalService
    lock_project(db,project_id)
    owned_row(db,"design_proposal_versions",project_id,version_id)
    for revision in db.query(ModelRevision).filter_by(project_id=project_id,source="building_specialist").all():
        if revision.document_json.get("metadata",{}).get("buildingProposalVersionId")==version_id:
            db.commit();return {"modelRevisionId":str(revision.id),"status":"BUILT"}
    for revision in db.query(ModelRevision).filter_by(project_id=project_id).all():
        if revision.document_json.get("metadata",{}).get("buildingPatchProposalVersionId") == version_id:
            db.commit();return {"modelRevisionId":str(revision.id),"status":"BUILT"}
    svc=ProposalService();view=svc.assert_build_current(db,project_id,version_id)
    routing=ExecutionRouter().route_approved(db,project_id,version_id)
    if not routing["canBuildAll"]:error(409,"GENERATION_UNAVAILABLE","Every asset must have a supported specialist adapter.")
    specification_ids = view["content"]["contract"]["assetSpecificationVersionIds"]
    if len(specification_ids) == 1:
        specification = owned_row(db,"asset_specification_versions",project_id,specification_ids[0])
        if specification["payload"].get("buildingPatch"):
            from app.services.assistant.building_patch_execution import execute
            return execute(db,project_id,version_id,view,specification)
    context=view["content"]["context"];source=context.get("modelRevisionId")
    base=db.get(ModelRevision,int(source)) if source else None
    if source and (not base or base.project_id!=project_id):error(422,"INVALID_SOURCE_REVISION","Source model revision is unavailable.")
    scenario=db.get(DesignScenario,int(view["content"]["contract"]["sourceScenarioId"]))
    project=db.get(Project,project_id);generated=[];specs=[]
    selected=owned_row(db,"site_selection_versions",project_id,context["siteSelectionVersionId"])["selection_payload"]["selection"]
    if selected["kind"]!="AREA":error(422,"SITE_AREA_REQUIRED","Building V1 requires a saved area selection.")
    placement=db.query(ModelPlacement).filter_by(project_id=project_id,model_revision_id=base.id).first() if base else None
    if base and not placement:error(422,"PLACEMENT_REQUIRED","Accept a geographic anchor before generating against an existing model.")
    if not base:
        from shapely.geometry import shape
        anchor=shape(selected["geometry"]).centroid
        placement=ModelPlacement(project_id=project_id,anchor_longitude=anchor.x,anchor_latitude=anchor.y,anchor_elevation=None,
            anchor_heading_deg=0,elevation_offset=0,placement_mode="GROUND_RELATIVE",height_reference="TERRAIN",placement_state="REVIEW_REQUIRED",
            elevation_resolution="UNKNOWN",anchor_locked=True,legacy_placement=False,local_transform_json={},
            elevation_provenance_json={"source":"UNKNOWN","anchorSource":"SELECTED_AREA_CENTROID","selectionVersionId":context["siteSelectionVersionId"]})
    from app.services.ai.building_plan import local_plot
    frame={"origin":{"lng":placement.anchor_longitude,"lat":placement.anchor_latitude,"heading_deg":placement.anchor_heading_deg},
        "placement":{c.name:getattr(placement,c.name) for c in ModelPlacement.__table__.columns}}
    plot=local_plot({**frame,"boundary":selected["geometry"]})
    if project.boundary_geojson:plot=plot.intersection(local_plot({**frame,"boundary":project.boundary_geojson}))
    for sid in view["content"]["contract"]["assetSpecificationVersionIds"]:
        row=owned_row(db,"asset_specification_versions",project_id,sid);raw=row["payload"]
        adapter=ADAPTERS.resolve(raw["assetType"])
        if not adapter or not raw.get("buildingSpec"):error(409,"GENERATION_UNAVAILABLE","A validated typed BuildingSpec is required; generic concepts cannot generate.")
        spec=adapter.specification_schema.model_validate(raw["buildingSpec"])
        result=adapter.validate_specification(spec)
        if result["issues"]:error(422,"INVALID_BUILDING_SPEC",result)
        footprint=affinity.rotate(Polygon(spec.footprint),spec.orientation,origin=(0,0))
        if not plot.covers(footprint):error(422,"FOOTPRINT_OUTSIDE_SITE","The approved footprint must fit the selected plot.")
        try:geometry=adapter.generate(spec)
        except Exception:error(422,"BUILDING_GENERATION_FAILED","Building generation failed; no revision was created.")
        if adapter.validate_geometry(geometry,spec)["issues"]:error(422,"INVALID_GENERATED_GEOMETRY","The generated model did not pass deterministic validation.")
        converted=geometry_spec_to_document(project,scenario,geometry)["components"]
        for obj,component in zip(geometry["objects"],converted):
            semantic=obj["semantic"];component["id"]=semantic["id"]
            component["quantity"]={"included":False}
            component["metadata"]={**semantic,"assetId":row["asset_id"],"specificationId":sid,"specificationVersion":row["version"],"specificationHash":row["content_hash"],
                "generatorId":adapter.metadata.id,"approvalId":identity(version_id,"approval"),**raw["provenance"]}
            generated.append(component)
        specs.append({"id":sid,"version":row["version"],"hash":row["content_hash"]})
    existing=deepcopy(base.document_json) if base else geometry_spec_to_document(project,scenario,{"objects":[]})
    parent=view["content"]["contract"].get("parentVersionId")
    if parent and existing.get("metadata",{}).get("buildingProposalVersionId")==parent:
        asset_ids={c["metadata"]["assetId"] for c in generated}
        # Regeneration replaces only this approved asset in a new snapshot; the old revision remains immutable.
        existing["components"]=[c for c in existing["components"] if c.get("metadata",{}).get("assetId") not in asset_ids]
    ids={c["id"] for c in existing["components"]}
    if len({c["id"] for c in generated})!=len(generated) or ids.intersection(c["id"] for c in generated):error(422,"COMPONENT_ID_CONFLICT","Use a distinct building ID; previous objects are never overwritten.")
    existing["components"].extend(generated)
    existing.update(project_id=project_id,scenario_id=scenario.id,project_type=project.project_type)
    existing["origin"]={"lng":placement.anchor_longitude,"lat":placement.anchor_latitude,
        "elevation_m":placement.anchor_elevation,"heading_deg":placement.anchor_heading_deg}
    existing["metadata"]={**existing.get("metadata",{}),"buildingProposalVersionId":version_id,"buildingSpecifications":specs,
        "sourceModelRevisionId":source,"adapterVersion":"1","generatedAt":now(),"generatedComponentIds":[c["id"] for c in generated],
        "elevation_known":placement.anchor_elevation is not None,"referencePlane":"LOCAL_VISUAL_REFERENCE",
        "placementProvenance":{c.name:getattr(placement,c.name) for c in ModelPlacement.__table__.columns if c.name not in {"created_at","updated_at"}}}
    existing["structural_layout"]={"assumptions":["Conceptual geometry only; no engineering adequacy or code validation."],"rule_preset":{}}
    errors=validate_document(existing,project_id=project_id,scenario_id=scenario.id,project_type=project.project_type)
    if errors:error(422,"MODEL_CONTRACT_INVALID",errors)
    svc.assert_build_current(db,project_id,version_id,source)
    number=max([r.revision_number for r in db.query(ModelRevision).filter_by(project_id=project_id,design_scenario_id=scenario.id).all()] or [0])+1
    revision=ModelRevision(project_id=project_id,design_scenario_id=scenario.id,revision_number=number,document_json=existing,source="building_specialist")
    db.add(revision);db.flush()
    fields={c.name:getattr(placement,c.name) for c in ModelPlacement.__table__.columns if c.name not in {"id","created_at","updated_at","model_revision_id"}}
    fields["placement_state"]="REVIEW_REQUIRED";db.add(ModelPlacement(model_revision_id=revision.id,**fields))
    from app.services.assistant.storage import rows
    retained={c["id"] for c in existing["components"]}-{c["id"] for c in generated}
    for lineage in rows(db,"model_object_lineage",project_id):
        if base and lineage["model_revision_id"]==base.id and lineage["object_id"] in retained:
            fields={key:lineage[key] for key in ("asset_id","proposal_version_id","specification_version_id","object_id","component_id","generator_id","generator_version","payload")}
            insert(db,"model_object_lineage",id=identity(revision.id,lineage["object_id"]),project_id=project_id,model_revision_id=revision.id,**fields)
    for component in generated:
        meta=component["metadata"]
        insert(db,"model_object_lineage",id=identity(revision.id,component["id"]),project_id=project_id,asset_id=meta["assetId"],
            proposal_version_id=version_id,specification_version_id=meta["specificationId"],model_revision_id=revision.id,object_id=component["id"],component_id=component["id"],generator_id="building-concept",generator_version="1",payload=meta)
    scenario.status="completed"
    scenario.design_output_json={**(scenario.design_output_json or {}),"editable_model_revision_id":revision.id,
        "editable_model_revision_number":number,"building_proposal_version_id":version_id,"concept_only":True}
    svc.transition(db,project_id,version_id,"BUILT");db.commit()
    return {"modelRevisionId":str(revision.id),"status":"BUILT"}

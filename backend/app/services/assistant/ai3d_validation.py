"""Geometry validation and saved-context gates, never engineering validation."""
import math
from shapely.geometry import Polygon, LineString, Point, shape
from pydantic import ValidationError
from app.domain.ai3d import AI3DDesign
from app.db.models import ModelRevision, ModelPlacement, Project
from app.services.assistant.storage import owned_row, error
from app.services.ai.building_plan import local_plot
from app.services.assistant.ai3d_geometry import compile_geometry, footprint


def site_summary(db, project_id, context):
    selected = owned_row(db,"site_selection_versions",project_id,context["siteSelectionVersionId"])
    selection = selected["selection_payload"]["selection"]
    if selection["kind"] == "ENDPOINTS":
        geometry = {"type":"LineString","coordinates":[selection["endpointA"]["coordinates"],selection["endpointB"]["coordinates"]]}
    else: geometry = selection["geometry"]
    base = db.get(ModelRevision,int(context["modelRevisionId"])) if context.get("modelRevisionId") else None
    if base and base.project_id != project_id: error(404,"NOT_FOUND","Source revision not found.")
    placement = db.query(ModelPlacement).filter_by(project_id=project_id,model_revision_id=base.id).first() if base else None
    if base and not placement: error(422,"PLACEMENT_REQUIRED","Save an accepted geographic anchor first.")
    anchor = shape(geometry).centroid
    origin = {"lng":placement.anchor_longitude if placement else anchor.x,"lat":placement.anchor_latitude if placement else anchor.y,
              "heading_deg":placement.anchor_heading_deg if placement else 0,"elevation_m":placement.anchor_elevation if placement else None}
    local = local_plot({"origin":origin,"boundary":geometry})
    profile = owned_row(db,"site_profile_versions",project_id,context["siteProfileVersionId"])
    return {"selectionReference":{"id":selected["id"],"version":selected["version"],"contentHash":selected["content_hash"]},
            "selectionKind":selection["kind"],"localGeometry":local.__geo_interface__,"coordinateFrame":"LOCAL_ENU","origin":origin,
            "frameSource":"SAVED_MODEL_PLACEMENT" if placement else "SELECTED_GEOMETRY_CENTROID",
            "referencePlane":"LOCAL_VISUAL_REFERENCE","sourceModelRevisionId":context.get("modelRevisionId"),
            "profileReference":{"id":profile["id"],"version":profile["version"],"contentHash":profile["content_hash"]},
            "facts":{k:profile["payload"][k] for k in ("dimensions","terrain","relief","constraints") if k in profile["payload"]},
            "unknowns":["soil","groundwater","structuralCapacity","designLoads","engineeringApproval"],
            "limitations":["Local reference coordinates are derived from saved selection and placement. Preview Z does not establish ground elevation.","No terrain-following generation or slope-aware optimization in V1."]}


class AI3DDesignValidator:
    def validate(self, raw, summary=None, boundary=None):
        try:
            spec = AI3DDesign.model_validate(raw)
            geometry,resolved = compile_geometry(spec)
        except ValidationError as exc:
            return {"status":"INVALID_DESIGN","issues":[{"code":"SCHEMA_VALIDATION_FAILED","path":".".join(map(str,e["loc"])),"message":e["msg"]} for e in exc.errors(include_input=False)]}
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            return {"status":"INVALID_DESIGN","issues":[{"code":str(exc).strip("'"),"path":"objects","message":"Invalid primitive composition."}]}
        issues=[]; checks=[]
        def issue(code,path): issues.append({"code":code,"path":path,"message":code.replace("_"," ")})
        if spec.input_source=="PREVIEW_ASSUMPTION" and not spec.assumptions: issue("PREVIEW_ASSUMPTION_REQUIRED","assumptions")
        if spec.terrain_dependencies: issue("TERRAIN_PLACEMENT_UNSUPPORTED","terrainDependencies")
        known=set(resolved)|{s.id for s in spec.systems}
        all_ids=[r.id for r in spec.relationships]+[c.id for c in spec.constraints]
        if len(set(all_ids))!=len(all_ids) or set(all_ids)&known: issue("DUPLICATE_REFERENCE_ID","relationships")
        for index,rel in enumerate(spec.relationships):
            if rel.from_id not in known or rel.to_id not in known: issue("UNRESOLVED_RELATIONSHIP",f"relationships.{index}")
        if summary:
            if spec.site_selection.model_dump(mode="json",by_alias=True)!=summary["selectionReference"]:issue("SITE_REFERENCE_MISMATCH","siteSelection")
            if spec.source_model_revision_id!=summary["sourceModelRevisionId"]:issue("SOURCE_REVISION_MISMATCH","sourceModelRevisionId")
            if summary["selectionKind"]=="AREA" and any(not shape(summary["localGeometry"]).buffer(1e-7).covers(footprint(raw)) for raw in geometry["objects"]):issue("OUTSIDE_SELECTED_AREA","objects")
        if boundary is not None and any(not boundary.buffer(1e-7).covers(footprint(raw)) for raw in geometry["objects"]):issue("OUTSIDE_PROJECT_BOUNDARY","objects")
        for index,constraint in enumerate(spec.constraints):
            code=None; kind=constraint.kind; target=resolved.get(constraint.target_id); reference=resolved.get(constraint.reference_id)
            solids=[raw for raw in geometry["objects"] if raw["semantic"]["sourceObjectId"]==constraint.target_id or raw["semantic"]["systemId"]==constraint.target_id]
            if constraint.target_id not in known: code="UNRESOLVED_CONSTRAINT_TARGET"
            elif kind=="WITHIN_AREA":
                if not summary or summary["selectionKind"]!="AREA":code="AREA_CONTEXT_REQUIRED"
                elif not solids or any(not shape(summary["localGeometry"]).buffer(1e-7).covers(footprint(raw)) for raw in solids):code="OUTSIDE_SELECTED_AREA"
            elif kind=="FOLLOW_ROUTE":
                if not summary or summary["selectionKind"] not in {"ROUTE","ENDPOINTS","CROSSING"}:code="ROUTE_CONTEXT_REQUIRED"
                elif not target or target["kind"] not in {"PATH","OFFSET"}:code="PATH_REFERENCE_REQUIRED"
                else:
                    points=list(shape(summary["localGeometry"]).coords)
                    if len(points)!=len(target["reference"]) or any(math.dist(a[:2],b[:2])>.001 for a,b in zip(points,target["reference"])):code="ROUTE_MISMATCH"
            elif kind in {"START_AT","END_AT"}:
                if not target or target["kind"] not in {"PATH","OFFSET"} or not reference or reference["kind"]!="POINT":code="INVALID_ENDPOINT_REFERENCE"
                elif math.dist(target["reference"][0 if kind=="START_AT" else -1],reference["reference"])>.001:code="ENDPOINT_MISMATCH"
            elif kind=="AVOID_AREA":
                if not reference or reference["kind"]!="POLYGON" or not solids:code="INVALID_AVOID_REFERENCE"
                elif any(footprint(raw).intersects(Polygon([p[:2] for p in reference["reference"]])) for raw in solids):code="AVOID_AREA_VIOLATION"
            else:code="UNSUPPORTED_CONSTRAINT"
            checks.append({"id":constraint.id,"kind":kind,"status":"SATISFIED" if code is None else "UNSUPPORTED" if code=="UNSUPPORTED_CONSTRAINT" else "FAILED"})
            if code:issue(code,f"constraints.{index}")
        return {"status":"INVALID_DESIGN" if issues else "DESIGN_VALID","geometryStatus":"GEOMETRY_INVALID" if issues else "GEOMETRY_VALID",
                "engineeringStatus":"UNVALIDATED","issues":issues,"constraintChecks":checks,"componentCount":len(geometry["objects"]),
                "relationshipStatus":"RECORDED_NOT_ENGINEERING_VALIDATED"}


def validate_saved_design(db, project_id, context, spec):
    summary=site_summary(db,project_id,context)
    current=db.query(ModelRevision).filter_by(project_id=project_id)
    if context.get("scenarioId"): current=current.filter_by(design_scenario_id=int(context["scenarioId"]))
    latest=current.order_by(ModelRevision.id.desc()).first()
    if (str(latest.id) if latest else None)!=context.get("modelRevisionId"):error(409,"STALE_DESIGN","Source revision changed; submit a new proposal.")
    if context.get("editorDirty"):error(409,"UNSAVED_MODEL","Save manual edits before proposing geometry.")
    project=db.get(Project,project_id)
    boundary=local_plot({"origin":summary["origin"],"boundary":project.boundary_geojson}) if project.boundary_geojson else None
    result=AI3DDesignValidator().validate(spec,summary,boundary)
    if result["issues"]:error(422,"INVALID_AI3D_DESIGN",result)
    return summary,result

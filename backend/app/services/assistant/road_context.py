"""Saved route grounding in the project's existing engineering frame."""
import math
from shapely.geometry import Polygon
from app.db.models import ModelRevision, ModelPlacement, Project
from app.services.assistant.storage import owned_row, error
from app.services.ai.building_plan import local_plot


def road_grounding(db, project_id, context):
    row = owned_row(db, "site_selection_versions", project_id, context["siteSelectionVersionId"])
    selected = row["selection_payload"]["selection"]
    if selected["kind"] == "ROUTE": geometry = selected["geometry"]
    elif selected["kind"] == "ENDPOINTS":
        geometry = {"type": "LineString", "coordinates": [selected["endpointA"]["coordinates"], selected["endpointB"]["coordinates"]]}
    else: error(422, "ROAD_ROUTE_REQUIRED", "Select and save a route or endpoints before generating a road.")
    source = context.get("modelRevisionId")
    base = db.get(ModelRevision, int(source)) if source else None
    if source and (not base or base.project_id != project_id): error(422, "INVALID_SOURCE_REVISION", "Road source revision is unavailable.")
    placement = db.query(ModelPlacement).filter_by(project_id=project_id, model_revision_id=base.id).first() if base else None
    if base and not placement: error(422, "PLACEMENT_REQUIRED", "The saved model needs an accepted geographic anchor.")
    anchor = geometry["coordinates"][0]
    origin = {"lng": placement.anchor_longitude if placement else anchor[0], "lat": placement.anchor_latitude if placement else anchor[1],
              "heading_deg": placement.anchor_heading_deg if placement else 0}
    local = local_plot({"origin": origin, "boundary": geometry})
    return {"routeReference": {"id": row["id"], "version": row["version"], "contentHash": row["content_hash"]},
            "sourceModelRevisionId": source, "alignment": [{"id": f"point-{i}", "position": list(xy)} for i, xy in enumerate(local.coords)],
            "origin": origin, "referencePlane": "LOCAL_VISUAL_REFERENCE", "elevationResolution": "UNKNOWN"}


def validate_road_context(db, project_id, context, spec):
    grounding = road_grounding(db, project_id, context)
    if spec.route_reference.model_dump(mode="json", by_alias=True) != grounding["routeReference"]:
        error(422, "INVALID_ROUTE_REFERENCE", "Copy the exact saved route reference, version and hash.")
    if spec.source_model_revision_id != context.get("modelRevisionId"):
        error(409, "STALE_SOURCE_REVISION", "Road specification must match the frozen saved model revision.")
    if context.get("editorDirty"): error(409, "UNSAVED_MODEL", "Save manual edits before proposing road generation.")
    current = db.query(ModelRevision).filter_by(project_id=project_id)
    if context.get("scenarioId"): current = current.filter_by(design_scenario_id=int(context["scenarioId"]))
    latest = current.order_by(ModelRevision.id.desc()).first()
    if (str(latest.id) if latest else None) != spec.source_model_revision_id:
        error(409, "STALE_SOURCE_REVISION", "Road source revision changed; submit a new request.")
    points = grounding["alignment"]
    if len(points) != len(spec.alignment) or any(math.dist(a.position, b["position"]) > .001 for a, b in zip(spec.alignment, points)):
        error(422, "ROUTE_ALIGNMENT_MISMATCH", "Control points must preserve the selected route and ordering in the saved local frame.")
    project = db.get(Project, project_id)
    if project.boundary_geojson:
        from app.services.assistant.road_specialist import section_width
        plot = local_plot({"origin": grounding["origin"], "boundary": project.boundary_geojson})
        half = section_width(spec.cross_section) / 2
        for a, b in zip(spec.alignment, spec.alignment[1:]):
            dx, dy = b.position[0]-a.position[0], b.position[1]-a.position[1]
            length = math.hypot(dx, dy)
            if length < .01: error(422, "INVALID_ROAD_SPEC", "Road segment has zero length.")
            nx, ny = -dy / length * half, dx / length * half
            footprint = Polygon([(a.position[0]+nx,a.position[1]+ny),(b.position[0]+nx,b.position[1]+ny),
                                 (b.position[0]-nx,b.position[1]-ny),(a.position[0]-nx,a.position[1]-ny)])
            if not plot.buffer(1e-6).covers(footprint): error(422, "ROAD_OUTSIDE_SITE", "The complete road cross-section must remain inside the project boundary.")
    return grounding

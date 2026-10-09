"""Deterministic patch validation and affected-component preview, never LLM execution."""
from copy import deepcopy
from dataclasses import dataclass
import math
from shapely.geometry import Polygon, Point
from shapely import affinity
from app.domain.building_specialist import BuildingSpec
from app.services.assistant.building_specialist import BuildingAdapter, BuildingSpecValidator
from app.services.assistant.storage import owned_row, rows, digest, error
from app.services.design.editable_model import geometry_spec_to_document, validate_document
from app.db.models import ModelRevision, Project, DesignScenario

SUPPORTED = frozenset({"MOVE_COMPONENT", "ROTATE_COMPONENT", "RESIZE_OPENING", "MOVE_OPENING", "ADD_OPENING", "REMOVE_OPENING"})

@dataclass(frozen=True)
class SavedBuildingPatchContext:
    """Server-only access to the authoritative saved snapshot; never a tool argument."""
    db: object
    project_id: int

class BuildingPatchValidator:
    def preview(self, db, project_id, patch):
        source = owned_row(db, "model_revisions", project_id, patch.source_model_revision_id)
        latest = db.query(ModelRevision).filter_by(project_id=project_id, design_scenario_id=source["design_scenario_id"]).order_by(ModelRevision.revision_number.desc()).first()
        if latest.id != source["id"]: error(409, "STALE_PATCH", "Patch source is not the current saved revision.")
        spec_row = owned_row(db, "asset_specification_versions", project_id, patch.source_specification_version_id)
        if spec_row["asset_id"] != patch.asset_id or spec_row["content_hash"] != patch.source_specification_hash:
            error(409, "STALE_PATCH", "Building specification identity differs.")
        raw = spec_row["payload"].get("buildingSpec")
        if not raw: error(422, "INVALID_PATCH_SOURCE", "A generated BuildingSpec is required.")
        spec = BuildingSpec.model_validate(raw)
        if spec.building_id != patch.building_id: error(422, "TARGET_BUILDING_MISMATCH", "Building identity differs.")
        document = deepcopy(source["document_json"])
        operation = patch.operations[0]; parameters = operation.parameters
        target = next((c for c in document["components"] if c["id"] == operation.target_component_id), None)
        if not target: error(422, "TARGET_NOT_FOUND", "The exact target component is missing.")
        lineage = next((r for r in rows(db, "model_object_lineage", project_id) if r["model_revision_id"] == source["id"] and r["object_id"] == target["id"]), None)
        if not lineage or lineage["asset_id"] != patch.asset_id or lineage["specification_version_id"] != spec_row["id"]:
            error(422, "TARGET_LINEAGE_MISMATCH", "Target is not grounded in the specified Building asset/specification.")
        if digest(target) != operation.expected_component_hash: error(409, "STALE_PATCH", "Target state differs from the reviewed source.")
        if target.get("locked"): error(422, "TARGET_LOCKED", "Unlock and save the component before proposing a patch.")
        before = deepcopy(target)
        kind = target.get("metadata", {}).get("componentKind")
        affected = [target["id"]]
        operation_type = parameters.operation_type
        summary = {"operation":operation_type,"target":target["id"],"before":deepcopy(target["transform"])}
        if operation_type in {"MOVE_COMPONENT", "ROTATE_COMPONENT"}:
            # Walls/openings/rooms have host or boundary dependencies; reject rather than detach them.
            if kind not in {"COLUMN", "BEAM"}: error(422, "DEPENDENT_EDIT_UNAVAILABLE", "V1 transforms only columns and beams; dependent geometry edits are unavailable.")
            if operation_type == "MOVE_COMPONENT":
                delta = [float(v) / (1000 if parameters.unit == "mm" else 1) for v in parameters.delta]
                if delta[2] != 0: error(422, "DEPENDENT_EDIT_UNAVAILABLE", "Vertical member movement requires floor dependency handling.")
                target["transform"]["position"] = [v + d for v, d in zip(target["transform"]["position"], delta)]
            else:
                target["transform"]["rotation_deg"][2] += float(parameters.angle_deg)
            footprint = affinity.rotate(Polygon(spec.footprint), spec.orientation, origin=(0, 0))
            x, y, _ = target["transform"]["position"]
            points = [(x, y)]
            if kind == "BEAM":
                angle = math.radians(target["transform"]["rotation_deg"][2])
                half = target["geometry"]["size"][0] * target["transform"]["scale"][0] / 2
                points += [(x + sign*half*math.cos(angle), y + sign*half*math.sin(angle)) for sign in (-1, 1)]
            if not all(footprint.buffer(1e-7).covers(Point(p)) for p in points): error(422, "OUTSIDE_FOOTPRINT", "Member axis must remain inside the approved footprint.")
        else:
            original_spec = deepcopy(raw)
            opening = next((o for o in original_spec["openings"] if o["id"] == target.get("metadata", {}).get("sourceComponentId")), None)
            summary["previousOpening"] = deepcopy(opening)
            if operation_type == "ADD_OPENING":
                if kind != "WALL": error(422, "INVALID_HOST_WALL", "Select an existing supported wall component.")
                source_id = target["metadata"]["sourceComponentId"]
                matches = [w for w in original_spec["walls"] if source_id == w["id"] + "-end" or source_id.startswith(w["id"] + "-")]
                if len(matches) != 1: error(422, "INVALID_HOST_WALL", "Host wall cannot be resolved exactly.")
                wall = matches[0]
                host = wall["id"]
                original_spec["openings"].append({"id":parameters.opening_id,"kind":parameters.kind,"wall_id":host,
                    "offset":parameters.offset_m,"width":parameters.width,"height":parameters.height,"sill":parameters.sill_m})
            else:
                if kind != "OPENING" or not opening: error(422, "INVALID_OPENING", "Target is not an original supported opening.")
                host = opening["wall_id"]
                if operation_type == "RESIZE_OPENING": opening["width"] = float(parameters.width)
                elif operation_type == "MOVE_OPENING": opening["offset"] = float(parameters.offset_m)
                else: original_spec["openings"].remove(opening)
            adapter = BuildingAdapter()
            project = db.get(Project, project_id); scenario = db.get(DesignScenario, source["design_scenario_id"])
            def converted(value):
                geometry = adapter.generate(BuildingSpec.model_validate(value))
                components = geometry_spec_to_document(project, scenario, geometry)["components"]
                for obj, component in zip(geometry["objects"], components):
                    component["id"] = obj["semantic"]["id"]
                    component["metadata"] = obj["semantic"]
                    component["quantity"] = {"included":False}
                return components
            old_components = converted(raw)
            host_openings = {o["id"] for o in raw["openings"] if o["wall_id"] == host}
            def belongs(component):
                sid = component.get("metadata", {}).get("sourceComponentId", "")
                return sid in host_openings or sid.startswith(host + "-")
            old_host = [c for c in old_components if belongs(c)]
            # Host edits must not erase previous manual or patch work. V1 rejects it explicitly.
            for old in old_host:
                saved = next((c for c in document["components"] if c["id"] == old["id"]), None)
                if not saved or saved.get("locked") or any(saved[k] != old[k] for k in ("transform", "geometry")):
                    error(422, "HOST_DEPENDENCY_CHANGED", "Host geometry was edited; reconcile it before opening edits.")
            result = BuildingSpecValidator().validate(original_spec)
            if result["issues"]: error(422, "INVALID_BUILDING_PATCH", result)
            updated_openings = {o["id"] for o in original_spec["openings"] if o["wall_id"] == host}
            summary.update(hostWallId=host,proposedOpening=next((o for o in original_spec["openings"] if o["id"] == (parameters.opening_id if operation_type=="ADD_OPENING" else before["metadata"]["sourceComponentId"])),None))
            new_host = [c for c in converted(original_spec) if c["metadata"]["sourceComponentId"] in updated_openings or c["metadata"]["sourceComponentId"].startswith(host + "-")]
            old_ids = {c["id"] for c in old_host}
            saved_map = {c["id"]:c for c in document["components"]}
            for component in new_host:
                previous = saved_map.get(component["id"])
                component["metadata"] = {**target["metadata"], **component["metadata"]}
                if previous:
                    for key in ("visible", "locked", "material"): component[key] = deepcopy(previous[key])
            document["components"] = [c for c in document["components"] if c["id"] not in old_ids] + new_host
            affected = sorted(old_ids | {c["id"] for c in new_host})
        errors = validate_document(document, project_id=project_id, scenario_id=source["design_scenario_id"], project_type=document["project_type"])
        if errors: error(422, "INVALID_PATCH_GEOMETRY", errors)
        return {"document":document,"affectedComponentIds":affected,"source":source,"lineage":dict(lineage),
                "summary":{**summary,"after":target["transform"]}}

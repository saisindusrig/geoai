"""Future editable-object adapter, isolated from current production validator.

This is a preview document, not an accepted editable-model/1 revision.
"""
from copy import deepcopy
import uuid
from app.experimental.cad_contract import digest, encode


def object_id(project_id, asset_id, component_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "geoai:cad:" + encode([project_id, asset_id, component_id]).decode()))


def preview_document(document, geometry, results, *, catalog_id):
    candidate = deepcopy(document)
    candidate["schema_version"] = "cad-workspace-preview/1"
    candidate["productionBuildEnabled"] = False
    owned_ids = {object_id(geometry.source.project_id, d.asset_id, d.component_id) for d in geometry.definitions}
    previous = {o.get("id"): o for o in candidate.get("components", [])}
    objects = [o for o in candidate.get("components", []) if o.get("id") not in owned_ids]
    compiled = {r.component_id: r for r in results}
    if set(compiled) != {d.component_id for d in geometry.definitions}:
        raise ValueError("ADAPTER_MEMBERSHIP_MISMATCH")
    for d in geometry.definitions:
        r = compiled[d.component_id]
        if r.definition_hash != digest(d):
            raise ValueError("ADAPTER_SOURCE_MISMATCH")
        id = object_id(geometry.source.project_id, d.asset_id, d.component_id)
        old = previous.get(id, {})
        objects.append({"id": id,
            "name": d.component_id, "componentId": d.component_id, "assemblyId": d.assembly_id, "assetId": d.asset_id,
            "parent_id": None, "category": d.component_type.lower(), "visible": old.get("visible", True), "locked": old.get("locked", False),
            "materialId": d.material.id, "semanticType": d.component_type,
            "parameters": {k:{"value":v,"unit":"m"} for k,v in d.recipe.parameters.items()},
            "provenance": d.provenance.model_dump(mode="json", by_alias=True),
            "source": {"schemaVersion": "cad-geometry/1", "definitionHash": r.definition_hash,
                       "catalogId": catalog_id, "baseRevisionId": geometry.source.revision_id},
            "geometry": {"kind": "cad_mesh_preview", "meshHash": r.mesh.sha256, "brepHash": r.brep.sha256, "frame": d.frame, "units": "m"},
            "transform": deepcopy(old.get("transform", {"position": [0, 0, 0], "rotation_deg": [0, 0, 0], "scale": [1, 1, 1]})),
            "material": d.material.model_dump(mode="json", by_alias=True), "quantity": {"included": False},
            "engineeringStatus": "UNVERIFIED", "quantities": "UNAVAILABLE"})
    candidate["components"] = objects
    return candidate

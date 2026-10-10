"""Small private references in ordinary editable ModelRevision documents."""
from copy import deepcopy
import math
from app.experimental.cad_adapter import object_id
from app.experimental.cad_contract import digest
from app.services.assistant.storage import identity


def revision_document(base, geometry, results, *, catalog_id, snapshot_id, proposal_id, snapshot_hash):
    document = deepcopy(base)
    owned = {object_id(geometry.source.project_id, d.asset_id, d.component_id) for d in geometry.definitions}
    old = {c["id"]: c for c in document["components"]}
    document["components"] = [c for c in document["components"] if c["id"] not in owned]
    compiled = {r.component_id: r for r in results}
    for d in geometry.definitions:
        r = compiled[d.component_id]
        component_id = object_id(geometry.source.project_id, d.asset_id, d.component_id)
        prior = old.get(component_id, {})
        center = [(r.bounds_m[i] + r.bounds_m[i+3])/2 for i in range(3)]
        transform = deepcopy(prior.get("transform", {"position": center, "rotation_deg": [0,0,0], "scale": [1,1,1]}))
        if prior:
            bounds = prior["geometry"]["bounds_m"]
            old_center = [(bounds[i] + bounds[i+3])/2 for i in range(3)]
            x,y,z = [center[i] - old_center[i] for i in range(3)]
            rx,ry,rz = [math.radians(v) for v in transform["rotation_deg"]]
            x,y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
            x,z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
            y,z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
            transform["position"] = [transform["position"][i] + delta for i,delta in enumerate((x,y,z))]
        document["components"].append({"id": component_id, "parent_id": None, "name": d.component_id,
            "category": d.component_type.lower(), "visible": prior.get("visible", True), "locked": prior.get("locked", False),
            "geometry": {"kind": "cad_mesh", "catalog_id": catalog_id, "mesh_hash": r.mesh.sha256,
                "brep_hash": r.brep.sha256, "definition_hash": digest(d), "bounds_m": r.bounds_m},
            "transform": transform,
            "material": {"name": d.material.name, "color": "#819aa8" if d.material.category == "STEEL" else "#b8c0cc", "roughness": .75, "metalness": .3 if d.material.category == "STEEL" else 0},
            "quantity": {"included": False},
            "metadata": {"assetId": d.asset_id, "assemblyId": d.assembly_id, "componentId": d.component_id,
                "materialId": d.material.id, "parameters": d.recipe.parameters, "geometryStatus": "BREP_VALID_MESH_VERIFIED",
                "designId": geometry.source.design_id, "designVersion": geometry.source.design_version,
                "sourceModelRevisionId": geometry.source.revision_id, "cadProposalVersionId": proposal_id,
                "approvalId": identity(proposal_id, "approval"),
                "cadSnapshotId": snapshot_id, "cadSnapshotHash": snapshot_hash, "engineeringStatus": "UNVERIFIED",
                "previewAssumptions": ["Project local visual reference; terrain/elevation unknown unless accepted placement", "Structural adequacy, foundations, loads and code compliance unvalidated"]}})
    document.setdefault("metadata", {}).update(cadCatalogId=catalog_id, cadSnapshotId=snapshot_id, cadExperimental=True)
    return document


def validate_references(db, *, project_id, user_id, document, base, publication=False):
    """Manual saves can change rigid transforms/visibility, never CAD authority."""
    from app.experimental.cad_capability import require_cad
    from app.experimental.cad_artifacts import retrieve
    from app.experimental.cad_contract import Manifest
    from fastapi import HTTPException
    require_cad(db, project_id, user_id)
    previous = {c["id"]: c for c in (base.document_json["components"] if base else [])}
    current = {c["id"]: c for c in document["components"]}
    if not publication:
        for component_id, prior in previous.items():
            if prior["geometry"]["kind"] == "cad_mesh" and (component_id not in current or current[component_id]["geometry"] != prior["geometry"]):
                raise HTTPException(422, "CAD geometry changes/deletion require a reviewed parametric proposal; hide components instead.")
    for component in document["components"]:
        if component["geometry"]["kind"] != "cad_mesh":
            continue
        g = component["geometry"]
        manifest = Manifest.model_validate_json(retrieve(db, user_id=user_id, project_id=project_id, catalog_id=g["catalog_id"]))
        expected = next((r for d,r in zip(manifest.geometry.definitions, manifest.results)
            if object_id(project_id, d.asset_id, d.component_id) == component["id"]), None)
        if not expected or (g["mesh_hash"],g["brep_hash"],g["definition_hash"],list(g["bounds_m"])) != (expected.mesh.sha256,expected.brep.sha256,expected.definition_hash,list(expected.bounds_m)):
            raise HTTPException(422, "CAD_REFERENCE_MISMATCH")
        for artifact in (expected.brep, expected.mesh):
            retrieve(db, user_id=user_id, project_id=project_id, catalog_id=g["catalog_id"], artifact_hash=artifact.sha256)
        t = component["transform"]
        if t["scale"] != [1,1,1] or any(not math.isfinite(float(v)) for key in ("position","rotation_deg") for v in t[key]):
            raise HTTPException(422, "CAD edits support rigid translation/rotation only; regenerate parameters for shape changes.")
        prior = previous.get(component["id"])
        if not publication and (not prior or prior.get("metadata") != component.get("metadata") or prior["material"] != component["material"]):
            raise HTTPException(422, "CAD authority may only be introduced by approved experimental execution.")
        if prior and prior["geometry"] == g and (prior.get("metadata") != component.get("metadata") or prior["material"] != component["material"]):
            raise HTTPException(422, "CAD semantic/parametric edits require a reviewed regeneration.")

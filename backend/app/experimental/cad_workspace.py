"""Approved experimental CAD orchestration using existing proposal persistence.

Snapshots are private, hash-bound proposal requirements. Native work is a fixed
resource-limited subprocess. No provider calls or production builder registration.
"""
from copy import deepcopy
import json
import sqlalchemy as sa
from fastapi import HTTPException
from app.db.models import GeneratedFile, ModelRevision, User
from app.domain.assistant_runtime import ProposalRequest
from app.experimental.cad_capability import require_cad
from app.experimental.cad_artifacts import PrivateStore, owned_source, publish, retrieve
from app.experimental.cad_contract import Geometry, Manifest, digest, encode, from_bim, review_changes
from app.experimental.bim_cad import CADMapping
from app.services.assistant.bim_foundation import validate_foundation
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import identity, owned_row, lock_project, table, insert


def _fail(code, status=409):
    raise HTTPException(status, detail={"code": code, "message": code.replace("_", " ")})


def _snapshot(db, project_id, version_id, store):
    records = db.query(GeneratedFile).filter_by(project_id=project_id, file_type="cad_review_v1").all()
    row = next((r for r in records if r.metadata_json.get("proposalVersionId") == version_id), None)
    if row is None:
        _fail("CAD_REVIEW_NOT_FOUND", 404)
    return row, json.loads(store.get(project_id, row.metadata_json["snapshotHash"]))


def create_review(db, *, project_id, user_id, request_id, message_id, bim, mapping, store=None):
    require_cad(db, project_id, user_id)
    store = store or PrivateStore()
    lock_project(db, project_id)
    message = owned_row(db, "conversation_messages", project_id, message_id)
    if message["role"] != "USER":
        _fail("HUMAN_REVIEW_CONTEXT_REQUIRED", 403)
    context = message["context"]
    base = db.query(ModelRevision).filter_by(project_id=project_id, design_scenario_id=int(context.get("scenarioId") or 0)).order_by(ModelRevision.revision_number.desc()).first()
    if not base or str(base.id) != context.get("modelRevisionId") or context.get("editorDirty"):
        _fail("STALE_SOURCE_REVISION")
    model, _ = validate_foundation(bim)
    mapping = CADMapping.model_validate(mapping)
    # Context/provenance is reconstructed by the server, not authored JSON.
    design_id = identity(project_id, "cad-design", request_id)
    design_version = 1
    parent_version_id = None
    if base.document_json.get("metadata", {}).get("cadCatalogId"):
        parent = Manifest.model_validate_json(retrieve(db, user_id=user_id, project_id=project_id,
            catalog_id=base.document_json["metadata"]["cadCatalogId"], store=store))
        design_id = parent.geometry.source.design_id
        design_version = parent.geometry.source.design_version + 1
        previous_snapshot = db.query(GeneratedFile).filter_by(id=base.document_json["metadata"].get("cadSnapshotId"), project_id=project_id, file_type="cad_review_v1").one_or_none()
        if not previous_snapshot:
            _fail("CAD_REVIEW_NOT_FOUND")
        parent_version_id = previous_snapshot.metadata_json["proposalVersionId"]
    raw = model.model_dump(mode="json", by_alias=False)
    for component in raw["components"]:
        component["provenance"] = {"design_id": design_id, "design_version": design_version,
            "source_model_revision_id": str(base.id), "source_kind": "PREVIEW_ASSUMPTION"}
    model, _ = validate_foundation(raw)
    source = owned_source(db, user_id=user_id, project_id=project_id, revision_id=base.id,
        design_id=design_id, design_version=design_version, source_model_revision_id=str(base.id))
    geometry = from_bim(model, mapping, source=source)
    if geometry.connections:
        _fail("CONNECTION_REQUIRES_REVIEW", 422)
    snapshot = {"schemaVersion": "cad-review/1", "bim": model.model_dump(mode="json", by_alias=True),
        "mapping": mapping.model_dump(mode="json", by_alias=True), "geometry": geometry.model_dump(mode="json", by_alias=True),
        "engineeringStatus": "UNVERIFIED", "terrainElevation": "UNKNOWN_UNLESS_ACCEPTED_PLACEMENT",
        "validationVersion": "cad-workspace-validation/1"}
    sha = digest(snapshot)
    # Exact snapshot hash is immutable and visible in the ordinary proposal.
    view = ProposalService().create(db, project_id, user_id, ProposalRequest(
        client_request_id=request_id, message_id=message_id, title="Experimental CAD assembly review",
        parent_version_id=parent_version_id,
        rationale="Review precise geometry and source binding; structural adequacy remains UNVERIFIED.",
        assets=[dict(asset_type="CUSTOM", name="Experimental CAD assembly", requirements=["cad-review-sha256:" + sha])],
        assumptions=["CAD validates geometry only. Terrain, foundations, loads and code compliance are unvalidated."],
        warnings=["Production CAD Build remains disabled. Review connections before finalization."]))
    existing = db.query(GeneratedFile).filter_by(project_id=project_id, file_type="cad_review_v1").all()
    if not any(r.metadata_json.get("proposalVersionId") == view["id"] for r in existing):
        store.put(project_id, sha, encode(snapshot))
        db.add(GeneratedFile(project_id=project_id, model_revision_id=base.id, design_scenario_id=base.design_scenario_id,
            file_type="cad_review_v1", file_url="cad-private:" + sha,
            metadata_json={"snapshotHash": sha, "proposalVersionId": view["id"]}))
        db.commit()
    return {"proposal": view, "snapshotHash": sha, "componentIds": [d.component_id for d in geometry.definitions],
        "components": [{"id":d.component_id, "assembly":d.assembly_id, "recipe":d.recipe.operation,
            "parameters":d.recipe.parameters, "material":d.material.name} for d in geometry.definitions],
        "engineeringStatus": "UNVERIFIED"}


def _geometry_identity(definition):
    value = definition.model_dump(mode="json", by_alias=True)
    value.pop("provenance")
    return digest(value)


def execute_review(db, *, project_id, user_id, version_id, store=None, compiler=None):
    require_cad(db, project_id, user_id)
    store = store or PrivateStore()
    lock_project(db, project_id)
    row, snapshot = _snapshot(db, project_id, version_id, store)
    previous_build = db.query(GeneratedFile).filter_by(project_id=project_id, file_type="cad_build_v1").all()
    done = next((r for r in previous_build if r.metadata_json.get("proposalVersionId") == version_id), None)
    if done:
        # A retry reads and verifies committed evidence; never recompiles.
        manifest = Manifest.model_validate_json(retrieve(db, user_id=user_id, project_id=project_id, catalog_id=done.metadata_json["catalogId"], store=store))
        for compiled in manifest.results:
            for artifact in (compiled.brep, compiled.mesh):
                retrieve(db, user_id=user_id, project_id=project_id, catalog_id=done.metadata_json["catalogId"], artifact_hash=artifact.sha256, store=store)
        return deepcopy(done.metadata_json["result"])
    geometry = Geometry.model_validate(snapshot["geometry"])
    view = ProposalService().assert_build_current(db, project_id, version_id, str(geometry.source.revision_id))
    approval = owned_row(db, "proposal_approvals", project_id, identity(version_id, "approval"))
    if approval["approved_by"] != user_id:
        _fail("APPROVAL_ACTOR_MISMATCH", 403)
    requirements = view["content"]["request"]["assets"][0]["requirements"]
    if requirements != ["cad-review-sha256:" + digest(snapshot)] or snapshot["validationVersion"] != "cad-workspace-validation/1":
        _fail("CAD_REVIEW_BINDING_MISMATCH")
    base = db.get(ModelRevision, geometry.source.revision_id)
    if not base or digest(base.document_json) != geometry.source.revision_document_hash:
        _fail("STALE_SOURCE_REVISION")
    source = base.id
    document = deepcopy(base.document_json)
    old_manifest = None
    if document.get("metadata", {}).get("cadCatalogId"):
        old_manifest = Manifest.model_validate_json(retrieve(db, user_id=user_id, project_id=project_id,
            catalog_id=document["metadata"]["cadCatalogId"], store=store))
    cached, blobs = {}, {}
    if old_manifest:
        review = review_changes(old_manifest.geometry, geometry)
        if any(i["code"] == "CONNECTION_REQUIRES_REVIEW" for i in review["issues"]):
            _fail("CONNECTION_REQUIRES_REVIEW", 422)
        old_definitions = {d.component_id: d for d in old_manifest.geometry.definitions}
        old_results = {r.component_id: r for r in old_manifest.results}
        for definition in geometry.definitions:
            old = old_definitions.get(definition.component_id)
            if old and _geometry_identity(old) == _geometry_identity(definition):
                result = old_results[definition.component_id].model_copy(update={"definition_hash": digest(definition)})
                cached[definition.component_id] = result
                for artifact in (result.brep, result.mesh):
                    blobs[artifact.sha256] = retrieve(db, user_id=user_id, project_id=project_id,
                        catalog_id=document["metadata"]["cadCatalogId"], artifact_hash=artifact.sha256, store=store)
    dirty = [d for d in geometry.definitions if d.component_id not in cached]
    # End the read transaction before native execution; revalidate on commit.
    db.rollback()
    if dirty:
        from app.experimental.cad_worker import compile_batch
        worker_definitions = [d.model_copy(update={"dependency_ids": [], "relationship_ids": []}) for d in dirty]
        subset = geometry.model_copy(update={"definitions": worker_definitions, "dependencies": [], "connections": []})
        generated, new_blobs = (compiler or compile_batch)(subset)
        original_definitions = {d.component_id: d for d in dirty}
        cached.update({r.component_id: r.model_copy(update={"definition_hash": digest(original_definitions[r.component_id])}) for r in generated})
        blobs.update(new_blobs)
    try:
        require_cad(db, project_id, user_id)
        lock_project(db, project_id)
        concurrent = db.query(GeneratedFile).filter_by(project_id=project_id, file_type="cad_build_v1").all()
        winner = next((r for r in concurrent if r.metadata_json.get("proposalVersionId") == version_id), None)
        if winner:
            response = deepcopy(winner.metadata_json["result"])
            db.rollback()
            return response
        ProposalService().assert_build_current(db, project_id, version_id, str(source))
        results = [cached[d.component_id] for d in geometry.definitions]
        catalog = publish(db, user_id=user_id, geometry=geometry, results=results, blobs=blobs,
            trusted_source=geometry.source, enabled=True, store=store)
        from app.experimental.cad_revision import revision_document
        document = revision_document(document, geometry, results, catalog_id=catalog.id, snapshot_id=row.id,
            proposal_id=version_id, snapshot_hash=digest(snapshot))
        from app.api.routes.model_revisions import persist_revision, RevisionCreate
        result = persist_revision(project_id, base.design_scenario_id, RevisionCreate(base_revision_id=source,
            document=document, source="import"), db, db.get(User, user_id), commit=False, cad_publication=True,
            lineage_updates={c["id"]: c["metadata"] for c in document["components"] if c.get("metadata", {}).get("cadProposalVersionId") == version_id})
        revision_id = result["id"]
        catalog.model_revision_id = revision_id
        spec_id = view["content"]["contract"]["assetSpecificationVersionIds"][0]
        spec = owned_row(db, "asset_specification_versions", project_id, spec_id)
        for component in document["components"]:
            if component.get("metadata", {}).get("cadProposalVersionId") != version_id:
                continue
            lineage = table("model_object_lineage")
            exists = db.execute(sa.select(lineage.c.id).where(lineage.c.model_revision_id == revision_id, lineage.c.object_id == component["id"])).first()
            if not exists:
                insert(db, "model_object_lineage", id=identity(revision_id, component["id"]), project_id=project_id,
                    model_revision_id=revision_id, asset_id=spec["asset_id"], proposal_version_id=version_id,
                    specification_version_id=spec_id, object_id=component["id"], component_id=component["metadata"]["componentId"],
                    generator_id="experimental-cad", generator_version="1", payload=component["metadata"])
        response = {"modelRevisionId": revision_id, "scenarioId": base.design_scenario_id, "catalogId": catalog.id,
            "regeneratedComponentIds": [d.component_id for d in dirty], "engineeringStatus": "UNVERIFIED"}
        db.add(GeneratedFile(project_id=project_id, model_revision_id=revision_id, file_type="cad_build_v1",
            file_url="cad-private:" + catalog.metadata_json["manifestHash"],
            metadata_json={"proposalVersionId": version_id, "catalogId": catalog.id, "result": response}))
        ProposalService().transition(db, project_id, version_id, "BUILT")
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise

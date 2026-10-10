"""Versioned editable-model API used by the professional 3D workspace."""

from __future__ import annotations

from typing import Any
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user, get_current_user_id
from app.db.models import DesignScenario, GeneratedFile, ModelRevision, QuantityEstimate, User, ModelPlacement, EngineeringAnalysis, EngineeringAuditEvent
from app.db.session import get_db
from app.services.design.editable_model import (
    apply_component_patch,
    build_ai_edit_preview,
    calculate_revision_impact,
    document_to_geometry_spec,
    validate_document,
)
from app.services.exports.gltf_export import generate_glb
from app.services.storage import save_file
from app.services.design.structural_layout import validate_layout

router = APIRouter(
    prefix="/api/projects/{project_id}/scenarios/{scenario_id}/model-revisions",
    tags=["model-revisions"],
)


class RevisionCreate(BaseModel):
    base_revision_id: int | None = None
    document: dict[str, Any]
    source: str = Field(default="manual_edit", pattern="^(manual_edit|ai_edit|ai_generate|import)$")
    prompt: str | None = Field(default=None, max_length=4000)


class AiEditRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)


def _scenario(db: Session, project_id: int, scenario_id: int) -> DesignScenario:
    scenario = db.get(DesignScenario, scenario_id)
    if scenario is None or scenario.project_id != project_id:
        raise HTTPException(404, "Scenario not found")
    return scenario


def _latest(db: Session, scenario_id: int) -> ModelRevision | None:
    return (
        db.query(ModelRevision)
        .filter(ModelRevision.design_scenario_id == scenario_id)
        .order_by(ModelRevision.revision_number.desc())
        .first()
    )


def revision_out(revision: ModelRevision, *, include_document: bool = True) -> dict[str, Any]:
    result = {
        "id": revision.id,
        "project_id": revision.project_id,
        "scenario_id": revision.design_scenario_id,
        "revision_number": revision.revision_number,
        "source": revision.source,
        "prompt": revision.prompt,
        "user_id": revision.user_id,
        "created_at": revision.created_at,
    }
    if include_document:
        result["document"] = revision.document_json
    return result


@router.get("")
def list_revisions(
    project_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    _scenario(db, project_id, scenario_id)
    revisions = (
        db.query(ModelRevision)
        .filter(ModelRevision.design_scenario_id == scenario_id)
        .order_by(ModelRevision.revision_number.desc())
        .all()
    )
    return {"revisions": [revision_out(item, include_document=False) for item in revisions]}


@router.get("/latest")
def latest_revision(
    project_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    _scenario(db, project_id, scenario_id)
    revision = _latest(db, scenario_id)
    if revision is None:
        raise HTTPException(404, "No editable model revision exists for this scenario")
    return revision_out(revision)


@router.post("")
def save_revision(
    project_id: int,
    scenario_id: int,
    payload: RevisionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return persist_revision(project_id, scenario_id, payload, db, user)


def persist_revision(project_id, scenario_id, payload, db, user, *, commit=True, lineage_updates=None, cad_publication=False):
    from app.services.assistant.storage import lock_project
    lock_project(db, project_id)
    project = get_owned_project(project_id, db, user.id)
    scenario = _scenario(db, project_id, scenario_id)
    latest = _latest(db, scenario_id)
    latest_id = latest.id if latest else None
    if payload.base_revision_id != latest_id:
        raise HTTPException(
            409,
            detail={
                "message": "The model changed after this editor was opened. Reload the latest revision before saving.",
                "latest_revision_id": latest_id,
            },
        )
    errors = validate_document(
        payload.document,
        project_id=project_id,
        scenario_id=scenario_id,
        project_type=project.project_type,
    )
    if errors:
        raise HTTPException(422, detail={"message": "Model validation failed", "errors": errors})
    has_cad = any(c.get("geometry", {}).get("kind") == "cad_mesh" for c in payload.document["components"])
    if has_cad or latest and any(c.get("geometry", {}).get("kind") == "cad_mesh" for c in latest.document_json.get("components", [])):
        from app.experimental.cad_revision import validate_references
        validate_references(db, project_id=project_id, user_id=user.id, document=payload.document, base=latest, publication=cad_publication)
    layout_validation = validate_layout(payload.document)
    if not layout_validation["passed"]:
        raise HTTPException(422, detail={"message": "Structural layout rule validation failed", "violations": layout_validation["violations"]})
    payload.document = deepcopy(payload.document)
    if isinstance(payload.document.get("structural_layout"), dict):
        payload.document["structural_layout"].pop("approval", None)

    revision_number = int(latest.revision_number + 1 if latest else 1)
    revision = ModelRevision(
        project_id=project_id,
        design_scenario_id=scenario_id,
        revision_number=revision_number,
        document_json=payload.document,
        source=payload.source,
        prompt=payload.prompt,
        user_id=user.id,
    )
    db.add(revision)
    db.flush()

    if latest:
        # Identity follows retained objects across snapshots. Trust persisted
        # lineage, never client-submitted provenance or newly introduced IDs.
        from app.services.assistant.storage import table, insert, identity
        import sqlalchemy as sa
        lineage_table = table("model_object_lineage")
        retained = {component["id"] for component in payload.document["components"]}
        previous = db.execute(sa.select(lineage_table).where(
            lineage_table.c.project_id == project_id,
            lineage_table.c.model_revision_id == latest.id,
        )).mappings().all()
        for lineage in previous:
            if lineage["object_id"] not in retained:
                continue
            fields = {key: deepcopy(lineage[key]) for key in (
                "asset_id", "proposal_version_id", "specification_version_id",
                "object_id", "component_id", "generator_id", "generator_version", "payload",
            )}
            fields["payload"].setdefault("generationModelRevisionId", latest.id)
            fields["payload"]["previousModelRevisionId"] = latest.id
            if lineage_updates and lineage["object_id"] in lineage_updates:
                fields["payload"]["patchProvenance"] = {**lineage_updates[lineage["object_id"]], "resultingModelRevisionId":revision.id}
            insert(db, "model_object_lineage", id=identity(revision.id, lineage["object_id"]),
                   project_id=project_id, model_revision_id=revision.id, **fields)
        previous_placement = db.query(ModelPlacement).filter_by(project_id=project_id, model_revision_id=latest.id).one_or_none()
        if previous_placement:
            origin_changed = latest.document_json.get("origin") != payload.document.get("origin")
            fields = {column.name: getattr(previous_placement, column.name) for column in ModelPlacement.__table__.columns
                      if column.name not in {"id", "model_revision_id", "created_at", "updated_at"}}
            fields["placement_state"] = "REVIEW_REQUIRED" if origin_changed else previous_placement.placement_state
            db.add(ModelPlacement(model_revision_id=revision.id, **fields))
        # Preserve immutable result payloads; only their current applicability
        # changes when a new model revision supersedes the analysed geometry.
        db.query(EngineeringAnalysis).filter_by(project_id=project_id, model_revision_id=latest.id).update({"status": "STALE"}, synchronize_session=False)
    db.add(EngineeringAuditEvent(project_id=project_id, actor_user_id=user.id, action="model.revision.created",
        before_json={"model_revision_id": latest_id}, after_json={"model_revision_id": revision.id, "source": payload.source}))

    impact = calculate_revision_impact(payload.document)
    quantities = impact["quantities"]
    estimate = QuantityEstimate(
        design_scenario_id=scenario_id,
        model_revision_id=revision.id,
        **quantities,
        total_cost_estimate=impact["total_cost_estimate"],
        line_items_json=[],
    )
    db.add(estimate)

    spec = document_to_geometry_spec(payload.document)
    # CAD meshes are fetched through authorized private references by the editor.
    # The ordinary export contains only non-CAD objects; no private mesh bytes
    # or B-reps enter its legacy file URL.
    glb = generate_glb(spec, quality="final")
    file_url = save_file(
        f"projects/{project_id}/scenario_{scenario_id}/revision_{revision_number}/model.glb",
        glb,
        "model/gltf-binary",
    )
    db.add(
        GeneratedFile(
            project_id=project_id,
            design_scenario_id=scenario_id,
            model_revision_id=revision.id,
            file_type="glb",
            file_url=file_url,
            metadata_json={"frame": "local_meters", "revision_number": revision_number},
        )
    )
    design = dict(scenario.design_output_json or {})
    design["geometry_spec"] = spec
    design["editable_model_revision_id"] = revision.id
    design["editable_model_revision_number"] = revision_number
    scenario.design_output_json = design
    if commit:
        db.commit()
        db.refresh(revision)
    else:
        db.flush()
    return {**revision_out(revision), "impact": impact, "model_url": file_url, "layout_validation": layout_validation}


@router.get("/{revision_id}")
def get_revision(project_id: int, scenario_id: int, revision_id: int,
                 db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    _scenario(db, project_id, scenario_id)
    revision = db.query(ModelRevision).filter_by(id=revision_id, project_id=project_id, design_scenario_id=scenario_id).one_or_none()
    if revision is None:
        raise HTTPException(404, "Revision not found")
    return revision_out(revision)


@router.post("/{revision_id}/ai-edit")
def preview_ai_edit(
    project_id: int,
    scenario_id: int,
    revision_id: int,
    payload: AiEditRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    _scenario(db, project_id, scenario_id)
    revision = db.get(ModelRevision, revision_id)
    if revision is None or revision.design_scenario_id != scenario_id:
        raise HTTPException(404, "Model revision not found")
    preview = build_ai_edit_preview(revision.document_json, payload.prompt)
    try:
        candidate = apply_component_patch(revision.document_json, preview["patch"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    errors = validate_document(
        candidate,
        project_id=project_id,
        scenario_id=scenario_id,
        project_type=project.project_type,
    )
    layout_validation = validate_layout(candidate)
    errors.extend(item["message"] for item in layout_validation["violations"])
    return {
        **preview,
        "base_revision_id": revision.id,
        "candidate_document": candidate,
        "validation_errors": errors,
        "impact_preview": calculate_revision_impact(candidate),
    }

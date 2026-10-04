"""Structural layout intelligence endpoints built on immutable model revisions."""
import hashlib
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user, get_current_user_id
from app.db.models import AuditLog, DesignScenario, ModelRevision, User
from app.db.session import get_db
from app.services.design.structural_layout import analysis_package, alternative_summaries, validate_layout
from app.services.design.editable_model import validate_document

router = APIRouter(prefix="/api/projects/{project_id}/scenarios/{scenario_id}/structural-layout", tags=["structural-layout"])


class DraftValidation(BaseModel):
    document: dict[str, Any]


class AnalysisFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component_id: str = Field(min_length=1, max_length=255)
    status: Literal["pass", "warning", "fail"]
    message: str = Field(min_length=1, max_length=2000)


class AnalysisResultImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format: Literal["sitegeoai.structural-analysis-result/v1"]
    revision_id: int
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    solver: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=4000)
    findings: list[AnalysisFinding] = Field(max_length=10000)


def document_hash(document: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@router.post("/validate")
def validate_draft(project_id: int, scenario_id: int, payload: DraftValidation, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    project = get_owned_project(project_id, db, user_id)
    scenario = db.get(DesignScenario, scenario_id)
    if scenario is None or scenario.project_id != project_id:
        raise HTTPException(404, "Scenario not found")
    try:
        errors = validate_document(payload.document, project_id=project_id, scenario_id=scenario_id, project_type=project.project_type)
        if errors:
            raise HTTPException(422, {"message": "Invalid model document", "errors": errors})
        return validate_layout(payload.document)
    except (ValueError, TypeError, AttributeError, IndexError, OverflowError) as exc:
        raise HTTPException(422, "Invalid structural layout values") from exc

def require_layout_approval(db: Session, revision: ModelRevision) -> AuditLog:
    validation = validate_layout(revision.document_json)
    if not validation["passed"]:
        raise HTTPException(422, {"message": "Layout rules failed", "violations": validation["violations"]})
    approval = db.query(AuditLog).filter(
        AuditLog.project_id == revision.project_id,
        AuditLog.entity_type == "model_revision",
        AuditLog.entity_id == str(revision.id),
        AuditLog.action == "layout.approved",
    ).order_by(AuditLog.id.desc()).first()
    if approval is None:
        raise HTTPException(409, "Engineer approval of this revision is required before formal export")
    return approval

def _revision(db: Session, project_id: int, scenario_id: int, revision_id: int) -> ModelRevision:
    revision = db.get(ModelRevision, revision_id)
    if revision is None or revision.project_id != project_id or revision.design_scenario_id != scenario_id:
        raise HTTPException(404, "Layout revision not found")
    return revision

@router.get("/{revision_id}/validation")
def validation(project_id: int, scenario_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    return validate_layout(_revision(db, project_id, scenario_id, revision_id).document_json)

@router.get("/{revision_id}/alternatives")
def alternatives(project_id: int, scenario_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    return {"alternatives": alternative_summaries(_revision(db, project_id, scenario_id, revision_id).document_json)}

@router.get("/{revision_id}/analysis-package")
def package(project_id: int, scenario_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    revision = _revision(db, project_id, scenario_id, revision_id)
    approval = require_layout_approval(db, revision)
    result = analysis_package(revision.document_json, revision, validate_layout(revision.document_json))
    result["document_sha256"] = document_hash(revision.document_json)
    result["result_import_format"] = "sitegeoai.structural-analysis-result/v1"
    result["approval"] = {"approved_by": approval.user_id, "approved_at": approval.created_at, "audit_id": approval.id}
    db.add(AuditLog(user_id=user_id, project_id=project_id, action="layout.exported", entity_type="model_revision", entity_id=str(revision.id), metadata_json={"format": result["format"]}))
    db.commit()
    return result


@router.get("/{revision_id}/analysis-results")
def analysis_results(project_id: int, scenario_id: int, revision_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    _revision(db, project_id, scenario_id, revision_id)
    rows = db.query(AuditLog).filter(AuditLog.project_id == project_id, AuditLog.entity_id == str(revision_id), AuditLog.entity_type == "model_revision", AuditLog.action == "layout.analysis_imported").order_by(AuditLog.id.desc()).all()
    return {"results": [{"id": row.id, "imported_at": row.created_at, **row.metadata_json} for row in rows]}


@router.post("/{revision_id}/analysis-results")
def import_analysis_results(project_id: int, scenario_id: int, revision_id: int, payload: AnalysisResultImport, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_project(project_id, db, user.id)
    revision = _revision(db, project_id, scenario_id, revision_id)
    if payload.revision_id != revision.id or payload.document_sha256 != document_hash(revision.document_json):
        raise HTTPException(409, "Analysis results belong to a different layout revision")
    ids = {item["id"] for item in revision.document_json["components"]}
    if any(item.component_id not in ids for item in payload.findings):
        raise HTTPException(422, "Analysis result references an unknown component")
    row = AuditLog(user_id=user.id, project_id=project_id, action="layout.analysis_imported", entity_type="model_revision", entity_id=str(revision_id), metadata_json=payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "imported_at": row.created_at, **row.metadata_json}

@router.post("/{revision_id}/approve")
def approve(project_id: int, scenario_id: int, revision_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_project(project_id, db, user.id)
    if user.role not in {"admin", "engineer"}:
        raise HTTPException(403, "An authorized engineer must approve this layout")
    revision = _revision(db, project_id, scenario_id, revision_id)
    validation = validate_layout(revision.document_json)
    if not validation["passed"]:
        raise HTTPException(422, {"message": "Resolve all rule violations before approval", "violations": validation["violations"]})
    db.add(AuditLog(user_id=user.id, project_id=project_id, action="layout.approved",
                    entity_type="model_revision", entity_id=str(revision.id),
                    metadata_json={"preset": validation["preset"], "role": user.role}))
    db.commit()
    return {"approved": True, "revision_id": revision.id, "validation": validation}

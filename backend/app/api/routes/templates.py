from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user, get_current_user_id
from app.db.models import ProjectTemplate, User
from app.db.session import get_db
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/admin/templates", tags=["admin"])
public_router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateIn(BaseModel):
    project_type: str
    name: str
    default_parameters_json: dict


def _out(t: ProjectTemplate) -> dict:
    return {
        "id": t.id,
        "project_type": t.project_type,
        "name": t.name,
        "default_parameters_json": t.default_parameters_json,
        "updated_at": t.updated_at,
    }


@router.get("")
def list_templates(
    project_type: str | None = None,
    db: Session = Depends(get_db),
    _user_id: int = Depends(get_current_user_id),
):
    """Read-only template library for all authenticated users."""
    query = db.query(ProjectTemplate)
    if project_type:
        query = query.filter(ProjectTemplate.project_type == project_type)
    return [_out(t) for t in query.order_by(ProjectTemplate.project_type)]


@public_router.get("")
def list_templates_public(
    project_type: str | None = None,
    db: Session = Depends(get_db),
    _user_id: int = Depends(get_current_user_id),
):
    return list_templates(project_type=project_type, db=db, _user_id=_user_id)


@router.post("", status_code=201)
def create_template(
    payload: TemplateIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    template = ProjectTemplate(**payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    log_audit_event(
        db,
        user_id=admin.id,
        action="template.create",
        entity_type="template",
        entity_id=template.id,
        metadata={"project_type": template.project_type, "name": template.name},
        request=request,
    )
    return _out(template)


@router.put("/{template_id}")
def update_template(
    template_id: int,
    payload: TemplateIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    template = db.get(ProjectTemplate, template_id)
    if template is None:
        raise HTTPException(404, "Template not found")
    for key, value in payload.model_dump().items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    log_audit_event(
        db,
        user_id=admin.id,
        action="template.update",
        entity_type="template",
        entity_id=template.id,
        metadata={"project_type": template.project_type, "name": template.name},
        request=request,
    )
    return _out(template)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    template = db.get(ProjectTemplate, template_id)
    if template is None:
        raise HTTPException(404, "Template not found")
    meta = {"project_type": template.project_type, "name": template.name}
    db.delete(template)
    db.commit()
    log_audit_event(
        db,
        user_id=admin.id,
        action="template.delete",
        entity_type="template",
        entity_id=template_id,
        metadata=meta,
        request=request,
    )

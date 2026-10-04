from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.services import jobs
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
def job_status(job_id: str, user_id: int = Depends(get_current_user_id)):
    if not jobs.user_can_access_job(job_id, user_id):
        raise HTTPException(404, "Job not found")
    status = jobs.public_status(job_id)
    if status is None:
        raise HTTPException(404, "Job not found")
    return status


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, request: Request, user_id: int = Depends(get_current_user_id)):
    if not jobs.user_can_access_job(job_id, user_id):
        raise HTTPException(404, "Job not found")
    job_meta = jobs.get_status(job_id) or {}
    status = jobs.cancel_job(job_id)
    if status is None:
        raise HTTPException(404, "Job not found")
    db = SessionLocal()
    try:
        log_audit_event(
            db,
            user_id=user_id,
            action="generation.cancelled",
            entity_type="job",
            entity_id=job_id,
            project_id=job_meta.get("project_id"),
            metadata={"failed_stage": status.get("failed_stage")},
            request=request,
        )
    finally:
        db.close()
    return status

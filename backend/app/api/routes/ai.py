"""Retired legacy chat URLs: no simulated AI or fabricated streaming."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user_id
from app.db.session import get_db

router = APIRouter(prefix="/api/projects/{project_id}/ai", tags=["ai"])
class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
@router.post("/chat/stream")
async def chat(project_id: int, payload: ChatMessage, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    raise HTTPException(410, "Legacy chat is retired. Use the site-wide Nebius Assistant; no offline fallback is available.")

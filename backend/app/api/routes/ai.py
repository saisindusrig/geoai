"""AI assistant endpoint for the workspace chat panel."""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.projects import get_owned_project
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.ai.copilot import run_copilot

router = APIRouter(prefix="/api/projects/{project_id}/ai", tags=["ai"])


class ChatMessage(BaseModel):
    message: str


@router.post("/chat")
async def chat(
    project_id: int,
    payload: ChatMessage,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    return await run_copilot(db, project, payload.message)


@router.post("/chat/stream")
async def chat_stream(
    project_id: int,
    payload: ChatMessage,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    result = await run_copilot(db, project, payload.message)
    message = result.get("message") or result.get("reply") or ""

    def generate():
        chunk_size = max(8, len(message) // 12) if message else 1
        for i in range(0, max(len(message), 1), chunk_size):
            part = message[i : i + chunk_size]
            yield f"data: {json.dumps({'chunk': part})}\n\n"
        yield f"data: {json.dumps({
            'done': True,
            'message': message,
            'actions': result.get('actions', []),
            'warnings': result.get('warnings', []),
            'provider': result.get('provider'),
            'action': result.get('action'),
            'disclaimer': result.get('disclaimer'),
        })}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

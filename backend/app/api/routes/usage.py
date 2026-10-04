"""User usage summary API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.services.usage import get_usage_summary

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/summary")
def usage_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_usage_summary(db, user)

"""Auth — mock dev user with optional JWT bearer tokens."""

import logging
from typing import Any

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.plans import PLAN_ADMIN
from app.db.models import User
from app.db.session import get_db

logger = logging.getLogger(__name__)

DEV_USER_ID = 1
ALGORITHM = "HS256"
ROLE_USER = "user"
ROLE_ADMIN = "admin"


def create_access_token(user_id: int, extra: dict[str, Any] | None = None) -> str:
    payload = {"sub": str(user_id), **(extra or {})}
    return jwt.encode(payload, settings.APP_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.APP_SECRET, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(401, "Invalid token")
        return int(sub)
    except (JWTError, ValueError) as e:
        raise HTTPException(401, "Invalid or expired token") from e


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_mock_user_id: int | None = Header(default=None),
) -> int:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        return decode_token(token)
    if settings.AUTH_REQUIRE_JWT:
        raise HTTPException(401, "Authorization required")
    return x_mock_user_id if x_mock_user_id is not None else DEV_USER_ID


def _dev_mock_role() -> str:
    role = (settings.DEV_MOCK_USER_ROLE or ROLE_ADMIN).lower()
    return ROLE_ADMIN if role == ROLE_ADMIN else ROLE_USER


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is not None:
        return user
    if settings.AUTH_REQUIRE_JWT:
        raise HTTPException(401, "User not found")
    return User(
        id=user_id,
        name="Dev User",
        email="dev@example.com",
        role=_dev_mock_role(),
        plan=PLAN_ADMIN if _dev_mock_role() == ROLE_ADMIN else "free",
    )


def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    return require_admin(user)


def require_admin(user: User) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(403, "Admin access required")
    return user


def is_admin(user: User) -> bool:
    return user.role == ROLE_ADMIN

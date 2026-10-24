"""Registration, login, and JWT token endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.passwords import hash_password, verify_password
from app.core.plans import PLAN_ADMIN
from app.core.security import DEV_USER_ID, ROLE_USER, create_access_token, get_current_user, get_current_user_id
from app.db.models import User
from app.db.session import get_db
from app.services.audit import log_audit_event
from app.services.rate_limit import enforce_rate_limit, enforce_login_account_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Equalize the expensive password check for unknown/passwordless accounts.
# This is a non-user dummy hash, never a valid account credential.
_DUMMY_PASSWORD_HASH = hash_password("struvocivil-non-user-timing-check")


def _require_legacy_auth():
    if settings.FIREBASE_AUTH_ENABLED:
        raise HTTPException(403, 'Password and development-token login are disabled in Firebase mode')


@router.get('/config')
def auth_configuration():
    from app.core.firebase_auth import readiness
    state = readiness()
    return {'mode': 'firebase' if settings.FIREBASE_AUTH_ENABLED else
            'legacy_jwt' if settings.AUTH_REQUIRE_JWT else 'local_development',
            'firebase': state, 'firebase_project_id': settings.FIREBASE_PROJECT_ID if state['enabled'] else None,
            'password_login_allowed': not settings.FIREBASE_AUTH_ENABLED,
            'registration_allowed': not settings.FIREBASE_AUTH_ENABLED and settings.ENVIRONMENT.lower() not in {'production', 'prod'}}


class TokenRequest(BaseModel):
    user_id: int = DEV_USER_ID


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role or ROLE_USER,
        "plan": user.plan or "free",
    }


def _issue_token(user: User) -> dict:
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "user": _user_out(user)}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    _require_legacy_auth()
    if settings.ENVIRONMENT.lower() in {"production", "prod"}:
        # Production onboarding belongs to the reviewed Firebase/linking flow.
        # Reject before looking up the address, regardless of account existence.
        raise HTTPException(403, "Legacy registration is unavailable in production")
    enforce_rate_limit("auth.register", request=request)
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=ROLE_USER,
        plan="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit_event(
        db,
        user_id=user.id,
        action="auth.register",
        entity_type="user",
        entity_id=user.id,
        metadata={"email": email},
        request=request,
    )
    return _issue_token(user)


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    _require_legacy_auth()
    enforce_rate_limit("auth.login", request=request)
    email = payload.email.strip().lower()
    enforce_login_account_limit(email)
    user = db.query(User).filter(User.email == email).first()
    valid_password = verify_password(payload.password, user.password_hash if user and user.password_hash else _DUMMY_PASSWORD_HASH)
    if user is None or not user.password_hash or not valid_password:
        log_audit_event(
            db,
            user_id=user.id if user else None,
            action="auth.login_failed",
            entity_type="user",
            metadata={"email": email},
            request=request,
        )
        raise HTTPException(401, "Invalid email or password")
    log_audit_event(
        db,
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        metadata={"email": email},
        request=request,
    )
    return _issue_token(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/token")
def issue_token(payload: TokenRequest, db: Session = Depends(get_db)):
    """Dev-only shortcut to mint a JWT without password. Disabled in production."""
    _require_legacy_auth()
    if settings.AUTH_REQUIRE_JWT or settings.ENVIRONMENT.lower() in ("production", "prod"):
        raise HTTPException(403, "Dev token endpoint is disabled when authentication is enforced")
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    return _issue_token(user)

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.bootstrap import verify_password
from app.auth.jwt import AuthTokenError, create_access_token, decode_access_token
from app.db.session import get_db_session
from app.models.public import Tenant, User, UserTenant

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def _api_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": {}})


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Invalid email")
        return normalized
    password: str


def _active_tenants(session: Session, user_id):
    stmt = (
        select(UserTenant, Tenant)
        .join(Tenant, Tenant.id == UserTenant.tenant_id)
        .where(UserTenant.user_id == user_id, UserTenant.status == "active", Tenant.status == "active")
        .order_by(Tenant.name)
    )
    return session.execute(stmt).all()


def _tenant_payload(rows):
    return [
        {"tenant_id": str(tenant.id), "tenant_name": tenant.name, "tenant_slug": tenant.slug, "role": link.role}
        for link, tenant in rows
    ]


def get_current_admin_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), session: Session = Depends(get_db_session)) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _api_error("AUTHENTICATION_REQUIRED", "Authorization bearer token is required.", 401)
    try:
        payload = decode_access_token(credentials.credentials)
    except AuthTokenError as exc:
        raise _api_error("AUTHENTICATION_REQUIRED", str(exc), 401) from exc
    user = session.get(User, payload["sub"])
    if user is None or user.status != "active":
        raise _api_error("AUTHENTICATION_REQUIRED", "Authenticated user is not active.", 401)
    return user


@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_db_session)):
    user = session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or user.status != "active" or not verify_password(payload.password, user.password_hash):
        raise _api_error("AUTHENTICATION_REQUIRED", "Invalid email or password.", 401)
    if not _active_tenants(session, user.id):
        raise _api_error("AUTHORIZATION_FAILED", "User has no active tenant access.", 403)
    try:
        token, expires_in = create_access_token(user_id=user.id, email=user.email)
    except AuthTokenError as exc:
        raise _api_error("AUTHENTICATION_REQUIRED", str(exc), 500) from exc
    return {"data": {"access_token": token, "token_type": "bearer", "expires_in": expires_in}}


@router.get("/me")
def me(user: User = Depends(get_current_admin_user), session: Session = Depends(get_db_session)):
    rows = _active_tenants(session, user.id)
    return {"data": {"id": str(user.id), "email": user.email, "full_name": user.full_name, "tenants": _tenant_payload(rows)}}

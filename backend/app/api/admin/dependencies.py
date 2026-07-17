from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.api.auth import get_current_admin_user
from app.models.public import Tenant, UserTenant, User
from app.tenancy.context import TenantContext
from app.tenancy.schema import is_valid_tenant_schema_name


def _api_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": {}})


def require_admin_tenant_id(
    x_totalchat_tenant_id: UUID | None = Header(default=None, alias="X-TotalChat-Tenant-Id"),
) -> UUID:
    if x_totalchat_tenant_id is None:
        raise _api_error("AUTHENTICATION_REQUIRED", "X-TotalChat-Tenant-Id header is required.", 401)
    return x_totalchat_tenant_id


def get_admin_tenant_context(
    x_totalchat_tenant_id: UUID = Depends(require_admin_tenant_id),
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_admin_user),
) -> TenantContext:
    """Resolve trusted admin tenant context from bearer token and selected tenant header."""
    tenant = session.get(Tenant, x_totalchat_tenant_id)
    if tenant is None or tenant.status != "active":
        raise _api_error("TENANT_NOT_FOUND", "Tenant not found.", 404)
    if not is_valid_tenant_schema_name(tenant.schema_name):
        raise _api_error("TENANT_NOT_FOUND", "Tenant not found.", 404)

    link = session.get(UserTenant, {"user_id": user.id, "tenant_id": tenant.id})
    if link is None or link.status != "active":
        raise _api_error("AUTHORIZATION_FAILED", "User is not authorized for the selected tenant.", 403)

    if session.get_bind().dialect.name != "sqlite":
        session.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))

    return TenantContext(tenant_id=tenant.id, slug=tenant.slug, schema_name=tenant.schema_name)

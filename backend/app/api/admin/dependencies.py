from __future__ import annotations

import re
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.public import Tenant
from app.tenancy.context import TenantContext

_SCHEMA_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _api_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": {}})


def get_admin_tenant_context(
    x_totalchat_tenant_id: UUID | None = Header(default=None, alias="X-TotalChat-Tenant-Id"),
    session: Session = Depends(get_db_session),
) -> TenantContext:
    """Resolve trusted admin tenant context from the selected tenant header.

    TODO(auth/admin): enforce authenticated admin user-to-tenant authorization before
    allowing access to tenant-scoped admin resources. This baseline only trusts the
    admin tenant selection header and validates the tenant record is active.
    """
    if x_totalchat_tenant_id is None:
        raise _api_error("AUTHENTICATION_REQUIRED", "X-TotalChat-Tenant-Id header is required.", 401)

    tenant = session.get(Tenant, x_totalchat_tenant_id)
    if tenant is None or tenant.status != "active":
        raise _api_error("TENANT_NOT_FOUND", "Tenant not found.", 404)
    if not _SCHEMA_NAME_RE.fullmatch(tenant.schema_name):
        raise _api_error("TENANT_NOT_FOUND", "Tenant not found.", 404)

    session.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))

    return TenantContext(tenant_id=tenant.id, slug=tenant.slug, schema_name=tenant.schema_name)

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.public import Tenant, User, UserTenant

AdminRole = Literal["owner", "admin", "staff", "readonly"]
ALLOWED_ADMIN_ROLES: frozenset[str] = frozenset({"owner", "admin", "staff", "readonly"})


class AdminBootstrapError(ValueError):
    """Raised when an admin bootstrap request is invalid or unsafe."""


@dataclass(frozen=True)
class AdminBootstrapResult:
    email: str
    full_name: str
    tenant_id: UUID
    tenant_slug: str
    tenant_name: str
    role: str
    user_created: bool
    user_updated: bool
    user_reactivated: bool
    link_created: bool
    link_reactivated: bool
    link_updated: bool


def hash_password(password: str) -> str:
    if not password:
        raise AdminBootstrapError("Password is required.")
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class AdminUserBootstrapService:
    """Internal service for bootstrapping tenant admin users in public tables only."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def bootstrap_admin_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        role: str = "owner",
        tenant_slug: str | None = None,
        tenant_id: UUID | None = None,
        reactivate_user: bool = True,
    ) -> AdminBootstrapResult:
        normalized_email = email.strip().lower()
        normalized_name = full_name.strip()
        normalized_role = role.strip().lower()

        if normalized_role not in ALLOWED_ADMIN_ROLES:
            raise AdminBootstrapError(f"Invalid role: {role}.")
        if not normalized_email:
            raise AdminBootstrapError("Email is required.")
        if not normalized_name:
            raise AdminBootstrapError("Full name is required.")
        if not tenant_slug and not tenant_id:
            raise AdminBootstrapError("tenant_slug or tenant_id is required.")

        tenant = self._find_active_tenant(tenant_slug=tenant_slug, tenant_id=tenant_id)
        password_hash = hash_password(password)

        user = self.session.scalar(select(User).where(User.email == normalized_email))
        user_created = False
        user_updated = False
        user_reactivated = False
        if user is None:
            user = User(email=normalized_email, full_name=normalized_name, password_hash=password_hash, status="active")
            self.session.add(user)
            self.session.flush()
            user_created = True
        else:
            if user.full_name != normalized_name:
                user.full_name = normalized_name
                user_updated = True
            if user.status != "active" and reactivate_user:
                user.status = "active"
                user_reactivated = True
            # Bootstrap intentionally rotates the credential for the same email only;
            # it never moves existing tenant memberships implicitly.
            user.password_hash = password_hash
            user_updated = True

        link = self.session.get(UserTenant, {"user_id": user.id, "tenant_id": tenant.id})
        link_created = False
        link_reactivated = False
        link_updated = False
        if link is None:
            link = UserTenant(user_id=user.id, tenant_id=tenant.id, role=normalized_role, status="active")
            self.session.add(link)
            link_created = True
        else:
            if link.status != "active":
                link.status = "active"
                link_reactivated = True
            if link.role != normalized_role:
                link.role = normalized_role
                link_updated = True

        self.session.commit()
        return AdminBootstrapResult(
            email=user.email,
            full_name=user.full_name,
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            tenant_name=tenant.name,
            role=link.role,
            user_created=user_created,
            user_updated=user_updated,
            user_reactivated=user_reactivated,
            link_created=link_created,
            link_reactivated=link_reactivated,
            link_updated=link_updated,
        )

    def _find_active_tenant(self, *, tenant_slug: str | None, tenant_id: UUID | None) -> Tenant:
        if tenant_id is not None:
            tenant = self.session.get(Tenant, tenant_id)
        else:
            tenant = self.session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
        if tenant is None:
            raise AdminBootstrapError("Tenant not found.")
        if tenant.status != "active":
            raise AdminBootstrapError("Tenant is not active.")
        return tenant

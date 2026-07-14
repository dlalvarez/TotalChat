from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.bootstrap import AdminBootstrapError, AdminUserBootstrapService, verify_password
from app.db.base import Base
from app.models.public import Tenant, User, UserTenant


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS public")
    Base.metadata.create_all(engine)
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def add_tenant(session: Session, *, slug: str = "clinica", status: str = "active") -> Tenant:
    tenant = Tenant(name="Clínica", slug=slug, schema_name="tenant_clinica", status=status)
    session.add(tenant)
    session.commit()
    return tenant


def test_bootstrap_creates_new_owner_user_for_active_tenant(session: Session) -> None:
    tenant = add_tenant(session)

    result = AdminUserBootstrapService(session).bootstrap_admin_user(
        tenant_slug="clinica",
        email="Admin@Clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
    )

    user = session.scalar(select(User).where(User.email == "admin@clinica.com"))
    assert user is not None
    assert result.user_created is True
    assert result.role == "owner"
    assert result.tenant_id == tenant.id
    assert user.full_name == "Admin Clínica"
    assert user.status == "active"


def test_bootstrap_creates_user_tenant_link(session: Session) -> None:
    tenant = add_tenant(session)

    AdminUserBootstrapService(session).bootstrap_admin_user(
        tenant_id=tenant.id,
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
        role="admin",
    )

    user = session.scalar(select(User).where(User.email == "admin@clinica.com"))
    link = session.get(UserTenant, {"user_id": user.id, "tenant_id": tenant.id})
    assert link is not None
    assert link.role == "admin"
    assert link.status == "active"


def test_bootstrap_rejects_missing_tenant(session: Session) -> None:
    with pytest.raises(AdminBootstrapError, match="Tenant not found"):
        AdminUserBootstrapService(session).bootstrap_admin_user(
            tenant_slug="missing",
            email="admin@clinica.com",
            full_name="Admin Clínica",
            password="secret-password",
        )


def test_bootstrap_rejects_inactive_tenant(session: Session) -> None:
    add_tenant(session, status="inactive")

    with pytest.raises(AdminBootstrapError, match="not active"):
        AdminUserBootstrapService(session).bootstrap_admin_user(
            tenant_slug="clinica",
            email="admin@clinica.com",
            full_name="Admin Clínica",
            password="secret-password",
        )


def test_bootstrap_rejects_invalid_role(session: Session) -> None:
    add_tenant(session)

    with pytest.raises(AdminBootstrapError, match="Invalid role"):
        AdminUserBootstrapService(session).bootstrap_admin_user(
            tenant_slug="clinica",
            email="admin@clinica.com",
            full_name="Admin Clínica",
            password="secret-password",
            role="superuser",
        )


def test_bootstrap_service_does_not_accept_or_return_schema_name(session: Session) -> None:
    add_tenant(session)

    result = AdminUserBootstrapService(session).bootstrap_admin_user(
        tenant_slug="clinica",
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
    )

    assert not hasattr(result, "schema_name")
    with pytest.raises(TypeError):
        AdminUserBootstrapService(session).bootstrap_admin_user(  # type: ignore[call-arg]
            tenant_slug="clinica",
            schema_name="tenant_evil",
            email="admin2@clinica.com",
            full_name="Admin Clínica",
            password="secret-password",
        )


def test_bootstrap_is_idempotent_for_same_user_and_tenant(session: Session) -> None:
    add_tenant(session)
    service = AdminUserBootstrapService(session)

    first = service.bootstrap_admin_user(
        tenant_slug="clinica",
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
    )
    second = service.bootstrap_admin_user(
        tenant_slug="clinica",
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="new-secret-password",
    )

    assert first.user_created is True
    assert second.user_created is False
    assert session.query(User).count() == 1
    assert session.query(UserTenant).count() == 1


def test_bootstrap_reactivates_inactive_user_tenant_link(session: Session) -> None:
    tenant = add_tenant(session)
    user = User(email="admin@clinica.com", full_name="Admin Clínica", password_hash="old-hash", status="active")
    session.add(user)
    session.flush()
    session.add(UserTenant(user_id=user.id, tenant_id=tenant.id, role="owner", status="inactive"))
    session.commit()

    result = AdminUserBootstrapService(session).bootstrap_admin_user(
        tenant_slug="clinica",
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
        role="owner",
    )

    link = session.get(UserTenant, {"user_id": user.id, "tenant_id": tenant.id})
    assert result.link_reactivated is True
    assert link.status == "active"


def test_bootstrap_stores_hashed_password_not_plain_text(session: Session) -> None:
    add_tenant(session)

    AdminUserBootstrapService(session).bootstrap_admin_user(
        tenant_slug="clinica",
        email="admin@clinica.com",
        full_name="Admin Clínica",
        password="secret-password",
    )

    user = session.scalar(select(User).where(User.email == "admin@clinica.com"))
    assert user.password_hash != "secret-password"
    assert user.password_hash.startswith("$2")
    assert verify_password("secret-password", user.password_hash) is True

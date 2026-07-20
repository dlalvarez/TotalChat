from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.public import Tenant
from app.tenancy.provisioning import (
    REQUIRED_TENANT_MIGRATIONS,
    TenantProvisioningError,
    TenantProvisioningService,
)


class FakeInspector:
    def __init__(self, schema_exists: bool) -> None:
        self.schema_exists = schema_exists

    def has_schema(self, schema_name: str) -> bool:
        return self.schema_exists


def _patch_schema_ops(monkeypatch: pytest.MonkeyPatch, *, schema_exists: bool = False, migrations_current: bool = False) -> dict[str, list[str]]:
    calls: dict[str, list[str]] = {"create": [], "base": [], "booking": []}
    monkeypatch.setattr("app.tenancy.provisioning.inspect", lambda connection: FakeInspector(schema_exists))
    monkeypatch.setattr("app.tenancy.provisioning.create_tenant_schema", lambda connection, schema_name: calls["create"].append(schema_name))
    monkeypatch.setattr("app.tenancy.provisioning.apply_base_tenant_migration", lambda connection, schema_name: calls["base"].append(schema_name))
    monkeypatch.setattr("app.tenancy.provisioning.apply_booking_domain_tenant_migration", lambda connection, schema_name: calls["booking"].append(schema_name))
    monkeypatch.setattr(TenantProvisioningService, "_migrations_current", lambda self, schema_name: migrations_current)
    return calls


def test_provision_tenant_creates_public_row_and_schema_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_schema_ops(monkeypatch)
    session = Mock()
    connection = Mock()
    session.connection.return_value = connection
    session.scalar.return_value = None

    context = TenantProvisioningService(session).provision_tenant(name="Tenant Alpha", slug="tenant-alpha", provision_schema=True)

    added_tenant = session.add.call_args.args[0]
    assert isinstance(added_tenant, Tenant)
    assert added_tenant.schema_name == "tenant_tenant_alpha"
    assert context.schema_name == "tenant_tenant_alpha"
    session.flush.assert_called_once()
    assert calls == {"create": ["tenant_tenant_alpha"], "base": ["tenant_tenant_alpha"], "booking": ["tenant_tenant_alpha"]}


def test_idempotent_provisioning_existing_active_does_not_duplicate_and_reports_current(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_schema_ops(monkeypatch, schema_exists=True, migrations_current=True)
    tenant = Tenant(id=uuid4(), name="Tenant Alpha", slug="tenant-alpha", schema_name="tenant_tenant_alpha", status="active")
    session = Mock()
    session.scalar.return_value = tenant

    result = TenantProvisioningService(session).provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")

    session.add.assert_not_called()
    session.flush.assert_not_called()
    assert result.tenant_id == tenant.id
    assert result.actions == ("tenant_exists", "schema_exists", "migrations_current")


def test_existing_inactive_tenant_fails_without_reactivation(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_schema_ops(monkeypatch)
    tenant = Tenant(id=uuid4(), name="Tenant Alpha", slug="tenant-alpha", schema_name="tenant_tenant_alpha", status="inactive")
    session = Mock()
    session.scalar.return_value = tenant

    with pytest.raises(TenantProvisioningError, match="not active"):
        TenantProvisioningService(session).provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")
    assert tenant.status == "inactive"


def test_existing_active_tenant_missing_schema_creates_schema_and_applies_migrations(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_schema_ops(monkeypatch, schema_exists=False)
    tenant = Tenant(id=uuid4(), name="Tenant Alpha", slug="tenant-alpha", schema_name="tenant_tenant_alpha", status="active")
    session = Mock()
    session.scalar.return_value = tenant

    result = TenantProvisioningService(session).provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")

    assert result.actions == ("tenant_exists", "schema_created", "migrations_applied")


def test_existing_schema_with_pending_migrations_applies_idempotently(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_schema_ops(monkeypatch, schema_exists=True, migrations_current=False)
    tenant = Tenant(id=uuid4(), name="Tenant Alpha", slug="tenant-alpha", schema_name="tenant_tenant_alpha", status="active")
    session = Mock()
    session.scalar.return_value = tenant

    result = TenantProvisioningService(session).provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")

    assert result.actions == ("tenant_exists", "schema_exists", "migrations_applied")
    assert calls["create"] == ["tenant_tenant_alpha"]
    assert calls["base"] == ["tenant_tenant_alpha"]
    assert calls["booking"] == ["tenant_tenant_alpha"]


def test_two_runs_with_same_slug_do_not_duplicate_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_schema_ops(monkeypatch, schema_exists=True, migrations_current=True)
    created: list[Tenant] = []
    session = Mock()
    session.scalar.side_effect = lambda statement: created[0] if created else None
    session.add.side_effect = lambda tenant: created.append(tenant)

    service = TenantProvisioningService(session)
    first = service.provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")
    second = service.provision_tenant_idempotently(name="Tenant Alpha", slug="tenant-alpha")

    assert len(created) == 1
    assert first.slug == second.slug == "tenant-alpha"
    assert second.actions == ("tenant_exists", "schema_exists", "migrations_current")


def test_semantic_documents_migration_is_required_for_current_schema() -> None:
    assert "009_semantic_documents" in REQUIRED_TENANT_MIGRATIONS

    session = Mock()
    connection = session.connection.return_value
    connection.execute.return_value = [
        (version,) for version in REQUIRED_TENANT_MIGRATIONS - {"009_semantic_documents"}
    ]

    assert TenantProvisioningService(session)._migrations_current("tenant_tenant_alpha") is False

    connection.execute.return_value = [(version,) for version in REQUIRED_TENANT_MIGRATIONS]
    assert TenantProvisioningService(session)._migrations_current("tenant_tenant_alpha") is True

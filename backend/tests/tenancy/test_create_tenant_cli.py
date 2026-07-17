from uuid import uuid4

import pytest

from app.tenancy import create_tenant
from app.tenancy.context import TenantContext
from app.tenancy.provisioning import TenantProvisioningError, TenantProvisioningResult


class FakeSession:
    committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


def _result() -> TenantProvisioningResult:
    tenant_id = uuid4()
    return TenantProvisioningResult(
        tenant_id=tenant_id,
        slug="clinica-demo",
        status="active",
        actions=("tenant_exists", "schema_exists", "migrations_current"),
        context=TenantContext(tenant_id=tenant_id, slug="clinica-demo", schema_name="tenant_clinica_demo"),
    )


def test_cli_outputs_safe_operational_result_without_schema_name(monkeypatch, capsys) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(create_tenant, "get_session_factory", lambda: lambda: fake_session)
    monkeypatch.setattr(
        create_tenant.TenantProvisioningService,
        "provision_tenant_idempotently",
        lambda self, name, slug: _result(),
    )

    exit_code = create_tenant.main(["--name", "Clínica Demo", "--slug", "clinica-demo"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert fake_session.committed is True
    assert "Tenant provisioning completed" in output
    assert "tenant_id=" in output
    assert "slug=clinica-demo" in output
    assert "status=active" in output
    assert "actions=tenant_exists,schema_exists,migrations_current" in output
    assert "schema_name" not in output
    assert "tenant_clinica_demo" not in output


def test_cli_rejects_schema_name_argument(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        create_tenant.main(["--name", "Clínica Demo", "--slug", "clinica-demo", "--schema-name", "tenant_custom"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "unrecognized arguments: --schema-name" in captured.err


def test_cli_invalid_slug_is_reported(monkeypatch, capsys) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(create_tenant, "get_session_factory", lambda: lambda: fake_session)

    def fail(self, name, slug):
        raise ValueError("Generated tenant schema name is invalid")

    monkeypatch.setattr(create_tenant.TenantProvisioningService, "provision_tenant_idempotently", fail)

    exit_code = create_tenant.main(["--name", "Invalid", "--slug", "invalid"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Tenant provisioning failed: Generated tenant schema name is invalid" in captured.err
    assert fake_session.committed is False


def test_cli_inactive_tenant_failure_is_clear(monkeypatch, capsys) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(create_tenant, "get_session_factory", lambda: lambda: fake_session)

    def fail(self, name, slug):
        raise TenantProvisioningError("Tenant exists but is not active; automatic reactivation is out of scope.")

    monkeypatch.setattr(create_tenant.TenantProvisioningService, "provision_tenant_idempotently", fail)

    exit_code = create_tenant.main(["--name", "Clínica Demo", "--slug", "clinica-demo"])

    assert exit_code == 2
    assert "automatic reactivation is out of scope" in capsys.readouterr().err
    assert fake_session.committed is False

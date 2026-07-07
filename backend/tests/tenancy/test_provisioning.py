from unittest.mock import Mock

from app.models.public import Tenant
from app.tenancy.provisioning import TenantProvisioningService


def test_provision_tenant_creates_public_row_and_schema_migration() -> None:
    session = Mock()
    connection = Mock()
    session.connection.return_value = connection

    context = TenantProvisioningService(session).provision_tenant(
        name="Tenant Alpha", slug="tenant-alpha", provision_schema=True
    )

    added_tenant = session.add.call_args.args[0]
    assert isinstance(added_tenant, Tenant)
    assert added_tenant.schema_name == "tenant_tenant_alpha"
    assert context.schema_name == "tenant_tenant_alpha"
    session.flush.assert_called_once()
    assert connection.execute.call_count == 3

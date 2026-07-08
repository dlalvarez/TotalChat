from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.public import Tenant
from app.tenancy.context import TenantContext
from app.tenancy.schema import apply_base_tenant_migration, apply_booking_domain_tenant_migration, create_tenant_schema, generate_tenant_schema_name


@dataclass(slots=True)
class TenantProvisioningService:
    session: Session

    def provision_tenant(self, *, name: str, slug: str, provision_schema: bool = True) -> TenantContext:
        schema_name = generate_tenant_schema_name(slug)
        tenant = Tenant(name=name, slug=slug, schema_name=schema_name, status="active")
        self.session.add(tenant)
        self.session.flush()

        if provision_schema:
            connection = self.session.connection()
            create_tenant_schema(connection, schema_name)
            apply_base_tenant_migration(connection, schema_name)
            apply_booking_domain_tenant_migration(connection, schema_name)

        return TenantContext(tenant_id=tenant.id, slug=tenant.slug, schema_name=tenant.schema_name)

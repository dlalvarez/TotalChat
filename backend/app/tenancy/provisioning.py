from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.public import Tenant
from app.tenancy.context import TenantContext
from app.tenancy.schema import (
    apply_base_tenant_migration,
    apply_booking_domain_tenant_migration,
    create_tenant_schema,
    generate_tenant_schema_name,
    is_valid_tenant_schema_name,
)

REQUIRED_TENANT_MIGRATIONS = frozenset(
    {
        "002_base",
        "003_booking_domain",
        "003_admin_cancellation_reason",
        "004_admin_reschedule_reason",
        "005_patient_payer_profiles",
        "006_manual_simulated_payments",
        "007_booking_notes",
        "007_organization_practitioners",
        "008_virtual_appointment_links",
    }
)


class TenantProvisioningError(RuntimeError):
    """Raised when a tenant cannot be provisioned safely."""


@dataclass(frozen=True, slots=True)
class TenantProvisioningResult:
    tenant_id: UUID
    slug: str
    status: str
    actions: tuple[str, ...]
    context: TenantContext


@dataclass(slots=True)
class TenantProvisioningService:
    session: Session

    def provision_tenant(self, *, name: str, slug: str, provision_schema: bool = True) -> TenantContext:
        """Backward-compatible provisioning API returning only tenant context."""
        return self.provision_tenant_idempotently(name=name, slug=slug, provision_schema=provision_schema).context

    def provision_tenant_idempotently(self, *, name: str, slug: str, provision_schema: bool = True) -> TenantProvisioningResult:
        schema_name = generate_tenant_schema_name(slug)
        tenant = self.session.scalar(select(Tenant).where(Tenant.slug == slug))
        actions: list[str] = []

        if tenant is None:
            tenant = Tenant(name=name, slug=slug, schema_name=schema_name, status="active")
            self.session.add(tenant)
            self.session.flush()
            actions.append("tenant_created")
        else:
            actions.append("tenant_exists")
            if tenant.status != "active":
                raise TenantProvisioningError("Tenant exists but is not active; automatic reactivation is out of scope.")
            if not is_valid_tenant_schema_name(tenant.schema_name):
                raise TenantProvisioningError("Tenant has an invalid stored schema name; manual intervention is required.")

        if provision_schema:
            schema_actions = self._ensure_schema_and_migrations(tenant.schema_name, schema_new_tenant="tenant_created" in actions)
            actions.extend(schema_actions)

        return TenantProvisioningResult(
            tenant_id=tenant.id,
            slug=tenant.slug,
            status=tenant.status,
            actions=tuple(actions),
            context=TenantContext(tenant_id=tenant.id, slug=tenant.slug, schema_name=tenant.schema_name),
        )

    def _ensure_schema_and_migrations(self, schema_name: str, *, schema_new_tenant: bool) -> list[str]:
        connection = self.session.connection()
        schema_exists = inspect(connection).has_schema(schema_name)
        migration_status = "migrations_applied"
        if schema_exists:
            migration_status = "migrations_current" if self._migrations_current(schema_name) else "migrations_applied"

        create_tenant_schema(connection, schema_name)
        apply_base_tenant_migration(connection, schema_name)
        apply_booking_domain_tenant_migration(connection, schema_name)

        schema_action = "schema_exists" if schema_exists else "schema_created"
        if schema_new_tenant and not schema_exists:
            migration_status = "migrations_applied"
        return [schema_action, migration_status]

    def _migrations_current(self, schema_name: str) -> bool:
        if not is_valid_tenant_schema_name(schema_name):
            raise TenantProvisioningError("Invalid tenant schema name")
        try:
            rows = self.session.connection().execute(
                text(f'SELECT version FROM "{schema_name}".tenant_schema_migrations')
            )
        except SQLAlchemyError:
            return False
        versions = {row[0] for row in rows}
        return REQUIRED_TENANT_MIGRATIONS.issubset(versions)

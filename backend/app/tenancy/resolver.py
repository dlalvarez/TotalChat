from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.public import Tenant, TenantChannel
from app.tenancy.context import TenantContext


@dataclass(slots=True)
class TenantResolver:
    session: Session

    def resolve_by_channel(self, *, channel_type: str, external_identifier: str) -> TenantContext | None:
        stmt = (
            select(Tenant)
            .join(TenantChannel, TenantChannel.tenant_id == Tenant.id)
            .where(
                TenantChannel.channel_type == channel_type,
                TenantChannel.external_identifier == external_identifier,
                TenantChannel.is_active.is_(True),
                Tenant.status == "active",
            )
        )
        tenant = self.session.execute(stmt).scalar_one_or_none()
        if tenant is None:
            return None
        return TenantContext(tenant_id=tenant.id, slug=tenant.slug, schema_name=tenant.schema_name)

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Explicit tenant context required for tenant-scoped operations.

    Backend services must receive this object from trusted platform resolution;
    LLMs, messaging channels, and automations must never select schema names.
    """

    tenant_id: UUID
    slug: str
    schema_name: str

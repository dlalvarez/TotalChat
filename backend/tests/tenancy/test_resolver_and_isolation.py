import uuid
from dataclasses import dataclass

from app.tenancy.context import TenantContext
from app.tenancy.resolver import TenantResolver


class ScalarResult:
    def __init__(self, tenant) -> None:
        self.tenant = tenant

    def scalar_one_or_none(self):
        return self.tenant


class FakeSession:
    def __init__(self, tenant) -> None:
        self.tenant = tenant
        self.executed = None

    def execute(self, stmt):
        self.executed = stmt
        return ScalarResult(self.tenant)


@dataclass
class FakeTenant:
    id: uuid.UUID
    slug: str
    schema_name: str


def test_resolver_returns_tenant_context_for_active_channel() -> None:
    tenant = FakeTenant(uuid.uuid4(), "tenant-a", "tenant_tenant_a")
    session = FakeSession(tenant)

    context = TenantResolver(session).resolve_by_channel(channel_type="telegram", external_identifier="bot_a")  # type: ignore[arg-type]

    assert context == TenantContext(tenant_id=tenant.id, slug="tenant-a", schema_name="tenant_tenant_a")
    assert "tenant_channels" in str(session.executed)


def test_resolver_returns_none_when_channel_is_unknown() -> None:
    assert TenantResolver(FakeSession(None)).resolve_by_channel(channel_type="telegram", external_identifier="missing") is None  # type: ignore[arg-type]


class TenantScopedMemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, str]] = {}

    def write(self, context: TenantContext, key: str, value: str) -> None:
        self._data.setdefault(context.schema_name, {})[key] = value

    def read(self, context: TenantContext, key: str) -> str | None:
        return self._data.get(context.schema_name, {}).get(key)


def test_tenant_scoped_operations_do_not_share_context_data() -> None:
    tenant_a = TenantContext(uuid.uuid4(), "tenant-a", "tenant_a")
    tenant_b = TenantContext(uuid.uuid4(), "tenant-b", "tenant_b")
    store = TenantScopedMemoryStore()

    store.write(tenant_a, "logical-id-1", "alpha")
    store.write(tenant_b, "logical-id-1", "bravo")

    assert store.read(tenant_a, "logical-id-1") == "alpha"
    assert store.read(tenant_b, "logical-id-1") == "bravo"

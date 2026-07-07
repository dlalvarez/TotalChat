from app.db.base import Base
from app.models.public import Tenant, TenantChannel, User, UserTenant
from app.tenancy.context import TenantContext


def test_public_models_are_registered() -> None:
    tables = Base.metadata.tables

    assert "public.tenants" in tables
    assert "public.tenant_channels" in tables
    assert "public.users" in tables
    assert "public.user_tenants" in tables
    assert Tenant.__tablename__ == "tenants"
    assert TenantChannel.__tablename__ == "tenant_channels"
    assert User.__tablename__ == "users"
    assert UserTenant.__tablename__ == "user_tenants"


def test_tenant_context_is_explicit_value_object() -> None:
    assert TenantContext.__dataclass_params__.frozen is True

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql.elements import TextClause

from app.tenancy.schema import apply_admin_cancellation_reason_tenant_migration, apply_booking_domain_tenant_migration


class RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement) -> None:  # type: ignore[no-untyped-def]
        if isinstance(statement, DDLElement):
            self.statements.append(str(statement.compile(dialect=postgresql.dialect())))
        elif isinstance(statement, TextClause):
            self.statements.append(str(statement))
        else:
            self.statements.append(str(statement))


def test_booking_domain_migration_creates_tables_in_tenant_schema_only() -> None:
    connection = RecordingConnection()
    apply_booking_domain_tenant_migration(connection, "tenant_alpha")  # type: ignore[arg-type]

    sql = "\n".join(connection.statements)
    assert "CREATE TABLE IF NOT EXISTS tenant_alpha.organizations" in sql
    assert "CREATE TABLE IF NOT EXISTS tenant_alpha.bookings" in sql
    assert "CREATE TABLE IF NOT EXISTS public.bookings" not in sql
    assert "public.organizations" not in sql
    assert "003_booking_domain" in sql
    assert 'ALTER TABLE "tenant_alpha".bookings' in sql
    assert "ADD COLUMN IF NOT EXISTS admin_cancellation_reason TEXT" in sql
    assert "003_admin_cancellation_reason" in sql


def test_booking_domain_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_booking_domain_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_admin_cancellation_reason_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_admin_cancellation_reason_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]

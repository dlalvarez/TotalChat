import pytest
from sqlalchemy.sql.elements import TextClause

from app.tenancy.schema import apply_base_tenant_migration, create_tenant_schema, generate_tenant_schema_name, is_valid_tenant_schema_name


def test_generate_tenant_schema_name_sanitizes_slug() -> None:
    assert generate_tenant_schema_name("Psicóloga Ana!") == "tenant_psicologa_ana"
    assert generate_tenant_schema_name("123-demo") == "tenant_t_123_demo"


@pytest.mark.parametrize("schema_name", ["public", "tenant_bad-name", "tenant_", "tenant_1bad", 'tenant_bad"'])
def test_invalid_schema_names_are_rejected(schema_name: str) -> None:
    assert not is_valid_tenant_schema_name(schema_name)


class RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement: TextClause) -> None:
        self.statements.append(str(statement))


def test_create_tenant_schema_and_base_migration_emit_schema_scoped_sql() -> None:
    connection = RecordingConnection()

    create_tenant_schema(connection, "tenant_alpha")  # type: ignore[arg-type]
    apply_base_tenant_migration(connection, "tenant_alpha")  # type: ignore[arg-type]

    joined = "\n".join(connection.statements)
    assert 'CREATE SCHEMA IF NOT EXISTS "tenant_alpha"' in joined
    assert '"tenant_alpha".tenant_schema_migrations' in joined
    assert "bookings" not in joined

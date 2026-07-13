from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine

from app.core.config import get_settings
from app.tenancy.schema import apply_base_tenant_migration, apply_booking_notes_tenant_migration, is_valid_tenant_schema_name

TenantMigration = Callable[[Connection, str], None]

@dataclass(frozen=True)
class PendingTenantMigration:
    version: str
    apply: TenantMigration

TENANT_MIGRATIONS: tuple[PendingTenantMigration, ...] = (
    PendingTenantMigration("007_booking_notes", apply_booking_notes_tenant_migration),
)


def discover_tenant_schemas(connection: Connection) -> list[str]:
    schemas = inspect(connection).get_schema_names()
    return sorted(schema for schema in schemas if is_valid_tenant_schema_name(schema))


def ensure_tenant_migration_table(connection: Connection, schema_name: str) -> None:
    apply_base_tenant_migration(connection, schema_name)


def tenant_has_migration(connection: Connection, schema_name: str, version: str) -> bool:
    result = connection.execute(text(f'SELECT 1 FROM "{schema_name}".tenant_schema_migrations WHERE version = :version'), {"version": version})
    return result.first() is not None


def apply_pending_migrations_to_schema(connection: Connection, schema_name: str, migrations: Sequence[PendingTenantMigration] = TENANT_MIGRATIONS) -> list[str]:
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")
    ensure_tenant_migration_table(connection, schema_name)
    applied: list[str] = []
    for migration in migrations:
        if tenant_has_migration(connection, schema_name, migration.version):
            continue
        migration.apply(connection, schema_name)
        applied.append(migration.version)
    return applied


def migrate_existing_tenants(engine: Engine | None = None) -> dict[str, list[str]]:
    if engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("TOTALCHAT_DATABASE_URL must be set before running tenant migrations")
        engine = create_engine(settings.database_url, pool_pre_ping=True)
    migrated: dict[str, list[str]] = {}
    with engine.begin() as connection:
        for schema_name in discover_tenant_schemas(connection):
            migrated[schema_name] = apply_pending_migrations_to_schema(connection, schema_name)
    return migrated


def main() -> None:
    migrated = migrate_existing_tenants()
    if not migrated:
        print("No tenant schemas found.")
        return
    for schema_name, applied in migrated.items():
        if applied:
            print(f"{schema_name}: applied {', '.join(applied)}")
        else:
            print(f"{schema_name}: up to date")

if __name__ == "__main__":
    main()

import re
import unicodedata

from sqlalchemy import Connection, MetaData, text
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base
import app.models.tenant  # noqa: F401 - register tenant models

MAX_PG_IDENTIFIER_LENGTH = 63
_SCHEMA_RE = re.compile(r"^tenant_[a-z][a-z0-9_]{0,55}$")


def generate_tenant_schema_name(slug: str) -> str:
    normalized = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode("ascii")
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    sanitized = re.sub(r"_+", "_", sanitized)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = f"t_{sanitized}" if sanitized else "tenant"
    schema_name = f"tenant_{sanitized}"[:MAX_PG_IDENTIFIER_LENGTH].rstrip("_")
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Generated tenant schema name is invalid")
    return schema_name


def is_valid_tenant_schema_name(schema_name: str) -> bool:
    return bool(_SCHEMA_RE.fullmatch(schema_name)) and len(schema_name) <= MAX_PG_IDENTIFIER_LENGTH


def create_tenant_schema(connection: Connection, schema_name: str) -> None:
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))


def apply_base_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Prepare tenant schema migration tracking without booking-domain tables."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")
    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".tenant_schema_migrations (
                version VARCHAR(64) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('002_base')
            ON CONFLICT (version) DO NOTHING
            '''
        )
    )


def apply_booking_domain_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Create booking-domain tables inside one validated tenant schema only."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")

    tenant_metadata = MetaData(schema=schema_name)
    tenant_tables = [table for table in Base.metadata.sorted_tables if table.schema is None]
    copied_tables = [table.to_metadata(tenant_metadata, schema=schema_name) for table in tenant_tables]

    for table in copied_tables:
        connection.execute(CreateTable(table, if_not_exists=True))
    for table in copied_tables:
        for index in table.indexes:
            connection.execute(CreateIndex(index, if_not_exists=True))

    connection.execute(
        text(
            f"""
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('003_booking_domain')
            ON CONFLICT (version) DO NOTHING
            """
        )
    )
    apply_admin_cancellation_reason_tenant_migration(connection, schema_name)


def apply_admin_cancellation_reason_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Add nullable admin cancellation reason to existing tenant booking tables."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")

    connection.execute(
        text(
            f'''
            ALTER TABLE "{schema_name}".bookings
            ADD COLUMN IF NOT EXISTS admin_cancellation_reason TEXT
            '''
        )
    )
    connection.execute(
        text(
            f'''
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('003_admin_cancellation_reason')
            ON CONFLICT (version) DO NOTHING
            '''
        )
    )

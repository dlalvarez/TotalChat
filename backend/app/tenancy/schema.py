import re
import unicodedata

from sqlalchemy import Connection, text

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

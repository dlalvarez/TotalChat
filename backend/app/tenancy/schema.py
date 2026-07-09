import re
import unicodedata

from sqlalchemy import Connection, MetaData, text
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base
import app.models.tenant  # noqa: F401 - register tenant models

MAX_PG_IDENTIFIER_LENGTH = 63
PAYMENT_TENANT_TABLES = {"payment_settings", "payment_attempts", "payment_evidence", "payment_reviews"}
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
    tenant_tables = [
        table
        for table in Base.metadata.sorted_tables
        if table.schema is None and table.name not in PAYMENT_TENANT_TABLES
    ]
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
    apply_admin_reschedule_reason_tenant_migration(connection, schema_name)
    apply_patient_payer_profiles_tenant_migration(connection, schema_name)
    apply_manual_payments_tenant_migration(connection, schema_name)


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


def apply_admin_reschedule_reason_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Add nullable admin reschedule reason to existing tenant booking tables."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")

    connection.execute(
        text(
            f'''
            ALTER TABLE "{schema_name}".bookings
            ADD COLUMN IF NOT EXISTS admin_reschedule_reason TEXT
            '''
        )
    )
    connection.execute(
        text(
            f'''
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('004_admin_reschedule_reason')
            ON CONFLICT (version) DO NOTHING
            '''
        )
    )


def apply_patient_payer_profiles_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Add patient payer profiles to existing tenant booking-domain schemas."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")

    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".patient_payer_profiles (
                id UUID NOT NULL,
                patient_id UUID NOT NULL,
                payer_plan_id UUID NOT NULL,
                member_id VARCHAR(120),
                authorization_required BOOLEAN DEFAULT false NOT NULL,
                notes TEXT,
                status VARCHAR(32) DEFAULT 'active' NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(patient_id) REFERENCES "{schema_name}".patients (id),
                FOREIGN KEY(payer_plan_id) REFERENCES "{schema_name}".payer_plans (id)
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('005_patient_payer_profiles')
            ON CONFLICT (version) DO NOTHING
            '''
        )
    )


def apply_manual_payments_tenant_migration(connection: Connection, schema_name: str) -> None:
    """Add manual and simulated payment persistence tables to tenant schemas."""
    if not is_valid_tenant_schema_name(schema_name):
        raise ValueError("Invalid tenant schema name")

    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".payment_settings (
                id UUID NOT NULL,
                organization_id UUID NOT NULL,
                allow_transfer BOOLEAN DEFAULT true NOT NULL,
                allow_simulated_payment BOOLEAN DEFAULT true NOT NULL,
                allow_pay_on_site BOOLEAN DEFAULT false NOT NULL,
                evidence_deadline_minutes INTEGER DEFAULT 60 NOT NULL,
                manual_review_deadline_minutes INTEGER DEFAULT 1440 NOT NULL,
                release_slot_on_missing_evidence BOOLEAN DEFAULT true NOT NULL,
                release_slot_on_review_overdue BOOLEAN DEFAULT false NOT NULL,
                status VARCHAR(32) DEFAULT 'active' NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(organization_id) REFERENCES "{schema_name}".organizations (id)
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".payment_attempts (
                id UUID NOT NULL,
                booking_id UUID NOT NULL,
                method VARCHAR(32) NOT NULL,
                amount NUMERIC(12, 2) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                expires_at TIMESTAMPTZ,
                evidence_received_at TIMESTAMPTZ,
                reviewed_at TIMESTAMPTZ,
                reviewed_by_user_id UUID,
                created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(booking_id) REFERENCES "{schema_name}".bookings (id)
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE INDEX IF NOT EXISTS ix_payment_attempts_booking_id
            ON "{schema_name}".payment_attempts (booking_id)
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".payment_evidence (
                id UUID NOT NULL,
                payment_attempt_id UUID NOT NULL,
                storage_object_key TEXT,
                original_filename VARCHAR(255),
                content_type VARCHAR(120),
                uploaded_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                uploaded_channel VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(payment_attempt_id) REFERENCES "{schema_name}".payment_attempts (id)
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE INDEX IF NOT EXISTS ix_payment_evidence_payment_attempt_id
            ON "{schema_name}".payment_evidence (payment_attempt_id)
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".payment_reviews (
                id UUID NOT NULL,
                payment_attempt_id UUID NOT NULL,
                decision VARCHAR(32) NOT NULL,
                reviewer_user_id UUID,
                reviewed_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(payment_attempt_id) REFERENCES "{schema_name}".payment_attempts (id)
            )
            '''
        )
    )
    connection.execute(
        text(
            f'''
            CREATE INDEX IF NOT EXISTS ix_payment_reviews_payment_attempt_id
            ON "{schema_name}".payment_reviews (payment_attempt_id)
            '''
        )
    )
    connection.execute(
        text(
            f'''
            INSERT INTO "{schema_name}".tenant_schema_migrations (version)
            VALUES ('006_manual_simulated_payments')
            ON CONFLICT (version) DO NOTHING
            '''
        )
    )

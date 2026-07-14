import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql.elements import TextClause

from app.tenancy.schema import (
    apply_admin_cancellation_reason_tenant_migration,
    apply_admin_reschedule_reason_tenant_migration,
    apply_booking_domain_tenant_migration,
    apply_patient_payer_profiles_tenant_migration,
    apply_manual_payments_tenant_migration,
    apply_virtual_link_columns_tenant_migration,
)


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
    assert "ADD COLUMN IF NOT EXISTS admin_reschedule_reason TEXT" in sql
    assert "004_admin_reschedule_reason" in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".patient_payer_profiles' in sql
    assert '"tenant_alpha".patients' in sql
    assert '"tenant_alpha".payer_plans' in sql
    assert '"public".patient_payer_profiles' not in sql
    assert "public.patient_payer_profiles" not in sql
    assert "005_patient_payer_profiles" in sql
    assert sql.index("005_patient_payer_profiles") < sql.index("006_manual_simulated_payments")
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_settings' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_attempts' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_evidence' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_reviews' in sql
    assert "public.payment_settings" not in sql
    assert "public.payment_attempts" not in sql
    assert "public.payment_evidence" not in sql
    assert "public.payment_reviews" not in sql
    assert "public.ix_payment_attempts_booking_id" not in sql
    assert "public.ix_payment_evidence_payment_attempt_id" not in sql
    assert "public.ix_payment_reviews_payment_attempt_id" not in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_meeting_url TEXT" in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_link_status VARCHAR(32) DEFAULT 'not_applicable' NOT NULL" in sql
    assert "008_virtual_appointment_links" in sql


def test_booking_domain_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_booking_domain_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_admin_cancellation_reason_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_admin_cancellation_reason_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_admin_reschedule_reason_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_admin_reschedule_reason_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_patient_payer_profiles_migration_creates_table_in_tenant_schema_only() -> None:
    connection = RecordingConnection()
    apply_patient_payer_profiles_tenant_migration(connection, "tenant_alpha")  # type: ignore[arg-type]

    sql = "\n".join(connection.statements)
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".patient_payer_profiles' in sql
    assert "patient_id UUID NOT NULL" in sql
    assert "payer_plan_id UUID NOT NULL" in sql
    assert "member_id VARCHAR(120)" in sql
    assert "authorization_required BOOLEAN DEFAULT false NOT NULL" in sql
    assert "status VARCHAR(32) DEFAULT 'active' NOT NULL" in sql
    assert 'FOREIGN KEY(patient_id) REFERENCES "tenant_alpha".patients (id)' in sql
    assert 'FOREIGN KEY(payer_plan_id) REFERENCES "tenant_alpha".payer_plans (id)' in sql
    assert '"public".patient_payer_profiles' not in sql
    assert "public.patient_payer_profiles" not in sql
    assert "005_patient_payer_profiles" in sql


def test_patient_payer_profiles_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_patient_payer_profiles_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_manual_payments_migration_creates_tables_in_tenant_schema_only() -> None:
    connection = RecordingConnection()
    apply_manual_payments_tenant_migration(connection, "tenant_alpha")  # type: ignore[arg-type]

    sql = "\n".join(connection.statements)
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_settings' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_attempts' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_evidence' in sql
    assert 'CREATE TABLE IF NOT EXISTS "tenant_alpha".payment_reviews' in sql
    assert 'FOREIGN KEY(organization_id) REFERENCES "tenant_alpha".organizations (id)' in sql
    assert 'FOREIGN KEY(booking_id) REFERENCES "tenant_alpha".bookings (id)' in sql
    assert 'FOREIGN KEY(payment_attempt_id) REFERENCES "tenant_alpha".payment_attempts (id)' in sql
    assert "CREATE INDEX IF NOT EXISTS ix_payment_attempts_booking_id" in sql
    assert 'ON "tenant_alpha".payment_attempts (booking_id)' in sql
    assert "CREATE INDEX IF NOT EXISTS ix_payment_evidence_payment_attempt_id" in sql
    assert 'ON "tenant_alpha".payment_evidence (payment_attempt_id)' in sql
    assert "CREATE INDEX IF NOT EXISTS ix_payment_reviews_payment_attempt_id" in sql
    assert 'ON "tenant_alpha".payment_reviews (payment_attempt_id)' in sql
    assert "release_slot_on_review_overdue BOOLEAN DEFAULT false NOT NULL" in sql
    assert "006_manual_simulated_payments" in sql
    assert "public.payment_settings" not in sql
    assert "public.payment_attempts" not in sql
    assert "public.payment_evidence" not in sql
    assert "public.payment_reviews" not in sql
    assert "public.ix_payment_attempts_booking_id" not in sql
    assert "public.ix_payment_evidence_payment_attempt_id" not in sql
    assert "public.ix_payment_reviews_payment_attempt_id" not in sql


def test_manual_payments_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_manual_payments_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]


def test_virtual_link_columns_migration_adds_booking_columns() -> None:
    connection = RecordingConnection()
    apply_virtual_link_columns_tenant_migration(connection, "tenant_alpha")  # type: ignore[arg-type]

    sql = "\n".join(connection.statements)
    assert 'ALTER TABLE "tenant_alpha".bookings ADD COLUMN IF NOT EXISTS virtual_meeting_url TEXT' in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_meeting_id VARCHAR(255)" in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_access_code VARCHAR(255)" in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_link_status VARCHAR(32) DEFAULT 'not_applicable' NOT NULL" in sql
    assert "ADD COLUMN IF NOT EXISTS virtual_link_sent_at TIMESTAMPTZ" in sql
    assert "008_virtual_appointment_links" in sql


def test_virtual_link_columns_migration_rejects_invalid_schema_name() -> None:
    with pytest.raises(ValueError):
        apply_virtual_link_columns_tenant_migration(RecordingConnection(), "public")  # type: ignore[arg-type]

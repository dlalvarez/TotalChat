from decimal import Decimal

from app.db.base import Base
from app.models.tenant import Booking, PractitionerServicePrice, Specialty


def test_tenant_booking_domain_models_are_registered_without_public_schema() -> None:
    expected = {
        "organizations", "locations", "rooms", "practitioners", "specialties", "practitioner_specialties",
        "practitioner_services", "service_modalities", "payer_types", "payers", "payer_plans",
        "practitioner_service_prices", "patients", "patient_contacts", "patient_payer_profiles", "availability_rules",
        "availability_exceptions", "bookings",
    }
    assert expected.issubset(Base.metadata.tables.keys())
    assert all(f"public.{table_name}" not in Base.metadata.tables for table_name in expected)


def test_specialty_does_not_define_price() -> None:
    specialty_columns = set(Specialty.__table__.columns.keys())
    assert "price" not in specialty_columns
    assert "currency" not in specialty_columns


def test_price_is_attached_to_practitioner_service_and_payer_plan() -> None:
    price_columns = set(PractitionerServicePrice.__table__.columns.keys())
    assert {"practitioner_service_id", "payer_plan_id", "price", "currency"}.issubset(price_columns)
    assert "specialty_id" not in price_columns


def test_booking_snapshot_fields_preserve_historical_commercial_truth() -> None:
    booking_columns = set(Booking.__table__.columns.keys())
    assert {
        "service_name_snapshot",
        "duration_minutes_snapshot",
        "practitioner_name_snapshot",
        "modality_snapshot",
        "location_name_snapshot",
        "payer_type_name_snapshot",
        "payer_name_snapshot",
        "payer_plan_name_snapshot",
        "price_snapshot",
        "currency_snapshot",
        "total_amount",
        "address_snapshot",
        "room_snapshot",
    }.issubset(booking_columns)
    assert not Booking.__table__.columns["service_name_snapshot"].nullable
    assert not Booking.__table__.columns["price_snapshot"].nullable


def test_booking_can_hold_minimum_patient_and_snapshot_values() -> None:
    booking = Booking(
        organization_id="00000000-0000-0000-0000-000000000001",
        patient_id="00000000-0000-0000-0000-000000000002",
        practitioner_id="00000000-0000-0000-0000-000000000003",
        practitioner_service_id="00000000-0000-0000-0000-000000000004",
        modality="in_person",
        starts_at="2026-07-07T10:00:00+00:00",
        ends_at="2026-07-07T10:30:00+00:00",
        service_name_snapshot="Consulta psicológica",
        duration_minutes_snapshot=30,
        practitioner_name_snapshot="Dra. Ana",
        modality_snapshot="in_person",
        location_name_snapshot="Sede Norte",
        payer_type_name_snapshot="Particular",
        payer_name_snapshot="Particular",
        payer_plan_name_snapshot="Tarifa particular",
        price_snapshot=Decimal("120000.00"),
        currency_snapshot="COP",
        total_amount=Decimal("120000.00"),
        address_snapshot="Calle 1 # 2-3",
        room_snapshot="Consultorio 1",
    )
    assert booking.service_name_snapshot == "Consulta psicológica"
    assert booking.price_snapshot == Decimal("120000.00")


def test_payment_domain_models_are_registered_without_public_schema() -> None:
    expected = {"payment_settings", "payment_attempts", "payment_evidence", "payment_reviews"}
    assert expected.issubset(Base.metadata.tables.keys())
    assert all(f"public.{table_name}" not in Base.metadata.tables for table_name in expected)


def test_payment_domain_foreign_keys_and_defaults() -> None:
    from app.models.tenant import PaymentAttempt, PaymentEvidence, PaymentReview, PaymentSettings

    attempt_fks = {fk.column.table.name for fk in PaymentAttempt.__table__.columns["booking_id"].foreign_keys}
    evidence_fks = {fk.column.table.name for fk in PaymentEvidence.__table__.columns["payment_attempt_id"].foreign_keys}
    review_fks = {fk.column.table.name for fk in PaymentReview.__table__.columns["payment_attempt_id"].foreign_keys}

    assert attempt_fks == {"bookings"}
    assert evidence_fks == {"payment_attempts"}
    assert review_fks == {"payment_attempts"}
    assert PaymentSettings.__table__.columns["release_slot_on_review_overdue"].default.arg is False
    assert str(PaymentSettings.__table__.columns["release_slot_on_review_overdue"].server_default.arg) == "false"

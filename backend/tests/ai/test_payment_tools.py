from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.payment_tools import PaymentPreparationRequest, PaymentStatusRequest, PaymentTools
from app.models.tenant import (
    Booking, Location, Organization, Patient, Payer, PayerPlan, PayerType,
    PaymentAttempt, PaymentSettings, Practitioner, PractitionerService, Room,
)
from app.services.errors import BusinessRuleViolation, ResourceNotFound


TABLES = [
    Organization.__table__, Location.__table__, Room.__table__, Practitioner.__table__,
    PractitionerService.__table__, PayerType.__table__, Payer.__table__, PayerPlan.__table__,
    Patient.__table__, Booking.__table__, PaymentSettings.__table__, PaymentAttempt.__table__,
]


@pytest.fixture
def payment_catalog():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in TABLES:
        table.create(engine)
    session = Session(engine)
    organization = Organization(name="Centro", organization_type="clinic", status="active")
    practitioner = Practitioner(full_name="Dra. Ana")
    service = PractitionerService(
        organization=organization, practitioner=practitioner, name="Consulta", duration_minutes=30
    )
    patient = Patient(full_name="Paciente")
    session.add_all([service, patient])
    session.flush()
    booking = Booking(
        organization_id=organization.id, patient_id=patient.id, practitioner_id=practitioner.id,
        practitioner_service_id=service.id, modality="virtual", starts_at=datetime(2026, 7, 22, 9),
        ends_at=datetime(2026, 7, 22, 9, 30), status="pending_payment", payment_status="pending",
        service_name_snapshot="Consulta", duration_minutes_snapshot=30,
        practitioner_name_snapshot="Dra. Ana", modality_snapshot="virtual",
        price_snapshot=Decimal("100000.00"), currency_snapshot="COP",
        total_amount=Decimal("100000.00"),
    )
    session.add(booking)
    session.commit()
    yield session, organization, booking
    session.close()
    engine.dispose()


def tools(session):
    return PaymentTools(tenant_id=uuid4(), session=session)


def settings(session, organization, **changes):
    values = dict(
        organization_id=organization.id, allow_transfer=True,
        allow_simulated_payment=True, allow_pay_on_site=False, status="active",
    )
    values.update(changes)
    row = PaymentSettings(**values)
    session.add(row)
    session.commit()
    return row


def test_status_is_structured_read_only_and_does_not_expose_schema(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization)

    result = tools(session).get_payment_status(PaymentStatusRequest(booking.id))

    assert result.booking_id == booking.id
    assert result.booking_status == "pending_payment"
    assert result.payment_status == "pending"
    assert result.amount == Decimal("100000.00")
    assert "schema_name" not in asdict(result)
    assert session.scalars(select(PaymentAttempt)).all() == []


def test_lists_only_methods_allowed_by_active_settings(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization, allow_simulated_payment=False, allow_pay_on_site=True)
    result = tools(session).get_payment_status(PaymentStatusRequest(booking.id))
    assert tuple(option.method for option in result.available_methods) == ("transfer", "pay_on_site")


def test_missing_settings_is_conservative(payment_catalog):
    session, _, booking = payment_catalog
    result = tools(session).get_payment_status(PaymentStatusRequest(booking.id))
    assert result.available_methods == ()
    with pytest.raises(BusinessRuleViolation):
        tools(session).prepare_payment(PaymentPreparationRequest(booking.id, "transfer"))
    assert session.scalars(select(PaymentAttempt)).all() == []


def test_transfer_preparation_requires_evidence_without_approval_or_slot_release(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization, allow_transfer=True)
    original_status = booking.status

    result = tools(session).prepare_payment(PaymentPreparationRequest(booking.id, "transfer"))

    attempt = session.get(PaymentAttempt, result.payment_attempt_id)
    assert attempt.status == result.attempt_status == "evidence_required"
    assert result.requires_evidence is True
    assert result.manual_review_required is False
    assert attempt.status not in {"approved", "rejected", "simulated_approved"}
    assert booking.status == original_status == "pending_payment"
    assert booking.payment_status == "pending"


def test_disabled_transfer_is_rejected_without_attempt(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization, allow_transfer=False)
    with pytest.raises(BusinessRuleViolation):
        tools(session).prepare_payment(PaymentPreparationRequest(booking.id, "transfer"))
    assert session.scalars(select(PaymentAttempt)).all() == []


@pytest.mark.parametrize(
    "terminal_status",
    ["cancelled", "cancelled_by_patient", "cancelled_by_admin", "expired", "completed", "no_show"],
)
def test_terminal_booking_status_cannot_prepare_payment(payment_catalog, terminal_status):
    session, organization, booking = payment_catalog
    settings(session, organization, allow_transfer=True)
    booking.status = terminal_status
    session.commit()
    original_payment_status = booking.payment_status

    with pytest.raises(BusinessRuleViolation, match="status does not allow"):
        tools(session).prepare_payment(PaymentPreparationRequest(booking.id, "transfer"))

    assert session.scalars(select(PaymentAttempt)).all() == []
    assert booking.status == terminal_status
    assert booking.payment_status == original_payment_status


def test_terminal_booking_status_remains_queryable(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization, allow_transfer=True)
    booking.status = "completed"
    session.commit()

    result = tools(session).get_payment_status(PaymentStatusRequest(booking.id))

    assert result.booking_status == "completed"
    assert result.payment_status == booking.payment_status
    assert session.scalars(select(PaymentAttempt)).all() == []


@pytest.mark.parametrize(
    ("method", "setting", "allowed"),
    [("pay_on_site", "allow_pay_on_site", True), ("simulated", "allow_simulated_payment", True)],
)
def test_other_methods_are_pending_only_when_allowed(payment_catalog, method, setting, allowed):
    session, organization, booking = payment_catalog
    settings(session, organization, **{setting: allowed})
    result = tools(session).prepare_payment(PaymentPreparationRequest(booking.id, method))
    assert result.attempt_status == "pending"
    assert result.payment_status == "pending"
    assert booking.status == "pending_payment"


@pytest.mark.parametrize("method", ["pay_on_site", "simulated"])
def test_disabled_other_methods_are_rejected(payment_catalog, method):
    session, organization, booking = payment_catalog
    settings(
        session, organization, allow_transfer=False,
        allow_pay_on_site=False, allow_simulated_payment=False,
    )
    with pytest.raises(BusinessRuleViolation):
        tools(session).prepare_payment(PaymentPreparationRequest(booking.id, method))


def test_nonexistent_booking_or_inactive_organization_creates_nothing(payment_catalog):
    session, organization, booking = payment_catalog
    settings(session, organization)
    with pytest.raises(ResourceNotFound):
        tools(session).prepare_payment(PaymentPreparationRequest(uuid4(), "transfer"))
    organization.status = "inactive"
    session.commit()
    with pytest.raises(ResourceNotFound):
        tools(session).get_payment_status(PaymentStatusRequest(booking.id))
    assert session.scalars(select(PaymentAttempt)).all() == []


def test_invalid_method_is_rejected_before_persistence(payment_catalog):
    session, _, booking = payment_catalog
    with pytest.raises(ValueError, match="method"):
        PaymentPreparationRequest(booking.id, "wompi")
    assert session.scalars(select(PaymentAttempt)).all() == []


def test_contract_requires_resolved_tenant_and_local_repository():
    annotations = PaymentTools.__init__.__annotations__
    assert all(name not in annotations for name in ("schema_name", "llm", "client"))
    with pytest.raises(ValueError, match="tenant-scoped"):
        PaymentTools(tenant_id=uuid4())

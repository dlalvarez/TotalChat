from dataclasses import asdict
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.pricing_tools import PricingOptionsRequest, PricingRequest, PricingTools
from app.models.tenant import (
    Organization,
    OrganizationPractitioner,
    Payer,
    PayerPlan,
    PayerType,
    Practitioner,
    PractitionerService,
    PractitionerServicePrice,
)


TABLES = [
    Organization.__table__,
    Practitioner.__table__,
    OrganizationPractitioner.__table__,
    PractitionerService.__table__,
    PayerType.__table__,
    Payer.__table__,
    PayerPlan.__table__,
    PractitionerServicePrice.__table__,
]
AS_OF = date(2026, 7, 21)


@pytest.fixture
def pricing_catalog():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in TABLES:
        table.create(engine)
    session = Session(engine)
    organization = Organization(name="Centro", organization_type="clinic")
    practitioner = Practitioner(full_name="Dra. Ana")
    service = PractitionerService(
        organization=organization,
        practitioner=practitioner,
        name="Consulta",
        duration_minutes=50,
    )
    payer_type = PayerType(code="private", name="Particular")
    payer = Payer(payer_type=payer_type, name="Particular")
    plan = PayerPlan(payer=payer, name="Tarifa particular")
    second_plan = PayerPlan(payer=payer, name="Tarifa preferencial")
    session.add_all([service, plan, second_plan])
    session.flush()
    relation = OrganizationPractitioner(
        organization_id=organization.id,
        practitioner_id=practitioner.id,
    )
    current = PractitionerServicePrice(
        practitioner_service=service,
        payer_plan=plan,
        price=Decimal("100000.00"),
        currency="COP",
        valid_from=date(2026, 1, 1),
    )
    second = PractitionerServicePrice(
        practitioner_service=service,
        payer_plan=second_plan,
        price=Decimal("80000.00"),
        currency="COP",
        valid_from=date(2026, 6, 1),
        valid_to=date(2026, 12, 31),
    )
    inactive = PractitionerServicePrice(
        practitioner_service=service,
        payer_plan=plan,
        price=Decimal("1.00"),
        currency="COP",
        valid_from=date(2025, 1, 1),
        status="inactive",
    )
    expired = PractitionerServicePrice(
        practitioner_service=service,
        payer_plan=second_plan,
        price=Decimal("2.00"),
        currency="COP",
        valid_from=date(2025, 1, 1),
        valid_to=date(2025, 12, 31),
    )
    future = PractitionerServicePrice(
        practitioner_service=service,
        payer_plan=second_plan,
        price=Decimal("3.00"),
        currency="COP",
        valid_from=date(2027, 1, 1),
    )
    session.add_all([relation, current, second, inactive, expired, future])
    session.commit()
    yield session, {
        "organization": organization,
        "practitioner": practitioner,
        "relation": relation,
        "service": service,
        "payer_type": payer_type,
        "payer": payer,
        "plan": plan,
        "second_plan": second_plan,
        "current": current,
    }
    session.close()
    engine.dispose()


def tools(session: Session) -> PricingTools:
    return PricingTools(tenant_id=uuid4(), session=session)


def test_gets_active_price_for_service_and_payer_plan(pricing_catalog) -> None:
    session, data = pricing_catalog

    quote = tools(session).get_service_price(
        PricingRequest(data["service"].id, data["plan"].id, AS_OF)
    )

    assert quote is not None
    assert quote.price_id == data["current"].id
    assert quote.amount == Decimal("100000.00")
    assert quote.currency == "COP"
    assert quote.payer_type_name == "Particular"
    assert quote.payer_name == "Particular"
    assert quote.payer_plan_name == "Tarifa particular"


def test_lists_only_current_active_pricing_options(pricing_catalog) -> None:
    session, data = pricing_catalog

    result = tools(session).get_pricing_options(PricingOptionsRequest(data["service"].id, AS_OF))

    assert {quote.payer_plan_id for quote in result.prices} == {
        data["plan"].id,
        data["second_plan"].id,
    }
    assert {quote.amount for quote in result.prices} == {Decimal("100000.00"), Decimal("80000.00")}


@pytest.mark.parametrize(
    "resource",
    ["service", "plan", "payer", "payer_type", "practitioner", "organization", "relation"],
)
def test_excludes_price_when_required_commercial_or_service_resource_is_inactive(
    pricing_catalog, resource
) -> None:
    session, data = pricing_catalog
    data[resource].status = "inactive"
    session.commit()

    assert tools(session).get_service_price(
        PricingRequest(data["service"].id, data["plan"].id, AS_OF)
    ) is None
    options = tools(session).get_pricing_options(
        PricingOptionsRequest(data["service"].id, AS_OF)
    ).prices
    assert data["plan"].id not in {quote.payer_plan_id for quote in options}
    if resource != "plan":
        assert options == ()


def test_out_of_validity_and_inactive_prices_are_not_returned(pricing_catalog) -> None:
    session, data = pricing_catalog

    before = tools(session).get_pricing_options(
        PricingOptionsRequest(data["service"].id, date(2024, 12, 31))
    )
    current = tools(session).get_pricing_options(PricingOptionsRequest(data["service"].id, AS_OF))

    assert before.prices == ()
    assert all(quote.amount not in {Decimal("1.00"), Decimal("2.00"), Decimal("3.00")} for quote in current.prices)


def test_result_has_no_schema_availability_slots_booking_or_payment_fields(pricing_catalog) -> None:
    session, data = pricing_catalog
    quote = tools(session).get_service_price(PricingRequest(data["service"].id, data["plan"].id, AS_OF))
    assert quote is not None

    fields = asdict(quote)
    for forbidden in ("schema_name", "availability", "slots", "booking", "payment"):
        assert forbidden not in fields


def test_tools_require_resolved_tenant_and_local_data_source() -> None:
    with pytest.raises(ValueError, match="tenant-scoped repository or session"):
        PricingTools(tenant_id=uuid4())
    with pytest.raises(TypeError, match="backend-resolved UUID"):
        PricingTools(tenant_id="tenant", repository=object())  # type: ignore[arg-type]

    constructor_fields = PricingTools.__init__.__annotations__
    assert "schema_name" not in constructor_fields
    assert "llm" not in constructor_fields
    assert "client" not in constructor_fields

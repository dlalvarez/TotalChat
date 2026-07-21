"""Tenant-scoped price lookup tools for the booking agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, Sequence
from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

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


@dataclass(frozen=True, slots=True)
class PricingRequest:
    practitioner_service_id: UUID
    payer_plan_id: UUID
    as_of: date | None = None


@dataclass(frozen=True, slots=True)
class PricingOptionsRequest:
    practitioner_service_id: UUID
    as_of: date | None = None


@dataclass(frozen=True, slots=True)
class PriceRecord:
    """Repository projection of configured commercial truth."""

    price_id: UUID
    practitioner_service_id: UUID
    payer_plan_id: UUID
    payer_plan_name: str
    payer_id: UUID
    payer_name: str
    payer_type_id: UUID
    payer_type_name: str
    amount: Decimal
    currency: str
    valid_from: date
    valid_to: date | None


@dataclass(frozen=True, slots=True)
class PriceQuote:
    price_id: UUID
    practitioner_service_id: UUID
    payer_plan_id: UUID
    payer_plan_name: str
    payer_id: UUID
    payer_name: str
    payer_type_id: UUID
    payer_type_name: str
    amount: Decimal
    currency: str
    valid_from: date
    valid_to: date | None


@dataclass(frozen=True, slots=True)
class PricingToolResult:
    prices: tuple[PriceQuote, ...]


class PricingRepository(Protocol):
    """Port for price reads bound to an already-resolved tenant session."""

    def list_active(self, practitioner_service_id: UUID, *, as_of: date) -> Sequence[PriceRecord]: ...

    def get_active(
        self,
        practitioner_service_id: UUID,
        payer_plan_id: UUID,
        *,
        as_of: date,
    ) -> PriceRecord | None: ...


class SQLAlchemyPricingRepository:
    """Reads configured prices through a tenant-scoped SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _active_query(
        self,
        practitioner_service_id: UUID,
        *,
        as_of: date,
    ) -> Select[tuple[PractitionerServicePrice, PayerPlan, Payer, PayerType]]:
        return (
            select(PractitionerServicePrice, PayerPlan, Payer, PayerType)
            .join(PractitionerService, PractitionerService.id == PractitionerServicePrice.practitioner_service_id)
            .join(Practitioner, Practitioner.id == PractitionerService.practitioner_id)
            .join(Organization, Organization.id == PractitionerService.organization_id)
            .join(
                OrganizationPractitioner,
                (OrganizationPractitioner.organization_id == PractitionerService.organization_id)
                & (OrganizationPractitioner.practitioner_id == PractitionerService.practitioner_id),
            )
            .join(PayerPlan, PayerPlan.id == PractitionerServicePrice.payer_plan_id)
            .join(Payer, Payer.id == PayerPlan.payer_id)
            .join(PayerType, PayerType.id == Payer.payer_type_id)
            .where(
                PractitionerServicePrice.practitioner_service_id == practitioner_service_id,
                PractitionerServicePrice.status == "active",
                PractitionerService.status == "active",
                Practitioner.status == "active",
                Organization.status == "active",
                OrganizationPractitioner.status == "active",
                PayerPlan.status == "active",
                Payer.status == "active",
                PayerType.status == "active",
                PractitionerServicePrice.valid_from <= as_of,
                or_(PractitionerServicePrice.valid_to.is_(None), PractitionerServicePrice.valid_to >= as_of),
            )
        )

    def list_active(self, practitioner_service_id: UUID, *, as_of: date) -> Sequence[PriceRecord]:
        rows = self._session.execute(
            self._active_query(practitioner_service_id, as_of=as_of).order_by(
                PayerType.name,
                Payer.name,
                PayerPlan.name,
                PractitionerServicePrice.valid_from.desc(),
                PractitionerServicePrice.id,
            )
        )
        records = [self._to_record(*row) for row in rows]
        # Active periods are prevented from overlapping by the admin domain. If
        # legacy data does overlap, expose only the newest period for each plan.
        selected: dict[UUID, PriceRecord] = {}
        for record in records:
            selected.setdefault(record.payer_plan_id, record)
        return tuple(selected.values())

    def get_active(
        self,
        practitioner_service_id: UUID,
        payer_plan_id: UUID,
        *,
        as_of: date,
    ) -> PriceRecord | None:
        row = self._session.execute(
            self._active_query(practitioner_service_id, as_of=as_of)
            .where(PractitionerServicePrice.payer_plan_id == payer_plan_id)
            .order_by(PractitionerServicePrice.valid_from.desc(), PractitionerServicePrice.id)
            .limit(1)
        ).first()
        return self._to_record(*row) if row else None

    @staticmethod
    def _to_record(
        price: PractitionerServicePrice,
        plan: PayerPlan,
        payer: Payer,
        payer_type: PayerType,
    ) -> PriceRecord:
        return PriceRecord(
            price_id=price.id,
            practitioner_service_id=price.practitioner_service_id,
            payer_plan_id=plan.id,
            payer_plan_name=plan.name,
            payer_id=payer.id,
            payer_name=payer.name,
            payer_type_id=payer_type.id,
            payer_type_name=payer_type.name,
            amount=price.price,
            currency=price.currency,
            valid_from=price.valid_from,
            valid_to=price.valid_to,
        )


class PricingTools:
    """Structured price tools operating only inside a resolved tenant."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        repository: PricingRepository | None = None,
        session: Session | None = None,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if repository is None and session is None:
            raise ValueError("a tenant-scoped repository or session is required")
        if repository is not None and session is not None:
            raise ValueError("provide repository or session, not both")
        self._tenant_id = tenant_id
        self._repository = repository or SQLAlchemyPricingRepository(session)  # type: ignore[arg-type]

    def get_service_price(self, request: PricingRequest) -> PriceQuote | None:
        record = self._repository.get_active(
            request.practitioner_service_id,
            request.payer_plan_id,
            as_of=request.as_of or date.today(),
        )
        return self._quote(record) if record else None

    def get_pricing_options(self, request: PricingOptionsRequest) -> PricingToolResult:
        records = self._repository.list_active(
            request.practitioner_service_id,
            as_of=request.as_of or date.today(),
        )
        return PricingToolResult(tuple(self._quote(record) for record in records))

    @staticmethod
    def _quote(record: PriceRecord) -> PriceQuote:
        return PriceQuote(**{field: getattr(record, field) for field in PriceQuote.__dataclass_fields__})

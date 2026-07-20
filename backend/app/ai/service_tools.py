"""Tenant-scoped service lookup tools for the booking agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence
from uuid import UUID

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.orm import Session

from app.models.tenant import Organization, Practitioner, PractitionerService, ServiceModality


@dataclass(frozen=True, slots=True)
class ServiceSearchRequest:
    text: str
    practitioner_id: UUID | None = None
    organization_id: UUID | None = None
    modality: str | None = None
    limit: int = 20

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("text must not be blank")
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")


@dataclass(frozen=True, slots=True)
class ServiceListRequest:
    practitioner_id: UUID | None = None
    organization_id: UUID | None = None
    modality: str | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")


@dataclass(frozen=True, slots=True)
class ServiceRecord:
    """Repository projection; deliberately excludes pricing and availability."""

    service_id: UUID
    name: str
    description: str | None
    duration_minutes: int
    practitioner_id: UUID
    practitioner_name: str | None
    organization_id: UUID
    organization_name: str | None
    modalities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceSummary:
    service_id: UUID
    name: str
    description: str | None
    duration_minutes: int
    practitioner_id: UUID
    practitioner_name: str | None
    modalities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ServiceDetail:
    service_id: UUID
    name: str
    description: str | None
    duration_minutes: int
    practitioner_id: UUID
    practitioner_name: str | None
    organization_id: UUID
    organization_name: str | None
    modalities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ServiceToolResult:
    services: tuple[ServiceSummary, ...]


class ServiceRepository(Protocol):
    """Port for a repository bound to an already-resolved tenant session."""

    def list_active(
        self,
        *,
        text: str | None = None,
        practitioner_id: UUID | None = None,
        organization_id: UUID | None = None,
        modality: str | None = None,
        limit: int = 100,
    ) -> Sequence[ServiceRecord]: ...

    def get_active(self, service_id: UUID) -> ServiceRecord | None: ...


class SQLAlchemyServiceRepository:
    """Reads practitioner services through a tenant-scoped SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _active_query(self) -> Select[tuple[PractitionerService, Practitioner, Organization]]:
        return (
            select(PractitionerService, Practitioner, Organization)
            .join(Practitioner, Practitioner.id == PractitionerService.practitioner_id)
            .join(Organization, Organization.id == PractitionerService.organization_id)
            .where(
                PractitionerService.status == "active",
                Practitioner.status == "active",
                Organization.status == "active",
            )
        )

    def list_active(
        self,
        *,
        text: str | None = None,
        practitioner_id: UUID | None = None,
        organization_id: UUID | None = None,
        modality: str | None = None,
        limit: int = 100,
    ) -> Sequence[ServiceRecord]:
        query = self._active_query()
        if text:
            pattern = f"%{text.strip()}%"
            query = query.where(
                or_(PractitionerService.name.ilike(pattern), PractitionerService.description.ilike(pattern))
            )
        if practitioner_id:
            query = query.where(PractitionerService.practitioner_id == practitioner_id)
        if organization_id:
            query = query.where(PractitionerService.organization_id == organization_id)
        if modality:
            query = query.where(
                exists().where(
                    ServiceModality.practitioner_service_id == PractitionerService.id,
                    ServiceModality.status == "active",
                    ServiceModality.modality == modality,
                )
            )
        rows = self._session.execute(query.order_by(PractitionerService.name, PractitionerService.id).limit(limit))
        return [self._to_record(service, practitioner, organization) for service, practitioner, organization in rows]

    def get_active(self, service_id: UUID) -> ServiceRecord | None:
        row = self._session.execute(
            self._active_query().where(PractitionerService.id == service_id)
        ).one_or_none()
        return self._to_record(*row) if row else None

    def _to_record(
        self,
        service: PractitionerService,
        practitioner: Practitioner,
        organization: Organization,
    ) -> ServiceRecord:
        modalities = self._session.scalars(
            select(ServiceModality.modality)
            .where(
                ServiceModality.practitioner_service_id == service.id,
                ServiceModality.status == "active",
            )
            .distinct()
            .order_by(ServiceModality.modality)
        ).all()
        return ServiceRecord(
            service_id=service.id,
            name=service.name,
            description=service.description,
            duration_minutes=service.duration_minutes,
            practitioner_id=service.practitioner_id,
            practitioner_name=practitioner.full_name,
            organization_id=service.organization_id,
            organization_name=organization.name,
            modalities=tuple(modalities),
        )


class ServiceTools:
    """Structured tools operating only inside a backend-resolved tenant."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        repository: ServiceRepository | None = None,
        session: Session | None = None,
    ) -> None:
        if not isinstance(tenant_id, UUID):
            raise TypeError("tenant_id must be a backend-resolved UUID")
        if repository is None and session is None:
            raise ValueError("a tenant-scoped repository or session is required")
        if repository is not None and session is not None:
            raise ValueError("provide repository or session, not both")
        self._tenant_id = tenant_id
        self._repository = repository or SQLAlchemyServiceRepository(session)  # type: ignore[arg-type]

    def search_services(self, request: ServiceSearchRequest) -> ServiceToolResult:
        records = self._repository.list_active(
            text=request.text,
            practitioner_id=request.practitioner_id,
            organization_id=request.organization_id,
            modality=request.modality,
            limit=request.limit,
        )
        return ServiceToolResult(tuple(self._summary(record) for record in records))

    def list_active_services(self, request: ServiceListRequest | None = None) -> ServiceToolResult:
        filters = request or ServiceListRequest()
        records = self._repository.list_active(
            practitioner_id=filters.practitioner_id,
            organization_id=filters.organization_id,
            modality=filters.modality,
            limit=filters.limit,
        )
        return ServiceToolResult(tuple(self._summary(record) for record in records))

    def get_service_detail(self, service_id: UUID) -> ServiceDetail | None:
        record = self._repository.get_active(service_id)
        if record is None:
            return None
        return ServiceDetail(
            service_id=record.service_id,
            name=record.name,
            description=record.description,
            duration_minutes=record.duration_minutes,
            practitioner_id=record.practitioner_id,
            practitioner_name=record.practitioner_name,
            organization_id=record.organization_id,
            organization_name=record.organization_name,
            modalities=record.modalities,
        )

    @staticmethod
    def _summary(record: ServiceRecord) -> ServiceSummary:
        return ServiceSummary(
            service_id=record.service_id,
            name=record.name,
            description=record.description,
            duration_minutes=record.duration_minutes,
            practitioner_id=record.practitioner_id,
            practitioner_name=record.practitioner_name,
            modalities=record.modalities,
        )

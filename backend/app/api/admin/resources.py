from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import Location, Organization, Practitioner, PractitionerService, PractitionerSpecialty, Room, ServiceModality, Specialty
from app.services.errors import BusinessRuleViolation, DomainValidationError, ResourceNotFound
from app.tenancy.context import TenantContext

router = APIRouter(tags=["admin-resources"])


class CreateOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    organization_type: str
    legal_name: str | None = None
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None


class PatchOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    organization_type: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None


class DisableOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    name: str
    address: str | None = None
    city: str | None = None
    neighborhood: str | None = None
    reference: str | None = None
    is_virtual: bool = False


class CreateRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_id: UUID
    name: str
    room_type: str | None = None
    capacity: int | None = None


class CreatePractitionerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    professional_type: str | None = None
    professional_license: str | None = None
    email: str | None = None
    phone: str | None = None


class PatchPractitionerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    professional_type: str | None = None
    professional_license: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None


class CreateSpecialtyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None


class CreatePractitionerServiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    practitioner_id: UUID
    name: str
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    requires_payment: bool = True


class CreateServiceModalityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modality: str
    location_id: UUID | None = None
    room_id: UUID | None = None


class AssignPractitionerSpecialtyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specialty_id: UUID


def serialize_organization(organization: Organization) -> dict[str, object]:
    return {
        "id": str(organization.id),
        "name": organization.name,
        "organization_type": organization.organization_type,
        "legal_name": organization.legal_name,
        "tax_id": organization.tax_id,
        "email": organization.email,
        "phone": organization.phone,
        "status": organization.status,
    }


def serialize_location(location: Location) -> dict[str, object]:
    return {
        "id": str(location.id),
        "organization_id": str(location.organization_id),
        "name": location.name,
        "address": location.address,
        "city": location.city,
        "neighborhood": location.neighborhood,
        "reference": location.reference,
        "is_virtual": location.is_virtual,
        "status": location.status,
    }


def serialize_room(room: Room) -> dict[str, object]:
    return {
        "id": str(room.id),
        "location_id": str(room.location_id),
        "name": room.name,
        "room_type": room.room_type,
        "capacity": room.capacity,
        "status": room.status,
    }


def serialize_practitioner(practitioner: Practitioner) -> dict[str, object]:
    return {
        "id": str(practitioner.id),
        "full_name": practitioner.full_name,
        "professional_type": practitioner.professional_type,
        "professional_license": practitioner.professional_license,
        "email": practitioner.email,
        "phone": practitioner.phone,
        "status": practitioner.status,
    }


def serialize_specialty(specialty: Specialty) -> dict[str, object]:
    return {
        "id": str(specialty.id),
        "name": specialty.name,
        "description": specialty.description,
        "status": specialty.status,
    }


def serialize_practitioner_service(service: PractitionerService) -> dict[str, object]:
    return {
        "id": str(service.id),
        "organization_id": str(service.organization_id),
        "practitioner_id": str(service.practitioner_id),
        "name": service.name,
        "description": service.description,
        "duration_minutes": service.duration_minutes,
        "requires_payment": service.requires_payment,
        "status": service.status,
    }


def serialize_service_modality(modality: ServiceModality) -> dict[str, object]:
    return {
        "id": str(modality.id),
        "practitioner_service_id": str(modality.practitioner_service_id),
        "modality": modality.modality,
        "location_id": str(modality.location_id) if modality.location_id is not None else None,
        "room_id": str(modality.room_id) if modality.room_id is not None else None,
        "status": modality.status,
    }


def serialize_practitioner_specialty(association: PractitionerSpecialty) -> dict[str, object]:
    return {
        "practitioner_id": str(association.practitioner_id),
        "specialty_id": str(association.specialty_id),
        "status": association.status,
    }


@router.post("/organizations")
def create_organization(
    payload: CreateOrganizationRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    organization = Organization(**payload.model_dump())
    try:
        session.add(organization)
        session.commit()
        session.refresh(organization)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization(organization)}


@router.get("/organizations")
def list_organizations(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    organizations = session.scalars(select(Organization).order_by(Organization.name, Organization.id)).all()
    return {"data": [serialize_organization(organization) for organization in organizations]}


@router.get("/organizations/{organization_id}")
def get_organization(
    organization_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    return {"data": serialize_organization(organization)}


@router.patch("/organizations/{organization_id}")
def patch_organization(
    organization_id: UUID,
    payload: PatchOrganizationRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(organization, field, value)
    try:
        session.commit()
        session.refresh(organization)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization(organization)}


@router.post("/organizations/{organization_id}/disable")
def disable_organization(
    organization_id: UUID,
    payload: DisableOrganizationRequest | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = payload
    _ = tenant_context
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    organization.status = "inactive"
    try:
        session.commit()
        session.refresh(organization)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization(organization)}


@router.post("/locations")
def create_location(
    payload: CreateLocationRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Organization, payload.organization_id) is None:
        raise ResourceNotFound("Organization not found.")
    location = Location(**payload.model_dump())
    try:
        session.add(location)
        session.commit()
        session.refresh(location)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_location(location)}


@router.get("/locations")
def list_locations(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    locations = session.scalars(select(Location).order_by(Location.name, Location.id)).all()
    return {"data": [serialize_location(location) for location in locations]}


@router.post("/rooms")
def create_room(
    payload: CreateRoomRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Location, payload.location_id) is None:
        raise ResourceNotFound("Location not found.")
    room = Room(**payload.model_dump())
    try:
        session.add(room)
        session.commit()
        session.refresh(room)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_room(room)}


@router.get("/rooms")
def list_rooms(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    rooms = session.scalars(select(Room).order_by(Room.name, Room.id)).all()
    return {"data": [serialize_room(room) for room in rooms]}


@router.post("/practitioners")
def create_practitioner(
    payload: CreatePractitionerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    practitioner = Practitioner(**payload.model_dump())
    try:
        session.add(practitioner)
        session.commit()
        session.refresh(practitioner)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner(practitioner)}


@router.get("/practitioners")
def list_practitioners(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    practitioners = session.scalars(select(Practitioner).order_by(Practitioner.full_name, Practitioner.id)).all()
    return {"data": [serialize_practitioner(practitioner) for practitioner in practitioners]}


@router.patch("/practitioners/{practitioner_id}")
def patch_practitioner(
    practitioner_id: UUID,
    payload: PatchPractitionerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    practitioner = session.get(Practitioner, practitioner_id)
    if practitioner is None:
        raise ResourceNotFound("Practitioner not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(practitioner, field, value)
    try:
        session.commit()
        session.refresh(practitioner)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner(practitioner)}


@router.post("/specialties")
def create_specialty(
    payload: CreateSpecialtyRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    specialty = Specialty(**payload.model_dump())
    try:
        session.add(specialty)
        session.commit()
        session.refresh(specialty)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_specialty(specialty)}


@router.get("/specialties")
def list_specialties(
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    specialties = session.scalars(select(Specialty).order_by(Specialty.name, Specialty.id)).all()
    return {"data": [serialize_specialty(specialty) for specialty in specialties]}


@router.post("/practitioners/{practitioner_id}/specialties")
def assign_practitioner_specialty(
    practitioner_id: UUID,
    payload: AssignPractitionerSpecialtyRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Practitioner, practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")
    if session.get(Specialty, payload.specialty_id) is None:
        raise ResourceNotFound("Specialty not found.")

    association = session.get(PractitionerSpecialty, {"practitioner_id": practitioner_id, "specialty_id": payload.specialty_id})
    if association is None:
        association = PractitionerSpecialty(practitioner_id=practitioner_id, specialty_id=payload.specialty_id)
        try:
            session.add(association)
            session.commit()
            session.refresh(association)
        except Exception:
            session.rollback()
            raise
    return {"data": serialize_practitioner_specialty(association)}


@router.post("/practitioner-services")
def create_practitioner_service(
    payload: CreatePractitionerServiceRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Organization, payload.organization_id) is None:
        raise ResourceNotFound("Organization not found.")
    if session.get(Practitioner, payload.practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")

    service = PractitionerService(**payload.model_dump())
    try:
        session.add(service)
        session.commit()
        session.refresh(service)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner_service(service)}


@router.get("/practitioner-services")
def list_practitioner_services(
    organization_id: UUID | None = None,
    practitioner_id: UUID | None = None,
    status: str | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    stmt = select(PractitionerService)
    if organization_id is not None:
        stmt = stmt.where(PractitionerService.organization_id == organization_id)
    if practitioner_id is not None:
        stmt = stmt.where(PractitionerService.practitioner_id == practitioner_id)
    if status is not None:
        stmt = stmt.where(PractitionerService.status == status)
    services = session.scalars(stmt.order_by(PractitionerService.name, PractitionerService.id)).all()
    return {"data": [serialize_practitioner_service(service) for service in services]}


@router.post("/practitioner-services/{service_id}/modalities")
def create_service_modality(
    service_id: UUID,
    payload: CreateServiceModalityRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(PractitionerService, service_id) is None:
        raise ResourceNotFound("Practitioner service not found.")

    if payload.modality not in {"in_person", "virtual"}:
        raise DomainValidationError("Unsupported service modality.")

    if payload.modality == "virtual":
        if payload.location_id is not None or payload.room_id is not None:
            raise BusinessRuleViolation("Virtual modalities must not include location_id or room_id.")
    else:
        if payload.location_id is None or payload.room_id is None:
            raise DomainValidationError("In-person modalities require location_id and room_id.")
        if session.get(Location, payload.location_id) is None:
            raise ResourceNotFound("Location not found.")
        room = session.get(Room, payload.room_id)
        if room is None:
            raise ResourceNotFound("Room not found.")
        if room.location_id != payload.location_id:
            raise BusinessRuleViolation("Room does not belong to the provided location.")

    modality = ServiceModality(practitioner_service_id=service_id, **payload.model_dump())
    try:
        session.add(modality)
        session.commit()
        session.refresh(modality)
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_service_modality(modality)}

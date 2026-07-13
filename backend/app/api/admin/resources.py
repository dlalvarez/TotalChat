from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.models.tenant import (
    Location,
    Organization,
    Patient,
    PatientPayerProfile,
    PaymentAttempt,
    PaymentEvidence,
    PaymentReview,
    PaymentSettings,
    Payer,
    PayerPlan,
    PayerType,
    Practitioner,
    AvailabilityRule,
    OrganizationPractitioner,
    PractitionerService,
    PractitionerServicePrice,
    PractitionerSpecialty,
    Room,
    ServiceModality,
    Specialty,
)
from app.services.errors import BusinessRuleViolation, ConflictError, DomainValidationError, ResourceNotFound
from app.services.payments import PAYMENT_ATTEMPT_METHODS, PAYMENT_ATTEMPT_STATUSES, PAYMENT_REVIEW_DECISIONS, PaymentAttemptService, PaymentEvidenceService, PaymentReviewService
from app.tenancy.context import TenantContext

router = APIRouter(tags=["admin-resources"])

ROOM_TYPES = {"consulta_general", "procedimientos", "terapia", "diagnostico", "virtual", "otro"}
ORGANIZATION_PRACTITIONER_ROLES = {"primary", "member", "external"}
RELATION_STATUSES = {"active", "inactive"}


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_code(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _validate_room_type(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    if value not in ROOM_TYPES:
        raise DomainValidationError("Tipo de consultorio no permitido.")
    return value


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

    @field_validator("room_type")
    @classmethod
    def validate_room_type(cls, value: str | None) -> str | None:
        return _validate_room_type(value)


class PatchLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID | None = None
    name: str | None = None
    address: str | None = None
    city: str | None = None
    neighborhood: str | None = None
    reference: str | None = None
    is_virtual: bool | None = None
    status: str | None = None


class DisableLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatchRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_id: UUID | None = None
    name: str | None = None
    room_type: str | None = None
    capacity: int | None = None
    status: str | None = None

    @field_validator("room_type")
    @classmethod
    def validate_room_type(cls, value: str | None) -> str | None:
        return _validate_room_type(value)


class DisableRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


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

    name: str = Field(min_length=1)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized


class PatchSpecialtyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        return value


class CreateOrganizationPractitionerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    practitioner_id: UUID
    role: str = "member"

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ORGANIZATION_PRACTITIONER_ROLES:
            raise ValueError("role must be primary, member or external")
        return value


class PatchOrganizationPractitionerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str | None = None
    status: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is not None and value not in ORGANIZATION_PRACTITIONER_ROLES:
            raise ValueError("role must be primary, member or external")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreatePractitionerServiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    practitioner_id: UUID
    name: str
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    requires_payment: bool = True

    @field_validator("name")
    @classmethod
    def normalize_non_empty_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name must not be empty")
        return normalized


class PatchPractitionerServiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    requires_payment: bool | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_non_empty_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name must not be empty")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreateServiceModalityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modality: str
    location_id: UUID | None = None
    room_id: UUID | None = None


class AssignPractitionerSpecialtyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specialty_id: UUID


class SyncPractitionerSpecialtiesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specialty_ids: list[UUID] = Field(default_factory=list)

    @field_validator("specialty_ids")
    @classmethod
    def reject_duplicates(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("specialty_ids must not contain duplicates")
        return value


class CreatePayerTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    description: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = _normalize_code(value)
        if not normalized:
            raise ValueError("code is required")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized


class PatchPayerTypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_code(value)
        if not normalized:
            raise ValueError("code is required")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreatePayerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payer_type_id: UUID
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized


class PatchPayerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreatePayerPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payer_id: UUID
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized


class PatchPayerPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("name is required")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreatePractitionerServicePriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    practitioner_service_id: UUID
    payer_plan_id: UUID
    price: Decimal = Field(ge=0)
    currency: str
    valid_from: date
    valid_to: date | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha() or value.upper() != value:
            raise ValueError("currency must be a 3-letter uppercase code")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "CreatePractitionerServicePriceRequest":
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not be before valid_from")
        return self


class PatchPractitionerServicePriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    status: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) != 3 or not value.isalpha() or value.upper() != value:
            raise ValueError("currency must be a 3-letter uppercase code")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class CreatePractitionerAvailabilityRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    practitioner_id: UUID
    practitioner_service_id: UUID | None = None
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    valid_from: date
    valid_to: date | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> "CreatePractitionerAvailabilityRuleRequest":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not be before valid_from")
        return self


class PatchPractitionerAvailabilityRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATION_STATUSES:
            raise ValueError("status must be active or inactive")
        return value


class DisablePractitionerAvailabilityRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreatePaymentSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    allow_transfer: bool = True
    allow_simulated_payment: bool = True
    allow_pay_on_site: bool = False
    evidence_deadline_minutes: int = Field(default=60, gt=0)
    manual_review_deadline_minutes: int = Field(default=1440, gt=0)
    release_slot_on_missing_evidence: bool = True
    release_slot_on_review_overdue: bool = False
    status: str = "active"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        return value


class PatchPaymentSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_transfer: bool | None = None
    allow_simulated_payment: bool | None = None
    allow_pay_on_site: bool | None = None
    evidence_deadline_minutes: int | None = Field(default=None, gt=0)
    manual_review_deadline_minutes: int | None = Field(default=None, gt=0)
    release_slot_on_missing_evidence: bool | None = None
    release_slot_on_review_overdue: bool | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        return value


class CreatePaymentAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: UUID
    method: str
    amount: Decimal = Field(ge=0)
    currency: str
    expires_at: datetime | None = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        if value not in PAYMENT_ATTEMPT_METHODS:
            raise ValueError("method must be one of transfer, simulated, pay_on_site")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha() or value.upper() != value:
            raise ValueError("currency must be a 3-letter uppercase code")
        return value


class RegisterPaymentEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_object_key: str | None = None
    original_filename: str | None = None
    content_type: str | None = None
    uploaded_channel: str | None = None
    notes: str | None = None


class ReviewPaymentAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_user_id: UUID | None = None
    notes: str | None = None


class CreatePatientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    document_type: str | None = None
    document_number: str | None = None
    email: str | None = None
    phone: str | None = None


class CreatePatientPayerProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payer_plan_id: UUID
    member_id: str | None = None
    authorization_required: bool = False
    notes: str | None = None



def _serialize_amount(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def serialize_payer_type(payer_type: PayerType) -> dict[str, object]:
    return {
        "id": str(payer_type.id),
        "code": payer_type.code,
        "name": payer_type.name,
        "description": payer_type.description,
        "status": payer_type.status,
    }


def serialize_payer(payer: Payer) -> dict[str, object]:
    payer_type = payer.payer_type
    return {
        "id": str(payer.id),
        "payer_type_id": str(payer.payer_type_id),
        "payer_type_name": payer_type.name if payer_type is not None else None,
        "payer_type_code": payer_type.code if payer_type is not None else None,
        "payer_type_status": payer_type.status if payer_type is not None else None,
        "name": payer.name,
        "description": payer.description,
        "status": payer.status,
    }


def serialize_payer_plan(plan: PayerPlan) -> dict[str, object]:
    payer = plan.payer
    payer_type = payer.payer_type if payer is not None else None
    return {
        "id": str(plan.id),
        "payer_id": str(plan.payer_id),
        "payer_name": payer.name if payer is not None else None,
        "payer_status": payer.status if payer is not None else None,
        "payer_type_id": str(payer.payer_type_id) if payer is not None else None,
        "payer_type_name": payer_type.name if payer_type is not None else None,
        "payer_type_code": payer_type.code if payer_type is not None else None,
        "payer_type_status": payer_type.status if payer_type is not None else None,
        "name": plan.name,
        "description": plan.description,
        "status": plan.status,
    }


def serialize_practitioner_service_price(price: PractitionerServicePrice) -> dict[str, object]:
    service = price.practitioner_service
    organization = service.organization if service is not None else None
    practitioner = service.practitioner if service is not None else None
    plan = price.payer_plan
    payer = plan.payer if plan is not None else None
    payer_type = payer.payer_type if payer is not None else None
    return {
        "id": str(price.id),
        "practitioner_service_id": str(price.practitioner_service_id),
        "practitioner_service_name": service.name if service is not None else None,
        "practitioner_service_status": service.status if service is not None else None,
        "organization_id": str(service.organization_id) if service is not None else None,
        "organization_name": organization.name if organization is not None else None,
        "organization_status": organization.status if organization is not None else None,
        "practitioner_id": str(service.practitioner_id) if service is not None else None,
        "practitioner_name": practitioner.full_name if practitioner is not None else None,
        "practitioner_status": practitioner.status if practitioner is not None else None,
        "payer_plan_id": str(price.payer_plan_id),
        "payer_plan_name": plan.name if plan is not None else None,
        "payer_plan_status": plan.status if plan is not None else None,
        "payer_id": str(plan.payer_id) if plan is not None else None,
        "payer_name": payer.name if payer is not None else None,
        "payer_status": payer.status if payer is not None else None,
        "payer_type_id": str(payer.payer_type_id) if payer is not None else None,
        "payer_type_name": payer_type.name if payer_type is not None else None,
        "payer_type_code": payer_type.code if payer_type is not None else None,
        "payer_type_status": payer_type.status if payer_type is not None else None,
        "price": _serialize_amount(price.price),
        "currency": price.currency,
        "valid_from": price.valid_from.isoformat(),
        "valid_to": price.valid_to.isoformat() if price.valid_to is not None else None,
        "status": price.status,
    }


def serialize_payment_settings(settings: PaymentSettings) -> dict[str, object]:
    return {
        "id": str(settings.id),
        "organization_id": str(settings.organization_id),
        "allow_transfer": settings.allow_transfer,
        "allow_simulated_payment": settings.allow_simulated_payment,
        "allow_pay_on_site": settings.allow_pay_on_site,
        "evidence_deadline_minutes": settings.evidence_deadline_minutes,
        "manual_review_deadline_minutes": settings.manual_review_deadline_minutes,
        "release_slot_on_missing_evidence": settings.release_slot_on_missing_evidence,
        "release_slot_on_review_overdue": settings.release_slot_on_review_overdue,
        "status": settings.status,
    }


def serialize_payment_attempt(attempt: PaymentAttempt) -> dict[str, object]:
    return {
        "id": str(attempt.id),
        "booking_id": str(attempt.booking_id),
        "method": attempt.method,
        "amount": _serialize_amount(attempt.amount),
        "currency": attempt.currency,
        "status": attempt.status,
        "expires_at": attempt.expires_at.isoformat() if attempt.expires_at is not None else None,
        "evidence_received_at": attempt.evidence_received_at.isoformat() if attempt.evidence_received_at is not None else None,
        "reviewed_at": attempt.reviewed_at.isoformat() if attempt.reviewed_at is not None else None,
        "reviewed_by_user_id": str(attempt.reviewed_by_user_id) if attempt.reviewed_by_user_id is not None else None,
    }


def serialize_payment_evidence(evidence: PaymentEvidence) -> dict[str, object]:
    return {
        "id": str(evidence.id),
        "payment_attempt_id": str(evidence.payment_attempt_id),
        "storage_object_key": evidence.storage_object_key,
        "original_filename": evidence.original_filename,
        "content_type": evidence.content_type,
        "uploaded_at": evidence.uploaded_at.isoformat(),
        "uploaded_channel": evidence.uploaded_channel,
        "notes": evidence.notes,
    }


def serialize_payment_review(review: PaymentReview) -> dict[str, object]:
    return {
        "id": str(review.id),
        "payment_attempt_id": str(review.payment_attempt_id),
        "decision": review.decision,
        "reviewer_user_id": str(review.reviewer_user_id) if review.reviewer_user_id is not None else None,
        "reviewed_at": review.reviewed_at.isoformat(),
        "notes": review.notes,
    }


def serialize_patient(patient: Patient) -> dict[str, object]:
    return {
        "id": str(patient.id),
        "full_name": patient.full_name,
        "document_type": patient.document_type,
        "document_number": patient.document_number,
        "email": patient.email,
        "phone": patient.phone,
        "status": patient.profile_status,
    }


def serialize_patient_payer_profile(profile: PatientPayerProfile) -> dict[str, object]:
    return {
        "id": str(profile.id),
        "patient_id": str(profile.patient_id),
        "payer_plan_id": str(profile.payer_plan_id),
        "member_id": profile.member_id,
        "authorization_required": profile.authorization_required,
        "notes": profile.notes,
        "status": profile.status,
    }


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


def serialize_practitioner_service(service: PractitionerService, association: OrganizationPractitioner | None = None) -> dict[str, object]:
    organization = association.organization if association is not None else service.organization
    practitioner = association.practitioner if association is not None else service.practitioner
    return {
        "id": str(service.id),
        "organization_id": str(service.organization_id),
        "organization_name": organization.name if organization is not None else None,
        "organization_status": organization.status if organization is not None else None,
        "practitioner_id": str(service.practitioner_id),
        "practitioner_name": practitioner.full_name if practitioner is not None else None,
        "practitioner_status": practitioner.status if practitioner is not None else None,
        "organization_practitioner_status": association.status if association is not None else None,
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


def serialize_organization_practitioner(association: OrganizationPractitioner) -> dict[str, object]:
    return {
        "organization_id": str(association.organization_id),
        "organization_name": association.organization.name if association.organization is not None else None,
        "organization_status": association.organization.status if association.organization is not None else None,
        "practitioner_id": str(association.practitioner_id),
        "practitioner_name": association.practitioner.full_name if association.practitioner is not None else None,
        "practitioner_status": association.practitioner.status if association.practitioner is not None else None,
        "role": association.role,
        "status": association.status,
    }


def serialize_practitioner_specialty(association: PractitionerSpecialty) -> dict[str, object]:
    return {
        "practitioner_id": str(association.practitioner_id),
        "specialty_id": str(association.specialty_id),
        "specialty_name": association.specialty.name if association.specialty is not None else None,
        "specialty_status": association.specialty.status if association.specialty is not None else None,
        "status": association.status,
    }


@router.get("/patients")
def list_patients(tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    rows = session.scalars(select(Patient).order_by(Patient.full_name, Patient.id)).all()
    return {"data": [serialize_patient(row) for row in rows]}


@router.post("/patients")
def create_patient(
    payload: CreatePatientRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    patient = Patient(**payload.model_dump())
    try:
        session.add(patient)
        session.flush()
        session.refresh(patient)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_patient(patient)}


@router.post("/patients/{patient_id}/payer-profiles")
def create_patient_payer_profile(
    patient_id: UUID,
    payload: CreatePatientPayerProfileRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Patient, patient_id) is None:
        raise ResourceNotFound("Patient not found.")
    if session.get(PayerPlan, payload.payer_plan_id) is None:
        raise ResourceNotFound("Payer plan not found.")
    profile = PatientPayerProfile(patient_id=patient_id, **payload.model_dump())
    try:
        session.add(profile)
        session.flush()
        session.refresh(profile)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_patient_payer_profile(profile)}


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
        session.flush()
        session.refresh(organization)
        session.commit()
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
        session.flush()
        session.refresh(organization)
        session.commit()
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
        session.flush()
        session.refresh(organization)
        session.commit()
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
        session.flush()
        session.refresh(location)
        session.commit()
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


@router.patch("/locations/{location_id}")
def patch_location(
    location_id: UUID,
    payload: PatchLocationRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    location = session.get(Location, location_id)
    if location is None:
        raise ResourceNotFound("Location not found.")
    if payload.organization_id is not None and session.get(Organization, payload.organization_id) is None:
        raise ResourceNotFound("Organization not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    try:
        session.flush()
        session.refresh(location)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_location(location)}


@router.post("/locations/{location_id}/disable")
def disable_location(
    location_id: UUID,
    payload: DisableLocationRequest | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = payload
    _ = tenant_context
    location = session.get(Location, location_id)
    if location is None:
        raise ResourceNotFound("Location not found.")
    location.status = "inactive"
    try:
        session.flush()
        session.refresh(location)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_location(location)}


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
        session.flush()
        session.refresh(room)
        session.commit()
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


@router.patch("/rooms/{room_id}")
def patch_room(
    room_id: UUID,
    payload: PatchRoomRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    room = session.get(Room, room_id)
    if room is None:
        raise ResourceNotFound("Room not found.")
    if payload.location_id is not None and session.get(Location, payload.location_id) is None:
        raise ResourceNotFound("Location not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    try:
        session.flush()
        session.refresh(room)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_room(room)}


@router.post("/rooms/{room_id}/disable")
def disable_room(
    room_id: UUID,
    payload: DisableRoomRequest | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = payload
    _ = tenant_context
    room = session.get(Room, room_id)
    if room is None:
        raise ResourceNotFound("Room not found.")
    room.status = "inactive"
    try:
        session.flush()
        session.refresh(room)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_room(room)}


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
        session.flush()
        session.refresh(practitioner)
        session.commit()
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
        session.flush()
        session.refresh(practitioner)
        session.commit()
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
    existing = session.scalar(select(Specialty).where(func.lower(Specialty.name) == payload.name.lower()))
    if existing is not None:
        raise ConflictError("Specialty name already exists.")
    specialty = Specialty(**payload.model_dump())
    try:
        session.add(specialty)
        session.flush()
        session.refresh(specialty)
        session.commit()
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


@router.get("/specialties/{specialty_id}")
def get_specialty(
    specialty_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    specialty = session.get(Specialty, specialty_id)
    if specialty is None:
        raise ResourceNotFound("Specialty not found.")
    return {"data": serialize_specialty(specialty)}


@router.patch("/specialties/{specialty_id}")
def patch_specialty(
    specialty_id: UUID,
    payload: PatchSpecialtyRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    specialty = session.get(Specialty, specialty_id)
    if specialty is None:
        raise ResourceNotFound("Specialty not found.")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        existing = session.scalar(select(Specialty).where(func.lower(Specialty.name) == data["name"].lower(), Specialty.id != specialty_id))
        if existing is not None:
            raise ConflictError("Specialty name already exists.")
    for field, value in data.items():
        setattr(specialty, field, value)
    try:
        session.flush()
        session.refresh(specialty)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_specialty(specialty)}


@router.post("/specialties/{specialty_id}/disable")
def disable_specialty(
    specialty_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    specialty = session.get(Specialty, specialty_id)
    if specialty is None:
        raise ResourceNotFound("Specialty not found.")
    specialty.status = "inactive"
    try:
        session.flush()
        session.refresh(specialty)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_specialty(specialty)}

@router.get("/practitioners/{practitioner_id}/specialties")
def list_practitioner_specialties(
    practitioner_id: UUID,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if session.get(Practitioner, practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")
    stmt = select(PractitionerSpecialty).where(PractitionerSpecialty.practitioner_id == practitioner_id).join(PractitionerSpecialty.specialty).order_by(Specialty.name, Specialty.id)
    if not include_inactive:
        stmt = stmt.where(PractitionerSpecialty.status == "active")
    associations = session.scalars(stmt).all()
    return {"data": [serialize_practitioner_specialty(association) for association in associations]}


@router.put("/practitioners/{practitioner_id}/specialties")
def sync_practitioner_specialties(
    practitioner_id: UUID,
    payload: SyncPractitionerSpecialtiesRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if session.get(Practitioner, practitioner_id) is None:
        raise ResourceNotFound("Practitioner not found.")

    desired_ids = set(payload.specialty_ids)
    existing = session.scalars(
        select(PractitionerSpecialty).where(PractitionerSpecialty.practitioner_id == practitioner_id)
    ).all()
    existing_by_id = {association.specialty_id: association for association in existing}

    specialties_by_id: dict[UUID, Specialty] = {}
    for specialty_id in desired_ids:
        specialty = session.get(Specialty, specialty_id)
        if specialty is None:
            raise ResourceNotFound("Specialty not found.")

        existing_association = existing_by_id.get(specialty_id)
        preserves_existing_active_relation = (
            existing_association is not None and existing_association.status == "active"
        )
        if specialty.status != "active" and not preserves_existing_active_relation:
            raise BusinessRuleViolation("Inactive specialties cannot be assigned.")
        specialties_by_id[specialty_id] = specialty

    try:
        for specialty_id in desired_ids:
            association = existing_by_id.get(specialty_id)
            if association is None:
                association = PractitionerSpecialty(practitioner_id=practitioner_id, specialty_id=specialty_id)
                association.specialty = specialties_by_id[specialty_id]
                session.add(association)
                existing_by_id[specialty_id] = association
            else:
                association.status = "active"

        for specialty_id, association in existing_by_id.items():
            if specialty_id not in desired_ids and association.status == "active":
                association.status = "inactive"

        session.flush()
        result = session.scalars(
            select(PractitionerSpecialty)
            .where(PractitionerSpecialty.practitioner_id == practitioner_id, PractitionerSpecialty.status == "active")
            .join(PractitionerSpecialty.specialty)
            .order_by(Specialty.name, Specialty.id)
        ).all()
        serialized = [serialize_practitioner_specialty(association) for association in result]
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialized}


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
    specialty = session.get(Specialty, payload.specialty_id)
    if specialty is None:
        raise ResourceNotFound("Specialty not found.")
    if specialty.status != "active":
        raise BusinessRuleViolation("Inactive specialties cannot be assigned.")

    association = session.get(PractitionerSpecialty, {"practitioner_id": practitioner_id, "specialty_id": payload.specialty_id})
    if association is None:
        association = PractitionerSpecialty(practitioner_id=practitioner_id, specialty_id=payload.specialty_id)
        try:
            session.add(association)
            session.flush()
            session.refresh(association)
            session.commit()
        except Exception:
            session.rollback()
            raise
    elif association.status != "active":
        association.status = "active"
        try:
            session.flush()
            session.refresh(association)
            session.commit()
        except Exception:
            session.rollback()
            raise
    return {"data": serialize_practitioner_specialty(association)}


@router.post("/practitioners/{practitioner_id}/specialties/{specialty_id}/disable")
def disable_practitioner_specialty(
    practitioner_id: UUID,
    specialty_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    association = session.get(PractitionerSpecialty, {"practitioner_id": practitioner_id, "specialty_id": specialty_id})
    if association is None:
        raise ResourceNotFound("Practitioner specialty not found.")
    association.status = "inactive"
    try:
        session.flush()
        session.refresh(association)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner_specialty(association)}


@router.get("/organization-practitioners")
def list_organization_practitioners(
    organization_id: UUID | None = None,
    practitioner_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(OrganizationPractitioner).join(OrganizationPractitioner.organization).join(OrganizationPractitioner.practitioner)
    if organization_id is not None:
        stmt = stmt.where(OrganizationPractitioner.organization_id == organization_id)
    if practitioner_id is not None:
        stmt = stmt.where(OrganizationPractitioner.practitioner_id == practitioner_id)
    if status is not None:
        stmt = stmt.where(OrganizationPractitioner.status == status)
    elif not include_inactive:
        stmt = stmt.where(OrganizationPractitioner.status == "active")
    stmt = stmt.order_by(Organization.name, Practitioner.full_name, OrganizationPractitioner.organization_id, OrganizationPractitioner.practitioner_id)
    associations = session.scalars(stmt).all()
    return {"data": [serialize_organization_practitioner(association) for association in associations]}


@router.post("/organization-practitioners")
def create_organization_practitioner(
    payload: CreateOrganizationPractitionerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    organization = session.get(Organization, payload.organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    practitioner = session.get(Practitioner, payload.practitioner_id)
    if practitioner is None:
        raise ResourceNotFound("Practitioner not found.")
    association = session.get(OrganizationPractitioner, {"organization_id": payload.organization_id, "practitioner_id": payload.practitioner_id})
    if association is None and organization.status != "active":
        raise BusinessRuleViolation("Inactive organizations cannot be assigned to new practitioner relationships.")
    if association is None and practitioner.status != "active":
        raise BusinessRuleViolation("Inactive practitioners cannot be assigned to new organization relationships.")
    if association is None:
        association = OrganizationPractitioner(organization_id=payload.organization_id, practitioner_id=payload.practitioner_id, role=payload.role, status="active")
        association.organization = organization
        association.practitioner = practitioner
        session.add(association)
    elif association.status != "active":
        if organization.status != "active":
            raise BusinessRuleViolation("Inactive organizations cannot be reactivated for practitioner relationships.")
        if practitioner.status != "active":
            raise BusinessRuleViolation("Inactive practitioners cannot be reactivated for organization relationships.")
        association.status = "active"
        association.role = payload.role
    else:
        association.role = payload.role
    try:
        session.flush()
        session.refresh(association)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization_practitioner(association)}


@router.patch("/organizations/{organization_id}/practitioners/{practitioner_id}")
def patch_organization_practitioner(
    organization_id: UUID,
    practitioner_id: UUID,
    payload: PatchOrganizationPractitionerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    association = session.get(OrganizationPractitioner, {"organization_id": organization_id, "practitioner_id": practitioner_id})
    if association is None:
        raise ResourceNotFound("Organization practitioner relationship not found.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "active":
        if association.organization is not None and association.organization.status != "active":
            raise BusinessRuleViolation("Inactive organizations cannot be reactivated for practitioner relationships.")
        if association.practitioner is not None and association.practitioner.status != "active":
            raise BusinessRuleViolation("Inactive practitioners cannot be reactivated for organization relationships.")
    for field, value in data.items():
        setattr(association, field, value)
    try:
        session.flush()
        session.refresh(association)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization_practitioner(association)}


@router.post("/organizations/{organization_id}/practitioners/{practitioner_id}/disable")
def disable_organization_practitioner(
    organization_id: UUID,
    practitioner_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    association = session.get(OrganizationPractitioner, {"organization_id": organization_id, "practitioner_id": practitioner_id})
    if association is None:
        raise ResourceNotFound("Organization practitioner relationship not found.")
    association.status = "inactive"
    try:
        session.flush()
        session.refresh(association)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_organization_practitioner(association)}


def _get_organization_practitioner(session: Session, organization_id: UUID, practitioner_id: UUID) -> OrganizationPractitioner | None:
    association = session.get(OrganizationPractitioner, {"organization_id": organization_id, "practitioner_id": practitioner_id})
    if association is None:
        return None
    association.organization = session.get(Organization, organization_id)
    association.practitioner = session.get(Practitioner, practitioner_id)
    return association


def _validate_active_service_parents(session: Session, organization_id: UUID, practitioner_id: UUID) -> OrganizationPractitioner:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    practitioner = session.get(Practitioner, practitioner_id)
    if practitioner is None:
        raise ResourceNotFound("Practitioner not found.")
    if organization.status != "active":
        raise BusinessRuleViolation("Inactive organizations cannot have active practitioner services.")
    if practitioner.status != "active":
        raise BusinessRuleViolation("Inactive practitioners cannot have active practitioner services.")
    association = _get_organization_practitioner(session, organization_id, practitioner_id)
    if association is None:
        raise BusinessRuleViolation("Practitioner must be actively associated to the organization before services can be configured.")
    if association.status != "active":
        raise BusinessRuleViolation("Inactive organization-practitioner relationships cannot have active services.")
    association.organization = organization
    association.practitioner = practitioner
    return association


def _find_duplicate_practitioner_service(session: Session, organization_id: UUID, practitioner_id: UUID, name: str, exclude_id: UUID | None = None) -> PractitionerService | None:
    stmt = select(PractitionerService).where(
        PractitionerService.organization_id == organization_id,
        PractitionerService.practitioner_id == practitioner_id,
        func.lower(PractitionerService.name) == name.lower(),
    )
    if exclude_id is not None:
        stmt = stmt.where(PractitionerService.id != exclude_id)
    return session.scalar(stmt)


@router.post("/practitioner-services")
def create_practitioner_service(
    payload: CreatePractitionerServiceRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    association = _validate_active_service_parents(session, payload.organization_id, payload.practitioner_id)
    if _find_duplicate_practitioner_service(session, payload.organization_id, payload.practitioner_id, payload.name) is not None:
        raise ConflictError("Practitioner service name already exists for this organization and practitioner.")
    service = PractitionerService(**payload.model_dump())
    try:
        session.add(service)
        session.flush()
        session.refresh(service)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner_service(service, association)}


@router.get("/practitioner-services")
def list_practitioner_services(
    organization_id: UUID | None = None,
    practitioner_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(PractitionerService).join(PractitionerService.organization).join(PractitionerService.practitioner)
    if organization_id is not None:
        stmt = stmt.where(PractitionerService.organization_id == organization_id)
    if practitioner_id is not None:
        stmt = stmt.where(PractitionerService.practitioner_id == practitioner_id)
    if status is not None:
        stmt = stmt.where(PractitionerService.status == status)
    elif not include_inactive:
        stmt = stmt.where(PractitionerService.status == "active")
    services = session.scalars(stmt.order_by(PractitionerService.name, PractitionerService.id)).all()
    return {"data": [serialize_practitioner_service(service, _get_organization_practitioner(session, service.organization_id, service.practitioner_id)) for service in services]}


@router.get("/practitioner-services/{service_id}")
def get_practitioner_service(
    service_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    service = session.get(PractitionerService, service_id)
    if service is None:
        raise ResourceNotFound("Practitioner service not found.")
    return {"data": serialize_practitioner_service(service, _get_organization_practitioner(session, service.organization_id, service.practitioner_id))}


@router.patch("/practitioner-services/{service_id}")
def patch_practitioner_service(
    service_id: UUID,
    payload: PatchPractitionerServiceRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    service = session.get(PractitionerService, service_id)
    if service is None:
        raise ResourceNotFound("Practitioner service not found.")
    data = payload.model_dump(exclude_unset=True)
    association = _get_organization_practitioner(session, service.organization_id, service.practitioner_id)
    if data.get("status") == "active":
        association = _validate_active_service_parents(session, service.organization_id, service.practitioner_id)
    if "name" in data and _find_duplicate_practitioner_service(session, service.organization_id, service.practitioner_id, data["name"], exclude_id=service_id) is not None:
        raise ConflictError("Practitioner service name already exists for this organization and practitioner.")
    for field, value in data.items():
        setattr(service, field, value)
    try:
        session.flush()
        session.refresh(service)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner_service(service, association)}


@router.post("/practitioner-services/{service_id}/disable")
def disable_practitioner_service(
    service_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    service = session.get(PractitionerService, service_id)
    if service is None:
        raise ResourceNotFound("Practitioner service not found.")
    service.status = "inactive"
    association = _get_organization_practitioner(session, service.organization_id, service.practitioner_id)
    try:
        session.flush()
        session.refresh(service)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_practitioner_service(service, association)}


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
        session.flush()
        session.refresh(modality)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_service_modality(modality)}


def _find_duplicate_payer_type_code(session: Session, code: str, exclude_id: UUID | None = None) -> PayerType | None:
    stmt = select(PayerType).where(func.lower(PayerType.code) == code.lower())
    if exclude_id is not None:
        stmt = stmt.where(PayerType.id != exclude_id)
    return session.scalar(stmt)


def _find_duplicate_payer(session: Session, payer_type_id: UUID, name: str, exclude_id: UUID | None = None) -> Payer | None:
    stmt = select(Payer).where(Payer.payer_type_id == payer_type_id, func.lower(Payer.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Payer.id != exclude_id)
    return session.scalar(stmt)


def _find_duplicate_payer_plan(session: Session, payer_id: UUID, name: str, exclude_id: UUID | None = None) -> PayerPlan | None:
    stmt = select(PayerPlan).where(PayerPlan.payer_id == payer_id, func.lower(PayerPlan.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(PayerPlan.id != exclude_id)
    return session.scalar(stmt)


def _get_payer_with_type(session: Session, payer_id: UUID) -> Payer | None:
    return session.scalar(select(Payer).options(joinedload(Payer.payer_type)).where(Payer.id == payer_id))


def _get_payer_plan_with_parents(session: Session, plan_id: UUID) -> PayerPlan | None:
    return session.scalar(select(PayerPlan).options(joinedload(PayerPlan.payer).joinedload(Payer.payer_type)).where(PayerPlan.id == plan_id))


@router.get("/payer-types")
def list_payer_types(
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(PayerType)
    if status is not None:
        stmt = stmt.where(PayerType.status == status)
    elif not include_inactive:
        stmt = stmt.where(PayerType.status == "active")
    payer_types = session.scalars(stmt.order_by(PayerType.name, PayerType.id)).all()
    return {"data": [serialize_payer_type(payer_type) for payer_type in payer_types]}


@router.get("/payer-types/{payer_type_id}")
def get_payer_type(
    payer_type_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer_type = session.get(PayerType, payer_type_id)
    if payer_type is None:
        raise ResourceNotFound("Payer type not found.")
    return {"data": serialize_payer_type(payer_type)}


@router.post("/payer-types")
def create_payer_type(
    payload: CreatePayerTypeRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if _find_duplicate_payer_type_code(session, payload.code) is not None:
        raise ConflictError("Payer type code already exists.")
    payer_type = PayerType(**payload.model_dump())
    try:
        session.add(payer_type)
        session.flush()
        session.refresh(payer_type)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payer_type(payer_type)}


@router.patch("/payer-types/{payer_type_id}")
def patch_payer_type(
    payer_type_id: UUID,
    payload: PatchPayerTypeRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer_type = session.get(PayerType, payer_type_id)
    if payer_type is None:
        raise ResourceNotFound("Payer type not found.")
    data = payload.model_dump(exclude_unset=True)
    if "code" in data and _find_duplicate_payer_type_code(session, data["code"], exclude_id=payer_type_id) is not None:
        raise ConflictError("Payer type code already exists.")
    for field, value in data.items():
        setattr(payer_type, field, value)
    try:
        session.flush()
        session.refresh(payer_type)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payer_type(payer_type)}


@router.post("/payer-types/{payer_type_id}/disable")
def disable_payer_type(
    payer_type_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer_type = session.get(PayerType, payer_type_id)
    if payer_type is None:
        raise ResourceNotFound("Payer type not found.")
    payer_type.status = "inactive"
    try:
        session.flush()
        session.refresh(payer_type)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payer_type(payer_type)}


@router.get("/payers")
def list_payers(
    payer_type_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(Payer).options(joinedload(Payer.payer_type)).join(Payer.payer_type)
    if payer_type_id is not None:
        stmt = stmt.where(Payer.payer_type_id == payer_type_id)
    if status is not None:
        stmt = stmt.where(Payer.status == status)
    elif not include_inactive:
        stmt = stmt.where(Payer.status == "active")
    payers = session.scalars(stmt.order_by(Payer.name, Payer.id)).all()
    return {"data": [serialize_payer(payer) for payer in payers]}


@router.get("/payers/{payer_id}")
def get_payer(
    payer_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer = _get_payer_with_type(session, payer_id)
    if payer is None:
        raise ResourceNotFound("Payer not found.")
    return {"data": serialize_payer(payer)}


@router.post("/payers")
def create_payer(
    payload: CreatePayerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer_type = session.get(PayerType, payload.payer_type_id)
    if payer_type is None:
        raise ResourceNotFound("Payer type not found.")
    if payer_type.status != "active":
        raise BusinessRuleViolation("Inactive payer types cannot have active payers.")
    if _find_duplicate_payer(session, payload.payer_type_id, payload.name) is not None:
        raise ConflictError("Payer name already exists for this payer type.")
    payer = Payer(**payload.model_dump())
    payer.payer_type = payer_type
    try:
        session.add(payer)
        session.flush()
        session.refresh(payer)
        data = serialize_payer(payer)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.patch("/payers/{payer_id}")
def patch_payer(
    payer_id: UUID,
    payload: PatchPayerRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer = _get_payer_with_type(session, payer_id)
    if payer is None:
        raise ResourceNotFound("Payer not found.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "active" and payer.payer_type.status != "active":
        raise BusinessRuleViolation("Payers cannot be activated while their payer type is inactive.")
    if "name" in data and _find_duplicate_payer(session, payer.payer_type_id, data["name"], exclude_id=payer_id) is not None:
        raise ConflictError("Payer name already exists for this payer type.")
    for field, value in data.items():
        setattr(payer, field, value)
    try:
        session.flush()
        session.refresh(payer)
        data = serialize_payer(payer)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.post("/payers/{payer_id}/disable")
def disable_payer(
    payer_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer = _get_payer_with_type(session, payer_id)
    if payer is None:
        raise ResourceNotFound("Payer not found.")
    payer.status = "inactive"
    try:
        session.flush()
        session.refresh(payer)
        data = serialize_payer(payer)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.get("/payer-plans")
def list_payer_plans(
    payer_type_id: UUID | None = None,
    payer_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(PayerPlan).options(joinedload(PayerPlan.payer).joinedload(Payer.payer_type)).join(PayerPlan.payer).join(Payer.payer_type)
    if payer_type_id is not None:
        stmt = stmt.where(Payer.payer_type_id == payer_type_id)
    if payer_id is not None:
        stmt = stmt.where(PayerPlan.payer_id == payer_id)
    if status is not None:
        stmt = stmt.where(PayerPlan.status == status)
    elif not include_inactive:
        stmt = stmt.where(PayerPlan.status == "active")
    plans = session.scalars(stmt.order_by(PayerPlan.name, PayerPlan.id)).all()
    return {"data": [serialize_payer_plan(plan) for plan in plans]}


@router.get("/payer-plans/{payer_plan_id}")
def get_payer_plan(
    payer_plan_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    plan = _get_payer_plan_with_parents(session, payer_plan_id)
    if plan is None:
        raise ResourceNotFound("Payer plan not found.")
    return {"data": serialize_payer_plan(plan)}


@router.post("/payer-plans")
def create_payer_plan(
    payload: CreatePayerPlanRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    payer = _get_payer_with_type(session, payload.payer_id)
    if payer is None:
        raise ResourceNotFound("Payer not found.")
    if payer.status != "active" or payer.payer_type.status != "active":
        raise BusinessRuleViolation("Payer plans require an active payer and active payer type.")
    if _find_duplicate_payer_plan(session, payload.payer_id, payload.name) is not None:
        raise ConflictError("Payer plan name already exists for this payer.")
    plan = PayerPlan(**payload.model_dump())
    plan.payer = payer
    try:
        session.add(plan)
        session.flush()
        session.refresh(plan)
        data = serialize_payer_plan(plan)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.patch("/payer-plans/{payer_plan_id}")
def patch_payer_plan(
    payer_plan_id: UUID,
    payload: PatchPayerPlanRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    plan = _get_payer_plan_with_parents(session, payer_plan_id)
    if plan is None:
        raise ResourceNotFound("Payer plan not found.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "active" and (plan.payer.status != "active" or plan.payer.payer_type.status != "active"):
        raise BusinessRuleViolation("Payer plans cannot be activated unless payer and payer type are active.")
    if "name" in data and _find_duplicate_payer_plan(session, plan.payer_id, data["name"], exclude_id=payer_plan_id) is not None:
        raise ConflictError("Payer plan name already exists for this payer.")
    for field, value in data.items():
        setattr(plan, field, value)
    try:
        session.flush()
        session.refresh(plan)
        data = serialize_payer_plan(plan)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.post("/payer-plans/{payer_plan_id}/disable")
def disable_payer_plan(
    payer_plan_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    plan = _get_payer_plan_with_parents(session, payer_plan_id)
    if plan is None:
        raise ResourceNotFound("Payer plan not found.")
    plan.status = "inactive"
    try:
        session.flush()
        session.refresh(plan)
        data = serialize_payer_plan(plan)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


def _price_options():
    return (
        joinedload(PractitionerServicePrice.practitioner_service).joinedload(PractitionerService.organization),
        joinedload(PractitionerServicePrice.practitioner_service).joinedload(PractitionerService.practitioner),
        joinedload(PractitionerServicePrice.payer_plan).joinedload(PayerPlan.payer).joinedload(Payer.payer_type),
    )


def _get_price_with_parents(session: Session, price_id: UUID) -> PractitionerServicePrice | None:
    return session.scalar(select(PractitionerServicePrice).options(*_price_options()).where(PractitionerServicePrice.id == price_id))


def _get_service_with_parents(session: Session, service_id: UUID) -> PractitionerService | None:
    return session.scalar(select(PractitionerService).options(joinedload(PractitionerService.organization), joinedload(PractitionerService.practitioner)).where(PractitionerService.id == service_id))


def _get_payer_plan_with_parents(session: Session, payer_plan_id: UUID) -> PayerPlan | None:
    return session.scalar(select(PayerPlan).options(joinedload(PayerPlan.payer).joinedload(Payer.payer_type)).where(PayerPlan.id == payer_plan_id))


def _validate_price_active_parents(service: PractitionerService, plan: PayerPlan) -> None:
    if service.status != "active":
        raise BusinessRuleViolation("Active prices require an active practitioner service.")
    if plan.status != "active":
        raise BusinessRuleViolation("Active prices require an active payer plan.")
    if plan.payer.status != "active":
        raise BusinessRuleViolation("Active prices require an active payer.")
    if plan.payer.payer_type.status != "active":
        raise BusinessRuleViolation("Active prices require an active payer type.")


def _validate_price_dates(valid_from: date, valid_to: date | None) -> None:
    if valid_to is not None and valid_to < valid_from:
        raise DomainValidationError("valid_to must not be before valid_from.")


def _validate_no_active_price_overlap(session: Session, service_id: UUID, plan_id: UUID, valid_from: date, valid_to: date | None, exclude_id: UUID | None = None) -> None:
    stmt = select(PractitionerServicePrice).where(
        PractitionerServicePrice.practitioner_service_id == service_id,
        PractitionerServicePrice.payer_plan_id == plan_id,
        PractitionerServicePrice.status == "active",
        PractitionerServicePrice.valid_from <= (valid_to or date.max),
        or_(PractitionerServicePrice.valid_to.is_(None), PractitionerServicePrice.valid_to >= valid_from),
    )
    if exclude_id is not None:
        stmt = stmt.where(PractitionerServicePrice.id != exclude_id)
    if session.scalar(stmt) is not None:
        raise ConflictError("Active price validity overlaps another active price for the same service and plan.")


@router.get("/practitioner-service-prices")
def list_all_practitioner_service_prices(
    organization_id: UUID | None = None,
    practitioner_id: UUID | None = None,
    practitioner_service_id: UUID | None = None,
    payer_type_id: UUID | None = None,
    payer_id: UUID | None = None,
    payer_plan_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = True,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    stmt = select(PractitionerServicePrice).options(*_price_options()).join(PractitionerServicePrice.practitioner_service).join(PractitionerServicePrice.payer_plan).join(PayerPlan.payer).join(Payer.payer_type)
    if organization_id is not None:
        stmt = stmt.where(PractitionerService.organization_id == organization_id)
    if practitioner_id is not None:
        stmt = stmt.where(PractitionerService.practitioner_id == practitioner_id)
    if practitioner_service_id is not None:
        stmt = stmt.where(PractitionerServicePrice.practitioner_service_id == practitioner_service_id)
    if payer_type_id is not None:
        stmt = stmt.where(Payer.payer_type_id == payer_type_id)
    if payer_id is not None:
        stmt = stmt.where(PayerPlan.payer_id == payer_id)
    if payer_plan_id is not None:
        stmt = stmt.where(PractitionerServicePrice.payer_plan_id == payer_plan_id)
    if status is not None:
        stmt = stmt.where(PractitionerServicePrice.status == status)
    elif not include_inactive:
        stmt = stmt.where(PractitionerServicePrice.status == "active")
    prices = session.scalars(stmt.order_by(PractitionerServicePrice.valid_from, PractitionerServicePrice.id)).all()
    return {"data": [serialize_practitioner_service_price(price) for price in prices]}


@router.get("/practitioner-service-prices/{price_id}")
def get_practitioner_service_price(price_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    price = _get_price_with_parents(session, price_id)
    if price is None:
        raise ResourceNotFound("Practitioner service price not found.")
    return {"data": serialize_practitioner_service_price(price)}


@router.post("/practitioner-service-prices")
def create_practitioner_service_price(payload: CreatePractitionerServicePriceRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    service = _get_service_with_parents(session, payload.practitioner_service_id)
    if service is None:
        raise ResourceNotFound("Practitioner service not found.")
    plan = _get_payer_plan_with_parents(session, payload.payer_plan_id)
    if plan is None:
        raise ResourceNotFound("Payer plan not found.")
    _validate_price_active_parents(service, plan)
    if session.scalar(select(PractitionerServicePrice).where(PractitionerServicePrice.practitioner_service_id == payload.practitioner_service_id, PractitionerServicePrice.payer_plan_id == payload.payer_plan_id, PractitionerServicePrice.valid_from == payload.valid_from)) is not None:
        raise ConflictError("Practitioner service price already exists for this service, plan and valid_from.")
    _validate_no_active_price_overlap(session, payload.practitioner_service_id, payload.payer_plan_id, payload.valid_from, payload.valid_to)
    price = PractitionerServicePrice(**payload.model_dump(), status="active")
    try:
        session.add(price)
        session.flush()
        price = _get_price_with_parents(session, price.id) or price
        data = serialize_practitioner_service_price(price)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.patch("/practitioner-service-prices/{price_id}")
def patch_practitioner_service_price(price_id: UUID, payload: PatchPractitionerServicePriceRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    price = _get_price_with_parents(session, price_id)
    if price is None:
        raise ResourceNotFound("Practitioner service price not found.")
    data = payload.model_dump(exclude_unset=True)
    valid_from = data.get("valid_from", price.valid_from)
    valid_to = data.get("valid_to", price.valid_to)
    _validate_price_dates(valid_from, valid_to)
    next_status = data.get("status", price.status)
    if next_status == "active":
        _validate_price_active_parents(price.practitioner_service, price.payer_plan)
        _validate_no_active_price_overlap(session, price.practitioner_service_id, price.payer_plan_id, valid_from, valid_to, exclude_id=price_id)
    for field, value in data.items():
        setattr(price, field, value)
    try:
        session.flush()
        price = _get_price_with_parents(session, price_id) or price
        data = serialize_practitioner_service_price(price)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}


@router.post("/practitioner-service-prices/{price_id}/disable")
def disable_practitioner_service_price(price_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    price = _get_price_with_parents(session, price_id)
    if price is None:
        raise ResourceNotFound("Practitioner service price not found.")
    price.status = "inactive"
    try:
        session.flush()
        price = _get_price_with_parents(session, price_id) or price
        data = serialize_practitioner_service_price(price)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": data}

def _relation_status(session: Session, organization_id: UUID, practitioner_id: UUID) -> str | None:
    relation = session.get(OrganizationPractitioner, {"organization_id": organization_id, "practitioner_id": practitioner_id})
    return relation.status if relation is not None else None


def _get_availability_rule(session: Session, rule_id: UUID) -> AvailabilityRule | None:
    return session.get(AvailabilityRule, rule_id)


def _serialize_practitioner_availability_rule(session: Session, rule: AvailabilityRule) -> dict[str, object]:
    organization = session.get(Organization, rule.organization_id)
    practitioner = session.get(Practitioner, rule.practitioner_id)
    service = session.get(PractitionerService, rule.practitioner_service_id) if rule.practitioner_service_id is not None else None
    return {
        "id": str(rule.id),
        "organization_id": str(rule.organization_id),
        "organization_name": organization.name if organization is not None else None,
        "organization_status": organization.status if organization is not None else None,
        "practitioner_id": str(rule.practitioner_id),
        "practitioner_name": practitioner.full_name if practitioner is not None else None,
        "practitioner_status": practitioner.status if practitioner is not None else None,
        "organization_practitioner_status": _relation_status(session, rule.organization_id, rule.practitioner_id),
        "practitioner_service_id": str(rule.practitioner_service_id) if rule.practitioner_service_id is not None else None,
        "practitioner_service_name": service.name if service is not None else None,
        "practitioner_service_status": service.status if service is not None else None,
        "scope_label": service.name if service is not None else "Todos los servicios",
        "day_of_week": rule.weekday,
        "start_time": rule.start_time.isoformat(),
        "end_time": rule.end_time.isoformat(),
        "valid_from": rule.valid_from.isoformat(),
        "valid_to": rule.valid_to.isoformat() if rule.valid_to is not None else None,
        "status": rule.status,
    }


def _validate_availability_dates_times(start_time: time, end_time: time, valid_from: date, valid_to: date | None) -> None:
    if start_time >= end_time:
        raise DomainValidationError("start_time must be before end_time.")
    if valid_to is not None and valid_to < valid_from:
        raise DomainValidationError("valid_to must not be before valid_from.")


def _validate_availability_active_parents(session: Session, organization_id: UUID, practitioner_id: UUID, practitioner_service_id: UUID | None) -> None:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise ResourceNotFound("Organization not found.")
    if organization.status != "active":
        raise BusinessRuleViolation("Availability rules require an active organization.")
    practitioner = session.get(Practitioner, practitioner_id)
    if practitioner is None:
        raise ResourceNotFound("Practitioner not found.")
    if practitioner.status != "active":
        raise BusinessRuleViolation("Availability rules require an active practitioner.")
    relation = session.get(OrganizationPractitioner, {"organization_id": organization_id, "practitioner_id": practitioner_id})
    if relation is None or relation.status != "active":
        raise BusinessRuleViolation("Availability rules require an active organization-practitioner relation.")
    if practitioner_service_id is not None:
        service = session.get(PractitionerService, practitioner_service_id)
        if service is None:
            raise ResourceNotFound("Practitioner service not found.")
        if service.status != "active":
            raise BusinessRuleViolation("Availability rules require an active practitioner service.")
        if service.organization_id != organization_id or service.practitioner_id != practitioner_id:
            raise BusinessRuleViolation("Practitioner service must belong to the selected organization and practitioner.")


def _validate_no_active_availability_overlap(session: Session, organization_id: UUID, practitioner_id: UUID, practitioner_service_id: UUID | None, day_of_week: int, start_time: time, end_time: time, valid_from: date, valid_to: date | None, exclude_id: UUID | None = None) -> None:
    stmt = select(AvailabilityRule).where(
        AvailabilityRule.organization_id == organization_id,
        AvailabilityRule.practitioner_id == practitioner_id,
        AvailabilityRule.weekday == day_of_week,
        AvailabilityRule.status == "active",
        AvailabilityRule.start_time < end_time,
        AvailabilityRule.end_time > start_time,
        AvailabilityRule.valid_from <= (valid_to or date.max),
        or_(AvailabilityRule.valid_to.is_(None), AvailabilityRule.valid_to >= valid_from),
    )
    if practitioner_service_id is None:
        stmt = stmt.where(AvailabilityRule.practitioner_service_id.is_(None))
    else:
        stmt = stmt.where(AvailabilityRule.practitioner_service_id == practitioner_service_id)
    if exclude_id is not None:
        stmt = stmt.where(AvailabilityRule.id != exclude_id)
    if session.scalar(stmt) is not None:
        raise ConflictError("Active availability rule overlaps another active rule for the same scope, day, time and validity.")


@router.get("/practitioner-availability-rules")
def list_practitioner_availability_rules(organization_id: UUID | None = None, practitioner_id: UUID | None = None, practitioner_service_id: UUID | None = None, day_of_week: int | None = None, status: str | None = None, include_inactive: bool = True, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in RELATION_STATUSES:
        raise DomainValidationError("status must be active or inactive.")
    if day_of_week is not None and not 0 <= day_of_week <= 6:
        raise DomainValidationError("day_of_week must be between 0 and 6.")
    stmt = select(AvailabilityRule)
    if organization_id is not None:
        stmt = stmt.where(AvailabilityRule.organization_id == organization_id)
    if practitioner_id is not None:
        stmt = stmt.where(AvailabilityRule.practitioner_id == practitioner_id)
    if practitioner_service_id is not None:
        stmt = stmt.where(AvailabilityRule.practitioner_service_id == practitioner_service_id)
    if day_of_week is not None:
        stmt = stmt.where(AvailabilityRule.weekday == day_of_week)
    if status is not None:
        stmt = stmt.where(AvailabilityRule.status == status)
    elif not include_inactive:
        stmt = stmt.where(AvailabilityRule.status == "active")
    rules = session.scalars(stmt.order_by(AvailabilityRule.weekday, AvailabilityRule.start_time, AvailabilityRule.id)).all()
    return {"data": [_serialize_practitioner_availability_rule(session, rule) for rule in rules]}


@router.get("/practitioner-availability-rules/{rule_id}")
def get_practitioner_availability_rule(rule_id: UUID, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    rule = _get_availability_rule(session, rule_id)
    if rule is None:
        raise ResourceNotFound("Practitioner availability rule not found.")
    return {"data": _serialize_practitioner_availability_rule(session, rule)}


@router.post("/practitioner-availability-rules")
def create_practitioner_availability_rule(payload: CreatePractitionerAvailabilityRuleRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    _validate_availability_active_parents(session, payload.organization_id, payload.practitioner_id, payload.practitioner_service_id)
    _validate_no_active_availability_overlap(session, payload.organization_id, payload.practitioner_id, payload.practitioner_service_id, payload.day_of_week, payload.start_time, payload.end_time, payload.valid_from, payload.valid_to)
    rule = AvailabilityRule(organization_id=payload.organization_id, practitioner_id=payload.practitioner_id, practitioner_service_id=payload.practitioner_service_id, weekday=payload.day_of_week, start_time=payload.start_time, end_time=payload.end_time, valid_from=payload.valid_from, valid_to=payload.valid_to, modality="both", buffer_minutes=0, status="active")
    try:
        session.add(rule); session.flush(); data = _serialize_practitioner_availability_rule(session, rule); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}


@router.patch("/practitioner-availability-rules/{rule_id}")
def patch_practitioner_availability_rule(rule_id: UUID, payload: PatchPractitionerAvailabilityRuleRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = tenant_context
    rule = _get_availability_rule(session, rule_id)
    if rule is None:
        raise ResourceNotFound("Practitioner availability rule not found.")
    data = payload.model_dump(exclude_unset=True)
    day_of_week = data.get("day_of_week", rule.weekday)
    start_time_value = data.get("start_time", rule.start_time)
    end_time_value = data.get("end_time", rule.end_time)
    valid_from = data.get("valid_from", rule.valid_from)
    valid_to = data.get("valid_to", rule.valid_to)
    _validate_availability_dates_times(start_time_value, end_time_value, valid_from, valid_to)
    if data.get("status", rule.status) == "active":
        _validate_availability_active_parents(session, rule.organization_id, rule.practitioner_id, rule.practitioner_service_id)
        _validate_no_active_availability_overlap(session, rule.organization_id, rule.practitioner_id, rule.practitioner_service_id, day_of_week, start_time_value, end_time_value, valid_from, valid_to, exclude_id=rule_id)
    for field, value in data.items():
        setattr(rule, "weekday" if field == "day_of_week" else field, value)
    try:
        session.flush(); data_out = _serialize_practitioner_availability_rule(session, rule); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data_out}


@router.post("/practitioner-availability-rules/{rule_id}/disable")
def disable_practitioner_availability_rule(rule_id: UUID, payload: DisablePractitionerAvailabilityRuleRequest, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, dict[str, object]]:
    _ = (tenant_context, payload)
    rule = _get_availability_rule(session, rule_id)
    if rule is None:
        raise ResourceNotFound("Practitioner availability rule not found.")
    rule.status = "inactive"
    try:
        session.flush(); data = _serialize_practitioner_availability_rule(session, rule); session.commit()
    except Exception:
        session.rollback(); raise
    return {"data": data}


@router.get("/practitioner-services/{service_id}/prices")
def list_practitioner_service_prices(service_id: UUID, status: str | None = None, tenant_context: TenantContext = Depends(get_admin_tenant_context), session: Session = Depends(get_db_session)) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if session.get(PractitionerService, service_id) is None:
        raise ResourceNotFound("Practitioner service not found.")
    stmt = select(PractitionerServicePrice).options(*_price_options()).where(PractitionerServicePrice.practitioner_service_id == service_id)
    if status is not None:
        if status not in RELATION_STATUSES:
            raise DomainValidationError("status must be active or inactive.")
        stmt = stmt.where(PractitionerServicePrice.status == status)
    prices = session.scalars(stmt.order_by(PractitionerServicePrice.valid_from, PractitionerServicePrice.payer_plan_id, PractitionerServicePrice.id)).all()
    return {"data": [serialize_practitioner_service_price(price) for price in prices]}


@router.post("/payment-attempts")
def create_payment_attempt(
    payload: CreatePaymentAttemptRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    try:
        attempt = PaymentAttemptService(session, tenant_context).create_attempt(**payload.model_dump())
        session.flush()
        session.refresh(attempt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payment_attempt(attempt)}


@router.get("/payment-attempts")
def list_payment_attempts(
    booking_id: UUID | None = None,
    method: str | None = None,
    status: str | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if method is not None and method not in PAYMENT_ATTEMPT_METHODS:
        raise DomainValidationError("method must be one of transfer, simulated, pay_on_site")
    if status is not None and status not in PAYMENT_ATTEMPT_STATUSES:
        raise DomainValidationError("Invalid payment attempt status.")
    stmt = select(PaymentAttempt)
    if booking_id is not None:
        stmt = stmt.where(PaymentAttempt.booking_id == booking_id)
    if method is not None:
        stmt = stmt.where(PaymentAttempt.method == method)
    if status is not None:
        stmt = stmt.where(PaymentAttempt.status == status)
    attempts = session.scalars(stmt.order_by(PaymentAttempt.created_at, PaymentAttempt.id)).all()
    return {"data": [serialize_payment_attempt(attempt) for attempt in attempts]}


@router.post("/payment-attempts/{payment_attempt_id}/evidence")
def register_payment_evidence(
    payment_attempt_id: UUID,
    payload: RegisterPaymentEvidenceRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    try:
        evidence = PaymentEvidenceService(session, tenant_context).register_evidence(
            payment_attempt_id=payment_attempt_id,
            **payload.model_dump(),
        )
        session.flush()
        session.refresh(evidence)
        attempt = session.get(PaymentAttempt, payment_attempt_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": {"payment_attempt": serialize_payment_attempt(attempt), "evidence": serialize_payment_evidence(evidence)}}


@router.get("/payment-attempts/{payment_attempt_id}/evidence")
def list_payment_evidence(
    payment_attempt_id: UUID,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if session.get(PaymentAttempt, payment_attempt_id) is None:
        raise ResourceNotFound("Payment attempt not found.")
    evidence_rows = session.scalars(
        select(PaymentEvidence)
        .where(PaymentEvidence.payment_attempt_id == payment_attempt_id)
        .order_by(PaymentEvidence.uploaded_at, PaymentEvidence.id)
    ).all()
    return {"data": [serialize_payment_evidence(evidence) for evidence in evidence_rows]}


@router.post("/payment-attempts/{payment_attempt_id}/approve")
def approve_payment_attempt(
    payment_attempt_id: UUID,
    payload: ReviewPaymentAttemptRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    try:
        review = PaymentReviewService(session, tenant_context).approve_attempt(
            payment_attempt_id=payment_attempt_id,
            **payload.model_dump(),
        )
        session.flush()
        session.refresh(review)
        attempt = session.get(PaymentAttempt, payment_attempt_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": {"payment_attempt": serialize_payment_attempt(attempt), "review": serialize_payment_review(review)}}


@router.post("/payment-attempts/{payment_attempt_id}/reject")
def reject_payment_attempt(
    payment_attempt_id: UUID,
    payload: ReviewPaymentAttemptRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    try:
        review = PaymentReviewService(session, tenant_context).reject_attempt(
            payment_attempt_id=payment_attempt_id,
            **payload.model_dump(),
        )
        session.flush()
        session.refresh(review)
        attempt = session.get(PaymentAttempt, payment_attempt_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": {"payment_attempt": serialize_payment_attempt(attempt), "review": serialize_payment_review(review)}}


@router.get("/payment-reviews")
def list_payment_reviews(
    payment_attempt_id: UUID | None = None,
    decision: str | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if decision is not None and decision not in PAYMENT_REVIEW_DECISIONS:
        raise DomainValidationError("decision must be approved or rejected")
    stmt = select(PaymentReview)
    if payment_attempt_id is not None:
        stmt = stmt.where(PaymentReview.payment_attempt_id == payment_attempt_id)
    if decision is not None:
        stmt = stmt.where(PaymentReview.decision == decision)
    reviews = session.scalars(stmt.order_by(PaymentReview.reviewed_at, PaymentReview.id)).all()
    return {"data": [serialize_payment_review(review) for review in reviews]}


@router.post("/payment-settings")
def create_payment_settings(
    payload: CreatePaymentSettingsRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    if session.get(Organization, payload.organization_id) is None:
        raise ResourceNotFound("Organization not found.")
    if payload.status == "active":
        existing_active = session.scalar(
            select(PaymentSettings).where(
                PaymentSettings.organization_id == payload.organization_id,
                PaymentSettings.status == "active",
            )
        )
        if existing_active is not None:
            raise ConflictError("Active payment settings already exist for this organization.")
    settings = PaymentSettings(**payload.model_dump())
    try:
        session.add(settings)
        session.flush()
        session.refresh(settings)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payment_settings(settings)}


@router.get("/payment-settings")
def list_payment_settings(
    organization_id: UUID | None = None,
    status: str | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, list[dict[str, object]]]:
    _ = tenant_context
    if status is not None and status not in {"active", "inactive"}:
        raise DomainValidationError("status must be active or inactive")
    stmt = select(PaymentSettings)
    if organization_id is not None:
        if session.get(Organization, organization_id) is None:
            raise ResourceNotFound("Organization not found.")
        stmt = stmt.where(PaymentSettings.organization_id == organization_id)
    if status is not None:
        stmt = stmt.where(PaymentSettings.status == status)
    settings = session.scalars(stmt.order_by(PaymentSettings.created_at, PaymentSettings.id)).all()
    return {"data": [serialize_payment_settings(item) for item in settings]}


@router.patch("/payment-settings/{payment_settings_id}")
def patch_payment_settings(
    payment_settings_id: UUID,
    payload: PatchPaymentSettingsRequest,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    _ = tenant_context
    settings = session.get(PaymentSettings, payment_settings_id)
    if settings is None:
        raise ResourceNotFound("Payment settings not found.")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("status") == "active" and settings.status != "active":
        existing_active = session.scalar(
            select(PaymentSettings).where(
                PaymentSettings.organization_id == settings.organization_id,
                PaymentSettings.status == "active",
                PaymentSettings.id != settings.id,
            )
        )
        if existing_active is not None:
            raise ConflictError("Active payment settings already exist for this organization.")
    for field, value in changes.items():
        setattr(settings, field, value)
    try:
        session.flush()
        session.refresh(settings)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"data": serialize_payment_settings(settings)}

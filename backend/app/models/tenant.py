import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.public import TimestampMixin


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    tax_id: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    locations: Mapped[list["Location"]] = relationship(back_populates="organization")
    practitioner_services: Mapped[list["PractitionerService"]] = relationship(back_populates="organization")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="organization")


class Location(TimestampMixin, Base):
    __tablename__ = "locations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    neighborhood: Mapped[str | None] = mapped_column(String(120))
    reference: Mapped[str | None] = mapped_column(Text)
    is_virtual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    organization: Mapped[Organization] = relationship(back_populates="locations")
    rooms: Mapped[list["Room"]] = relationship(back_populates="location")


class Room(TimestampMixin, Base):
    __tablename__ = "rooms"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_type: Mapped[str | None] = mapped_column(String(80))
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    location: Mapped[Location] = relationship(back_populates="rooms")


class Practitioner(TimestampMixin, Base):
    __tablename__ = "practitioners"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    professional_type: Mapped[str | None] = mapped_column(String(80))
    professional_license: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    specialties: Mapped[list["PractitionerSpecialty"]] = relationship(back_populates="practitioner")
    services: Mapped[list["PractitionerService"]] = relationship(back_populates="practitioner")


class Specialty(Base):
    __tablename__ = "specialties"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    practitioners: Mapped[list["PractitionerSpecialty"]] = relationship(back_populates="specialty")


class PractitionerSpecialty(Base):
    __tablename__ = "practitioner_specialties"
    __table_args__ = (UniqueConstraint("practitioner_id", "specialty_id", name="uq_practitioner_specialty"),)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioners.id"), primary_key=True)
    specialty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("specialties.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    practitioner: Mapped[Practitioner] = relationship(back_populates="specialties")
    specialty: Mapped[Specialty] = relationship(back_populates="practitioners")


class PractitionerService(TimestampMixin, Base):
    __tablename__ = "practitioner_services"
    __table_args__ = (CheckConstraint("duration_minutes > 0", name="ck_practitioner_services_duration_positive"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    requires_payment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    organization: Mapped[Organization] = relationship(back_populates="practitioner_services")
    practitioner: Mapped[Practitioner] = relationship(back_populates="services")
    prices: Mapped[list["PractitionerServicePrice"]] = relationship(back_populates="practitioner_service")


class ServiceModality(Base):
    __tablename__ = "service_modalities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practitioner_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioner_services.id"), nullable=False)
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")


class PayerType(Base):
    __tablename__ = "payer_types"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    payers: Mapped[list["Payer"]] = relationship(back_populates="payer_type")


class Payer(Base):
    __tablename__ = "payers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payer_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payer_types.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    payer_type: Mapped[PayerType] = relationship(back_populates="payers")
    plans: Mapped[list["PayerPlan"]] = relationship(back_populates="payer")


class PayerPlan(Base):
    __tablename__ = "payer_plans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    payer: Mapped[Payer] = relationship(back_populates="plans")
    prices: Mapped[list["PractitionerServicePrice"]] = relationship(back_populates="payer_plan")


class PractitionerServicePrice(Base):
    __tablename__ = "practitioner_service_prices"
    __table_args__ = (UniqueConstraint("practitioner_service_id", "payer_plan_id", "valid_from", name="uq_service_plan_price_valid_from"), CheckConstraint("price >= 0", name="ck_practitioner_service_prices_nonnegative"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practitioner_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioner_services.id"), nullable=False)
    payer_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payer_plans.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    practitioner_service: Mapped[PractitionerService] = relationship(back_populates="prices")
    payer_plan: Mapped[PayerPlan] = relationship(back_populates="prices")


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(80))
    email: Mapped[str | None] = mapped_column(String(255))
    document_type: Mapped[str | None] = mapped_column(String(50))
    document_number: Mapped[str | None] = mapped_column(String(120))
    profile_status: Mapped[str] = mapped_column(String(32), nullable=False, default="minimal", server_default="minimal")
    created_from_channel: Mapped[str | None] = mapped_column(String(50))
    contacts: Mapped[list["PatientContact"]] = relationship(back_populates="patient")


class PatientContact(Base):
    __tablename__ = "patient_contacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    patient: Mapped[Patient] = relationship(back_populates="contacts")


class AvailabilityRule(Base):
    __tablename__ = "availability_rules"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    practitioner_service_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioner_services.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")


class AvailabilityException(Base):
    __tablename__ = "availability_exceptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exception_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_starts_at", "starts_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    practitioner_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practitioner_services.id"), nullable=False)
    payer_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payer_types.id"))
    payer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payers.id"))
    payer_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payer_plans.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", server_default="draft")
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default="pending")
    attendance_confirmation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="not_requested", server_default="not_requested")
    service_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    practitioner_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    modality_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    location_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    payer_type_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    payer_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    payer_plan_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_snapshot: Mapped[str] = mapped_column(String(3), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    address_snapshot: Mapped[str | None] = mapped_column(Text)
    room_snapshot: Mapped[str | None] = mapped_column(String(255))
    created_channel: Mapped[str | None] = mapped_column(String(50))
    pending_patient_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    organization: Mapped[Organization] = relationship(back_populates="bookings")

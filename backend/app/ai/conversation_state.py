"""Serializable, temporary state for the future booking conversation graph."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class ConversationStage(StrEnum):
    START = "start"
    IDENTIFY_PATIENT = "identify_patient"
    SELECT_SERVICE = "select_service"
    SELECT_PRACTITIONER = "select_practitioner"
    SELECT_LOCATION = "select_location"
    SELECT_MODALITY = "select_modality"
    SELECT_PAYER = "select_payer"
    SELECT_SLOT = "select_slot"
    REVIEW_BOOKING = "review_booking"
    HANDLE_PAYMENT = "handle_payment"
    COMPLETE = "complete"


class ConversationIntent(StrEnum):
    UNKNOWN = "unknown"
    START_BOOKING = "start_booking"
    PROVIDE_INFORMATION = "provide_information"
    SELECT_OPTION = "select_option"
    CHANGE_SELECTION = "change_selection"
    ASK_QUESTION = "ask_question"
    CANCEL = "cancel"


class InitialConversationIntent(StrEnum):
    """Small intent vocabulary owned by the 8A.9 conversational layer."""

    BOOKING_REQUEST = "booking_request"
    SERVICE_INFORMATION = "service_information"
    CASUAL_CONVERSATION = "casual_conversation"


class InitialConversationStage(StrEnum):
    START = "start"
    COLLECT_SERVICE = "collect_service"
    SERVICE_IDENTIFIED = "service_identified"


class InitialBookingContext(BaseModel):
    """Persistent, JSON-safe context that can become a future graph state."""

    model_config = ConfigDict(extra="forbid")

    intent: InitialConversationIntent = InitialConversationIntent.CASUAL_CONVERSATION
    stage: InitialConversationStage = InitialConversationStage.START
    collected_context: dict[str, JsonValue] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    last_relevant_context: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_internal_material(self) -> Self:
        _reject_forbidden_metadata(self.model_dump(mode="json"), path="conversation_state")
        return self

    def to_persistent_dict(self) -> dict[str, JsonValue]:
        return self.model_dump(mode="json")


class ChannelType(StrEnum):
    SIMULATED = "simulated"
    TELEGRAM = "telegram"
    INTERNAL = "internal"


class BookingModality(StrEnum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"


class ConversationPaymentStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    EVIDENCE_REQUIRED = "evidence_required"
    EVIDENCE_RECEIVED = "evidence_received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SIMULATED_APPROVED = "simulated_approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PendingField(StrEnum):
    PATIENT = "patient"
    SERVICE = "service"
    PRACTITIONER = "practitioner"
    LOCATION = "location"
    MODALITY = "modality"
    PAYER = "payer"
    SLOT = "slot"
    PAYMENT_OPTION = "payment_option"


class SelectedSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("selected slot timestamps must include a timezone")
        if self.ends_at <= self.starts_at:
            raise ValueError("selected slot ends_at must be after starts_at")
        return self


_FORBIDDEN_STATE_KEY_FRAGMENTS = {
    "api_key",
    "authorization",
    "password",
    "prompt",
    "reasoning_content",
    "schema_name",
    "secret",
}


def _reject_forbidden_metadata(value: JsonValue, path: str = "metadata") -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).strip().lower().replace("-", "_")
            if any(
                fragment in normalized_key for fragment in _FORBIDDEN_STATE_KEY_FRAGMENTS
            ):
                raise ValueError(f"{path} cannot contain '{normalized_key}'")
            _reject_forbidden_metadata(nested_value, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            _reject_forbidden_metadata(nested_value, f"{path}[{index}]")


class BookingConversationState(BaseModel):
    """Backend-owned state suitable for future temporary Redis storage.

    Identifiers are internal references only. PostgreSQL remains authoritative for
    every referenced entity and critical status.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    conversation_id: UUID
    tenant_id: UUID
    channel_type: ChannelType
    external_user_id: str | None = None
    patient_id: UUID | None = None
    current_intent: ConversationIntent = ConversationIntent.UNKNOWN
    current_stage: ConversationStage = ConversationStage.START
    selected_service_id: UUID | None = None
    selected_practitioner_id: UUID | None = None
    selected_location_id: UUID | None = None
    selected_room_id: UUID | None = None
    selected_modality: BookingModality | None = None
    selected_payer_type_id: UUID | None = None
    selected_payer_id: UUID | None = None
    selected_payer_plan_id: UUID | None = None
    selected_slot: SelectedSlot | None = None
    booking_id: UUID | None = None
    payment_attempt_id: UUID | None = None
    payment_status: ConversationPaymentStatus = ConversationPaymentStatus.NOT_STARTED
    pending_fields: list[PendingField] = Field(default_factory=list)
    last_user_message: str | None = None
    last_assistant_message: str | None = None
    message_summary: str | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _reject_forbidden_metadata(value)
        return value

    def advance_stage(self, stage: ConversationStage) -> None:
        """Record an orchestrator-selected stage without executing domain work."""
        self.current_stage = stage

    def register_intent(self, intent: ConversationIntent) -> None:
        self.current_intent = intent

    def clear_booking_selection(self) -> None:
        """Discard derived selections when the user restarts or changes context."""
        self.selected_service_id = None
        self.selected_practitioner_id = None
        self.selected_location_id = None
        self.selected_room_id = None
        self.selected_modality = None
        self.selected_payer_type_id = None
        self.selected_payer_id = None
        self.selected_payer_plan_id = None
        self.selected_slot = None
        self.booking_id = None
        self.payment_attempt_id = None
        self.payment_status = ConversationPaymentStatus.NOT_STARTED

    def to_redis_json(self) -> str:
        """Return a JSON representation; no Redis client is used in this phase."""
        _reject_forbidden_metadata(self.metadata)
        return self.model_dump_json()

    @classmethod
    def from_redis_json(cls, payload: str | bytes) -> Self:
        """Validate an untrusted serialized representation before it is used."""
        return cls.model_validate_json(payload)

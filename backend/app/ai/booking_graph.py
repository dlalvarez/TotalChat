"""Deterministic booking graph skeleton without domain tools or external calls."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.ai.conversation_state import (
    BookingConversationState,
    BookingModality,
    ConversationPaymentStatus,
    ConversationStage,
    PendingField,
)


class BookingGraphNode(StrEnum):
    RECEIVE_STATE = "receive_state"
    CLASSIFY_STAGE = "classify_stage"
    DETECT_MISSING_FIELDS = "detect_missing_fields"
    ADVANCE_STAGE = "advance_stage"
    PREPARE_RESULT = "prepare_result"


class BookingGraphAction(StrEnum):
    ASK_FOR_PATIENT = "ask_for_patient"
    ASK_FOR_SERVICE = "ask_for_service"
    ASK_FOR_PRACTITIONER = "ask_for_practitioner"
    ASK_FOR_LOCATION = "ask_for_location"
    ASK_FOR_MODALITY = "ask_for_modality"
    ASK_FOR_PAYER = "ask_for_payer"
    ASK_FOR_SLOT = "ask_for_slot"
    REVIEW_BOOKING = "review_booking"
    HANDLE_PAYMENT = "handle_payment"
    COMPLETE = "complete"


class BookingGraphResult(BaseModel):
    """Internal orchestration result; it is not a user-facing confirmation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state: BookingConversationState
    action: BookingGraphAction
    pending_fields: tuple[PendingField, ...]
    visited_nodes: tuple[BookingGraphNode, ...]
    response_code: str


_ACTION_BY_FIELD = {
    PendingField.PATIENT: BookingGraphAction.ASK_FOR_PATIENT,
    PendingField.SERVICE: BookingGraphAction.ASK_FOR_SERVICE,
    PendingField.PRACTITIONER: BookingGraphAction.ASK_FOR_PRACTITIONER,
    PendingField.LOCATION: BookingGraphAction.ASK_FOR_LOCATION,
    PendingField.MODALITY: BookingGraphAction.ASK_FOR_MODALITY,
    PendingField.PAYER: BookingGraphAction.ASK_FOR_PAYER,
    PendingField.SLOT: BookingGraphAction.ASK_FOR_SLOT,
}

_STAGE_BY_FIELD = {
    PendingField.PATIENT: ConversationStage.IDENTIFY_PATIENT,
    PendingField.SERVICE: ConversationStage.SELECT_SERVICE,
    PendingField.PRACTITIONER: ConversationStage.SELECT_PRACTITIONER,
    PendingField.LOCATION: ConversationStage.SELECT_LOCATION,
    PendingField.MODALITY: ConversationStage.SELECT_MODALITY,
    PendingField.PAYER: ConversationStage.SELECT_PAYER,
    PendingField.SLOT: ConversationStage.SELECT_SLOT,
}


def _detect_missing_fields(state: BookingConversationState) -> tuple[PendingField, ...]:
    missing: list[PendingField] = []
    if state.patient_id is None:
        missing.append(PendingField.PATIENT)
    if state.selected_service_id is None:
        missing.append(PendingField.SERVICE)
    if state.selected_practitioner_id is None:
        missing.append(PendingField.PRACTITIONER)
    if state.selected_modality is None:
        missing.append(PendingField.MODALITY)
    elif (
        state.selected_modality is BookingModality.IN_PERSON
        and state.selected_location_id is None
    ):
        missing.append(PendingField.LOCATION)
    if (
        state.selected_payer_type_id is None
        or state.selected_payer_id is None
        or state.selected_payer_plan_id is None
    ):
        missing.append(PendingField.PAYER)
    if state.selected_slot is None:
        missing.append(PendingField.SLOT)
    return tuple(missing)


def _classify_next_step(
    state: BookingConversationState, missing: tuple[PendingField, ...]
) -> tuple[ConversationStage, BookingGraphAction]:
    if missing:
        first_missing = missing[0]
        return _STAGE_BY_FIELD[first_missing], _ACTION_BY_FIELD[first_missing]
    if state.booking_id is None:
        return ConversationStage.REVIEW_BOOKING, BookingGraphAction.REVIEW_BOOKING
    if state.payment_status not in {
        ConversationPaymentStatus.APPROVED,
        ConversationPaymentStatus.SIMULATED_APPROVED,
    }:
        return ConversationStage.HANDLE_PAYMENT, BookingGraphAction.HANDLE_PAYMENT
    return ConversationStage.COMPLETE, BookingGraphAction.COMPLETE


def run_booking_graph(state: BookingConversationState) -> BookingGraphResult:
    """Run the structural graph without mutating input or executing domain work."""

    graph_state = state.model_copy(deep=True)
    missing = _detect_missing_fields(graph_state)
    stage, action = _classify_next_step(graph_state, missing)
    graph_state.pending_fields = list(missing)
    graph_state.advance_stage(stage)

    return BookingGraphResult(
        state=graph_state,
        action=action,
        pending_fields=missing,
        visited_nodes=tuple(BookingGraphNode),
        response_code=f"booking_graph.{action.value}",
    )

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.ai.booking_graph import BookingGraphAction, BookingGraphNode, run_booking_graph
from app.ai.conversation_state import (
    BookingConversationState,
    BookingModality,
    ChannelType,
    ConversationPaymentStatus,
    ConversationStage,
    PendingField,
    SelectedSlot,
)


def make_state(**overrides):
    values = {
        "conversation_id": uuid4(),
        "tenant_id": uuid4(),
        "channel_type": ChannelType.SIMULATED,
    }
    values.update(overrides)
    return BookingConversationState(**values)


def complete_selection(**overrides):
    start = datetime(2026, 7, 21, 14, tzinfo=timezone.utc)
    values = {
        "patient_id": uuid4(),
        "selected_service_id": uuid4(),
        "selected_practitioner_id": uuid4(),
        "selected_modality": BookingModality.VIRTUAL,
        "selected_payer_type_id": uuid4(),
        "selected_payer_id": uuid4(),
        "selected_payer_plan_id": uuid4(),
        "selected_slot": SelectedSlot(
            starts_at=start, ends_at=start + timedelta(minutes=45)
        ),
    }
    values.update(overrides)
    return make_state(**values)


def test_graph_detects_missing_fields_and_asks_for_first_one():
    state = make_state(current_stage=ConversationStage.COMPLETE)

    result = run_booking_graph(state)

    assert result.action is BookingGraphAction.ASK_FOR_PATIENT
    assert result.state.current_stage is ConversationStage.IDENTIFY_PATIENT
    assert result.pending_fields == (
        PendingField.PATIENT,
        PendingField.SERVICE,
        PendingField.PRACTITIONER,
        PendingField.MODALITY,
        PendingField.PAYER,
        PendingField.SLOT,
    )
    assert state.current_stage is ConversationStage.COMPLETE
    assert state.pending_fields == []


@pytest.mark.parametrize(
    ("modality", "location_id", "expected_action"),
    [
        (BookingModality.IN_PERSON, None, BookingGraphAction.ASK_FOR_LOCATION),
        (BookingModality.VIRTUAL, None, BookingGraphAction.REVIEW_BOOKING),
        (BookingModality.IN_PERSON, uuid4(), BookingGraphAction.REVIEW_BOOKING),
    ],
)
def test_location_is_required_only_for_in_person_bookings(
    modality, location_id, expected_action
):
    result = run_booking_graph(
        complete_selection(
            selected_modality=modality, selected_location_id=location_id
        )
    )

    assert result.action is expected_action


@pytest.mark.parametrize(
    ("payer_context", "expected_action"),
    [
        (
            {
                "selected_payer_type_id": uuid4(),
                "selected_payer_id": None,
                "selected_payer_plan_id": None,
            },
            BookingGraphAction.ASK_FOR_PAYER,
        ),
        (
            {
                "selected_payer_type_id": uuid4(),
                "selected_payer_id": uuid4(),
                "selected_payer_plan_id": None,
            },
            BookingGraphAction.ASK_FOR_PAYER,
        ),
        (
            {
                "selected_payer_type_id": uuid4(),
                "selected_payer_id": uuid4(),
                "selected_payer_plan_id": uuid4(),
            },
            BookingGraphAction.REVIEW_BOOKING,
        ),
    ],
)
def test_graph_requires_complete_payer_context(payer_context, expected_action):
    result = run_booking_graph(complete_selection(**payer_context))

    assert result.action is expected_action
    assert (PendingField.PAYER in result.pending_fields) is (
        expected_action is BookingGraphAction.ASK_FOR_PAYER
    )


def test_graph_structurally_advances_from_review_to_payment_and_complete():
    review = run_booking_graph(complete_selection())
    assert review.action is BookingGraphAction.REVIEW_BOOKING
    assert review.state.current_stage is ConversationStage.REVIEW_BOOKING

    booking_id = uuid4()
    payment = run_booking_graph(complete_selection(booking_id=booking_id))
    assert payment.action is BookingGraphAction.HANDLE_PAYMENT
    assert payment.state.current_stage is ConversationStage.HANDLE_PAYMENT

    complete = run_booking_graph(
        complete_selection(
            booking_id=booking_id,
            payment_status=ConversationPaymentStatus.SIMULATED_APPROVED,
        )
    )
    assert complete.action is BookingGraphAction.COMPLETE
    assert complete.state.current_stage is ConversationStage.COMPLETE


def test_result_is_structured_and_contains_only_internal_graph_nodes():
    result = run_booking_graph(make_state())

    assert result.visited_nodes == tuple(BookingGraphNode)
    assert result.response_code == "booking_graph.ask_for_patient"
    payload = result.model_dump(mode="json")
    assert "schema_name" not in payload["state"]
    assert "reasoning_content" not in payload["state"]

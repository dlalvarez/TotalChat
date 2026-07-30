from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.ai.conversation_state import (
    BookingConversationState,
    ChannelType,
    ConversationIntent,
    ConversationPaymentStatus,
    ConversationStage,
    PendingField,
    SelectedSlot,
    InitialBookingContext,
    CandidateConversationService,
    SelectedConversationService,
)


def make_state(**overrides):
    values = {
        "conversation_id": uuid4(),
        "tenant_id": uuid4(),
        "channel_type": ChannelType.SIMULATED,
    }
    values.update(overrides)
    return BookingConversationState(**values)


def test_state_round_trip_is_json_safe():
    starts_at = datetime(2026, 7, 21, 14, tzinfo=timezone.utc)
    state = make_state(
        selected_service_id=uuid4(),
        selected_slot=SelectedSlot(starts_at=starts_at, ends_at=starts_at + timedelta(minutes=45)),
        pending_fields=[PendingField.PATIENT],
        metadata={"locale": "es-CO", "attempt": 1},
    )

    restored = BookingConversationState.from_redis_json(state.to_redis_json())

    assert restored == state
    assert restored.selected_slot.starts_at.tzinfo is not None


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "schema_name",
        "reasoning_content",
        "api_key",
        "prompt",
        "openai_api_key",
        "totalchat_llm_api_key",
        "jwt_secret",
        "system_prompt",
        "developer_prompt",
        "authorization_header",
        "api-key",
    ],
)
def test_metadata_rejects_forbidden_keys_at_any_depth(forbidden_key):
    with pytest.raises(ValidationError, match="cannot contain"):
        make_state(metadata={"nested": [{forbidden_key: "must-not-be-stored"}]})


def test_serialized_state_rejects_schema_and_reasoning_fields():
    state = make_state()

    for forbidden_field in ("schema_name", "reasoning_content"):
        payload = state.model_dump(mode="json") | {forbidden_field: "forbidden"}
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            BookingConversationState.model_validate(payload)


def test_slot_requires_ordered_timezone_aware_timestamps():
    start = datetime(2026, 7, 21, 14)
    with pytest.raises(ValidationError, match="timezone"):
        SelectedSlot(starts_at=start, ends_at=start + timedelta(minutes=30))

    aware_start = start.replace(tzinfo=timezone.utc)
    with pytest.raises(ValidationError, match="after starts_at"):
        SelectedSlot(starts_at=aware_start, ends_at=aware_start)


def test_helpers_only_update_conversation_state():
    state = make_state(
        selected_service_id=uuid4(),
        selected_practitioner_id=uuid4(),
        selected_slot=SelectedSlot(
            starts_at=datetime(2026, 7, 21, 14, tzinfo=timezone.utc),
            ends_at=datetime(2026, 7, 21, 15, tzinfo=timezone.utc),
        ),
        booking_id=uuid4(),
        payment_attempt_id=uuid4(),
        payment_status=ConversationPaymentStatus.PENDING,
    )

    state.register_intent(ConversationIntent.CHANGE_SELECTION)
    state.advance_stage(ConversationStage.SELECT_SERVICE)
    state.clear_booking_selection()

    assert state.current_intent is ConversationIntent.CHANGE_SELECTION
    assert state.current_stage is ConversationStage.SELECT_SERVICE
    assert state.selected_service_id is None
    assert state.selected_practitioner_id is None
    assert state.selected_slot is None
    assert state.booking_id is None
    assert state.payment_attempt_id is None
    assert state.payment_status is ConversationPaymentStatus.NOT_STARTED


def test_deserialization_rejects_unknown_or_invalid_values():
    state = make_state()
    payload = state.model_dump(mode="json")
    payload["current_stage"] = "invented_stage"

    with pytest.raises(ValidationError):
        BookingConversationState.model_validate(payload)


def test_metadata_must_be_json_serializable():
    with pytest.raises(ValidationError):
        make_state(metadata={"unsafe": object()})


def test_serialization_rechecks_mutated_metadata():
    state = make_state(metadata={"safe": True})
    state.metadata["schema_name"] = "must-not-be-stored"

    with pytest.raises(ValueError, match="schema_name"):
        state.to_redis_json()


def test_initial_context_is_json_safe_and_rejects_internal_material():
    service_id = uuid4()
    context = InitialBookingContext.model_validate({
        "intent": "booking_request",
        "stage": "service_identified",
        "candidate_service": {"name": "consulta pediátrica"},
        "selected_service": {"id": str(service_id), "name": "Pediatría"},
        "collected_context": {"service_name": "Pediatría"},
        "last_relevant_context": {"user_message": "Pediatría"},
        "conversation_progress": {
            "service_confirmed": True,
            "next_expected_action": "continue_booking",
        },
    })
    assert context.to_persistent_dict()["intent"] == "booking_request"
    assert context.selected_service == SelectedConversationService(
        id=service_id, name="Pediatría"
    )
    assert context.to_persistent_dict()["selected_service"]["id"] == str(service_id)
    assert context.candidate_service == CandidateConversationService(
        name="consulta pediátrica"
    )
    assert context.conversation_progress.service_confirmed is True
    assert context.conversation_progress.next_expected_action == "continue_booking"

    with pytest.raises(ValidationError, match="schema_name"):
        InitialBookingContext.model_validate({
            "last_relevant_context": {"schema_name": "tenant_private"}
        })


def test_initial_context_rejects_impossible_service_selection_states():
    with pytest.raises(ValidationError, match="requires selected_service"):
        InitialBookingContext(stage="service_identified")
    with pytest.raises(ValidationError, match="requires service_identified"):
        InitialBookingContext(
            stage="collect_service",
            selected_service={"id": str(uuid4()), "name": "Pediatría"},
        )

    with pytest.raises(ValidationError, match="progress must match"):
        InitialBookingContext(
            stage="service_identified",
            selected_service={"id": str(uuid4()), "name": "Pediatría"},
        )

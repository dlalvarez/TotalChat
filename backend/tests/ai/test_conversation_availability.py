from datetime import date, datetime, timedelta
import json
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.availability_language import parse_availability_query
from app.ai.conversation_invoker import NaturalConversationAgentInvoker
from app.ai.conversation_state import (
    InitialBookingContext,
    InitialConversationProgress,
    InitialConversationStage,
    SelectedConversationService,
    SuggestedConversationService,
)
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.providers import LLMResponse
from app.services.availability import AvailableSlot
from app.tenancy.context import TenantContext
from app.models.tenant import ConversationSession, Message


class FakeSchedulingProvider:
    def __init__(self, count=12):
        self.count = count
        self.calls = []

    def get_available_slots(self, session, tenant_context, request):
        self.calls.append((tenant_context, request))
        start = datetime.combine(request.date_from, datetime.min.time()).replace(hour=8)
        return [AvailableSlot(start + timedelta(minutes=30 * index), start + timedelta(minutes=30 * (index + 1)), uuid.uuid4(), None, None, request.modality) for index in range(self.count)]


class NoopProvider:
    def __init__(self, content="Respuesta natural grounded"):
        self.content = content
        self.calls = []

    def complete(self, messages, *, tools=()):
        self.calls.append((messages, tools))
        return LLMResponse(content=self.content, model="fake", provider="fake")


def confirmed_state(service_id):
    return InitialBookingContext(
        stage=InitialConversationStage.SERVICE_IDENTIFIED,
        selected_service=SelectedConversationService(id=service_id, name="Consulta pediátrica"),
        collected_context={"service_name": "Consulta pediátrica"},
        conversation_progress=InitialConversationProgress(service_confirmed=True, next_expected_action="continue_booking"),
    ).to_persistent_dict()


def create_conversation_tables(engine):
    ConversationSession.__table__.create(engine)
    Message.__table__.create(engine)


def test_natural_dates_and_time_preferences_use_controlled_clock():
    today = date(2026, 8, 6)  # Thursday
    tomorrow = parse_availability_query("¿Qué horarios tienes mañana?", today=today)
    friday = parse_availability_query("próximo viernes después de las 2", today=today)
    afternoon = parse_availability_query("jueves en la tarde", today=today)

    assert tomorrow.date_from == date(2026, 8, 7)
    assert friday.date_from == date(2026, 8, 7) and friday.time_from.hour == 14
    assert afternoon.date_from == today and afternoon.time_from.hour == 12


def test_availability_tool_is_closed_and_returns_only_readable_slot_fields():
    service_id, tenant_id = uuid.uuid4(), uuid.uuid4()
    provider = FakeSchedulingProvider(1)
    registry = ConversationToolRegistry(
        tenant_id=tenant_id,
        repository=object(),
        availability_session=object(),
        tenant_context=TenantContext(tenant_id, "safe", "tenant_internal"),
        selected_service=ResolvedConversationService(service_id, "Consulta pediátrica"),
        scheduling_provider=provider,
    )
    result = registry.execute("get_available_slots", json.dumps({
        "date_from": "2026-08-07", "date_to": "2026-08-07", "modality": "in_person"
    }))

    serialized = json.dumps(dict(result))
    assert result["slots"] == [{"date": "2026-08-07", "start_time": "08:00", "end_time": "08:30"}]
    assert result["kind"] == "availability_lookup"
    assert result["status"] == "available"
    assert result["total_slots"] == result["shown_slots"] == 1
    assert result["has_more"] is False
    assert result["limits"] == {
        "can_create_booking": False,
        "can_hold_slot": False,
        "can_take_payment": False,
    }
    assert str(service_id) not in serialized and str(tenant_id) not in serialized
    assert "schema_name" not in serialized and "tenant_internal" not in serialized


def test_confirmed_service_queries_real_slots_limits_visible_output_and_blocks_booking():
    # Conversation persistence does not require domain tables when the provider is injected.
    engine = create_engine("sqlite+pysqlite:///:memory:")
    create_conversation_tables(engine)
    provider = FakeSchedulingProvider(12)
    llm = NoopProvider("Redacción natural generada por el provider")
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="availability", state=confirmed_state(uuid.uuid4()))
        session.add(conversation)
        session.flush()
        invoker = NaturalConversationAgentInvoker(session, llm, scheduling_provider=provider, today_provider=lambda: date(2026, 8, 6))
        result = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?")
        blocked = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="Sepárame la de las 9")

    assert result.code == "grounded_availability_response"
    assert result.content == "Redacción natural generada por el provider"
    availability_message = next(
        item.content for item in llm.calls[0][0]
        if item.content and "Resultado estructurado autoritativo" in item.content
    )
    payload = json.loads(availability_message.split("hechos: ", 1)[1])
    assert payload["status"] == "available"
    assert payload["shown_slots"] == 10 and payload["total_slots"] == 12
    assert payload["has_more"] is True and len(payload["slots"]) == 10
    assert blocked.code == "grounded_guardrail_response"
    blocked_message = next(
        item.content for item in llm.calls[1][0]
        if item.content and "Resultado estructurado autoritativo" in item.content
    )
    blocked_payload = json.loads(blocked_message.split("hechos: ", 1)[1])
    assert blocked_payload["kind"] == "booking_request_blocked"
    assert blocked_payload["reason"] == "booking_creation_out_of_scope"
    assert conversation.state["last_availability_query"]["service_name"] == "Consulta pediátrica"


def test_unconfirmed_service_never_calls_availability_provider():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    create_conversation_tables(engine)
    provider = FakeSchedulingProvider()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="unconfirmed")
        session.add(conversation)
        session.flush()
        llm = NoopProvider()
        result = NaturalConversationAgentInvoker(session, llm, scheduling_provider=provider, today_provider=lambda: date(2026, 8, 6)).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?"
        )
    assert result.code == "grounded_guardrail_response"
    assert provider.calls == []
    payload_message = next(item.content for item in llm.calls[0][0] if item.content and "Resultado estructurado autoritativo" in item.content)
    assert '"reason": "service_not_confirmed"' in payload_message


def test_no_slots_and_ambiguous_date_are_structured_for_provider_without_lookup_guessing():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    create_conversation_tables(engine)
    scheduling = FakeSchedulingProvider(0)
    llm = NoopProvider()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="empty", state=confirmed_state(uuid.uuid4()))
        session.add(conversation)
        session.flush()
        invoker = NaturalConversationAgentInvoker(session, llm, scheduling_provider=scheduling, today_provider=lambda: date(2026, 8, 6))
        no_slots = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?")
        calls_after_lookup = len(scheduling.calls)
        ambiguous = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes?")

    no_slots_message = next(item.content for item in llm.calls[0][0] if item.content and "Resultado estructurado autoritativo" in item.content)
    no_slots_payload = json.loads(no_slots_message.split("hechos: ", 1)[1])
    assert no_slots.code == "grounded_availability_response"
    assert no_slots_payload["status"] == "no_slots" and no_slots_payload["slots"] == []
    ambiguous_message = next(item.content for item in llm.calls[1][0] if item.content and "Resultado estructurado autoritativo" in item.content)
    assert '"reason": "date_requires_clarification"' in ambiguous_message
    assert ambiguous.code == "grounded_guardrail_response"
    assert len(scheduling.calls) == calls_after_lookup


def test_pending_suggestion_blocks_availability_tool_with_structured_reason():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    create_conversation_tables(engine)
    scheduling, llm = FakeSchedulingProvider(), NoopProvider()
    state = InitialBookingContext(
        stage=InitialConversationStage.COLLECT_SERVICE,
        suggested_service=SuggestedConversationService(name="Consulta pediátrica"),
        missing_information=["service"],
        conversation_progress=InitialConversationProgress(
            service_confirmed=False, next_expected_action="collect_service"
        ),
    ).to_persistent_dict()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="suggested", state=state)
        session.add(conversation)
        session.flush()
        result = NaturalConversationAgentInvoker(session, llm, scheduling_provider=scheduling).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?"
        )
    payload_message = next(item.content for item in llm.calls[0][0] if item.content and "Resultado estructurado autoritativo" in item.content)
    assert result.code == "grounded_guardrail_response"
    assert '"reason": "suggested_service_pending"' in payload_message
    assert scheduling.calls == []

from datetime import date, datetime, timedelta
import json
import uuid

from sqlalchemy.orm import Session

from app.ai.availability_language import parse_availability_query
from app.ai.conversation_invoker import NaturalConversationAgentInvoker
from app.ai.conversation_state import (
    InitialBookingContext,
    InitialConversationProgress,
    InitialConversationStage,
    SelectedConversationService,
)
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.providers import LLMResponse
from app.services.availability import AvailableSlot
from app.tenancy.context import TenantContext
from app.models.tenant import ConversationSession


class FakeSchedulingProvider:
    def __init__(self, count=12):
        self.count = count
        self.calls = []

    def get_available_slots(self, session, tenant_context, request):
        self.calls.append((tenant_context, request))
        start = datetime.combine(request.date_from, datetime.min.time()).replace(hour=8)
        return [AvailableSlot(start + timedelta(minutes=30 * index), start + timedelta(minutes=30 * (index + 1)), uuid.uuid4(), None, None, request.modality) for index in range(self.count)]


class NoopProvider:
    def complete(self, messages, *, tools=()):
        return LLMResponse(content="natural", model="fake", provider="fake")


def confirmed_state(service_id):
    return InitialBookingContext(
        stage=InitialConversationStage.SERVICE_IDENTIFIED,
        selected_service=SelectedConversationService(id=service_id, name="Consulta pediátrica"),
        collected_context={"service_name": "Consulta pediátrica"},
        conversation_progress=InitialConversationProgress(service_confirmed=True, next_expected_action="continue_booking"),
    ).to_persistent_dict()


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
    assert str(service_id) not in serialized and str(tenant_id) not in serialized
    assert "schema_name" not in serialized and "tenant_internal" not in serialized


def test_confirmed_service_queries_real_slots_limits_visible_output_and_blocks_booking():
    # Conversation persistence does not require domain tables when the provider is injected.
    from sqlalchemy import create_engine
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    provider = FakeSchedulingProvider(12)
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="availability", state=confirmed_state(uuid.uuid4()))
        session.add(conversation)
        session.flush()
        invoker = NaturalConversationAgentInvoker(session, NoopProvider(), scheduling_provider=provider, today_provider=lambda: date(2026, 8, 6))
        result = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?")
        blocked = invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="Sepárame la de las 9")

    assert result.code == "grounded_availability_response"
    assert sum(result.content.count(f"{hour:02d}:") for hour in range(24)) == 10
    assert "Hay más horarios" in result.content
    assert blocked.code == "availability_booking_blocked"
    assert "no puedo separar ni crear" in blocked.content
    assert conversation.state["last_availability_query"]["service_name"] == "Consulta pediátrica"


def test_unconfirmed_service_never_calls_availability_provider():
    from sqlalchemy import create_engine
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    provider = FakeSchedulingProvider()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="unconfirmed")
        session.add(conversation)
        session.flush()
        result = NaturalConversationAgentInvoker(session, NoopProvider(), scheduling_provider=provider, today_provider=lambda: date(2026, 8, 6)).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="¿Qué horarios tienes mañana?"
        )
    assert result.code == "availability_service_unconfirmed"
    assert provider.calls == []

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.ai.conversation_invoker import (
    NaturalConversationAgentInvoker, update_initial_booking_context,
)
from app.ai.conversation_prompts import ConversationAssistantIdentity
from app.ai.providers import LLMResponse
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.service_tools import ServiceRecord
from app.models.tenant import ConversationSession, Message


class CapturingProvider:
    def __init__(self):
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        return LLMResponse(content="respuesta exacta", model="fake", provider="fake")


def add_message(session, conversation, *, offset, direction, content, status=None, payload=None):
    raw_payload = dict(payload or {})
    if status is not None:
        raw_payload["delivery_status"] = status
    session.add(Message(
        conversation_session_id=conversation.id,
        channel_type="telegram",
        external_message_id=f"{conversation.id}:{offset}:{direction}",
        direction=direction,
        message_type="text",
        content=content,
        raw_payload=raw_payload,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=offset),
    ))


def make_database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    Message.__table__.create(engine)
    return engine


def test_invoker_uses_only_visible_ordered_messages_from_resolved_conversation():
    engine = make_database()
    provider = CapturingProvider()
    with Session(engine) as session:
        conversation = ConversationSession(
            channel_type="telegram", external_user_id="chat-1", state={"phase": "welcome"}
        )
        other = ConversationSession(channel_type="telegram", external_user_id="chat-2")
        session.add_all([conversation, other])
        session.flush()
        add_message(session, conversation, offset=1, direction="incoming", content="mensaje anterior")
        add_message(session, conversation, offset=2, direction="outgoing", content="respuesta visible", status="sent")
        add_message(session, conversation, offset=3, direction="outgoing", content="respuesta fallida", status="failed")
        add_message(session, conversation, offset=4, direction="outgoing", content="respuesta pendiente", status="pending")
        add_message(session, conversation, offset=5, direction="internal", content="dato interno")
        add_message(session, other, offset=6, direction="incoming", content="otro tenant schema_name")
        add_message(
            session, conversation, offset=7, direction="incoming", content="mensaje actual",
            payload={"chat_id": 999, "token": "secret", "schema_name": "tenant_secret"},
        )
        session.commit()

        result = NaturalConversationAgentInvoker(session, provider).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="mensaje actual"
        )

    sent = provider.calls[0]
    history = [(message.role, message.content) for message in sent if message.role != "system"]
    assert history == [
        ("user", "mensaje anterior"),
        ("assistant", "respuesta visible"),
        ("user", "mensaje actual"),
    ]
    assert result.content == "respuesta exacta"
    serialized = repr(sent)
    for excluded in (
        "respuesta fallida", "respuesta pendiente", "dato interno", "otro tenant",
        "chat_id", "tenant_secret", '"token": "secret"',
    ):
        assert excluded not in serialized
    assert "intent=casual_conversation; stage=start" in serialized
    assert "Sofía" in sent[0].content and "Sofi" in sent[0].content


def test_invoker_applies_eight_message_limit_after_visibility_filtering():
    engine = make_database()
    provider = CapturingProvider()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="chat")
        session.add(conversation)
        session.flush()
        for index in range(12):
            add_message(session, conversation, offset=index, direction="incoming", content=f"visible-{index}")
        for index in range(12, 24):
            add_message(session, conversation, offset=index, direction="outgoing", content=f"failed-{index}", status="failed")
        add_message(session, conversation, offset=24, direction="incoming", content="actual")
        session.commit()
        NaturalConversationAgentInvoker(session, provider).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="actual"
        )

    history = [message.content for message in provider.calls[0] if message.role == "user"]
    assert history == [f"visible-{index}" for index in range(4, 12)] + ["actual"]


def test_long_conversation_uses_bounded_keyset_batches_past_recent_failures():
    engine = make_database()
    provider = CapturingProvider()
    message_queries = []

    @event.listens_for(engine, "before_cursor_execute")
    def capture_message_queries(connection, cursor, statement, parameters, context, executemany):
        if "FROM messages" in statement:
            message_queries.append(statement)

    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="long-chat")
        other = ConversationSession(channel_type="telegram", external_user_id="other-chat")
        session.add_all([conversation, other])
        session.flush()
        for index in range(10):
            add_message(
                session, conversation, offset=index, direction="incoming", content=f"old-visible-{index}"
            )
        for index in range(10, 90):
            add_message(
                session, conversation, offset=index, direction="outgoing",
                content=f"recent-failed-{index}", status="failed",
            )
        add_message(session, other, offset=95, direction="incoming", content="other-conversation")
        add_message(session, conversation, offset=100, direction="incoming", content="actual")
        session.commit()

        NaturalConversationAgentInvoker(session, provider).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation, message_text="actual"
        )

    history = [message.content for message in provider.calls[0] if message.role == "user"]
    assert history == [f"old-visible-{index}" for index in range(2, 10)] + ["actual"]
    assert "other-conversation" not in repr(provider.calls)
    assert len(message_queries) >= 4
    assert all("LIMIT" in statement.upper() for statement in message_queries)
    assert any("messages.created_at <" in statement for statement in message_queries[1:])


def test_backend_configured_identity_reaches_runtime_without_uuid_or_schema():
    engine = make_database()
    provider = CapturingProvider()
    identity = ConversationAssistantIdentity(
        display_name="Valentina", friendly_name="Vale", organization_display_name="Clínica Vida"
    )
    tenant_id = uuid.uuid4()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="chat")
        session.add(conversation)
        session.flush()
        add_message(session, conversation, offset=1, direction="incoming", content="actual")
        session.commit()
        NaturalConversationAgentInvoker(
            session, provider, assistant_identity=identity
        ).invoke(tenant_id=tenant_id, conversation=conversation, message_text="actual")

    prompt = provider.calls[0][0].content
    assert "Valentina" in prompt and "Vale" in prompt and "Clínica Vida" in prompt
    assert str(tenant_id) not in repr(provider.calls)
    assert str(conversation.id) not in repr(provider.calls)
    assert "schema_name" in prompt  # only the immutable prohibition, never a configured schema value


def test_initial_intents_are_classified_without_exposing_them_to_the_user():
    booking = update_initial_booking_context({}, "Quiero una cita")
    services = update_initial_booking_context({}, "¿Qué servicios tienen?")
    casual = update_initial_booking_context({}, "Hola")

    assert booking.intent.value == "booking_request"
    assert booking.stage.value == "collect_service"
    assert booking.missing_information == ["service"]
    assert services.intent.value == "service_information"
    assert casual.intent.value == "casual_conversation"


def test_booking_context_progresses_using_persisted_state():
    first = update_initial_booking_context({}, "Quiero una cita")
    service_id = uuid.uuid4()
    second = update_initial_booking_context(
        first.to_persistent_dict(),
        "Pediatría",
        resolve_service=lambda query: ResolvedConversationService(
            service_id=service_id, name="Consulta pediátrica"
        ),
    )

    assert second.intent.value == "booking_request"
    assert second.stage.value == "service_identified"
    assert second.selected_service is not None
    assert second.selected_service.id == service_id
    assert second.selected_service.name == "Consulta pediátrica"
    assert second.collected_context == {"service_name": "Consulta pediátrica"}
    assert second.missing_information == []


def test_invoker_persists_booking_context_between_messages():
    engine = make_database()
    provider = CapturingProvider()
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="booking-chat")
        session.add(conversation)
        session.flush()

        repository = BookingServiceRepository("Consulta pediátrica")
        invoker = NaturalConversationAgentInvoker(
            session, provider, service_repository=repository
        )
        invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="Quiero una cita")
        session.commit()
        assert conversation.state["stage"] == "collect_service"

        invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="Pediatría")
        session.commit()
        session.refresh(conversation)

        assert conversation.state["intent"] == "booking_request"
        assert conversation.state["stage"] == "service_identified"
        assert conversation.state["selected_service"] == {
            "id": str(repository.record.service_id), "name": "Consulta pediátrica",
        }
        assert conversation.state["collected_context"] == {"service_name": "Consulta pediátrica"}
        serialized = repr(provider.calls)
        assert "schema_name=" not in serialized
        assert str(repository.record.service_id) not in serialized
        assert "service_name=Consulta pediátrica" in serialized


class BookingServiceRepository:
    def __init__(self, name: str, *additional_names: str):
        self.records = [ServiceRecord(
            service_id=uuid.uuid4(), name=service_name, description=service_name,
            duration_minutes=30, practitioner_id=uuid.uuid4(), practitioner_name="Dra. Ana",
            organization_id=uuid.uuid4(), organization_name="Clínica",
        ) for service_name in (name, *additional_names)]
        self.record = self.records[0]
        self.queries = []

    def list_active(self, **filters):
        self.queries.append(filters)
        return self.records

    def get_active(self, service_id):
        return self.record if service_id == self.record.service_id else None


def test_unknown_service_stays_in_collection_stage_and_requests_clarification():
    first = update_initial_booking_context({}, "Quiero una cita")
    second = update_initial_booking_context(
        first.to_persistent_dict(),
        "Servicio inexistente XYZ",
        resolve_service=lambda query: None,
    )

    assert second.stage.value == "collect_service"
    assert second.selected_service is None
    assert second.missing_information == ["service"]
    assert second.collected_context == {}
    assert second.last_relevant_context["service_resolution"] == "not_found"


def test_invoker_surfaces_unknown_service_as_safe_clarification_context():
    engine = make_database()
    provider = CapturingProvider()
    repository = BookingServiceRepository("Consulta pediátrica")
    repository.list_active = lambda **filters: []
    with Session(engine) as session:
        conversation = ConversationSession(
            channel_type="telegram",
            external_user_id="unknown-service",
            state=update_initial_booking_context(
                {}, "Quiero una cita"
            ).to_persistent_dict(),
        )
        session.add(conversation)
        session.flush()

        result = NaturalConversationAgentInvoker(
            session, provider, service_repository=repository
        ).invoke(
            tenant_id=uuid.uuid4(),
            conversation=conversation,
            message_text="Servicio inexistente XYZ",
        )

    assert result.content == "respuesta exacta"
    assert conversation.state["stage"] == "collect_service"
    safe_state_message = next(
        message.content
        for message in provider.calls[0]
        if message.role == "system" and message.content.startswith("Estado conversacional permitido:")
    )
    assert "service_resolution=not_found" in safe_state_message


def test_explicit_valid_service_change_replaces_selected_entity():
    repository = BookingServiceRepository("Pediatría", "Neurología")
    first = update_initial_booking_context({}, "Quiero una cita")
    pediatrics = update_initial_booking_context(
        first.to_persistent_dict(), "Pediatría",
        resolve_service=ConversationToolRegistry(
            tenant_id=uuid.uuid4(), repository=repository
        ).resolve_service,
    )

    neurology = update_initial_booking_context(
        pediatrics.to_persistent_dict(), "Quiero una cita en Neurología",
        resolve_service=ConversationToolRegistry(
            tenant_id=uuid.uuid4(), repository=repository
        ).resolve_service,
    )

    assert neurology.stage.value == "service_identified"
    assert neurology.selected_service is not None
    assert neurology.selected_service.name == "Neurología"
    assert neurology.selected_service.id == repository.records[1].service_id
    assert neurology.collected_context == {"service_name": "Neurología"}


def test_explicit_invalid_service_change_clears_previous_selection():
    service_id = uuid.uuid4()
    selected = update_initial_booking_context(
        update_initial_booking_context({}, "Quiero una cita").to_persistent_dict(),
        "Pediatría",
        resolve_service=lambda query: ResolvedConversationService(
            service_id=service_id, name="Pediatría"
        ),
    )

    changed = update_initial_booking_context(
        selected.to_persistent_dict(), "Quiero una cita en CardiologíaXYZ",
        resolve_service=lambda query: None,
    )

    assert changed.selected_service is None
    assert changed.stage.value == "collect_service"
    assert changed.collected_context == {}
    assert changed.missing_information == ["service"]
    assert changed.last_relevant_context["service_resolution"] == "not_found"


def test_booking_reiteration_without_new_service_keeps_valid_selection():
    service_id = uuid.uuid4()
    selected = update_initial_booking_context(
        update_initial_booking_context({}, "Quiero una cita").to_persistent_dict(),
        "Pediatría",
        resolve_service=lambda query: ResolvedConversationService(
            service_id=service_id, name="Pediatría"
        ),
    )

    unchanged = update_initial_booking_context(
        selected.to_persistent_dict(), "Quiero una cita", resolve_service=lambda query: None
    )

    assert unchanged.selected_service == selected.selected_service
    assert unchanged.stage.value == "service_identified"

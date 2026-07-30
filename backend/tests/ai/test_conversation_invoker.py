from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.ai.conversation_invoker import (
    NaturalConversationAgentInvoker,
    _response_guard,
    _safe_context_instruction,
    update_initial_booking_context,
)
from app.ai.conversation_prompts import ConversationAssistantIdentity
from app.ai.providers import LLMResponse
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.service_tools import ServiceRecord
from app.ai.conversation_state import (
    CandidateConversationService,
    InitialBookingContext,
    InitialConversationProposal,
)
from app.models.tenant import ConversationSession, Message


class CapturingProvider:
    def __init__(self):
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        return LLMResponse(content="respuesta exacta", model="fake", provider="fake")


def proposal(intent, candidate=None, decision=None):
    if decision is None:
        decision = (
            "select" if intent == "booking_request" and candidate
            else ("explore" if intent == "service_information" else "none")
        )
    return InitialConversationProposal(
        intent=intent,
        candidate_service=(
            CandidateConversationService(name=candidate) if candidate else None
        ),
        service_decision=decision,
    )


def casual_proposal(context, text):
    return proposal("casual_conversation")


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

        result = NaturalConversationAgentInvoker(
            session, provider, proposal_interpreter=casual_proposal
        ).invoke(
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
    assert "Assistant" in sent[0].content and "TotalChat" in sent[0].content


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
        NaturalConversationAgentInvoker(
            session, provider, proposal_interpreter=casual_proposal
        ).invoke(
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

        NaturalConversationAgentInvoker(
            session, provider, proposal_interpreter=casual_proposal
        ).invoke(
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
            session, provider, assistant_identity=identity,
            proposal_interpreter=casual_proposal,
        ).invoke(tenant_id=tenant_id, conversation=conversation, message_text="actual")

    prompt = provider.calls[0][0].content
    assert "Valentina" in prompt and "Vale" in prompt and "Clínica Vida" in prompt
    assert str(tenant_id) not in repr(provider.calls)
    assert str(conversation.id) not in repr(provider.calls)
    assert "schema_name" in prompt  # only the immutable prohibition, never a configured schema value


def test_proposals_separate_information_questions_from_booking_selection():
    booking = update_initial_booking_context(
        InitialBookingContext(), "Quiero una cita", proposal=proposal("booking_request")
    )
    information = update_initial_booking_context(
        booking, "¿Tienes pediatría?",
        proposal=proposal("service_information", "Pediatría"),
    )

    assert information.intent.value == "service_information"
    assert information.candidate_service is not None
    assert information.candidate_service.name == "Pediatría"
    assert information.selected_service is None
    assert information.stage.value == "collect_service"


def test_explicit_confirmation_promotes_prior_candidate_but_ambiguous_ack_does_not():
    repository = BookingServiceRepository("Pediatría")
    explored = update_initial_booking_context(
        InitialBookingContext(), "¿Tienen pediatría?",
        proposal=proposal("service_information", "Pediatría"),
    )
    ambiguous = update_initial_booking_context(
        explored, "Perfecto", proposal=proposal("casual_conversation")
    )
    confirmed = update_initial_booking_context(
        ambiguous, "Sí, esa quiero",
        proposal=proposal("booking_request", decision="confirm_candidate"),
        resolve_service=resolver(repository),
    )

    assert ambiguous.selected_service is None
    assert ambiguous.candidate_service.name == "Pediatría"
    assert confirmed.selected_service.id == repository.record.service_id
    assert confirmed.selected_service.name == "Pediatría"


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
        return next((record for record in self.records if record.service_id == service_id), None)


def resolver(repository):
    return ConversationToolRegistry(
        tenant_id=uuid.uuid4(), repository=repository
    ).resolve_service


def suggester(repository):
    return ConversationToolRegistry(
        tenant_id=uuid.uuid4(), repository=repository
    ).suggest_service


def test_related_service_is_persisted_as_suggestion_without_selection():
    repository = BookingServiceRepository("Consulta pediátrica")

    context = update_initial_booking_context(
        InitialBookingContext(),
        "Quiero una cita con pediatría",
        proposal=proposal("booking_request", "pediatría"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert context.selected_service is None
    assert context.suggested_service.name == "Consulta pediátrica"
    assert context.stage.value == "collect_service"
    assert context.conversation_progress.service_confirmed is False
    assert context.last_relevant_context["service_resolution"] == "suggested"
    safe_context = _safe_context_instruction(context)
    assert "service_confirmed=false" in safe_context
    assert "service_resolution=suggested" in safe_context
    assert "candidate_service=pediatría" in safe_context
    assert "suggested_service_name=Consulta pediátrica" in safe_context


def test_explicit_confirmation_promotes_prior_suggested_service():
    repository = BookingServiceRepository("Consulta pediátrica")
    suggested = update_initial_booking_context(
        InitialBookingContext(),
        "¿Tienen pediatría?",
        proposal=proposal("service_information", "pediatría"),
        suggest_service=suggester(repository),
    )

    confirmed = update_initial_booking_context(
        suggested,
        "Sí, ese",
        proposal=proposal("booking_request", decision="confirm_candidate"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert confirmed.suggested_service is None
    assert confirmed.selected_service.id == repository.record.service_id
    assert confirmed.selected_service.name == "Consulta pediátrica"
    assert confirmed.conversation_progress.service_confirmed is True
    assert confirmed.last_relevant_context["service_resolution"] == "identified"


@pytest.mark.parametrize("message", ["¿La cambiaste?", "¿Ya quedó?", "Perfecto"])
def test_ambiguous_or_interrogative_turn_does_not_confirm_suggestion(message):
    repository = BookingServiceRepository("Consulta pediátrica")
    suggested = update_initial_booking_context(
        InitialBookingContext(),
        "Quiero pediatría",
        proposal=proposal("booking_request", "pediatría"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    unchanged = update_initial_booking_context(
        suggested,
        message,
        proposal=proposal("booking_request", decision="confirm_candidate"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert unchanged.selected_service is None
    assert unchanged.suggested_service.name == "Consulta pediátrica"
    assert unchanged.stage.value == "collect_service"
    assert unchanged.conversation_progress.service_confirmed is False
    assert unchanged.last_relevant_context["service_resolution"] == "suggested"


@pytest.mark.parametrize("message", ["Sí, ese", "Confirmo"])
def test_affirmative_confirmation_promotes_suggestion(message):
    repository = BookingServiceRepository("Consulta pediátrica")
    suggested = update_initial_booking_context(
        InitialBookingContext(),
        "Quiero pediatría",
        proposal=proposal("booking_request", "pediatría"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    confirmed = update_initial_booking_context(
        suggested,
        message,
        proposal=proposal("booking_request", decision="confirm_candidate"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert confirmed.selected_service.name == "Consulta pediátrica"
    assert confirmed.suggested_service is None
    assert confirmed.conversation_progress.service_confirmed is True
    assert confirmed.last_relevant_context["service_resolution"] == "identified"


def test_explicit_change_with_real_service_name_is_selected_directly():
    repository = BookingServiceRepository("Consulta pediátrica")

    selected = update_initial_booking_context(
        InitialBookingContext(),
        "Cámbiala a Consulta pediátrica",
        proposal=proposal("booking_request", "Consulta pediátrica"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert selected.selected_service.name == "Consulta pediátrica"
    assert selected.suggested_service is None
    assert selected.last_relevant_context["service_resolution"] == "identified"


def test_booking_proposal_is_validated_and_persists_confirmed_service():
    repository = BookingServiceRepository("Consulta pediátrica")
    collecting = update_initial_booking_context(
        InitialBookingContext(), "Quiero una cita", proposal=proposal("booking_request")
    )
    selected = update_initial_booking_context(
        collecting, "Quiero una consulta pediátrica",
        proposal=proposal("booking_request", "Consulta pediátrica"),
        resolve_service=resolver(repository),
    )

    assert selected.stage.value == "service_identified"
    assert selected.candidate_service.name == "Consulta pediátrica"
    assert selected.selected_service.id == repository.record.service_id
    assert selected.selected_service.name == "Consulta pediátrica"
    assert selected.collected_context == {"service_name": "Consulta pediátrica"}


def test_valid_change_replaces_confirmed_service_and_invalid_change_clears_it():
    repository = BookingServiceRepository("Consulta pediátrica", "Nefrología")
    selected = update_initial_booking_context(
        InitialBookingContext(), "Quiero consulta pediátrica",
        proposal=proposal("booking_request", "Consulta pediátrica"),
        resolve_service=resolver(repository),
    )
    changed = update_initial_booking_context(
        selected, "Mejor nefrología", proposal=proposal("booking_request", "Nefrología"),
        resolve_service=resolver(repository),
    )

    assert changed.selected_service.id == repository.records[1].service_id
    assert changed.selected_service.name == "Nefrología"

    missing = update_initial_booking_context(
        changed, "Ahora CardiologíaXYZ",
        proposal=proposal("booking_request", "CardiologíaXYZ"),
        resolve_service=lambda query: None,
    )
    assert missing.selected_service is None
    assert missing.stage.value == "collect_service"
    assert missing.collected_context == {}
    assert missing.last_relevant_context["service_resolution"] == "not_found"


def test_clinically_risky_typo_stays_unresolved_until_explicit_confirmation():
    repository = BookingServiceRepository("Consulta nefrología")
    unresolved = update_initial_booking_context(
        InitialBookingContext(), "Quiero nuerología",
        proposal=proposal("booking_request", "nuerología"),
        resolve_service=resolver(repository),
        suggest_service=suggester(repository),
    )

    assert unresolved.candidate_service.name == "nuerología"
    assert unresolved.selected_service is None
    assert unresolved.suggested_service is None
    assert unresolved.stage.value == "collect_service"
    assert unresolved.conversation_progress.service_confirmed is False
    assert unresolved.conversation_progress.next_expected_action == "collect_service"
    assert unresolved.last_relevant_context["service_resolution"] == "not_found"


def test_information_turn_keeps_existing_confirmed_service_until_new_selection():
    repository = BookingServiceRepository("Consulta pediátrica", "Nefrología")
    selected = update_initial_booking_context(
        InitialBookingContext(), "Quiero una cita pediátrica",
        proposal=proposal("booking_request", "Consulta pediátrica"),
        resolve_service=resolver(repository),
    )
    price_question = update_initial_booking_context(
        selected, "¿Tienes neurología?",
        proposal=proposal("service_information", "Neurología"),
    )
    changed = update_initial_booking_context(
        price_question, "Ahora quiero nefrología",
        proposal=proposal("booking_request", "Nefrología"),
        resolve_service=resolver(repository),
    )

    assert price_question.selected_service == selected.selected_service
    assert price_question.candidate_service.name == "Neurología"
    assert price_question.intent.value == "service_information"
    safe_context = _safe_context_instruction(price_question)
    assert "service_confirmed=true" in safe_context
    assert "service_resolution=not_found" in safe_context
    assert "service_name=Consulta pediátrica" in safe_context
    assert "candidate_service=Neurología" in safe_context
    response_guard = _response_guard(price_question)
    assert response_guard.intent == "service_information"
    assert response_guard.service_resolution == "not_found"
    assert response_guard.service_name == "Consulta pediátrica"
    assert response_guard.candidate_service == "Neurología"
    assert changed.selected_service.id == repository.records[1].service_id


def test_multiple_service_changes_keep_only_latest_confirmed_selection():
    repository = BookingServiceRepository("Pediatría", "Nefrología")
    context = InitialBookingContext()
    for message, candidate in (
        ("Pediatría", "Pediatría"),
        ("Nefrología", "Nefrología"),
        ("No, mejor pediatría", "Pediatría"),
    ):
        context = update_initial_booking_context(
            context, message, proposal=proposal("booking_request", candidate),
            resolve_service=resolver(repository),
        )

    assert context.selected_service.id == repository.records[0].service_id
    assert context.selected_service.name == "Pediatría"
    assert context.conversation_progress.service_confirmed is True
    assert context.conversation_progress.next_expected_action == "continue_booking"


def test_booking_follow_up_without_new_candidate_preserves_progress_without_booking():
    repository = BookingServiceRepository("Pediatría")
    selected = update_initial_booking_context(
        InitialBookingContext(), "Quiero una cita pediátrica",
        proposal=proposal("booking_request", "Pediatría"),
        resolve_service=resolver(repository),
    )
    follow_up = update_initial_booking_context(
        selected, "Necesito fecha y hora", proposal=proposal("booking_request")
    )

    assert follow_up.selected_service == selected.selected_service
    assert follow_up.stage.value == "service_identified"
    assert follow_up.conversation_progress.next_expected_action == "continue_booking"
    assert "booking_id" not in follow_up.to_persistent_dict()


def test_invoker_persists_confirmed_service_but_never_sends_uuid_to_llm():
    engine = make_database()
    provider = CapturingProvider()
    repository = BookingServiceRepository("Consulta pediátrica")
    proposals = iter([
        proposal("booking_request"),
        proposal("booking_request", "Consulta pediátrica"),
    ])
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="booking-chat")
        session.add(conversation)
        session.flush()
        conversation_id = conversation.id
        invoker = NaturalConversationAgentInvoker(
            session, provider, service_repository=repository,
            proposal_interpreter=lambda context, text: next(proposals),
        )
        invoker.invoke(tenant_id=uuid.uuid4(), conversation=conversation, message_text="Quiero una cita")
        invoker.invoke(
            tenant_id=uuid.uuid4(), conversation=conversation,
            message_text="Quiero una consulta pediátrica",
        )
        session.commit()

    with Session(engine) as session:
        refreshed = session.get(ConversationSession, conversation_id)
        assert refreshed is not None
        assert refreshed.state["selected_service"] == {
            "id": str(repository.record.service_id), "name": "Consulta pediátrica",
        }
    serialized = repr(provider.calls)
    assert str(repository.record.service_id) not in serialized
    assert "service_name=Consulta pediátrica" in serialized


def test_llm_interpreter_returns_structured_proposal_without_persisting_raw_output():
    class ProposalProvider(CapturingProvider):
        def complete(self, messages):
            self.calls.append(messages)
            if messages[0].content.startswith("Interpreta únicamente"):
                return LLMResponse(
                    content=(
                        '{"intent":"booking_request",'
                        '"candidate_service":{"name":"Pediatría"},'
                        '"service_decision":"select"}'
                    ),
                    model="fake", provider="fake",
                )
            return LLMResponse(content="respuesta", model="fake", provider="fake")

    engine = make_database()
    provider = ProposalProvider()
    repository = BookingServiceRepository("Pediatría")
    with Session(engine) as session:
        conversation = ConversationSession(channel_type="telegram", external_user_id="proposal")
        session.add(conversation)
        session.flush()
        NaturalConversationAgentInvoker(
            session, provider, service_repository=repository
        ).invoke(
            tenant_id=uuid.uuid4(), conversation=conversation,
            message_text="ok, me interesa una consulta pediátrica",
        )

    assert conversation.state["selected_service"]["name"] == "Pediatría"
    assert "candidate_service=Pediatría" in repr(provider.calls[-1])
    assert "service_confirmed=true" in repr(provider.calls[-1])
    proposal_prompt = provider.calls[0][0].content
    assert "aceptación afirmativa explícita" in proposal_prompt
    assert "pregunta sobre si algo ya cambió" in proposal_prompt
    assert 'expresiones ambiguas como "Perfecto"' in proposal_prompt
    assert str(repository.record.service_id) not in repr(provider.calls)

import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.booking_agent import BookingConversationResult
from app.channels.telegram import TelegramUpdate, TelegramWebhookService
from app.models.tenant import ConversationSession, Message
from app.tenancy.context import TenantContext


UPDATE = {"update_id": 51001, "message": {"message_id": 91, "chat": {"id": 80001}, "text": "consulta general"}}

COMPLETE_STATE = {
    "patient_id": str(uuid.uuid4()),
    "payer_type": "prepaid",
    "payer_name": "Sura",
    "plan_name": "Plan básico",
    "preferred_date": "2026-07-22",
    "preferred_modality": "in_person",
    "payment_method": "transfer",
}


@dataclass
class AgentSpy:
    fail: bool = False
    calls: list[dict[str, object]] = field(default_factory=list)

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("controlled agent failure")
        return BookingConversationResult(status="service_not_found", completed_steps=())


def make_service(monkeypatch, agent, *, state=None):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    Message.__table__.create(engine)
    tenant = TenantContext(uuid.uuid4(), "agent-tenant", "tenant_agent_tenant")
    monkeypatch.setattr("app.channels.telegram.TenantResolver.resolve_by_channel", lambda self, **kwargs: tenant)
    if state is not None:
        with Session(engine) as session:
            session.add(ConversationSession(
                channel_type="telegram",
                external_user_id=str(UPDATE["message"]["chat"]["id"]),
                state=state,
            ))
            session.commit()
    return engine, TelegramUpdate.model_validate(UPDATE), tenant


def test_valid_intake_invokes_agent_with_backend_tenant_and_persists_pending_result(monkeypatch):
    agent = AgentSpy()
    engine, update, tenant = make_service(monkeypatch, agent, state=COMPLETE_STATE)

    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        messages = session.scalars(select(Message).order_by(Message.direction)).all()

    assert result.accepted is True
    assert len(agent.calls) == 1
    assert agent.calls[0]["tenant_id"] == tenant.tenant_id
    assert agent.calls[0]["message_text"] == "consulta general"
    assert [(item.direction, item.content) for item in messages] == [
        ("incoming", "consulta general"), ("outgoing", "BookingAgent: service_not_found")
    ]
    assert messages[1].raw_payload == {
        "delivery_status": "pending", "agent_status": "service_not_found", "source_update_id": 51001
    }
    assert "schema_name" not in repr(agent.calls)


def test_agent_error_keeps_incoming_and_persists_unsent_controlled_result(monkeypatch):
    agent = AgentSpy(fail=True)
    engine, update, _ = make_service(monkeypatch, agent, state=COMPLETE_STATE)

    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        messages = session.scalars(select(Message).order_by(Message.direction)).all()

    assert result.accepted is True
    assert len(agent.calls) == 1
    assert [item.direction for item in messages] == ["incoming", "outgoing"]
    assert messages[1].content == (
        "No pude continuar con la reserva en este momento. "
        "Por favor, intenta de nuevo más tarde."
    )
    assert messages[1].raw_payload["delivery_status"] == "pending"
    assert messages[1].raw_payload["agent_status"] == "error"


def test_duplicate_update_does_not_invoke_agent_twice(monkeypatch):
    agent = AgentSpy()
    engine, update, _ = make_service(monkeypatch, agent, state=COMPLETE_STATE)
    with Session(engine) as session:
        service = TelegramWebhookService(session, agent_invoker=agent)
        first = service.process(update, bot_identifier="bot")
        second = service.process(update, bot_identifier="bot")
        messages = session.scalars(select(Message)).all()

    assert first.duplicate is False and second.duplicate is True
    assert len(agent.calls) == 1
    assert len(messages) == 2


def test_default_bridge_builds_controlled_request_and_calls_booking_agent(monkeypatch):
    engine, update, tenant = make_service(monkeypatch, AgentSpy())
    patient_id = uuid.uuid4()
    captured = []

    def run(agent, request):
        captured.append(request)
        return BookingConversationResult(status="no_availability", completed_steps=())

    monkeypatch.setattr("app.channels.telegram.BookingAgent.run", run)
    with Session(engine) as session:
        session.add(ConversationSession(
            channel_type="telegram",
            external_user_id=str(UPDATE["message"]["chat"]["id"]),
            state={
                "patient_id": str(patient_id),
                "payer_type": "prepaid",
                "payer_name": "Sura",
                "plan_name": "Plan básico",
                "preferred_date": "2026-07-22",
                "preferred_modality": "in_person",
                "payment_method": "transfer",
                "schema_name": "must_be_ignored",
                "unexpected": "must_be_ignored",
            },
        ))
        session.commit()
        TelegramWebhookService(session).process(update, bot_identifier="bot")
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert len(captured) == 1
    request = captured[0]
    assert request.tenant_id == tenant.tenant_id
    assert request.patient_id == patient_id
    assert request.service_query == "consulta general"
    assert request.preferred_date == date(2026, 7, 22)
    assert not hasattr(request, "schema_name")
    assert outgoing.content == "BookingAgent: no_availability"
    assert outgoing.raw_payload["delivery_status"] == "pending"


def test_empty_state_starts_booking_context_without_invoking_agent(monkeypatch):
    agent = AgentSpy()
    engine, update, _ = make_service(monkeypatch, agent)
    update.message.text = "Hola"

    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        conversation = session.scalars(select(ConversationSession)).one()
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert result.accepted is True
    assert agent.calls == []
    assert outgoing.content == (
        "Hola, soy el asistente de MediChat. Puedo ayudarte a iniciar una reserva. "
        "Para empezar, dime qué servicio necesitas."
    )
    assert outgoing.raw_payload["agent_status"] == "collecting_booking_context"
    assert conversation.state == {
        "phase": "collecting_booking_context",
        "last_user_message": "Hola",
        "missing_fields": [
            "patient_id", "payer_type", "payer_name", "plan_name", "preferred_date",
            "preferred_modality", "payment_method",
        ],
    }


def test_incomplete_state_preserves_progress_and_refreshes_missing_fields(monkeypatch):
    agent = AgentSpy()
    state = {"payer_type": "private", "last_user_message": "mensaje anterior"}
    engine, update, _ = make_service(monkeypatch, agent, state=state)

    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        conversation = session.scalars(select(ConversationSession)).one()

    assert agent.calls == []
    assert conversation.state["payer_type"] == "private"
    assert conversation.state["phase"] == "collecting_booking_context"
    assert conversation.state["last_user_message"] == "consulta general"
    assert "payer_type" not in conversation.state["missing_fields"]

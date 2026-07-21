import uuid
from dataclasses import dataclass, field

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.conversation_types import ConversationTurnResult
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
        return ConversationTurnResult(
            content="¿Qué fecha prefieres?",
            status="needs_date",
            state={**(kwargs["conversation"].state or {}), "phase": "collecting_booking_context"},
        )


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
        ("incoming", "consulta general"), ("outgoing", "¿Qué fecha prefieres?")
    ]
    assert messages[1].raw_payload == {
        "delivery_status": "pending", "agent_status": "needs_date", "source_update_id": 51001
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


def test_empty_state_invokes_conversation_agent(monkeypatch):
    agent = AgentSpy()
    engine, update, _ = make_service(monkeypatch, agent)
    update.message.text = "Hola"

    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        conversation = session.scalars(select(ConversationSession)).one()
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert result.accepted is True
    assert len(agent.calls) == 1
    assert outgoing.content == "¿Qué fecha prefieres?"
    assert outgoing.raw_payload["agent_status"] == "needs_date"
    assert conversation.state["phase"] == "collecting_booking_context"


def test_invoker_result_replaces_state_without_adapter_domain_logic(monkeypatch):
    agent = AgentSpy()
    state = {"payer_type": "private", "last_user_message": "mensaje anterior"}
    engine, update, _ = make_service(monkeypatch, agent, state=state)

    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        conversation = session.scalars(select(ConversationSession)).one()

    assert len(agent.calls) == 1
    assert conversation.state["phase"] == "collecting_booking_context"

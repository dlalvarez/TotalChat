import uuid
from dataclasses import dataclass, field

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.conversation_runtime import ConversationTurnResult, TECHNICAL_FALLBACK
from app.channels.telegram import TelegramUpdate, TelegramWebhookService
from app.models.tenant import ConversationSession, Message
from app.tenancy.context import TenantContext


UPDATE = {"update_id": 51001, "message": {"message_id": 91, "chat": {"id": 80001}, "text": "Hola"}}


@dataclass
class AgentSpy:
    content: str = "Respuesta natural del provider"
    fail: bool = False
    calls: list[dict[str, object]] = field(default_factory=list)

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("secret provider detail")
        return ConversationTurnResult(content=self.content, code="natural_response")


def make_service(monkeypatch, *, state=None):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    Message.__table__.create(engine)
    tenant = TenantContext(uuid.uuid4(), "agent-tenant", "tenant_agent_tenant")
    monkeypatch.setattr("app.channels.telegram.TenantResolver.resolve_by_channel", lambda self, **kwargs: tenant)
    if state is not None:
        with Session(engine) as session:
            session.add(ConversationSession(
                channel_type="telegram", external_user_id="80001", state=state
            ))
            session.commit()
    return engine, TelegramUpdate.model_validate(UPDATE), tenant


def test_intake_invokes_agnostic_runtime_and_persists_exact_provider_content(monkeypatch):
    agent = AgentSpy(content="Claro, cuéntame qué necesitas gestionar.")
    engine, update, tenant = make_service(monkeypatch)

    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        messages = session.scalars(select(Message).order_by(Message.direction)).all()
        conversation = session.scalars(select(ConversationSession)).one()

    assert result.accepted is True
    assert len(agent.calls) == 1
    assert agent.calls[0]["tenant_id"] == tenant.tenant_id
    assert agent.calls[0]["message_text"] == "Hola"
    assert [(item.direction, item.content) for item in messages] == [
        ("incoming", "Hola"), ("outgoing", "Claro, cuéntame qué necesitas gestionar.")
    ]
    assert messages[1].raw_payload == {
        "delivery_status": "pending", "agent_status": "natural_response", "source_update_id": 51001
    }
    assert conversation.state == {}
    assert "schema_name" not in repr(agent.calls)
    assert "chat_id" not in repr(agent.calls)


def test_runtime_error_persists_generic_nonempty_fallback(monkeypatch):
    agent = AgentSpy(fail=True)
    engine, update, _ = make_service(monkeypatch)

    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert outgoing.content == TECHNICAL_FALLBACK
    assert "secret provider detail" not in outgoing.content
    assert outgoing.raw_payload["delivery_status"] == "pending"
    assert outgoing.raw_payload["agent_status"] == "runtime_error"


def test_duplicate_update_does_not_reinvoke_runtime(monkeypatch):
    agent = AgentSpy()
    engine, update, _ = make_service(monkeypatch)
    with Session(engine) as session:
        service = TelegramWebhookService(session, agent_invoker=agent)
        first = service.process(update, bot_identifier="bot")
        second = service.process(update, bot_identifier="bot")
        messages = session.scalars(select(Message)).all()

    assert first.duplicate is False and second.duplicate is True
    assert len(agent.calls) == 1
    assert len(messages) == 2


def test_channel_does_not_rewrite_existing_conversation_state(monkeypatch):
    agent = AgentSpy()
    engine, update, _ = make_service(monkeypatch, state={"phase": "welcome", "custom": "kept"})
    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=agent).process(update, bot_identifier="bot")
        conversation = session.scalars(select(ConversationSession)).one()

    assert conversation.state == {"phase": "welcome", "custom": "kept"}

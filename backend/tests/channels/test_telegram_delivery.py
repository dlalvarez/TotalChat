import uuid
from dataclasses import dataclass, field

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.booking_agent import BookingConversationResult
from app.channels.telegram import TelegramUpdate, TelegramWebhookService
from app.models.tenant import ConversationSession, Message
from app.tenancy.context import TenantContext


UPDATE = {"update_id": 61001, "message": {"message_id": 101, "chat": {"id": 70001}, "text": "consulta"}}


class Agent:
    def invoke(self, **kwargs):
        return BookingConversationResult(status="service_not_found", completed_steps=())


@dataclass
class FakeTelegramClient:
    fail: bool = False
    calls: list[dict[str, object]] = field(default_factory=list)

    def send_message(self, *, chat_id: int, text: str) -> int:
        self.calls.append({"chat_id": chat_id, "text": text})
        if self.fail:
            raise OSError("synthetic network failure")
        return 9876


def make_service(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    ConversationSession.__table__.create(engine)
    Message.__table__.create(engine)
    tenant = TenantContext(uuid.uuid4(), "delivery-tenant", "tenant_delivery_tenant")
    monkeypatch.setattr("app.channels.telegram.TenantResolver.resolve_by_channel", lambda self, **kwargs: tenant)
    return engine


def test_pending_outgoing_is_sent_and_confirmation_is_persisted(monkeypatch):
    client = FakeTelegramClient()
    engine = make_service(monkeypatch)
    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=Agent(), telegram_client=client).process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert result.accepted is True
    assert client.calls == [{"chat_id": 70001, "text": "BookingAgent: service_not_found"}]
    assert outgoing.raw_payload["delivery_status"] == "sent"
    assert outgoing.raw_payload["telegram_message_id"] == 9876
    assert "schema_name" not in repr(client.calls)


def test_api_or_network_failure_marks_failed_without_breaking_webhook(monkeypatch):
    client = FakeTelegramClient(fail=True)
    engine = make_service(monkeypatch)
    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=Agent(), telegram_client=client).process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert result.accepted is True
    assert outgoing.raw_payload["delivery_status"] == "failed"
    assert len(client.calls) == 1


def test_duplicate_update_never_sends_twice(monkeypatch):
    client = FakeTelegramClient()
    engine = make_service(monkeypatch)
    with Session(engine) as session:
        service = TelegramWebhookService(session, agent_invoker=Agent(), telegram_client=client)
        first = service.process(TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot")
        second = service.process(TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot")

    assert first.duplicate is False and second.duplicate is True
    assert len(client.calls) == 1


def test_no_configured_client_leaves_pending_without_network(monkeypatch):
    engine = make_service(monkeypatch)
    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=Agent()).process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert outgoing.raw_payload["delivery_status"] == "pending"

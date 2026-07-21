import uuid
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai import ConversationTurnResult
from app.channels.telegram import TelegramUpdate, TelegramWebhookService
from app.models.tenant import ConversationSession, Message
from app.tenancy.context import TenantContext


UPDATE = {"update_id": 61001, "message": {"message_id": 101, "chat": {"id": 70001}, "text": "consulta"}}
TEST_RESPONSE_CONTENT = "Respuesta conversacional generada para la prueba."


@dataclass
class FakeConversationInvoker:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def invoke(
        self,
        *,
        tenant_id: UUID,
        conversation: ConversationSession,
        message_text: str,
    ) -> ConversationTurnResult:
        self.calls.append({
            "tenant_id": tenant_id,
            "conversation_id": conversation.id,
            "message_text": message_text,
        })
        return ConversationTurnResult(
            content=TEST_RESPONSE_CONTENT,
            status="conversation_progressed",
            state={"phase": "collecting_booking_context"},
        )


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
    return engine, tenant


def test_pending_outgoing_is_sent_and_confirmation_is_persisted(monkeypatch):
    client = FakeTelegramClient()
    invoker = FakeConversationInvoker()
    engine, tenant = make_service(monkeypatch)
    with Session(engine) as session:
        result = TelegramWebhookService(session, agent_invoker=invoker, telegram_client=client).process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()
        conversation = session.scalars(select(ConversationSession)).one()

    assert result.accepted is True
    assert len(invoker.calls) == 1
    assert invoker.calls[0]["tenant_id"] == tenant.tenant_id
    assert invoker.calls[0]["conversation_id"] == conversation.id
    assert invoker.calls[0]["message_text"] == "consulta"
    assert set(invoker.calls[0]) == {"tenant_id", "conversation_id", "message_text"}
    assert conversation.state == {"phase": "collecting_booking_context"}
    assert outgoing.content == TEST_RESPONSE_CONTENT
    assert client.calls == [{"chat_id": 70001, "text": TEST_RESPONSE_CONTENT}]
    assert client.calls[0]["text"] == TEST_RESPONSE_CONTENT
    assert outgoing.raw_payload["delivery_status"] == "sent"
    assert outgoing.raw_payload["telegram_message_id"] == 9876
    assert "schema_name" not in repr(client.calls)


def test_api_or_network_failure_marks_failed_without_breaking_webhook(monkeypatch):
    client = FakeTelegramClient(fail=True)
    engine, _tenant = make_service(monkeypatch)
    original_select_tenant_schema = TelegramWebhookService._select_tenant_schema
    selected_schemas = []

    def spy_select_tenant_schema(self, schema_name):
        selected_schemas.append(schema_name)
        return original_select_tenant_schema(self, schema_name)

    monkeypatch.setattr(
        TelegramWebhookService, "_select_tenant_schema", spy_select_tenant_schema
    )
    with Session(engine) as session:
        service = TelegramWebhookService(
            session, agent_invoker=FakeConversationInvoker(), telegram_client=client
        )
        result = service.process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert result.accepted is True
    assert outgoing.raw_payload["delivery_status"] == "failed"
    assert len(client.calls) == 1
    assert selected_schemas == ["tenant_delivery_tenant"] * 4


def test_duplicate_update_never_sends_twice(monkeypatch):
    client = FakeTelegramClient()
    engine, _tenant = make_service(monkeypatch)
    with Session(engine) as session:
        service = TelegramWebhookService(
            session, agent_invoker=FakeConversationInvoker(), telegram_client=client
        )
        first = service.process(TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot")
        second = service.process(TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot")

    assert first.duplicate is False and second.duplicate is True
    assert len(client.calls) == 1


def test_no_configured_client_leaves_pending_without_network(monkeypatch):
    engine, _tenant = make_service(monkeypatch)
    with Session(engine) as session:
        TelegramWebhookService(session, agent_invoker=FakeConversationInvoker()).process(
            TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot"
        )
        outgoing = session.scalars(select(Message).where(Message.direction == "outgoing")).one()

    assert outgoing.raw_payload["delivery_status"] == "pending"


def test_delivery_reselects_tenant_schema_after_outgoing_commit(monkeypatch):
    client = FakeTelegramClient()
    engine, _tenant = make_service(monkeypatch)
    original_select_tenant_schema = TelegramWebhookService._select_tenant_schema
    selected_schemas = []

    def spy_select_tenant_schema(self, schema_name):
        selected_schemas.append(schema_name)
        return original_select_tenant_schema(self, schema_name)

    monkeypatch.setattr(
        TelegramWebhookService, "_select_tenant_schema", spy_select_tenant_schema
    )
    with Session(engine) as session:
        service = TelegramWebhookService(
            session, agent_invoker=FakeConversationInvoker(), telegram_client=client
        )

        service.process(TelegramUpdate.model_validate(UPDATE), bot_identifier="configured-bot")

    assert selected_schemas == ["tenant_delivery_tenant"] * 3

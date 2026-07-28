from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.conversation_invoker import NaturalConversationAgentInvoker
from app.ai.conversation_prompts import ConversationAssistantIdentity
from app.ai.providers import LLMResponse
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
    assert "Estado conversacional permitido: welcome" in serialized
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

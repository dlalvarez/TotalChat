"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.conversation_prompts import ConversationAssistantIdentity
from app.ai.conversation_runtime import (
    ConversationContextMessage,
    ConversationTurnRequest,
    ConversationTurnResult,
    NaturalConversationRuntime,
)
from app.ai.providers import LLMProvider
from app.models.tenant import ConversationSession, Message


class NaturalConversationAgentInvoker:
    """Load bounded tenant-scoped history and invoke the provider-neutral runtime."""

    def __init__(
        self,
        session: Session,
        llm_provider: LLMProvider,
        *,
        assistant_identity: ConversationAssistantIdentity | None = None,
    ) -> None:
        self._session = session
        self._runtime = NaturalConversationRuntime(llm_provider)
        self._assistant_identity = assistant_identity or ConversationAssistantIdentity()

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult:
        state = conversation.state or {}
        stored_messages = list(self._session.scalars(
            select(Message)
            .where(Message.conversation_session_id == conversation.id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        ).all())
        chronological = stored_messages
        if chronological and chronological[-1].direction == "incoming":
            chronological = chronological[:-1]
        visible_messages = [
            message for message in chronological if _is_visible_conversation_message(message)
        ][-8:]
        recent_messages = tuple(
            ConversationContextMessage(
                role="user" if item.direction == "incoming" else "assistant",
                content=item.content,
            )
            for item in visible_messages
        )
        return self._runtime.run(ConversationTurnRequest(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            message_text=message_text,
            recent_messages=recent_messages,
            conversation_phase=(str(state["phase"]) if state.get("phase") else None),
            assistant_identity=self._assistant_identity,
        ))


def _is_visible_conversation_message(message: Message) -> bool:
    if message.direction == "incoming":
        return True
    if message.direction != "outgoing":
        return False
    payload = message.raw_payload or {}
    return payload.get("delivery_status") == "sent"

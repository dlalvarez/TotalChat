"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

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

    def __init__(self, session: Session, llm_provider: LLMProvider) -> None:
        self._session = session
        self._runtime = NaturalConversationRuntime(llm_provider)

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult:
        state = conversation.state or {}
        stored_messages = self._session.scalars(
            select(Message)
            .where(Message.conversation_session_id == conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(9)
        ).all()
        chronological = list(reversed(stored_messages))
        if chronological and chronological[-1].direction == "incoming":
            chronological = chronological[:-1]
        recent_messages = tuple(
            ConversationContextMessage(
                role="user" if item.direction == "incoming" else "assistant",
                content=item.content,
            )
            for item in chronological
        )
        return self._runtime.run(ConversationTurnRequest(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            message_text=message_text,
            recent_messages=recent_messages,
            conversation_phase=(str(state["phase"]) if state.get("phase") else None),
        ))

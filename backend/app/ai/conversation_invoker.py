"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
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


VISIBLE_HISTORY_LIMIT = 8
HISTORY_BATCH_SIZE = 24


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
        visible_messages = self._load_visible_history(conversation.id)
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

    def _load_visible_history(self, conversation_id: UUID) -> list[Message]:
        """Walk backward in bounded keyset pages until eight visible messages exist."""

        visible_descending: list[Message] = []
        cursor: tuple[datetime, UUID] | None = None
        current_incoming_removed = False
        while len(visible_descending) < VISIBLE_HISTORY_LIMIT:
            conditions = [Message.conversation_session_id == conversation_id]
            if cursor is not None:
                created_at, message_id = cursor
                conditions.append(or_(
                    Message.created_at < created_at,
                    and_(Message.created_at == created_at, Message.id < message_id),
                ))
            batch = list(self._session.scalars(
                select(Message)
                .where(*conditions)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(HISTORY_BATCH_SIZE)
            ).all())
            if not batch:
                break

            for message in batch:
                if not current_incoming_removed and message.direction == "incoming":
                    current_incoming_removed = True
                    continue
                if _is_visible_conversation_message(message):
                    visible_descending.append(message)
                    if len(visible_descending) == VISIBLE_HISTORY_LIMIT:
                        break

            oldest = batch[-1]
            cursor = (oldest.created_at, oldest.id)
            if len(batch) < HISTORY_BATCH_SIZE:
                break

        return list(reversed(visible_descending))


def _is_visible_conversation_message(message: Message) -> bool:
    if message.direction == "incoming":
        return True
    if message.direction != "outgoing":
        return False
    payload = message.raw_payload or {}
    return payload.get("delivery_status") == "sent"

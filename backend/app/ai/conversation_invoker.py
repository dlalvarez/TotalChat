"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Callable
import unicodedata
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
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.conversation_state import (
    InitialBookingContext,
    InitialConversationIntent,
    InitialConversationStage,
)
from app.ai.providers import LLMProvider
from app.ai.service_tools import ServiceRepository
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
        enable_service_tools: bool = False,
        service_repository: ServiceRepository | None = None,
    ) -> None:
        self._session = session
        self._llm_provider = llm_provider
        self._enable_service_tools = enable_service_tools
        self._assistant_identity = assistant_identity or ConversationAssistantIdentity()
        self._service_repository = service_repository

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult:
        registry = ConversationToolRegistry(
            tenant_id=tenant_id,
            repository=self._service_repository,
            session=None if self._service_repository is not None else self._session,
        )
        context = update_initial_booking_context(
            conversation.state or {}, message_text, resolve_service=registry.resolve_service
        )
        conversation.state = context.to_persistent_dict()
        visible_messages = _load_visible_history(self._session, conversation.id)
        recent_messages = tuple(
            ConversationContextMessage(
                role="user" if item.direction == "incoming" else "assistant",
                content=item.content,
            )
            for item in visible_messages
        )
        runtime_registry = registry if self._enable_service_tools else None
        return NaturalConversationRuntime(self._llm_provider, runtime_registry).run(
            ConversationTurnRequest(
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                message_text=message_text,
                recent_messages=recent_messages,
                conversation_phase=_safe_context_instruction(context),
                assistant_identity=self._assistant_identity,
            )
        )


def update_initial_booking_context(
    persisted_state: dict,
    message_text: str,
    *,
    resolve_service: Callable[[str], ResolvedConversationService | None] | None = None,
) -> InitialBookingContext:
    """Classify a turn using both the utterance and the persisted conversation."""

    try:
        current = InitialBookingContext.model_validate(persisted_state)
    except (ValueError, TypeError):
        current = InitialBookingContext()

    normalized = _normalize(message_text)
    if current.intent is InitialConversationIntent.BOOKING_REQUEST:
        intent = current.intent
    elif _contains_any(normalized, _BOOKING_MARKERS):
        intent = InitialConversationIntent.BOOKING_REQUEST
    elif _contains_any(normalized, _SERVICE_INFORMATION_MARKERS):
        intent = InitialConversationIntent.SERVICE_INFORMATION
    else:
        intent = InitialConversationIntent.CASUAL_CONVERSATION

    collected = dict(current.collected_context)
    resolution: str | None = None
    if intent is InitialConversationIntent.BOOKING_REQUEST:
        if current.stage is InitialConversationStage.COLLECT_SERVICE and normalized:
            match = resolve_service(message_text) if resolve_service is not None else None
            if match is None:
                collected = {}
                stage = InitialConversationStage.COLLECT_SERVICE
                missing: list[str] = ["service"]
                resolution = "not_found"
            else:
                collected = {
                    "service_id": str(match.service_id),
                    "service_name": match.name,
                }
                stage = InitialConversationStage.SERVICE_IDENTIFIED
                missing = []
                resolution = "identified"
        elif current.stage is InitialConversationStage.SERVICE_IDENTIFIED:
            stage = current.stage
            missing = []
        else:
            stage = InitialConversationStage.COLLECT_SERVICE
            missing = ["service"]
    else:
        stage = InitialConversationStage.START
        missing = []

    return InitialBookingContext(
        intent=intent,
        stage=stage,
        collected_context=collected,
        missing_information=missing,
        last_relevant_context={
            "user_message": message_text.strip()[:500],
            **({"service_resolution": resolution} if resolution is not None else {}),
        },
    )


def _safe_context_instruction(context: InitialBookingContext) -> str:
    parts: list[str] = []
    resolution = context.last_relevant_context.get("service_resolution")
    if resolution in {"identified", "not_found"}:
        # Keep the resolution first because the runtime deliberately bounds this
        # safe state instruction to 80 characters.
        parts.append(f"service_resolution={resolution}")
    parts.extend([
        f"intent={context.intent.value}",
        f"stage={context.stage.value}",
        f"missing_information={','.join(context.missing_information) or 'none'}",
    ])
    return "; ".join(parts)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character)).split()
    )


def _contains_any(value: str, markers: tuple[re.Pattern[str], ...]) -> bool:
    return any(marker.search(value) for marker in markers)


_BOOKING_MARKERS = tuple(re.compile(pattern) for pattern in (
    r"\b(cita|reserv(?:a|ar|acion)|agend(?:a|ar)|turno)\b",
    r"\bquiero\s+(?:una|un)\s+(?:cita|turno)\b",
))
_SERVICE_INFORMATION_MARKERS = tuple(re.compile(pattern) for pattern in (
    r"\bque\s+servicios?\b", r"\bservicios?\s+(?:tienen|ofrecen|disponibles)\b",
    r"\binformacion\s+(?:de|sobre)\s+(?:los\s+)?servicios?\b",
))


def _load_visible_history(session: Session, conversation_id: UUID) -> list[Message]:
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
        batch = list(session.scalars(
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

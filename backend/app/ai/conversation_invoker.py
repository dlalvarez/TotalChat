"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Callable
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.ai.conversation_prompts import (
    ConversationAssistantIdentity,
    resolve_conversation_assistant_identity,
)
from app.ai.conversation_runtime import (
    ConversationContextMessage,
    ConversationTurnRequest,
    ConversationTurnResult,
    NaturalConversationRuntime,
)
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.conversation_state import (
    InitialBookingContext,
    InitialConversationProgress,
    ConversationEntityDecision,
    InitialConversationIntent,
    InitialConversationStage,
    InitialConversationProposal,
    SelectedConversationService,
)
from app.ai.providers import LLMMessage, LLMProvider
from app.ai.service_tools import ServiceRepository
from app.models.tenant import ConversationSession, Message


VISIBLE_HISTORY_LIMIT = 8
HISTORY_BATCH_SIZE = 24
PROPOSAL_SYSTEM_PROMPT = """\
Interpreta únicamente el turno actual y devuelve JSON estricto con esta forma:
{"intent":"booking_request|service_information|casual_conversation",
 "candidate_service":{"name":"texto mencionado"}|null,
 "service_decision":"none|explore|select|confirm_candidate"}
booking_request significa que quiere seleccionar o cambiar un servicio para una cita.
service_information significa que pregunta si existe, qué ofrece o información sobre uno.
candidate_service conserva solo el nombre mencionado, sin inventar IDs ni confirmar existencia.
explore es una pregunta o mención informativa y nunca cambia una selección.
select requiere una decisión explícita de seleccionar o reemplazar por el candidato nombrado.
confirm_candidate requiere confirmación explícita del candidato previo aunque no repita su nombre.
none cubre conversación sin decisión. No infieras confirmación de expresiones ambiguas.
No devuelvas markdown, explicación, UUID, tenant, schema ni razonamiento.
"""


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
        proposal_interpreter: Callable[
            [InitialBookingContext, str], InitialConversationProposal
        ] | None = None,
    ) -> None:
        self._session = session
        self._llm_provider = llm_provider
        self._enable_service_tools = enable_service_tools
        self._assistant_identity = resolve_conversation_assistant_identity(
            assistant_identity
        )
        self._service_repository = service_repository
        self._proposal_interpreter = proposal_interpreter or self._interpret_proposal

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult:
        registry = ConversationToolRegistry(
            tenant_id=tenant_id,
            repository=self._service_repository,
            session=None if self._service_repository is not None else self._session,
        )
        current = _load_initial_context(conversation.state or {})
        proposal = self._proposal_interpreter(current, message_text)
        context = update_initial_booking_context(
            current,
            message_text,
            proposal=proposal,
            resolve_service=registry.resolve_service,
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

    def _interpret_proposal(
        self, context: InitialBookingContext, message_text: str
    ) -> InitialConversationProposal:
        safe_prior = (
            f"intent={context.intent.value}; stage={context.stage.value}; "
            f"selected_service={'yes' if context.selected_service else 'no'}; "
            f"candidate_service={context.candidate_service.name if context.candidate_service else 'none'}"
        )
        response = self._llm_provider.complete([
            LLMMessage(role="system", content=PROPOSAL_SYSTEM_PROMPT),
            LLMMessage(role="system", content=f"Contexto previo seguro: {safe_prior}"),
            LLMMessage(role="user", content=message_text[:2_000]),
        ])
        try:
            payload = json.loads(response.content)
            return InitialConversationProposal.model_validate(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            return InitialConversationProposal(
                intent=InitialConversationIntent.CASUAL_CONVERSATION
            )


def update_initial_booking_context(
    current: InitialBookingContext,
    message_text: str,
    *,
    proposal: InitialConversationProposal,
    resolve_service: Callable[[str], ResolvedConversationService | None] | None = None,
) -> InitialBookingContext:
    """Validate an LLM proposal and derive backend-confirmed operational state."""

    intent = proposal.intent

    selected_service = current.selected_service
    collected = dict(current.collected_context)
    if selected_service is None and current.stage is InitialConversationStage.SERVICE_IDENTIFIED:
        legacy_id = collected.get("service_id")
        legacy_name = collected.get("service_name")
        if isinstance(legacy_id, str) and isinstance(legacy_name, str):
            try:
                selected_service = SelectedConversationService(id=UUID(legacy_id), name=legacy_name)
                collected = {"service_name": legacy_name}
            except ValueError:
                selected_service = None
    candidate = proposal.candidate_service or current.candidate_service
    resolution: str | None = None
    if intent is InitialConversationIntent.BOOKING_REQUEST:
        if can_replace_confirmed_service(proposal) and candidate is not None:
            match = resolve_service(candidate.name) if resolve_service is not None else None
            if match is None:
                selected_service = None
                collected = {}
                stage = InitialConversationStage.COLLECT_SERVICE
                missing: list[str] = ["service"]
                resolution = "not_found"
            else:
                selected_service = SelectedConversationService(
                    id=match.service_id, name=match.name
                )
                collected = {"service_name": match.name}
                stage = InitialConversationStage.SERVICE_IDENTIFIED
                missing = []
                resolution = "identified"
        elif current.stage is InitialConversationStage.SERVICE_IDENTIFIED:
            if selected_service is None:
                collected = {}
                stage = InitialConversationStage.COLLECT_SERVICE
                missing = ["service"]
            else:
                stage = current.stage
                missing = []
        else:
            stage = InitialConversationStage.COLLECT_SERVICE
            missing = ["service"]
    elif intent is InitialConversationIntent.SERVICE_INFORMATION:
        stage = (
            InitialConversationStage.SERVICE_IDENTIFIED
            if selected_service is not None
            else InitialConversationStage.COLLECT_SERVICE
        )
        missing = []
        collected = (
            {"service_name": selected_service.name}
            if selected_service is not None else {}
        )
    else:
        stage = (
            InitialConversationStage.SERVICE_IDENTIFIED
            if selected_service is not None
            else InitialConversationStage.START
        )
        missing = []
        collected = (
            {"service_name": selected_service.name}
            if selected_service is not None else {}
        )

    return InitialBookingContext(
        intent=intent,
        stage=stage,
        candidate_service=candidate,
        selected_service=selected_service,
        collected_context=collected,
        missing_information=missing,
        conversation_progress=InitialConversationProgress(
            service_confirmed=selected_service is not None,
            next_expected_action=(
                "continue_booking"
                if selected_service is not None
                else ("collect_service" if stage is InitialConversationStage.COLLECT_SERVICE else None)
            ),
        ),
        last_relevant_context={
            "user_message": message_text.strip()[:500],
            **({"service_resolution": resolution} if resolution is not None else {}),
        },
    )


def can_replace_confirmed_service(proposal: InitialConversationProposal) -> bool:
    """Authorize confirmed-state mutation from structured decisions, never text."""

    return (
        proposal.intent is InitialConversationIntent.BOOKING_REQUEST
        and proposal.service_decision in {
            ConversationEntityDecision.SELECT,
            ConversationEntityDecision.CONFIRM_CANDIDATE,
        }
    )


def _load_initial_context(persisted_state: dict) -> InitialBookingContext:
    try:
        return InitialBookingContext.model_validate(persisted_state)
    except (ValueError, TypeError):
        migrated = dict(persisted_state)
        collected = migrated.get("collected_context")
        if isinstance(collected, dict) and migrated.get("selected_service") is None:
            service_id, service_name = collected.get("service_id"), collected.get("service_name")
            if isinstance(service_id, str) and isinstance(service_name, str):
                migrated["selected_service"] = {"id": service_id, "name": service_name}
                migrated["collected_context"] = {"service_name": service_name}
        selected = migrated.get("selected_service")
        stage = migrated.get("stage")
        migrated["conversation_progress"] = {
            "service_confirmed": selected is not None,
            "next_expected_action": (
                "continue_booking" if selected is not None
                else ("collect_service" if stage == "collect_service" else None)
            ),
        }
        try:
            return InitialBookingContext.model_validate(migrated)
        except (ValueError, TypeError):
            return InitialBookingContext()


def _safe_context_instruction(context: InitialBookingContext) -> str:
    parts: list[str] = []
    resolution = context.last_relevant_context.get("service_resolution")
    if resolution in {"identified", "not_found"}:
        # Keep the resolution first because the runtime deliberately bounds this
        # safe state instruction to 80 characters.
        parts.append(f"service_resolution={resolution}")
    if context.selected_service is not None:
        parts.append(f"service_name={context.selected_service.name}")
    elif context.candidate_service is not None:
        parts.append(f"candidate_service={context.candidate_service.name}")
    parts.extend([
        f"intent={context.intent.value}",
        f"stage={context.stage.value}",
        f"missing_information={','.join(context.missing_information) or 'none'}",
        f"next_expected_action={context.conversation_progress.next_expected_action or 'none'}",
    ])
    return "; ".join(parts)


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

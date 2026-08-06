"""Persistence-aware, channel-neutral bridge to the natural runtime."""

from __future__ import annotations

from datetime import date, datetime
import json
import logging
from typing import Callable
import unicodedata
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.ai.conversation_prompts import (
    ConversationAssistantIdentity,
    resolve_conversation_assistant_identity,
)
from app.ai.availability_language import (
    is_availability_request,
    is_booking_action,
    parse_availability_query,
)
from app.ai.conversation_runtime import (
    ConversationContextMessage,
    ConversationResponseGuard,
    ConversationTurnRequest,
    ConversationTurnResult,
    NaturalConversationRuntime,
    TECHNICAL_FALLBACK,
)
from app.ai.conversation_tools import ConversationToolRegistry, ResolvedConversationService
from app.ai.conversation_state import (
    InitialBookingContext,
    InitialConversationProgress,
    CandidateConversationService,
    ConversationEntityDecision,
    InitialConversationIntent,
    InitialConversationStage,
    InitialConversationProposal,
    SelectedConversationService,
    SuggestedConversationService,
    LastAvailabilityQuery,
)
from app.ai.providers import LLMMessage, LLMProvider
from app.ai.service_tools import ServiceRepository
from app.services.availability import SchedulingProvider
from app.tenancy.context import TenantContext
from app.models.tenant import ConversationSession, Message


logger = logging.getLogger(__name__)

VISIBLE_HISTORY_LIMIT = 8
HISTORY_BATCH_SIZE = 24
PROPOSAL_SYSTEM_PROMPT = """\
Interpreta únicamente el turno actual y devuelve JSON estricto con esta forma:
{"intent":"booking_request|service_information|casual_conversation",
 "candidate_service":{"name":"texto mencionado"}|null,
 "service_decision":"none|explore|select|confirm_candidate|confirm_pending_suggestion|reject_pending_suggestion"}
booking_request significa que quiere seleccionar o cambiar un servicio para una cita.
service_information significa que pregunta si existe, qué ofrece o información sobre uno.
candidate_service conserva solo el nombre mencionado, sin inventar IDs ni confirmar existencia.
explore es una pregunta o mención informativa y nunca cambia una selección.
select requiere una decisión explícita de seleccionar o reemplazar por el candidato nombrado.
confirm_candidate confirma un candidato previo solo cuando no existe una sugerencia backend pendiente.
confirm_pending_suggestion acepta semánticamente la suggested_service indicada en el contexto previo.
reject_pending_suggestion rechaza, cancela o se aparta de esa sugerencia pendiente.
Una pregunta sobre si algo ya cambió, quedó, se hizo o está listo nunca confirma.
Una expresión social o de cierre como "Perfecto", "Ok" o "Gracias" no confirma.
Si menciona otro servicio, usa select o explore; nunca confirmes la sugerencia anterior.
none cubre conversación sin decisión. Interpreta significado, no coincidencias literales.
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
        scheduling_provider: SchedulingProvider | None = None,
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self._session = session
        self._llm_provider = llm_provider
        self._enable_service_tools = enable_service_tools
        self._assistant_identity = resolve_conversation_assistant_identity(
            assistant_identity
        )
        self._service_repository = service_repository
        self._proposal_interpreter = proposal_interpreter or self._interpret_proposal
        self._scheduling_provider = scheduling_provider
        self._today_provider = today_provider

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult:
        current = _load_initial_context(conversation.state or {})
        selected = (
            ResolvedConversationService(
                service_id=current.selected_service.id,
                name=current.selected_service.name,
            )
            if current.selected_service is not None else None
        )
        registry = ConversationToolRegistry(
            tenant_id=tenant_id,
            repository=self._service_repository,
            session=None if self._service_repository is not None else self._session,
            tenant_context=TenantContext(tenant_id=tenant_id, slug="resolved", schema_name=""),
            selected_service=selected,
            scheduling_provider=self._scheduling_provider,
            availability_session=self._session,
        )
        if is_booking_action(message_text) and current.last_availability_query is not None:
            return self._run_grounded_response(
                tenant_id=tenant_id,
                conversation=conversation,
                message_text=message_text,
                context=current,
                registry=registry,
                payload={
                    "kind": "booking_request_blocked",
                    "reason": "booking_creation_out_of_scope",
                    "limits": {
                        "can_create_booking": False,
                        "can_hold_slot": False,
                        "can_take_payment": False,
                    },
                },
            )
        if is_availability_request(message_text):
            return self._availability_response(
                tenant_id, current, registry, conversation, message_text
            )
        proposal = self._proposal_interpreter(current, message_text)
        context = update_initial_booking_context(
            current,
            message_text,
            proposal=proposal,
            resolve_service=registry.resolve_service,
            suggest_service=registry.suggest_service,
        )
        pending_suggestion_follow_up = (
            current.suggested_service is not None
            and context.suggested_service is not None
        )
        pending_suggestion_change = (
            context.selected_service is not None
            and context.suggested_service is not None
            and context.selected_service.name != context.suggested_service.name
            and (
                pending_suggestion_follow_up
                or proposal.service_decision is ConversationEntityDecision.SELECT
            )
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
                response_guard=_response_guard(
                    context,
                    pending_suggestion_follow_up=pending_suggestion_follow_up,
                    pending_suggestion_change=pending_suggestion_change,
                ),
                assistant_identity=self._assistant_identity,
            )
        )

    def _availability_response(
        self,
        tenant_id: UUID,
        context: InitialBookingContext,
        registry: ConversationToolRegistry,
        conversation: ConversationSession,
        message_text: str,
    ) -> ConversationTurnResult:
        if context.suggested_service is not None:
            return self._run_grounded_response(
                tenant_id=tenant_id, conversation=conversation,
                message_text=message_text, context=context, registry=registry,
                payload={
                    "kind": "availability_lookup_blocked",
                    "reason": "suggested_service_pending",
                    "suggested_service_name": context.suggested_service.name,
                },
            )
        if context.selected_service is None or not context.conversation_progress.service_confirmed:
            return self._run_grounded_response(
                tenant_id=tenant_id, conversation=conversation,
                message_text=message_text, context=context, registry=registry,
                payload={
                    "kind": "availability_lookup_blocked",
                    "reason": "service_not_confirmed",
                },
            )
        query = parse_availability_query(message_text, today=self._today_provider())
        if query is None:
            return self._run_grounded_response(
                tenant_id=tenant_id, conversation=conversation,
                message_text=message_text, context=context, registry=registry,
                payload={
                    "kind": "availability_lookup_blocked",
                    "reason": "date_requires_clarification",
                    "service_name": context.selected_service.name,
                },
            )
        arguments = {
            "date_from": query.date_from.isoformat(),
            "date_to": query.date_to.isoformat(),
            "modality": query.modality,
            **({"time_from": query.time_from.strftime("%H:%M")} if query.time_from else {}),
            **({"time_to": query.time_to.strftime("%H:%M")} if query.time_to else {}),
        }
        try:
            result = registry.execute("get_available_slots", json.dumps(arguments))
        except Exception as exc:
            logger.warning("Availability lookup failed exception_type=%s", type(exc).__name__)
            return ConversationTurnResult(content=TECHNICAL_FALLBACK, code="availability_error")
        context.last_availability_query = LastAvailabilityQuery(
            service_name=context.selected_service.name,
            date_from=query.date_from.isoformat(), date_to=query.date_to.isoformat(),
            modality=query.modality,
        )
        conversation.state = context.to_persistent_dict()
        return self._run_grounded_response(
            tenant_id=tenant_id, conversation=conversation,
            message_text=message_text, context=context, registry=registry,
            payload=dict(result),
        )

    def _run_grounded_response(
        self,
        *,
        tenant_id: UUID,
        conversation: ConversationSession,
        message_text: str,
        context: InitialBookingContext,
        registry: ConversationToolRegistry,
        payload: dict[str, object],
    ) -> ConversationTurnResult:
        visible_messages = _load_visible_history(self._session, conversation.id)
        recent_messages = tuple(
            ConversationContextMessage(
                role="user" if item.direction == "incoming" else "assistant",
                content=item.content,
            )
            for item in visible_messages
        )
        return NaturalConversationRuntime(self._llm_provider, registry).run(
            ConversationTurnRequest(
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                message_text=message_text,
                recent_messages=recent_messages,
                conversation_phase=_safe_context_instruction(context),
                grounded_context=payload,
                assistant_identity=self._assistant_identity,
            )
        )

    def _interpret_proposal(
        self, context: InitialBookingContext, message_text: str
    ) -> InitialConversationProposal:
        safe_prior = (
            f"intent={context.intent.value}; stage={context.stage.value}; "
            f"selected_service={'yes' if context.selected_service else 'no'}; "
            f"candidate_service={context.candidate_service.name if context.candidate_service else 'none'}; "
            f"suggested_service={context.suggested_service.name if context.suggested_service else 'none'}"
        )
        try:
            response = self._llm_provider.complete([
                LLMMessage(role="system", content=PROPOSAL_SYSTEM_PROMPT),
                LLMMessage(role="system", content=f"Contexto previo seguro: {safe_prior}"),
                LLMMessage(role="user", content=message_text[:2_000]),
            ])
        except Exception as exc:
            # Provider exception values may contain request or credential material.
            # Keep the turn recoverable and log only a stable technical category.
            logger.warning(
                "Conversation proposal provider invocation failed exception_type=%s",
                type(exc).__name__,
            )
            return InitialConversationProposal(
                intent=InitialConversationIntent.CASUAL_CONVERSATION
            )
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
    suggest_service: Callable[[str], ResolvedConversationService | None] | None = None,
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
    suggested_service = current.suggested_service
    if (
        proposal.candidate_service is not None
        and current.candidate_service is not None
        and proposal.candidate_service.name != current.candidate_service.name
    ):
        suggested_service = None
    resolution: str | None = None
    if intent is InitialConversationIntent.BOOKING_REQUEST:
        if (
            proposal.service_decision
            is ConversationEntityDecision.REJECT_PENDING_SUGGESTION
            and current.suggested_service is not None
        ):
            suggested_service = None
            resolution = "rejected"
            if selected_service is not None:
                stage = InitialConversationStage.SERVICE_IDENTIFIED
                collected = {"service_name": selected_service.name}
                missing = []
            else:
                stage = InitialConversationStage.COLLECT_SERVICE
                collected = {}
                missing = ["service"]
        elif (
            proposal.service_decision
            is ConversationEntityDecision.CONFIRM_PENDING_SUGGESTION
            and current.suggested_service is not None
        ):
            if _can_confirm_pending_suggestion(current, proposal, message_text):
                match = (
                    resolve_service(current.suggested_service.name)
                    if resolve_service is not None else None
                )
            else:
                match = None
            if match is not None:
                selected_service = SelectedConversationService(
                    id=match.service_id,
                    name=match.name,
                )
                candidate = CandidateConversationService(name=match.name)
                suggested_service = None
                collected = {"service_name": match.name}
                stage = InitialConversationStage.SERVICE_IDENTIFIED
                missing = []
                resolution = "identified"
            else:
                suggested_service = current.suggested_service
                resolution = "suggested"
                if selected_service is not None:
                    stage = InitialConversationStage.SERVICE_IDENTIFIED
                    collected = {"service_name": selected_service.name}
                    missing = []
                else:
                    stage = InitialConversationStage.COLLECT_SERVICE
                    collected = {}
                    missing = ["service"]
        elif (
            can_replace_confirmed_service(proposal)
            and candidate is not None
            and suggested_service is None
        ):
            lookup_name = candidate.name
            match = resolve_service(lookup_name) if resolve_service is not None else None
            if match is None:
                suggestion = (
                    suggest_service(candidate.name)
                    if suggest_service is not None else None
                )
                if suggestion is None:
                    selected_service = None
                    collected = {}
                    stage = InitialConversationStage.COLLECT_SERVICE
                    missing: list[str] = ["service"]
                    suggested_service = None
                    resolution = "not_found"
                else:
                    suggested_service = SuggestedConversationService(
                        name=suggestion.name
                    )
                    stage = (
                        InitialConversationStage.SERVICE_IDENTIFIED
                        if selected_service is not None
                        else InitialConversationStage.COLLECT_SERVICE
                    )
                    collected = (
                        {"service_name": selected_service.name}
                        if selected_service is not None else {}
                    )
                    missing = [] if selected_service is not None else ["service"]
                    resolution = "suggested"
            else:
                selected_service = SelectedConversationService(
                    id=match.service_id, name=match.name
                )
                suggested_service = None
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
                if suggested_service is not None:
                    resolution = "suggested"
        elif current.suggested_service is not None:
            stage = InitialConversationStage.COLLECT_SERVICE
            missing = ["service"]
            resolution = "suggested"
        else:
            stage = InitialConversationStage.COLLECT_SERVICE
            missing = ["service"]
    elif intent is InitialConversationIntent.SERVICE_INFORMATION:
        if proposal.candidate_service is not None:
            suggestion = (
                suggest_service(proposal.candidate_service.name)
                if suggest_service is not None else None
            )
            if suggestion is None:
                suggested_service = None
                resolution = "not_found"
            else:
                suggested_service = SuggestedConversationService(name=suggestion.name)
                resolution = "suggested"
        elif suggested_service is not None:
            resolution = "suggested"
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
        if selected_service is not None:
            stage = InitialConversationStage.SERVICE_IDENTIFIED
            missing = []
            if suggested_service is not None:
                resolution = "suggested"
        elif suggested_service is not None:
            stage = InitialConversationStage.COLLECT_SERVICE
            missing = ["service"]
            resolution = "suggested"
        else:
            stage = InitialConversationStage.START
            missing = []
        collected = (
            {"service_name": selected_service.name}
            if selected_service is not None else {}
        )

    return InitialBookingContext(
        intent=intent,
        stage=stage,
        candidate_service=candidate,
        suggested_service=suggested_service,
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
    """Authorize named candidate mutation outside pending-suggestion semantics."""

    if proposal.intent is not InitialConversationIntent.BOOKING_REQUEST:
        return False
    if proposal.service_decision is ConversationEntityDecision.SELECT:
        return proposal.candidate_service is not None
    if proposal.service_decision is ConversationEntityDecision.CONFIRM_CANDIDATE:
        return True
    return False


def _can_confirm_pending_suggestion(
    current: InitialBookingContext,
    proposal: InitialConversationProposal,
    message_text: str,
) -> bool:
    """Validate semantic confirmation against current backend-owned state."""

    if current.suggested_service is None:
        return False
    if "?" in message_text or "¿" in message_text:
        return False
    if proposal.intent is not InitialConversationIntent.BOOKING_REQUEST:
        return False
    proposed_candidate = proposal.candidate_service
    if proposed_candidate is None:
        return True
    allowed_names = {_normalize_entity_name(current.suggested_service.name)}
    if current.candidate_service is not None:
        allowed_names.add(_normalize_entity_name(current.candidate_service.name))
    return _normalize_entity_name(proposed_candidate.name) in allowed_names


def _normalize_entity_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        ).split()
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
    resolution = _safe_service_resolution(context)
    parts = [
        f"service_confirmed={'true' if context.selected_service is not None else 'false'}",
        f"service_resolution={resolution}",
    ]
    if context.selected_service is not None:
        parts.append(f"service_name={_safe_context_value(context.selected_service.name)}")
    if context.candidate_service is not None:
        parts.append(
            f"candidate_service={_safe_context_value(context.candidate_service.name)}"
        )
    if context.suggested_service is not None:
        parts.append(
            "suggested_service_name="
            f"{_safe_context_value(context.suggested_service.name)}"
        )
    parts.extend([
        f"intent={context.intent.value}",
        f"stage={context.stage.value}",
        f"missing_information={','.join(context.missing_information) or 'none'}",
        f"next_expected_action={context.conversation_progress.next_expected_action or 'none'}",
    ])
    return "; ".join(parts)


def _safe_service_resolution(context: InitialBookingContext) -> str:
    resolution = context.last_relevant_context.get("service_resolution")
    if resolution in {"not_found", "suggested", "rejected"}:
        return resolution
    if context.selected_service is not None:
        return "identified"
    return "unresolved"


def _response_guard(
    context: InitialBookingContext,
    *,
    pending_suggestion_follow_up: bool = False,
    pending_suggestion_change: bool = False,
) -> ConversationResponseGuard:
    return ConversationResponseGuard(
        service_confirmed=context.selected_service is not None,
        service_resolution=_safe_service_resolution(context),
        service_name=(
            _safe_context_value(context.selected_service.name)
            if context.selected_service is not None else None
        ),
        candidate_service=(
            _safe_context_value(context.candidate_service.name)
            if context.candidate_service is not None else None
        ),
        suggested_service_name=(
            _safe_context_value(context.suggested_service.name)
            if context.suggested_service is not None else None
        ),
        intent=context.intent.value,
        pending_suggestion_follow_up=pending_suggestion_follow_up,
        pending_suggestion_change=pending_suggestion_change,
    )


def _safe_context_value(value: str) -> str:
    """Keep validated display text from becoming a second system instruction."""

    translation = str.maketrans({";": " ", "\n": " ", "\r": " ", "\t": " "})
    return " ".join(value.translate(translation).split())[:200]


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

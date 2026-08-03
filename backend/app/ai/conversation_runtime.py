"""Channel-agnostic natural conversation runtime for phase 8A.7."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from app.ai.conversation_prompts import (
    NATURAL_CONVERSATION_SYSTEM_PROMPT_VERSION,
    ConversationAssistantIdentity,
    build_natural_conversation_system_prompt,
    resolve_conversation_assistant_identity,
)
from app.ai.conversation_tools import ConversationToolRegistry
from app.ai.providers import LLMMessage, LLMProvider


logger = logging.getLogger(__name__)

TECHNICAL_FALLBACK = (
    "No pude procesar tu mensaje en este momento. Por favor, intenta nuevamente."
)
MAX_CONTEXT_MESSAGES = 8
MAX_MESSAGE_CHARS = 2_000
MAX_SAFE_STATE_CHARS = 500


@dataclass(frozen=True, slots=True)
class ConversationResponseGuard:
    """Backend facts used only to reject visibly unsupported responses."""

    service_confirmed: bool = False
    service_resolution: str = "unresolved"
    service_name: str | None = None
    candidate_service: str | None = None
    suggested_service_name: str | None = None
    intent: str = "casual_conversation"
    pending_suggestion_follow_up: bool = False
    pending_suggestion_change: bool = False


@dataclass(frozen=True, slots=True)
class ConversationContextMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ConversationTurnRequest:
    """Safe input assembled after tenant and conversation resolution."""

    tenant_id: UUID
    conversation_id: UUID
    message_text: str
    recent_messages: tuple[ConversationContextMessage, ...] = ()
    conversation_phase: str | None = None
    response_guard: ConversationResponseGuard | None = None
    assistant_identity: ConversationAssistantIdentity = field(
        default_factory=resolve_conversation_assistant_identity
    )


@dataclass(frozen=True, slots=True)
class ConversationTurnResult:
    content: str
    code: str
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({
            "runtime": "natural_conversation",
            "system_prompt_version": NATURAL_CONVERSATION_SYSTEM_PROMPT_VERSION,
        })
    )


class NaturalConversationRuntime:
    """Prepare bounded safe context and return only provider-authored normal text."""

    def __init__(
        self, llm_provider: LLMProvider, tool_registry: ConversationToolRegistry | None = None
    ) -> None:
        self._llm_provider = llm_provider
        self._tool_registry = tool_registry

    def run(self, request: ConversationTurnRequest) -> ConversationTurnResult:
        if request.response_guard is not None:
            deterministic = _critical_booking_response(
                request.response_guard,
                allow_grounded_information=(
                    request.response_guard.intent == "service_information"
                    and self._tool_registry is not None
                ),
            )
            if deterministic is not None:
                return ConversationTurnResult(
                    content=deterministic,
                    code="guarded_booking_response",
                )
        messages = self._build_messages(request)
        service_lookup_performed = False
        grounded_by_service_tool = False
        try:
            if self._tool_registry is None:
                response = self._llm_provider.complete(messages)
            else:
                response = self._llm_provider.complete(
                    messages, tools=self._tool_registry.definitions
                )
                if response.tool_calls:
                    # 8A.8 authorizes exactly one read-only service lookup per turn.
                    if len(response.tool_calls) != 1:
                        raise ValueError("unsupported tool call count")
                    tool_call = response.tool_calls[0]
                    tool_result = self._tool_registry.execute(
                        tool_call.name, tool_call.arguments
                    )
                    service_lookup_performed = True
                    grounded_by_service_tool = bool(tool_result.get("services"))
                    messages.extend((
                        LLMMessage(role="assistant", content=None, tool_calls=(tool_call,)),
                        LLMMessage(
                            role="tool",
                            content=json.dumps(dict(tool_result), ensure_ascii=False),
                            tool_call_id=tool_call.id,
                        ),
                    ))
                    response = self._llm_provider.complete(messages)
            content = response.content
            if not isinstance(content, str) or not content.strip():
                raise ValueError("unusable provider content")
            if request.response_guard is not None:
                deterministic = _critical_booking_response(
                    request.response_guard,
                    allow_grounded_information=grounded_by_service_tool,
                )
                if deterministic is not None:
                    content = deterministic
                elif _violates_response_guard(
                    content,
                    request.response_guard,
                    service_lookup_performed=service_lookup_performed,
                    grounded_by_service_tool=grounded_by_service_tool,
                ):
                    content = _guarded_booking_response(
                        request.response_guard,
                        service_lookup_performed=service_lookup_performed,
                        grounded_by_service_tool=grounded_by_service_tool,
                    )
        except Exception as exc:
            # Do not log exception values: provider errors can contain request or
            # credential material. The visible response is deliberately generic.
            logger.warning(
                "Natural conversation provider invocation failed exception_type=%s",
                type(exc).__name__,
            )
            return ConversationTurnResult(content=TECHNICAL_FALLBACK, code="provider_error")

        code = (
            "grounded_service_response"
            if len(messages) > 1 and messages[-1].role == "tool"
            else "natural_response"
        )
        return ConversationTurnResult(content=content, code=code)

    def _build_messages(self, request: ConversationTurnRequest) -> list[LLMMessage]:
        messages = [LLMMessage(
            role="system",
            content=build_natural_conversation_system_prompt(
                request.assistant_identity,
                services_tool_enabled=self._tool_registry is not None,
            ),
        )]
        if request.conversation_phase:
            messages.append(LLMMessage(
                role="system",
                content=(
                    "Estado conversacional permitido: "
                    f"{request.conversation_phase[:MAX_SAFE_STATE_CHARS]}"
                ),
            ))
        for item in request.recent_messages[-MAX_CONTEXT_MESSAGES:]:
            if item.role in {"user", "assistant"} and item.content.strip():
                messages.append(LLMMessage(
                    role=item.role,
                    content=item.content[:MAX_MESSAGE_CHARS],
                ))
        messages.append(LLMMessage(role="user", content=request.message_text[:MAX_MESSAGE_CHARS]))
        return messages


_OUT_OF_SCOPE_REQUEST_PATTERN = re.compile(
    r"(?:\b(?:dime|indica(?:me)?|necesito|confirma(?:me)?)\b[^.!?]{0,45}"
    r"\b(?:fecha|hora|d[ií]a|horario|disponibilidad|datos personales|documento|tel[eé]fono)\b|"
    r"\b(?:qu[eé]|cu[aá]l)\s+(?:fecha|hora|d[ií]a|horario)\b|"
    r"\b(?:prefieres|te gustar[ií]a|quisieras)\b[^.!?]{0,45}"
    r"\b(?:fecha|hora|d[ií]a|horario)\b)",
    re.IGNORECASE,
)
_OUT_OF_SCOPE_PROMISE_PATTERN = re.compile(
    r"\b(?:voy a (?:revisar|consultar|buscar) (?:la )?disponibilidad|"
    r"separar[eé]|reservar[eé]|agendar[eé]|"
    r"(?:puedo|podemos) (?:separar|reservar|agendar|gestionar|crear)|"
    r"tu cita qued[oó] (?:reservada|agendada|confirmada))\b",
    re.IGNORECASE,
)
_UNSUPPORTED_SERVICE_CONFIRMATION_PATTERN = re.compile(
    r"\b(?:coincid\w*|configurad[oa]s?|confirmad[oa]s?|identificad[oa]s?|"
    r"existe(?:n)?|tenemos)\b",
    re.IGNORECASE,
)
_CONFIRMED_SELECTION_LANGUAGE_PATTERN = re.compile(
    r"\b(?:seleccionad[oa]|registrad[oa]|actualizad[oa]|cambiad[oa]|"
    r"confirmad[oa]|identificad[oa]|tom[eé] nota)\b",
    re.IGNORECASE,
)
_UNSUPPORTED_NOT_FOUND_CONTINUATION_PATTERN = re.compile(
    r"\b(?:siguiente paso|continuar con|ayudarte con)\b",
    re.IGNORECASE,
)
_UNSUPPORTED_SUGGESTION_PROMOTION_PATTERN = re.compile(
    r"\b(?:ya (?:la |lo )?cambi(?:e|é)|ya qued[oó]|qued[oó] cambiad[oa]|"
    r"(?:la|lo) cambi(?:e|é))\b",
    re.IGNORECASE,
)


def _violates_response_guard(
    content: str,
    guard: ConversationResponseGuard,
    *,
    service_lookup_performed: bool,
    grounded_by_service_tool: bool,
) -> bool:
    """Apply a closed safety check; this does not interpret the user message."""

    if _OUT_OF_SCOPE_REQUEST_PATTERN.search(content):
        return True
    if _OUT_OF_SCOPE_PROMISE_PATTERN.search(content):
        return True
    if (
        not guard.service_confirmed
        and _CONFIRMED_SELECTION_LANGUAGE_PATTERN.search(content)
    ):
        return True
    if (
        guard.intent == "service_information"
        and guard.candidate_service is not None
        and service_lookup_performed
        and not grounded_by_service_tool
    ):
        return True
    if (
        guard.service_resolution == "not_found"
        and _UNSUPPORTED_NOT_FOUND_CONTINUATION_PATTERN.search(content)
    ):
        return True
    if (
        guard.service_resolution == "suggested"
        and _UNSUPPORTED_SUGGESTION_PROMOTION_PATTERN.search(content)
    ):
        return True
    candidate_is_unconfirmed = (
        guard.candidate_service is not None
        and (
            guard.service_name is None
            or guard.candidate_service.casefold() != guard.service_name.casefold()
        )
    )
    confirmation_is_unsupported = (
        not guard.service_confirmed
        or guard.service_resolution != "identified"
        or candidate_is_unconfirmed
    )
    return bool(
        confirmation_is_unsupported
        and not grounded_by_service_tool
        and _UNSUPPORTED_SERVICE_CONFIRMATION_PATTERN.search(content)
    )


def _guarded_booking_response(
    guard: ConversationResponseGuard,
    *,
    service_lookup_performed: bool,
    grounded_by_service_tool: bool,
) -> str:
    """Return deterministic, bounded language when provider output violates 8A.9."""

    if guard.service_resolution == "suggested" and guard.suggested_service_name:
        if guard.pending_suggestion_change:
            return (
                "Aún no he cambiado el servicio. Encontré "
                f"{guard.suggested_service_name} como opción relacionada. "
                "¿Confirmas que quieres cambiar a ese servicio?"
            )
        if guard.pending_suggestion_follow_up:
            return (
                "Aún no he cambiado el servicio. Encontré "
                f"{guard.suggested_service_name} como opción relacionada. "
                "¿Confirmas que quieres usar ese servicio?"
            )
        return (
            f"Encontré un servicio relacionado: {guard.suggested_service_name}. "
            "¿Confirmas que te refieres a ese servicio?"
        )
    if guard.service_resolution == "not_found" and guard.candidate_service:
        return (
            f"No encontré un servicio configurado para {guard.candidate_service}. "
            "¿Quieres revisar otro servicio disponible?"
        )
    if guard.service_resolution == "rejected":
        return "Entendido. ¿Qué otro servicio necesitas?"
    if guard.intent == "service_information" and guard.candidate_service:
        if service_lookup_performed and not grounded_by_service_tool:
            return (
                f"No encontré un servicio configurado para {guard.candidate_service}. "
                "¿Quieres revisar otro servicio disponible?"
            )
        return (
            f"No pude confirmar {guard.candidate_service} con información del backend. "
            "Puedo ayudarte a revisar los servicios disponibles."
        )
    if guard.service_confirmed and guard.service_name:
        return (
            f"Tengo identificado el servicio {guard.service_name}. En esta etapa todavía "
            "no puedo consultar disponibilidad ni crear la cita desde aquí."
        )
    if guard.service_resolution == "not_found":
        return (
            "No encontré una coincidencia clara para ese servicio. "
            "¿Quieres revisar otro servicio disponible?"
        )
    return (
        "Ese servicio aún no está confirmado. Puedo ayudarte a aclarar cuál necesitas "
        "o a revisar las opciones disponibles."
    )


def _critical_booking_response(
    guard: ConversationResponseGuard,
    *,
    allow_grounded_information: bool,
) -> str | None:
    """Own visible output for critical 8A.9 states before provider generation."""

    if guard.intent == "service_information" and allow_grounded_information:
        return None
    if (
        guard.service_resolution == "suggested"
        and guard.suggested_service_name
    ):
        if guard.pending_suggestion_change:
            return (
                "Aún no he cambiado el servicio. Encontré "
                f"{guard.suggested_service_name} como opción relacionada. "
                "¿Confirmas que quieres cambiar a ese servicio?"
            )
        if guard.service_confirmed:
            return None
        if guard.pending_suggestion_follow_up:
            return (
                "Aún no he cambiado el servicio. Encontré "
                f"{guard.suggested_service_name} como opción relacionada. "
                "¿Confirmas que quieres usar ese servicio?"
            )
        return (
            f"Encontré un servicio relacionado: {guard.suggested_service_name}. "
            "¿Confirmas que te refieres a ese servicio?"
        )
    if guard.service_resolution == "not_found" and guard.candidate_service:
        return (
            f"No encontré un servicio configurado para {guard.candidate_service}. "
            "¿Quieres revisar otro servicio disponible?"
        )
    if guard.service_resolution == "rejected":
        return "Entendido. ¿Qué otro servicio necesitas?"
    if (
        guard.service_confirmed
        and guard.service_name
        and guard.intent == "booking_request"
    ):
        return (
            f"Tengo identificado el servicio {guard.service_name}. En esta etapa todavía "
            "no puedo consultar disponibilidad ni crear la cita desde aquí."
        )
    return None

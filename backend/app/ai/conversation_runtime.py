"""Channel-agnostic natural conversation runtime for phase 8A.7."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from app.ai.conversation_prompts import (
    NATURAL_CONVERSATION_SYSTEM_PROMPT_VERSION,
    ConversationAssistantIdentity,
    build_natural_conversation_system_prompt,
)
from app.ai.providers import LLMMessage, LLMProvider


logger = logging.getLogger(__name__)

TECHNICAL_FALLBACK = (
    "No pude procesar tu mensaje en este momento. Por favor, intenta nuevamente."
)
MAX_CONTEXT_MESSAGES = 8
MAX_MESSAGE_CHARS = 2_000


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
    assistant_identity: ConversationAssistantIdentity = field(
        default_factory=ConversationAssistantIdentity
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

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider

    def run(self, request: ConversationTurnRequest) -> ConversationTurnResult:
        messages = self._build_messages(request)
        try:
            response = self._llm_provider.complete(messages)
            content = response.content
            if not isinstance(content, str) or not content.strip():
                raise ValueError("unusable provider content")
        except Exception:
            # Do not log exception values: provider errors can contain request or
            # credential material. The visible response is deliberately generic.
            logger.warning("Natural conversation provider invocation failed")
            return ConversationTurnResult(content=TECHNICAL_FALLBACK, code="provider_error")

        return ConversationTurnResult(content=content, code="natural_response")

    def _build_messages(self, request: ConversationTurnRequest) -> list[LLMMessage]:
        messages = [LLMMessage(
            role="system",
            content=build_natural_conversation_system_prompt(request.assistant_identity),
        )]
        if request.conversation_phase:
            messages.append(LLMMessage(
                role="system",
                content=f"Estado conversacional permitido: {request.conversation_phase[:80]}",
            ))
        for item in request.recent_messages[-MAX_CONTEXT_MESSAGES:]:
            if item.role in {"user", "assistant"} and item.content.strip():
                messages.append(LLMMessage(
                    role=item.role,
                    content=item.content[:MAX_MESSAGE_CHARS],
                ))
        messages.append(LLMMessage(role="user", content=request.message_text[:MAX_MESSAGE_CHARS]))
        return messages

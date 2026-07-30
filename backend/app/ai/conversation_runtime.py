"""Channel-agnostic natural conversation runtime for phase 8A.7."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
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
        messages = self._build_messages(request)
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
        except Exception:
            # Do not log exception values: provider errors can contain request or
            # credential material. The visible response is deliberately generic.
            logger.warning("Natural conversation provider invocation failed")
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

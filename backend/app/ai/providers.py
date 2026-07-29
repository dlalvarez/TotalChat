from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str | None
    tool_call_id: str | None = None
    tool_calls: tuple["LLMToolCall", ...] = ()


@dataclass(frozen=True)
class LLMToolDefinition:
    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True)
class LLMToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: tuple[LLMToolCall, ...] = ()


@dataclass(frozen=True)
class EmbeddingRequest:
    input: str


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]
    model: str
    provider: str = "unknown"


class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: tuple[LLMToolDefinition, ...] = (),
    ) -> LLMResponse:
        """Return an LLM completion for an already tenant-scoped operation."""


class EmbeddingsProvider(Protocol):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Return one embedding for an already tenant-scoped document or query."""


def create_llm_provider() -> LLMProvider:
    """Select the active adapter exclusively from generic configuration."""
    from app.ai.openai_compatible_provider import OpenAICompatibleProvider
    from app.core.config import get_settings

    settings = get_settings()
    return OpenAICompatibleProvider(
        provider_name=settings.llm_provider,
        base_url=settings.llm_base_url,
        api_key=settings.effective_llm_api_key,
        model=settings.llm_model,
        embeddings_model=settings.embeddings_model,
        timeout_seconds=settings.llm_timeout_seconds,
        capture_reasoning=settings.llm_capture_reasoning,
        reasoning_effort=settings.llm_reasoning_effort,
        max_retries=settings.llm_max_retries,
        max_completion_tokens=settings.llm_max_completion_tokens,
    )


def create_embeddings_provider() -> EmbeddingsProvider:
    """Build the embeddings adapter, defaulting its connection to LLM settings."""
    from app.ai.openai_compatible_provider import OpenAICompatibleProvider
    from app.core.config import get_settings

    settings = get_settings()
    return OpenAICompatibleProvider(
        provider_name=settings.effective_embeddings_provider,
        base_url=settings.effective_embeddings_base_url,
        api_key=settings.effective_embeddings_api_key,
        model=settings.llm_model,
        embeddings_model=settings.embeddings_model,
        timeout_seconds=settings.llm_timeout_seconds,
        capture_reasoning=settings.llm_capture_reasoning,
    )

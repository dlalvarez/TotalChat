"""Tenant-scoped AI provider abstractions for TotalChat."""

from app.ai.openai_provider import OpenAIProvider
from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.providers import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingsProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    create_embeddings_provider,
    create_llm_provider,
)
from app.ai.semantic_documents import SemanticDocument

__all__ = [
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingsProvider",
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "OpenAIProvider",
    "OpenAICompatibleProvider",
    "SemanticDocument",
    "create_embeddings_provider",
    "create_llm_provider",
]

"""Tenant-scoped AI provider abstractions for TotalChat."""

from app.ai.conversation_state import (
    BookingConversationState,
    BookingModality,
    ChannelType,
    ConversationIntent,
    ConversationPaymentStatus,
    ConversationStage,
    PendingField,
    SelectedSlot,
)
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
    "BookingConversationState",
    "BookingModality",
    "ChannelType",
    "ConversationIntent",
    "ConversationPaymentStatus",
    "ConversationStage",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingsProvider",
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "OpenAICompatibleProvider",
    "PendingField",
    "SemanticDocument",
    "SelectedSlot",
    "create_embeddings_provider",
    "create_llm_provider",
]

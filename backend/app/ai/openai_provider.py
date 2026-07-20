from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.core.config import get_settings


class OpenAIProvider(OpenAICompatibleProvider):
    """Backward-compatible OpenAI adapter over the generic provider."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        llm_model: str | None = None,
        embeddings_model: str | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            provider_name="openai",
            base_url=settings.llm_base_url,
            api_key=api_key if api_key is not None else settings.effective_llm_api_key,
            model=llm_model or settings.llm_model,
            embeddings_model=embeddings_model or settings.embeddings_model,
            timeout_seconds=settings.llm_timeout_seconds,
            capture_reasoning=settings.llm_capture_reasoning,
            client_factory=client_factory,
        )

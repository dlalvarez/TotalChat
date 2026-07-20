from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.ai.providers import EmbeddingRequest, EmbeddingResponse, LLMMessage, LLMResponse
from app.core.config import get_settings


class OpenAIProvider:
    """Initial OpenAI-backed LLM and embeddings provider.

    The OpenAI SDK is imported only when a network-backed operation is used so
    importing this module remains safe in tests and environments without keys.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        llm_model: str | None = None,
        embeddings_model: str | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.llm_model = llm_model or settings.llm_model
        self.embeddings_model = embeddings_model or settings.embeddings_model
        self._client_factory = client_factory
        self._client: Any | None = None

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
        )
        content = response.choices[0].message.content or ""
        return LLMResponse(content=content, model=self.llm_model)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        client = self._get_client()
        response = client.embeddings.create(model=self.embeddings_model, input=request.input)
        return EmbeddingResponse(embedding=list(response.data[0].embedding), model=self.embeddings_model)

    def _get_client(self) -> Any:
        if not self.api_key:
            raise RuntimeError("TOTALCHAT_OPENAI_API_KEY must be set before using OpenAIProvider")
        if self._client is None:
            factory = self._client_factory or self._load_openai_client_factory()
            self._client = factory(api_key=self.api_key)
        return self._client

    @staticmethod
    def _load_openai_client_factory() -> Callable[..., Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai package must be installed before using OpenAIProvider") from exc
        return OpenAI

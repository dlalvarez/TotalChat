from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.ai.providers import EmbeddingRequest, EmbeddingResponse, LLMMessage, LLMResponse


class OpenAICompatibleProvider:
    """Generic adapter for providers exposing the OpenAI client contract."""

    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key: str | None,
        model: str,
        embeddings_model: str,
        timeout_seconds: float = 30,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.embeddings_model = embeddings_model
        self.timeout_seconds = timeout_seconds
        self._client_factory = client_factory
        self._client: Any | None = None

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
        )
        # reasoning_content is intentionally neither read nor returned.
        content = response.choices[0].message.content or ""
        return LLMResponse(content=content, model=self.model, provider=self.provider_name)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        response = self._get_client().embeddings.create(model=self.embeddings_model, input=request.input)
        return EmbeddingResponse(
            embedding=list(response.data[0].embedding),
            model=self.embeddings_model,
            provider=self.provider_name,
        )

    def _get_client(self) -> Any:
        if not self.api_key:
            raise RuntimeError(
                f"TOTALCHAT_LLM_API_KEY must be set before using provider '{self.provider_name}'"
            )
        if self._client is None:
            factory = self._client_factory or self._load_client_factory()
            self._client = factory(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            )
        return self._client

    @staticmethod
    def _load_client_factory() -> Callable[..., Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai package must be installed before using an AI provider") from exc
        return OpenAI

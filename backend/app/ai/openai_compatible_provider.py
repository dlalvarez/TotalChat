from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.ai.providers import (
    EmbeddingRequest, EmbeddingResponse, LLMMessage, LLMResponse,
    LLMToolCall, LLMToolDefinition,
)


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
        capture_reasoning: bool = False,
        reasoning_effort: str | None = None,
        max_retries: int = 0,
        max_completion_tokens: int = 256,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.embeddings_model = embeddings_model
        self.timeout_seconds = timeout_seconds
        self.capture_reasoning = capture_reasoning
        self.reasoning_effort = reasoning_effort
        self.max_retries = max_retries
        self.max_completion_tokens = max_completion_tokens
        self._client_factory = client_factory
        self._client: Any | None = None

    def complete(
        self, messages: list[LLMMessage], *, tools: tuple[LLMToolDefinition, ...] = ()
    ) -> LLMResponse:
        serialized_messages = []
        for message in messages:
            item: dict[str, Any] = {"role": message.role, "content": message.content}
            if message.tool_call_id:
                item["tool_call_id"] = message.tool_call_id
            if message.tool_calls:
                item["tool_calls"] = [
                    {"id": call.id, "type": "function", "function": {
                        "name": call.name, "arguments": call.arguments,
                    }} for call in message.tool_calls
                ]
            serialized_messages.append(item)
        completion_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": serialized_messages,
            "max_completion_tokens": self.max_completion_tokens,
        }
        if tools:
            completion_kwargs["tools"] = [
                {"type": "function", "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": dict(tool.parameters),
                }} for tool in tools
            ]
            completion_kwargs["tool_choice"] = "auto"
        if self.reasoning_effort is not None:
            completion_kwargs["extra_body"] = {"reasoning_effort": self.reasoning_effort}
        response = self._get_client().chat.completions.create(**completion_kwargs)
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = tuple(
            LLMToolCall(
                id=call.id,
                name=call.function.name,
                arguments=call.function.arguments,
            )
            for call in (getattr(choice.message, "tool_calls", None) or ())
        )
        metadata: dict[str, Any] = {}
        reasoning_content = getattr(choice.message, "reasoning_content", None)
        if self.capture_reasoning and reasoning_content is not None:
            metadata["reasoning_content"] = reasoning_content
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            metadata=metadata,
            tool_calls=tool_calls,
        )

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
                max_retries=self.max_retries,
            )
        return self._client

    @staticmethod
    def _load_client_factory() -> Callable[..., Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai package must be installed before using an AI provider") from exc
        return OpenAI

import importlib

import pytest

from app.ai.providers import EmbeddingRequest, EmbeddingResponse, LLMMessage, LLMResponse


class FakeProvider:
    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        return LLMResponse(content="ok: " + messages[-1].content, model="fake")

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return EmbeddingResponse(embedding=[0.1, 0.2, 0.3], model="fake-embed")


def test_import_ai_modules_without_api_key(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_OPENAI_API_KEY", raising=False)
    importlib.import_module("app.ai.providers")
    importlib.import_module("app.ai.openai_provider")
    importlib.import_module("app.ai.semantic_documents")


def test_openai_provider_without_api_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_OPENAI_API_KEY", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.ai.openai_provider import OpenAIProvider

    provider = OpenAIProvider()
    with pytest.raises(RuntimeError, match="TOTALCHAT_OPENAI_API_KEY"):
        provider.complete([LLMMessage(role="user", content="hola")])


def test_fake_provider_supports_network_free_tests():
    provider = FakeProvider()
    assert provider.complete([LLMMessage(role="user", content="hola")]).content == "ok: hola"
    assert provider.embed(EmbeddingRequest(input="doc")).embedding == [0.1, 0.2, 0.3]

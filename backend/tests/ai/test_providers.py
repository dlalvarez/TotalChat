import importlib
from types import SimpleNamespace

import pytest

from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.providers import EmbeddingRequest, LLMMessage, create_llm_provider
from app.core.config import get_settings


class FakeClient:
    def __init__(self) -> None:
        message = SimpleNamespace(content="respuesta visible", reasoning_content="razonamiento privado")
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)])
            )
        )
        self.embeddings = SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(data=[SimpleNamespace(embedding=(0.1, 0.2))])
        )


def test_import_ai_modules_without_api_key(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("TOTALCHAT_OPENAI_API_KEY", raising=False)
    importlib.import_module("app.ai.providers")
    importlib.import_module("app.ai.openai_compatible_provider")
    importlib.import_module("app.ai.openai_provider")


def test_provider_without_generic_api_key_fails_clearly():
    provider = OpenAICompatibleProvider(
        provider_name="deepinfra",
        base_url="https://api.deepinfra.com/v1/openai",
        api_key=None,
        model="Qwen/Qwen3.6-35B-A3B",
        embeddings_model="embed-model",
    )
    with pytest.raises(RuntimeError, match="TOTALCHAT_LLM_API_KEY"):
        provider.complete([LLMMessage(role="user", content="hola")])


def test_deepinfra_client_configuration_and_normalized_responses():
    captured = {}

    def client_factory(**kwargs):
        captured.update(kwargs)
        return FakeClient()

    provider = OpenAICompatibleProvider(
        provider_name="deepinfra",
        base_url="https://api.deepinfra.com/v1/openai",
        api_key="fake-key",
        model="Qwen/Qwen3.6-35B-A3B",
        embeddings_model="embed-model",
        timeout_seconds=17,
        client_factory=client_factory,
    )
    response = provider.complete([LLMMessage(role="user", content="hola")])
    embedding = provider.embed(EmbeddingRequest(input="documento"))

    assert captured == {
        "api_key": "fake-key",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "timeout": 17,
    }
    assert response.content == "respuesta visible"
    assert response.model == "Qwen/Qwen3.6-35B-A3B"
    assert response.provider == "deepinfra"
    assert not hasattr(response, "reasoning_content")
    assert embedding.embedding == [0.1, 0.2]
    assert embedding.provider == "deepinfra"


def test_factory_selects_openai_with_generic_key_preferred(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("TOTALCHAT_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("TOTALCHAT_LLM_API_KEY", "generic")
    monkeypatch.setenv("TOTALCHAT_OPENAI_API_KEY", "legacy")
    monkeypatch.setenv("TOTALCHAT_LLM_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    provider = create_llm_provider()
    assert provider.provider_name == "openai"
    assert provider.api_key == "generic"
    assert provider.base_url == "https://api.openai.com/v1"


def test_legacy_key_is_only_fallback_for_openai(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_LLM_API_KEY", raising=False)
    monkeypatch.setenv("TOTALCHAT_OPENAI_API_KEY", "legacy")
    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "deepinfra")
    get_settings.cache_clear()
    assert create_llm_provider().api_key is None

    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "openai")
    get_settings.cache_clear()
    assert create_llm_provider().api_key == "legacy"

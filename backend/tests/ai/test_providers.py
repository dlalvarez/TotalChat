import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.providers import EmbeddingRequest, LLMMessage, create_llm_provider
from app.core.config import Settings, get_settings


class FakeClient:
    def __init__(self, *, reasoning_content="razonamiento privado") -> None:
        message = SimpleNamespace(content="respuesta visible")
        if reasoning_content is not None:
            message.reasoning_content = reasoning_content
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
    assert "reasoning_content" not in response.metadata
    assert embedding.embedding == [0.1, 0.2]
    assert embedding.provider == "deepinfra"


def test_reasoning_is_captured_as_metadata_only_when_enabled(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_CAPTURE_REASONING", "true")
    get_settings.cache_clear()
    provider = OpenAICompatibleProvider(
        provider_name="deepinfra",
        base_url="https://api.deepinfra.com/v1/openai",
        api_key="fake-key",
        model="Qwen/Qwen3.6-35B-A3B",
        embeddings_model="embed-model",
        capture_reasoning=get_settings().llm_capture_reasoning,
        client_factory=lambda **kwargs: FakeClient(),
    )

    response = provider.complete([LLMMessage(role="user", content="hola")])

    assert response.content == "respuesta visible"
    assert response.metadata["reasoning_content"] == "razonamiento privado"


def test_capture_enabled_without_reasoning_content_is_safe(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_CAPTURE_REASONING", "true")
    get_settings.cache_clear()
    provider = OpenAICompatibleProvider(
        provider_name="openai",
        base_url="https://api.openai.com/v1",
        api_key="fake-key",
        model="gpt-4o-mini",
        embeddings_model="text-embedding-3-small",
        capture_reasoning=get_settings().llm_capture_reasoning,
        client_factory=lambda **kwargs: FakeClient(reasoning_content=None),
    )

    response = provider.complete([LLMMessage(role="user", content="hola")])

    assert response.content == "respuesta visible"
    assert "reasoning_content" not in response.metadata


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


def test_deepinfra_llm_and_openai_embeddings_configuration_is_coherent():
    settings = Settings(
        llm_provider="deepinfra",
        llm_base_url="https://api.deepinfra.com/v1/openai",
        llm_model="Qwen/Qwen3.6-35B-A3B",
        embeddings_provider="openai",
        embeddings_base_url="https://api.openai.com/v1",
        embeddings_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )

    assert settings.llm_provider == "deepinfra"
    assert settings.llm_base_url == "https://api.deepinfra.com/v1/openai"
    assert settings.llm_model == "Qwen/Qwen3.6-35B-A3B"
    assert settings.effective_embeddings_provider == "openai"
    assert settings.effective_embeddings_base_url == "https://api.openai.com/v1"
    assert settings.embeddings_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536


def test_documented_example_does_not_pair_openai_embedding_model_with_deepinfra():
    env_example = Path(__file__).parents[3] / ".env.example"
    values = dict(
        line.split("=", maxsplit=1)
        for line in env_example.read_text().splitlines()
        if line and not line.startswith("#") and "=" in line
    )

    assert values["TOTALCHAT_EMBEDDINGS_MODEL"] == "text-embedding-3-small"
    assert values["TOTALCHAT_EMBEDDINGS_PROVIDER"] == "openai"
    assert values["TOTALCHAT_EMBEDDINGS_BASE_URL"] == "https://api.openai.com/v1"
    assert values["TOTALCHAT_EMBEDDING_DIMENSIONS"] == "1536"

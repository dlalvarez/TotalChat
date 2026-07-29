import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.providers import EmbeddingRequest, LLMMessage, create_llm_provider
from app.core.config import Settings, get_settings


class FakeClient:
    def __init__(self, *, reasoning_content="razonamiento privado", completion_calls=None) -> None:
        message = SimpleNamespace(content="respuesta visible")
        if reasoning_content is not None:
            message.reasoning_content = reasoning_content

        def complete(**kwargs):
            if completion_calls is not None:
                completion_calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=complete))
        self.embeddings = SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(data=[SimpleNamespace(embedding=(0.1, 0.2))])
        )


def test_import_ai_modules_without_api_key(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_LLM_API_KEY", raising=False)
    importlib.import_module("app.ai.providers")
    importlib.import_module("app.ai.openai_compatible_provider")


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
    completion_calls = []

    def client_factory(**kwargs):
        captured.update(kwargs)
        return FakeClient(completion_calls=completion_calls)

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
        "max_retries": 0,
    }
    assert completion_calls == [{
        "model": "Qwen/Qwen3.6-35B-A3B",
        "messages": [{"role": "user", "content": "hola"}],
        "max_completion_tokens": 256,
    }]
    assert response.content == "respuesta visible"
    assert response.model == "Qwen/Qwen3.6-35B-A3B"
    assert response.provider == "deepinfra"
    assert "reasoning_content" not in response.metadata
    assert embedding.embedding == [0.1, 0.2]
    assert embedding.provider == "deepinfra"


def test_reasoning_is_captured_as_metadata_only_when_enabled(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_CAPTURE_REASONING", "true")
    get_settings.cache_clear()
    try:
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
    finally:
        get_settings.cache_clear()


def test_capture_enabled_without_reasoning_content_is_safe(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_CAPTURE_REASONING", "true")
    get_settings.cache_clear()
    try:
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
    finally:
        get_settings.cache_clear()


def test_factory_configures_openai_with_generic_key(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("TOTALCHAT_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("TOTALCHAT_LLM_API_KEY", "generic")
    monkeypatch.setenv("TOTALCHAT_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.delenv("TOTALCHAT_LLM_REASONING_EFFORT", raising=False)
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_RETRIES", "0")
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_COMPLETION_TOKENS", "256")
    get_settings.cache_clear()

    try:
        provider = create_llm_provider()
        assert provider.provider_name == "openai"
        assert provider.api_key == "generic"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.reasoning_effort is None
        assert provider.max_retries == 0
        assert provider.max_completion_tokens == 256
    finally:
        get_settings.cache_clear()


def test_llm_operational_defaults_are_safe(monkeypatch):
    for variable in (
        "TOTALCHAT_LLM_TIMEOUT_SECONDS",
        "TOTALCHAT_LLM_REASONING_EFFORT",
        "TOTALCHAT_LLM_MAX_RETRIES",
        "TOTALCHAT_LLM_MAX_COMPLETION_TOKENS",
    ):
        monkeypatch.delenv(variable, raising=False)
    settings = Settings()
    assert settings.llm_timeout_seconds == 30
    assert settings.llm_reasoning_effort is None
    assert settings.llm_max_retries == 0
    assert settings.llm_max_completion_tokens == 256


def test_llm_operational_environment_overrides(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_REASONING_EFFORT", "medium")
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_COMPLETION_TOKENS", "512")
    settings = Settings()
    assert settings.llm_reasoning_effort == "medium"
    assert settings.llm_max_retries == 2
    assert settings.llm_max_completion_tokens == 512


def test_explicit_none_reasoning_effort_is_preserved(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_REASONING_EFFORT", "none")
    settings = Settings()
    assert settings.llm_reasoning_effort == "none"


@pytest.mark.parametrize("reasoning_effort", ["off", "minimal", "", "NONE"])
def test_invalid_reasoning_effort_is_rejected(reasoning_effort):
    with pytest.raises(ValidationError):
        Settings(llm_reasoning_effort=reasoning_effort)


def test_negative_max_retries_is_rejected():
    with pytest.raises(ValidationError):
        Settings(llm_max_retries=-1)


@pytest.mark.parametrize("maximum", [0, -1])
def test_nonpositive_max_completion_tokens_is_rejected(maximum):
    with pytest.raises(ValidationError):
        Settings(llm_max_completion_tokens=maximum)


def test_factory_forwards_custom_operational_controls(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_REASONING_EFFORT", "low")
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("TOTALCHAT_LLM_MAX_COMPLETION_TOKENS", "384")
    get_settings.cache_clear()
    try:
        provider = create_llm_provider()
        assert provider.reasoning_effort == "low"
        assert provider.max_retries == 3
        assert provider.max_completion_tokens == 384
    finally:
        get_settings.cache_clear()


def test_custom_operational_controls_reach_client_and_completion():
    client_configuration = {}
    completion_calls = []

    def client_factory(**kwargs):
        client_configuration.update(kwargs)
        return FakeClient(completion_calls=completion_calls)

    provider = OpenAICompatibleProvider(
        provider_name="compatible",
        base_url="https://compatible.invalid/v1",
        api_key="fake-key",
        model="model",
        embeddings_model="embeddings",
        reasoning_effort="high",
        max_retries=4,
        max_completion_tokens=640,
        client_factory=client_factory,
    )
    provider.complete([LLMMessage(role="user", content="hola")])

    assert client_configuration["max_retries"] == 4
    assert completion_calls[0]["max_completion_tokens"] == 640
    assert completion_calls[0]["extra_body"] == {"reasoning_effort": "high"}


def test_completion_omits_reasoning_effort_when_not_configured():
    completion_calls = []

    class StrictCompatibleClient:
        def __init__(self):
            message = SimpleNamespace(content="respuesta visible")

            def strict_complete(**kwargs):
                if "extra_body" in kwargs:
                    raise AssertionError("strict endpoint rejects extra_body")
                completion_calls.append(kwargs)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=strict_complete))

    provider = OpenAICompatibleProvider(
        provider_name="strict-compatible",
        base_url="https://compatible.invalid/v1",
        api_key="fake-key",
        model="model",
        embeddings_model="embeddings",
        client_factory=lambda **kwargs: StrictCompatibleClient(),
    )
    provider.complete([LLMMessage(role="user", content="hola")])

    assert "extra_body" not in completion_calls[0]
    assert "reasoning_effort" not in repr(completion_calls[0])


def test_completion_sends_reasoning_effort_none_when_configured(monkeypatch):
    completion_calls = []
    monkeypatch.setenv("TOTALCHAT_LLM_REASONING_EFFORT", "none")
    get_settings.cache_clear()
    try:
        provider = create_llm_provider()
        provider.api_key = "fake-key"
        provider._client_factory = lambda **kwargs: FakeClient(completion_calls=completion_calls)
        provider.complete([LLMMessage(role="user", content="hola")])
        assert provider.reasoning_effort == "none"
        assert completion_calls[0]["extra_body"] == {"reasoning_effort": "none"}
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_supported_reasoning_efforts_are_forwarded_without_transformation(effort):
    completion_calls = []
    provider = OpenAICompatibleProvider(
        provider_name="compatible",
        base_url="https://compatible.invalid/v1",
        api_key="fake-key",
        model="model",
        embeddings_model="embeddings",
        reasoning_effort=effort,
        client_factory=lambda **kwargs: FakeClient(completion_calls=completion_calls),
    )
    provider.complete([LLMMessage(role="user", content="hola")])
    assert completion_calls[0]["extra_body"] == {"reasoning_effort": effort}


def test_provider_specific_openai_key_has_no_effect(monkeypatch):
    monkeypatch.delenv("TOTALCHAT_LLM_API_KEY", raising=False)
    removed_provider_key = "TOTALCHAT_OPENAI" + "_API_KEY"
    monkeypatch.setenv(removed_provider_key, "ignored-provider-specific-key")
    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "openai")
    get_settings.cache_clear()
    try:
        assert create_llm_provider().api_key is None
    finally:
        get_settings.cache_clear()


def test_factory_configures_deepinfra_with_generic_key(monkeypatch):
    monkeypatch.setenv("TOTALCHAT_LLM_API_KEY", "generic-deepinfra-key")
    monkeypatch.setenv("TOTALCHAT_LLM_PROVIDER", "deepinfra")
    get_settings.cache_clear()
    try:
        provider = create_llm_provider()
        assert provider.provider_name == "deepinfra"
        assert provider.api_key == "generic-deepinfra-key"
    finally:
        get_settings.cache_clear()


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
    assert values["TOTALCHAT_LLM_MAX_RETRIES"] == "0"
    assert values["TOTALCHAT_LLM_MAX_COMPLETION_TOKENS"] == "256"
    assert "# TOTALCHAT_LLM_REASONING_EFFORT=none" in env_example.read_text()

import uuid

import pytest

from app.ai.conversation_prompts import (
    NATURAL_CONVERSATION_SYSTEM_PROMPT_VERSION,
    ConversationAssistantIdentity,
    build_natural_conversation_system_prompt,
)
from app.ai.conversation_runtime import (
    ConversationContextMessage,
    ConversationTurnRequest,
    MAX_CONTEXT_MESSAGES,
    NaturalConversationRuntime,
    TECHNICAL_FALLBACK,
)
from app.ai.providers import LLMResponse


class FakeProvider:
    def __init__(self, content="Respuesta generada", error=None):
        self.content = content
        self.error = error
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return LLMResponse(
            content=self.content,
            model="fake-model",
            provider="fake",
            metadata={"reasoning_content": "must not escape"},
        )


def request(text="Hola", *, history=(), phase=None, identity=None):
    return ConversationTurnRequest(
        tenant_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        message_text=text,
        recent_messages=history,
        conversation_phase=phase,
        assistant_identity=identity or ConversationAssistantIdentity(),
    )


@pytest.mark.parametrize("text", ["Hola", "Necesito una cita para mi hijo", "Gracias"])
def test_provider_generates_complete_visible_response_for_basic_intents(text):
    provider = FakeProvider(content=f"natural: {text}")
    result = NaturalConversationRuntime(provider).run(request(text))

    assert result.content == f"natural: {text}"
    assert result.code == "natural_response"
    assert result.metadata == {
        "runtime": "natural_conversation",
        "system_prompt_version": "8a9-v1",
    }
    assert "reasoning" not in repr(result)
    assert NATURAL_CONVERSATION_SYSTEM_PROMPT_VERSION not in result.content


def test_first_provider_message_is_built_system_prompt_with_default_identity():
    provider = FakeProvider()
    turn = request()
    NaturalConversationRuntime(provider).run(turn)

    first = provider.calls[0][0]
    assert first.role == "system"
    assert first.content == build_natural_conversation_system_prompt(turn.assistant_identity)
    assert "Sofía" in first.content
    assert "Sofi" in first.content


def test_configured_identity_reaches_system_prompt_without_internal_ids():
    provider = FakeProvider()
    turn = request(identity=ConversationAssistantIdentity(display_name="Luna", friendly_name="Lunita"))
    NaturalConversationRuntime(provider).run(turn)

    prompt = provider.calls[0][0].content
    assert "Luna" in prompt and "Lunita" in prompt
    assert str(turn.tenant_id) not in prompt
    assert str(turn.conversation_id) not in prompt


def test_recent_context_is_ordered_bounded_and_current_message_is_last():
    history = tuple(
        ConversationContextMessage(role="user" if index % 2 == 0 else "assistant", content=f"m{index}")
        for index in range(MAX_CONTEXT_MESSAGES + 3)
    )
    provider = FakeProvider()
    NaturalConversationRuntime(provider).run(request("mensaje actual", history=history, phase="welcome"))

    messages = provider.calls[0]
    context = [item.content for item in messages if item.role in {"user", "assistant"}]
    assert context == [f"m{index}" for index in range(3, 11)] + ["mensaje actual"]
    assert messages[-1].role == "user"


def test_history_keeps_only_authorized_roles():
    provider = FakeProvider()
    NaturalConversationRuntime(provider).run(request(history=(
        ConversationContextMessage(role="tool", content="internal tool output"),
        ConversationContextMessage(role="assistant", content="visible answer"),
        ConversationContextMessage(role="unknown", content="internal message"),
    )))
    context = [(item.role, item.content) for item in provider.calls[0]]
    assert ("assistant", "visible answer") in context
    assert all("internal" not in content for _, content in context)


@pytest.mark.parametrize("content", ["", "   ", None])
def test_empty_or_invalid_provider_content_uses_technical_fallback(content):
    result = NaturalConversationRuntime(FakeProvider(content=content)).run(request())
    assert result.content == TECHNICAL_FALLBACK
    assert result.code == "provider_error"


@pytest.mark.parametrize("error", [RuntimeError("api-key=secret"), TimeoutError("timed out")])
def test_provider_failure_is_sanitized(error):
    result = NaturalConversationRuntime(FakeProvider(error=error)).run(request())
    assert result.content == TECHNICAL_FALLBACK
    assert str(error) not in result.content


def test_prompt_contains_only_safe_allowlisted_context():
    provider = FakeProvider()
    unsafe = "schema_name tenant_private token=telegram-secret chat_id=999 payload={secret}"
    turn = request("consulta general", history=(
        ConversationContextMessage(role="tool", content=unsafe),
        ConversationContextMessage(role="assistant", content="respuesta anterior"),
    ))
    NaturalConversationRuntime(provider).run(turn)

    serialized = repr(provider.calls)
    assert "respuesta anterior" in serialized
    assert "consulta general" in serialized
    assert unsafe not in serialized
    assert str(turn.tenant_id) not in serialized
    assert str(turn.conversation_id) not in serialized


def test_context_content_is_truncated():
    provider = FakeProvider()
    NaturalConversationRuntime(provider).run(request(
        "actual", history=(ConversationContextMessage(role="user", content="x" * 3000),)
    ))
    user_history = provider.calls[0][-2]
    assert len(user_history.content) == 2000

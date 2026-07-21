from pathlib import Path

from app.channels.base import ConversationAgentInvoker


def test_common_agent_contract_is_channel_agnostic() -> None:
    annotations = ConversationAgentInvoker.invoke.__annotations__

    assert set(annotations) == {"tenant_id", "conversation", "message_text", "return"}
    assert "schema_name" not in annotations


def test_common_contract_does_not_import_concrete_adapters() -> None:
    source = Path("app/channels/base.py").read_text(encoding="utf-8").lower()

    assert "app.channels.telegram" not in source
    assert "whatsapp" not in source
    assert "webchat" not in source

"""Channel-agnostic contracts for the conversational ingress pipeline.

Concrete adapters own external payloads, identifiers, credentials, and transport
semantics.  The contracts in this module only describe the internal hand-off to
the already tenant-scoped conversation agent.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.ai.telegram_conversation import ConversationTurnResult
from app.models.tenant import ConversationSession


class ConversationAgentInvoker(Protocol):
    """Invoke the agent after the backend has resolved the tenant."""

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> ConversationTurnResult: ...

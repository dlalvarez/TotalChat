"""Channel-agnostic contracts for one safe conversational turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(frozen=True, slots=True)
class ConversationTurnResult:
    """User-visible content and allowlisted, JSON-serializable state."""

    content: str
    status: str
    state: dict[str, JsonValue]

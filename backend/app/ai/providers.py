from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str


@dataclass(frozen=True)
class EmbeddingRequest:
    input: str


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]
    model: str


class LLMProvider(Protocol):
    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        """Return an LLM completion for an already tenant-scoped operation."""


class EmbeddingsProvider(Protocol):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Return one embedding for an already tenant-scoped document or query."""

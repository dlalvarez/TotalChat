"""Closed, tenant-scoped conversational tool catalog for phase 8A.8."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
import json
from types import MappingProxyType
from typing import Any, Mapping
import unicodedata
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers import LLMToolDefinition
from app.ai.service_tools import (
    ServiceListRequest,
    ServiceRepository,
    ServiceSearchRequest,
    ServiceSummary,
    ServiceTools,
)


SEARCH_SERVICES_DEFINITION = LLMToolDefinition(
    name="search_services",
    description=(
        "Consulta los servicios activos reales del tenant. Úsala para preguntas sobre "
        "servicios, descripciones o duración. No consulta precios, disponibilidad o citas."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Texto opcional para filtrar por nombre o descripción.",
                "maxLength": 200,
            }
        },
        "additionalProperties": False,
    },
)


@dataclass(frozen=True, slots=True)
class PublicService:
    name: str
    description: str | None
    duration_minutes: int


@dataclass(frozen=True, slots=True)
class ResolvedConversationService:
    """Backend-only service identity; never part of an LLM tool result."""

    service_id: UUID
    name: str


class ConversationToolRegistry:
    """Validate requests and expose only user-safe structured facts."""

    def __init__(
        self,
        *,
        tenant_id: UUID,
        session: Session | None = None,
        repository: ServiceRepository | None = None,
    ) -> None:
        self._tools = ServiceTools(
            tenant_id=tenant_id, session=session, repository=repository
        )

    @property
    def definitions(self) -> tuple[LLMToolDefinition, ...]:
        return (SEARCH_SERVICES_DEFINITION,)

    def execute(self, name: str, raw_arguments: str) -> Mapping[str, Any]:
        if name != SEARCH_SERVICES_DEFINITION.name:
            raise ValueError("tool is not allowed")
        try:
            arguments = json.loads(raw_arguments or "{}")
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid tool arguments") from exc
        if not isinstance(arguments, dict) or set(arguments) - {"query"}:
            raise ValueError("invalid tool arguments")
        query = arguments.get("query", "")
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError("invalid tool arguments")
        result = (
            self._tools.search_services(ServiceSearchRequest(text=query.strip(), limit=20))
            if query.strip()
            else self._tools.list_active_services(ServiceListRequest(limit=20))
        )
        services = tuple(PublicService(
            name=service.name,
            description=service.description,
            duration_minutes=service.duration_minutes,
        ) for service in result.services)
        return MappingProxyType({"services": [asdict(service) for service in services]})

    def resolve_service(self, query: str) -> ResolvedConversationService | None:
        """Resolve one active service conservatively inside the current tenant."""

        normalized_query = _normalize_service_text(query)
        if not normalized_query:
            return None
        services = self._tools.list_active_services(ServiceListRequest(limit=100)).services
        ranked: list[tuple[float, str, ServiceSummary]] = []
        for service in services:
            candidates = (service.name, service.description or "")
            score = max(
                _service_match_score(normalized_query, candidate) for candidate in candidates
            )
            if score >= 0.8:
                ranked.append((score, _normalize_service_text(service.name), service))
        ranked.sort(key=lambda item: (-item[0], item[1], str(item[2].service_id)))
        if not ranked or (len(ranked) > 1 and ranked[0][0] == ranked[1][0]):
            return None
        match = ranked[0][2]
        return ResolvedConversationService(service_id=match.service_id, name=match.name)


def _normalize_service_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character)).split()
    )


def _service_match_score(query: str, candidate: str) -> float:
    normalized_candidate = _normalize_service_text(candidate)
    if not normalized_candidate:
        return 0.0
    if query == normalized_candidate:
        return 1.0
    if query in normalized_candidate:
        return 0.95
    query_tokens = [token for token in query.split() if token not in _GENERIC_SERVICE_TOKENS]
    candidate_tokens = [
        token for token in normalized_candidate.split() if token not in _GENERIC_SERVICE_TOKENS
    ]
    if not query_tokens or not candidate_tokens:
        return 0.0
    return min(
        max(
            SequenceMatcher(None, query_token, candidate_token).ratio()
            for candidate_token in candidate_tokens
        )
        for query_token in query_tokens
    )


_GENERIC_SERVICE_TOKENS = {
    "a", "agendar", "agendo", "cambiar", "cambio", "cita", "consulta", "de", "del",
    "el", "en", "la",
    "mejor", "necesito", "otra", "otro", "por", "prefiero", "quiero", "servicio", "un",
    "reservar", "turno", "una",
}

"""Closed, tenant-scoped conversational read-only tool catalog."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
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
    ServiceSummary,
    ServiceTools,
)
from app.services.availability import (
    AvailableSlotsRequest,
    InternalSchedulingProvider,
    SchedulingProvider,
)
from app.tenancy.context import TenantContext


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

GET_AVAILABLE_SLOTS_DEFINITION = LLMToolDefinition(
    name="get_available_slots",
    description=(
        "Consulta horarios reales de solo lectura para el servicio ya confirmado. "
        "Requiere un rango cerrado de máximo 31 días; no reserva ni bloquea horarios."
    ),
    parameters={
        "type": "object",
        "properties": {
            "date_from": {"type": "string", "format": "date"},
            "date_to": {"type": "string", "format": "date"},
            "modality": {"type": "string", "enum": ["in_person", "virtual"]},
            "time_from": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
            "time_to": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
        },
        "required": ["date_from", "date_to", "modality"],
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
        tenant_context: TenantContext | None = None,
        selected_service: ResolvedConversationService | None = None,
        scheduling_provider: SchedulingProvider | None = None,
        availability_session: Session | None = None,
    ) -> None:
        self._tools = ServiceTools(
            tenant_id=tenant_id, session=session, repository=repository
        )
        self._session = availability_session or session
        self._tenant_context = tenant_context
        self._selected_service = selected_service
        self._scheduling_provider = scheduling_provider or InternalSchedulingProvider()

    @property
    def definitions(self) -> tuple[LLMToolDefinition, ...]:
        if self._selected_service is not None and self._tenant_context is not None:
            return (SEARCH_SERVICES_DEFINITION, GET_AVAILABLE_SLOTS_DEFINITION)
        return (SEARCH_SERVICES_DEFINITION,)

    def execute(self, name: str, raw_arguments: str) -> Mapping[str, Any]:
        if name not in {item.name for item in self.definitions}:
            raise ValueError("tool is not allowed")
        try:
            arguments = json.loads(raw_arguments or "{}")
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid tool arguments") from exc
        if not isinstance(arguments, dict):
            raise ValueError("invalid tool arguments")
        if name == GET_AVAILABLE_SLOTS_DEFINITION.name:
            return self._execute_availability(arguments)
        if set(arguments) - {"query"}:
            raise ValueError("invalid tool arguments")
        query = arguments.get("query", "")
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError("invalid tool arguments")
        if query.strip():
            active = self._tools.list_active_services(ServiceListRequest(limit=100)).services
            matched = tuple(item[2] for item in _rank_services(query, active))[:20]
        else:
            matched = self._tools.list_active_services(ServiceListRequest(limit=20)).services
        services = tuple(PublicService(
            name=service.name,
            description=service.description,
            duration_minutes=service.duration_minutes,
        ) for service in matched)
        return MappingProxyType({"services": [asdict(service) for service in services]})

    def _execute_availability(self, arguments: dict[str, Any]) -> Mapping[str, Any]:
        allowed = {"date_from", "date_to", "modality", "time_from", "time_to"}
        if set(arguments) - allowed or not {"date_from", "date_to", "modality"} <= set(arguments):
            raise ValueError("invalid tool arguments")
        if self._session is None or self._tenant_context is None or self._selected_service is None:
            raise ValueError("availability requires a confirmed service")
        try:
            date_from = date.fromisoformat(arguments["date_from"])
            date_to = date.fromisoformat(arguments["date_to"])
            modality = arguments["modality"]
            time_from = time.fromisoformat(arguments["time_from"]) if "time_from" in arguments else None
            time_to = time.fromisoformat(arguments["time_to"]) if "time_to" in arguments else None
        except (TypeError, ValueError):
            raise ValueError("invalid tool arguments") from None
        if modality not in {"in_person", "virtual"} or date_from > date_to or (date_to - date_from).days >= 31:
            raise ValueError("invalid tool arguments")
        slots = self._scheduling_provider.get_available_slots(
            self._session,
            self._tenant_context,
            AvailableSlotsRequest(
                practitioner_service_id=self._selected_service.service_id,
                date_from=date_from,
                date_to=date_to,
                modality=modality,
            ),
        )
        visible = [slot for slot in slots if (time_from is None or slot.starts_at.time() >= time_from) and (time_to is None or slot.starts_at.time() < time_to)]
        shown = visible[:10]
        return MappingProxyType({
            "kind": "availability_lookup",
            "status": "available" if visible else "no_slots",
            "service_name": self._selected_service.name,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "modality": modality,
            "slots": [
                {"date": slot.starts_at.date().isoformat(), "start_time": slot.starts_at.strftime("%H:%M"), "end_time": slot.ends_at.strftime("%H:%M")}
                for slot in shown
            ],
            "total_slots": len(visible),
            "shown_slots": len(shown),
            "has_more": len(visible) > len(shown),
            "limits": {
                "can_create_booking": False,
                "can_hold_slot": False,
                "can_take_payment": False,
            },
        })

    def resolve_service(self, query: str) -> ResolvedConversationService | None:
        """Resolve only one exact or unequivocal active tenant service."""

        if not _normalize_service_text(query):
            return None
        services = self._tools.list_active_services(ServiceListRequest(limit=100)).services
        ranked = _rank_services(query, services, include_suggestions=False)
        if not ranked or (
            len(ranked) > 1 and ranked[0][0] - ranked[1][0] < _MIN_UNIQUE_SCORE_MARGIN
        ):
            return None
        match = ranked[0][2]
        return ResolvedConversationService(service_id=match.service_id, name=match.name)

    def suggest_service(self, query: str) -> ResolvedConversationService | None:
        """Return one conservative related service without confirming selection."""

        if not _normalize_service_text(query):
            return None
        services = self._tools.list_active_services(ServiceListRequest(limit=100)).services
        ranked = _rank_services(query, services, include_suggestions=True)
        if not ranked or (
            len(ranked) > 1 and ranked[0][0] - ranked[1][0] < _MIN_UNIQUE_SCORE_MARGIN
        ):
            return None
        match = ranked[0][2]
        return ResolvedConversationService(service_id=match.service_id, name=match.name)


def _normalize_service_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character)).split()
    )


def _rank_services(
    query: str,
    services: tuple[ServiceSummary, ...],
    *,
    include_suggestions: bool = True,
) -> list[tuple[float, str, ServiceSummary]]:
    normalized_query = _normalize_service_text(query)
    ranked: list[tuple[float, str, ServiceSummary]] = []
    for service in services:
        score = max(
            _service_match_score(
                normalized_query,
                candidate,
                include_suggestions=include_suggestions,
            )
            for candidate in (service.name, service.description or "")
        )
        if score >= _MIN_SERVICE_MATCH_SCORE:
            ranked.append((score, _normalize_service_text(service.name), service))
    ranked.sort(key=lambda item: (-item[0], item[1], str(item[2].service_id)))
    return ranked


def _service_match_score(
    query: str,
    candidate: str,
    *,
    include_suggestions: bool,
) -> float:
    normalized_candidate = _normalize_service_text(candidate)
    if not normalized_candidate:
        return 0.0
    query_tokens = [token for token in query.split() if token not in _GENERIC_SERVICE_TOKENS]
    candidate_tokens = [
        token for token in normalized_candidate.split() if token not in _GENERIC_SERVICE_TOKENS
    ]
    if not query_tokens or not candidate_tokens:
        return 0.0
    meaningful_query = " ".join(query_tokens)
    meaningful_candidate = " ".join(candidate_tokens)
    if meaningful_query == meaningful_candidate:
        return 1.0
    if meaningful_query in meaningful_candidate:
        return 0.95
    if not include_suggestions:
        return 0.0
    prefix_length = 0
    for query_character, candidate_character in zip(
        meaningful_query, meaningful_candidate, strict=False
    ):
        if query_character != candidate_character:
            break
        prefix_length += 1
    prefix_ratio = prefix_length / min(len(meaningful_query), len(meaningful_candidate))
    similarity = SequenceMatcher(None, meaningful_query, meaningful_candidate).ratio()
    if prefix_ratio >= _MIN_SUGGESTION_PREFIX_RATIO and similarity >= _MIN_SUGGESTION_SCORE:
        return similarity
    return 0.0


_MIN_SERVICE_MATCH_SCORE = 0.8
_MIN_SUGGESTION_SCORE = 0.88
_MIN_SUGGESTION_PREFIX_RATIO = 0.75
_MIN_UNIQUE_SCORE_MARGIN = 0.05


_GENERIC_SERVICE_TOKENS = {
    "a", "agendar", "agendo", "cambiar", "cambio", "cita", "consulta", "de", "del",
    "el", "en", "la",
    "mejor", "necesito", "otra", "otro", "por", "prefiero", "quiero", "servicio", "un",
    "reservar", "turno", "una",
}

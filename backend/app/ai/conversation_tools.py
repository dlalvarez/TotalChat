"""Closed, tenant-scoped conversational tool catalog for phase 8A.8."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers import LLMToolDefinition
from app.ai.service_tools import (
    ServiceListRequest, ServiceRepository, ServiceSearchRequest, ServiceTools,
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

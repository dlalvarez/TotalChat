"""Conservative LLM-assisted orchestration for an initial Telegram booking flow."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from uuid import UUID

from app.ai.providers import LLMMessage, LLMProvider
from app.ai.service_tools import ServiceListRequest, ServiceSearchRequest, ServiceTools


@dataclass(frozen=True, slots=True)
class ConversationTurnResult:
    content: str
    status: str
    state: dict[str, Any]


class TelegramConversationOrchestrator:
    """Interpret one turn, then validate factual selections with backend tools."""

    def __init__(self, *, tenant_id: UUID, llm: LLMProvider, service_tools: ServiceTools) -> None:
        self._tenant_id = tenant_id
        self._llm = llm
        self._services = service_tools

    def run(self, *, message_text: str, current_state: dict[str, Any]) -> ConversationTurnResult:
        interpretation = self._interpret(message_text, current_state)
        state = self._safe_state(current_state)
        state.update({
            "phase": "collecting_booking_context",
            "last_user_message": message_text,
            "intent": interpretation["intent"],
        })

        service_query = interpretation.get("service_query")
        if service_query and not state.get("selected_service_id"):
            matches = self._services.search_services(ServiceSearchRequest(text=service_query, limit=10)).services
            if len(matches) == 1:
                service = matches[0]
                state.update({
                    "selected_service_id": str(service.service_id),
                    "selected_service_name": service.name,
                    "selected_practitioner_id": str(service.practitioner_id),
                })
            elif len(matches) > 1:
                names = ", ".join(item.name for item in matches[:5])
                return self._result(state, "service_ambiguous", f"Encontré varias opciones: {names}. ¿Cuál prefieres?")
            else:
                available = self._services.list_active_services(ServiceListRequest(limit=5)).services
                if available:
                    names = ", ".join(item.name for item in available)
                    return self._result(
                        state, "service_not_found",
                        f"No pude confirmar ese servicio. Los servicios disponibles son: {names}. ¿Cuál necesitas?",
                    )
                return self._result(
                    state, "service_not_found",
                    "No pude confirmar ese servicio en este momento. ¿Puedes aclarar qué servicio necesitas?",
                )

        for key in ("date_preference", "time_preference", "modality"):
            value = interpretation.get(key)
            if value:
                state[key] = value

        missing = self._missing(state)
        state["missing_fields"] = missing
        if "service" in missing:
            return self._result(
                state, "needs_service",
                "Hola, soy el asistente de MediChat. Puedo ayudarte a iniciar una reserva. ¿Qué servicio necesitas?",
            )
        if "date_preference" in missing:
            return self._result(
                state, "needs_date",
                f"Entendido, buscas {state['selected_service_name']}. ¿Para qué fecha te gustaría reservar?",
            )
        if "time_preference" in missing:
            return self._result(state, "needs_time", "¿En qué horario prefieres la cita?")
        if "modality" in missing:
            return self._result(state, "needs_modality", "¿Prefieres una cita presencial o virtual?")
        return self._result(
            state, "context_partial",
            "Gracias. Ya tengo el servicio y tus preferencias iniciales. Aún debo validar las opciones disponibles antes de continuar.",
        )

    def _interpret(self, message_text: str, state: dict[str, Any]) -> dict[str, str | None]:
        safe_context = {
            key: state.get(key) for key in
            ("selected_service_name", "date_preference", "time_preference", "modality")
            if state.get(key)
        }
        response = self._llm.complete([
            LLMMessage(role="system", content=(
                "Eres un extractor administrativo de reservas. No diagnostiques ni inventes datos. "
                "Devuelve SOLO JSON con intent, service_query, date_preference, time_preference y modality. "
                "Usa null si no está explícito. Conserva expresiones relativas como 'mañana'; modality solo "
                "puede ser in_person, virtual o null. intent: greeting, booking, information, ambiguous u other."
            )),
            LLMMessage(role="user", content=json.dumps(
                {"current_context": safe_context, "message": message_text}, ensure_ascii=False
            )),
        ])
        try:
            value = json.loads(response.content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("LLM returned an invalid structured interpretation") from exc
        if not isinstance(value, dict):
            raise ValueError("LLM interpretation must be an object")
        allowed = {"intent", "service_query", "date_preference", "time_preference", "modality"}
        result = {key: value.get(key) if isinstance(value.get(key), str) else None for key in allowed}
        result["intent"] = result["intent"] or "ambiguous"
        if result["modality"] not in {None, "in_person", "virtual"}:
            result["modality"] = None
        return result

    @staticmethod
    def _safe_state(state: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in state.items() if key != "schema_name"}

    @staticmethod
    def _missing(state: dict[str, Any]) -> list[str]:
        fields = (("service", "selected_service_id"), ("date_preference", "date_preference"),
                  ("time_preference", "time_preference"), ("modality", "modality"))
        return [label for label, key in fields if not state.get(key)]

    @staticmethod
    def _result(state: dict[str, Any], status: str, content: str) -> ConversationTurnResult:
        state["last_assistant_message"] = content
        state["missing_fields"] = TelegramConversationOrchestrator._missing(state)
        return ConversationTurnResult(content=content, status=status, state=state)

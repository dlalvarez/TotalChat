import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest

from app.ai.providers import LLMResponse
from app.ai.service_tools import ServiceRecord, ServiceTools
from app.ai.booking_conversation import InitialBookingConversationOrchestrator


@dataclass
class FakeLLM:
    payload: dict | str

    def complete(self, messages):
        assert "schema_name" not in repr(messages)
        content = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return LLMResponse(content=content, model="test")


class ServiceRepository:
    def __init__(self, records):
        self.records = records

    def list_active(self, *, text=None, **kwargs):
        if text:
            return [record for record in self.records if text.casefold() in record.name.casefold()]
        return self.records

    def get_active(self, service_id):
        return next((record for record in self.records if record.service_id == service_id), None)


def orchestrator(payload, records=()):
    tenant_id = uuid4()
    return InitialBookingConversationOrchestrator(
        tenant_id=tenant_id,
        llm=FakeLLM(payload),
        service_tools=ServiceTools(tenant_id=tenant_id, repository=ServiceRepository(records)),
    )


def service(name="Consulta general"):
    return ServiceRecord(
        service_id=uuid4(), name=name, description=None, duration_minutes=30,
        practitioner_id=uuid4(), practitioner_name="Dra. Ana", organization_id=uuid4(),
        organization_name="Centro", modalities=("in_person",),
    )


def test_greeting_requests_service_and_persists_partial_state():
    result = orchestrator({"intent": "greeting"}).run(message_text="Hola", current_state={})

    assert result.status == "needs_service"
    assert "servicio" in result.content.lower()
    assert result.state["last_user_message"] == "Hola"
    assert result.state["missing_fields"][0] == "service"


def test_orchestrator_and_contract_are_channel_agnostic():
    source = Path("app/ai/booking_conversation.py").read_text(encoding="utf-8").lower()
    contract = Path("app/ai/conversation_types.py").read_text(encoding="utf-8").lower()

    for forbidden in ("telegram", "chat_id", "update_id", "schema_name", "bot_token"):
        assert forbidden not in source
        assert forbidden not in contract


def test_service_is_confirmed_by_tool_before_requesting_date():
    record = service()
    result = orchestrator(
        {"intent": "booking", "service_query": "Consulta general"}, (record,)
    ).run(message_text="Consulta general", current_state={})

    assert result.status == "needs_date"
    assert result.state["selected_service_id"] == str(record.service_id)
    assert result.state["selected_service_name"] == "Consulta general"
    assert str(record.service_id) not in result.content


def test_relative_date_and_time_extend_existing_state_without_restart():
    record = service()
    state = {"selected_service_id": str(record.service_id), "selected_service_name": record.name}
    result = orchestrator({
        "intent": "information", "date_preference": "mañana", "time_preference": "tarde"
    }, (record,)).run(message_text="Mañana en la tarde", current_state=state)

    assert result.state["date_preference"] == "mañana"
    assert result.state["time_preference"] == "tarde"
    assert result.status == "needs_modality"


def test_ambiguous_service_presents_only_tool_results():
    records = (service("Consulta general adultos"), service("Consulta general infantil"))
    result = orchestrator(
        {"intent": "booking", "service_query": "Consulta general"}, records
    ).run(message_text="Consulta general", current_state={})

    assert result.status == "service_ambiguous"
    assert all(record.name in result.content for record in records)
    assert "selected_service_id" not in result.state


def test_missing_service_lists_only_real_tool_results():
    record = service("Consulta pediátrica")
    result = orchestrator(
        {"intent": "booking", "service_query": "Cardiología"}, (record,)
    ).run(message_text="Cardiología", current_state={})

    assert result.status == "service_not_found"
    assert record.name in result.content
    assert "Cardiología" not in result.content


def test_state_is_explicitly_allowlisted_and_json_serializable():
    unsafe = {
        "phase": "old", "selected_service_name": "Consulta general",
        "schema_name": "tenant_secret", "api_key": "key", "token": "token",
        "credentials": {"password": "secret"}, "reasoning_content": "private",
        "prompt": "internal", "raw_payload": {"update_id": 1}, "object": object(),
    }
    result = orchestrator({"intent": "greeting"}).run(message_text="Hola", current_state=unsafe)

    assert set(result.state) <= {
        "phase", "intent", "selected_service_id", "selected_service_name",
        "selected_practitioner_id", "date_preference", "time_preference", "modality",
        "missing_fields", "last_user_message", "last_assistant_message",
    }
    serialized = json.dumps(result.state)
    assert "tenant_secret" not in serialized
    assert "private" not in serialized
    assert "internal" not in serialized


def test_unknown_intent_and_modality_are_normalized_safely():
    record = service()
    result = orchestrator({
        "intent": "confirm_booking", "service_query": record.name, "modality": "home_visit"
    }, (record,)).run(message_text="Confirma a domicilio", current_state={})

    assert result.state["intent"] == "ambiguous"
    assert "modality" not in result.state
    assert result.status == "needs_date"
    assert "confirmada" not in result.content.lower()


def test_invalid_llm_json_is_rejected_without_persistable_partial_result():
    with pytest.raises(ValueError, match="invalid structured interpretation"):
        orchestrator("not-json").run(message_text="Hola", current_state={})


@pytest.mark.parametrize(
    ("state", "payload", "status"),
    [
        ({"selected_service_id": str(uuid4()), "selected_service_name": "Consulta"},
         {"intent": "information"}, "needs_date"),
        ({"selected_service_id": str(uuid4()), "selected_service_name": "Consulta",
          "date_preference": "mañana"}, {"intent": "information"}, "needs_time"),
        ({"selected_service_id": str(uuid4()), "selected_service_name": "Consulta",
          "date_preference": "mañana", "time_preference": "tarde"},
         {"intent": "information"}, "needs_modality"),
    ],
)
def test_next_missing_field_is_requested(state, payload, status):
    result = orchestrator(payload).run(message_text="Continuar", current_state=state)
    assert result.status == status

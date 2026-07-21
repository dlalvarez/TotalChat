import json
from dataclasses import dataclass
from uuid import uuid4

from app.ai.providers import LLMResponse
from app.ai.service_tools import ServiceRecord, ServiceTools
from app.ai.telegram_conversation import TelegramConversationOrchestrator


@dataclass
class FakeLLM:
    payload: dict

    def complete(self, messages):
        assert "schema_name" not in repr(messages)
        return LLMResponse(content=json.dumps(self.payload), model="test")


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
    return TelegramConversationOrchestrator(
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

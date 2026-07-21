from dataclasses import dataclass, field

from fastapi.testclient import TestClient

from app.api.telegram import get_telegram_service
from app.channels.telegram import TelegramIntakeResult, TelegramUpdate
from app.core.config import Settings, get_settings
from app.main import create_app

UPDATE = {"update_id": 41001, "message": {"message_id": 81, "chat": {"id": 90001, "first_name": "Synthetic"}, "text": "Hola"}}


@dataclass
class IntakeSpy:
    accepted: bool = True
    calls: list[tuple[TelegramUpdate, str]] = field(default_factory=list)
    persisted: list[dict[str, object]] = field(default_factory=list)

    def process(self, update: TelegramUpdate, *, bot_identifier: str) -> TelegramIntakeResult:
        self.calls.append((update, bot_identifier))
        if self.accepted:
            self.persisted.append({"direction": "incoming", "content": update.message.text, "external_message_id": str(update.update_id)})
        return TelegramIntakeResult(accepted=self.accepted)


def make_client(spy: IntakeSpy) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(telegram_webhook_secret="test-only-webhook-secret", telegram_bot_identifier="configured-test-bot", telegram_bot_token=None)
    app.dependency_overrides[get_telegram_service] = lambda: spy
    return TestClient(app)


def test_webhook_accepts_valid_update_and_persists_incoming_message() -> None:
    spy = IntakeSpy()
    response = make_client(spy).post("/api/webhooks/telegram/test-only-webhook-secret", json=UPDATE)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert spy.persisted == [{"direction": "incoming", "content": "Hola", "external_message_id": "41001"}]
    assert spy.calls[0][1] == "configured-test-bot"


def test_webhook_rejects_invalid_secret_without_processing() -> None:
    spy = IntakeSpy()
    response = make_client(spy).post("/api/webhooks/telegram/wrong-secret", json=UPDATE)
    assert response.status_code == 404
    assert spy.calls == []
    assert "test-only-webhook-secret" not in response.text


def test_update_without_configured_tenant_does_not_persist_tenant_data() -> None:
    spy = IntakeSpy(accepted=False)
    response = make_client(spy).post("/api/webhooks/telegram/test-only-webhook-secret", json=UPDATE)
    assert response.status_code == 200
    assert spy.persisted == []


def test_webhook_response_does_not_expose_schema_or_secrets() -> None:
    response = make_client(IntakeSpy()).post("/api/webhooks/telegram/test-only-webhook-secret", json=UPDATE)
    assert "schema_name" not in response.text
    assert "test-only-webhook-secret" not in response.text


def test_intake_has_no_agent_or_outbound_network_side_effects(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("Agent, LLM, network, and outbound Telegram calls are out of scope")

    monkeypatch.setattr("app.ai.booking_agent.BookingAgent.run", forbidden)
    monkeypatch.setattr("app.ai.openai_compatible_provider.OpenAICompatibleProvider.complete", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    spy = IntakeSpy()
    response = make_client(spy).post("/api/webhooks/telegram/test-only-webhook-secret", json=UPDATE)
    assert response.status_code == 200
    assert len(spy.calls) == 1

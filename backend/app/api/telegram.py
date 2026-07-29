import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.conversation_invoker import NaturalConversationAgentInvoker
from app.ai.providers import create_llm_provider
from app.channels.telegram import TelegramHTTPClient, TelegramUpdate, TelegramWebhookService
from app.core.config import Settings, get_settings
from app.db.session import get_db_session

router = APIRouter(prefix="/api/webhooks/telegram", tags=["telegram"])


def get_telegram_service(
    session: Session = Depends(get_db_session), settings: Settings = Depends(get_settings)
) -> TelegramWebhookService:
    client = TelegramHTTPClient(settings.telegram_bot_token) if settings.telegram_bot_token else None
    invoker = NaturalConversationAgentInvoker(session, create_llm_provider())
    return TelegramWebhookService(session, agent_invoker=invoker, telegram_client=client)


@router.post("/{webhook_secret}")
def telegram_webhook(
    webhook_secret: str,
    update: TelegramUpdate,
    settings: Settings = Depends(get_settings),
    service: TelegramWebhookService = Depends(get_telegram_service),
) -> dict[str, bool]:
    configured_secret = settings.telegram_webhook_secret
    bot_identifier = settings.telegram_bot_identifier
    if not configured_secret or not secrets.compare_digest(webhook_secret, configured_secret):
        raise HTTPException(status_code=404, detail="Webhook not found")
    if not bot_identifier:
        raise HTTPException(status_code=503, detail="Telegram channel is not configured")

    # Telegram receives 200 even when this backend cannot map the bot to an
    # active tenant. No tenant-scoped data is touched in that case.
    service.process(update, bot_identifier=bot_identifier)
    return {"ok": True}

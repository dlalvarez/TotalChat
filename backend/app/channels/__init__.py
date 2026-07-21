"""Messaging channel adapters owned by the backend."""

from app.channels.telegram import TelegramUpdate, TelegramWebhookService

__all__ = ["TelegramUpdate", "TelegramWebhookService"]

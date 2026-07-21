"""Telegram intake only: parsing, tenant resolution, and persistence.

This module intentionally has no Telegram client, network call, LLM, or booking
agent dependency. Outbound delivery and agent invocation belong to later work.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tenant import ConversationSession, Message
from app.tenancy.resolver import TenantResolver
from app.tenancy.schema import is_valid_tenant_schema_name


class TelegramChat(BaseModel):
    id: int
    model_config = ConfigDict(extra="ignore")


class TelegramMessage(BaseModel):
    message_id: int
    chat: TelegramChat
    text: str
    model_config = ConfigDict(extra="ignore")


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage
    model_config = ConfigDict(extra="ignore")


@dataclass(frozen=True, slots=True)
class TelegramIntakeResult:
    accepted: bool
    duplicate: bool = False


@dataclass(slots=True)
class TelegramWebhookService:
    session: Session

    def process(self, update: TelegramUpdate, *, bot_identifier: str) -> TelegramIntakeResult:
        tenant = TenantResolver(self.session).resolve_by_channel(
            channel_type="telegram", external_identifier=bot_identifier
        )
        if tenant is None or not is_valid_tenant_schema_name(tenant.schema_name):
            return TelegramIntakeResult(accepted=False)

        if self.session.get_bind().dialect.name != "sqlite":
            self.session.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))

        external_user_id = str(update.message.chat.id)
        conversation = self.session.execute(
            select(ConversationSession).where(
                ConversationSession.channel_type == "telegram",
                ConversationSession.external_user_id == external_user_id,
            )
        ).scalar_one_or_none()
        if conversation is None:
            conversation = ConversationSession(channel_type="telegram", external_user_id=external_user_id)
            self.session.add(conversation)
            self.session.flush()

        external_message_id = str(update.update_id)
        existing = self.session.execute(
            select(Message.id).where(
                Message.channel_type == "telegram", Message.external_message_id == external_message_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            self.session.rollback()
            return TelegramIntakeResult(accepted=True, duplicate=True)

        self.session.add(
            Message(
                conversation_session_id=conversation.id,
                channel_type="telegram",
                external_message_id=external_message_id,
                direction="incoming",
                message_type="text",
                content=update.message.text,
                raw_payload={
                    "update_id": update.update_id,
                    "message_id": update.message.message_id,
                    "chat_id": update.message.chat.id,
                },
            )
        )
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return TelegramIntakeResult(accepted=True, duplicate=True)
        return TelegramIntakeResult(accepted=True)

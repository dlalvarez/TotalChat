"""Tenant-scoped Telegram intake, agent bridge, and controlled delivery."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import traceback
from typing import Protocol
from urllib import error, request
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.conversation_runtime import TECHNICAL_FALLBACK
from app.channels.base import ConversationAgentInvoker
from app.models.tenant import ConversationSession, Message
from app.tenancy.resolver import TenantResolver
from app.tenancy.schema import is_valid_tenant_schema_name


logger = logging.getLogger(__name__)


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


class TelegramDeliveryError(RuntimeError):
    """A sanitized Telegram transport or API failure."""


class TelegramClient(Protocol):
    def send_message(self, *, chat_id: int, text: str) -> int: ...


@dataclass(frozen=True, slots=True)
class TelegramHTTPClient:
    """Minimal Bot API client whose credential is never persisted or logged."""

    token: str
    timeout_seconds: float = 10.0

    def send_message(self, *, chat_id: int, text: str) -> int:
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        outbound = request.Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(outbound, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise TelegramDeliveryError("Telegram delivery failed") from exc

        result = body.get("result") if isinstance(body, dict) else None
        message_id = result.get("message_id") if isinstance(result, dict) else None
        if not isinstance(body, dict) or body.get("ok") is not True or not isinstance(message_id, int):
            raise TelegramDeliveryError("Telegram did not confirm delivery")
        return message_id


@dataclass(slots=True)
class TelegramWebhookService:
    session: Session
    agent_invoker: ConversationAgentInvoker | None = None
    telegram_client: TelegramClient | None = None

    def process(self, update: TelegramUpdate, *, bot_identifier: str) -> TelegramIntakeResult:
        tenant = TenantResolver(self.session).resolve_by_channel(
            channel_type="telegram", external_identifier=bot_identifier
        )
        if tenant is None or not is_valid_tenant_schema_name(tenant.schema_name):
            return TelegramIntakeResult(accepted=False)

        self._select_tenant_schema(tenant.schema_name)
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

        self.session.add(Message(
            conversation_session_id=conversation.id,
            channel_type="telegram",
            external_message_id=external_message_id,
            direction="incoming",
            message_type="text",
            content=update.message.text,
            raw_payload={"update_id": update.update_id, "message_id": update.message.message_id,
                         "chat_id": update.message.chat.id},
        ))
        try:
            # Make intake durable before invoking the agent so a controlled agent
            # failure can never make Telegram retry an already accepted update.
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return TelegramIntakeResult(accepted=True, duplicate=True)

        self._select_tenant_schema(tenant.schema_name)
        conversation = self.session.get(ConversationSession, conversation.id)
        assert conversation is not None
        try:
            if self.agent_invoker is None:
                raise RuntimeError("conversation agent is not configured")
            invoker = self.agent_invoker
            result = invoker.invoke(
                tenant_id=tenant.tenant_id,
                conversation=conversation,
                message_text=update.message.text,
            )
            content = result.content
            agent_status = result.code
        except Exception as exc:
            # Keep the acknowledgement boundary and never persist exception details.
            # Frame locations make unexpected failures diagnosable without logging
            # exception values, request payloads, tenant schemas, or credentials.
            logger.error(
                "Telegram agent invocation failed exception_type=%s trace=%s",
                type(exc).__name__,
                _safe_traceback_locations(exc),
            )
            self.session.rollback()
            self._select_tenant_schema(tenant.schema_name)
            conversation = self.session.execute(select(ConversationSession).where(
                ConversationSession.channel_type == "telegram",
                ConversationSession.external_user_id == external_user_id,
            )).scalar_one()
            content = TECHNICAL_FALLBACK
            agent_status = "runtime_error"

        outgoing = Message(
            conversation_session_id=conversation.id,
            channel_type="telegram",
            external_message_id=f"agent:{update.update_id}",
            direction="outgoing",
            message_type="text",
            content=content,
            raw_payload={"delivery_status": "pending", "agent_status": agent_status,
                         "source_update_id": update.update_id},
        )
        self.session.add(outgoing)
        self.session.commit()
        if self.telegram_client is not None:
            self._deliver_pending(
                outgoing.id,
                chat_id=update.message.chat.id,
                schema_name=tenant.schema_name,
            )
        return TelegramIntakeResult(accepted=True)

    def _deliver_pending(self, message_id: UUID, *, chat_id: int, schema_name: str) -> None:
        """Attempt one delivery of one durable pending outgoing message."""
        self._select_tenant_schema(schema_name)
        message = self.session.get(Message, message_id)
        if (
            message is None
            or message.direction != "outgoing"
            or message.raw_payload.get("delivery_status") != "pending"
            or self.telegram_client is None
        ):
            return
        try:
            telegram_message_id = self.telegram_client.send_message(chat_id=chat_id, text=message.content)
        except Exception:
            self.session.rollback()
            self._select_tenant_schema(schema_name)
            message = self.session.get(Message, message_id)
            if message is not None and message.raw_payload.get("delivery_status") == "pending":
                message.raw_payload = {**message.raw_payload, "delivery_status": "failed"}
                self.session.commit()
            return

        message.raw_payload = {
            **message.raw_payload,
            "delivery_status": "sent",
            "telegram_message_id": telegram_message_id,
        }
        self.session.commit()

    def _select_tenant_schema(self, schema_name: str) -> None:
        if self.session.get_bind().dialect.name != "sqlite":
            self.session.execute(text(f'SET LOCAL search_path TO "{schema_name}", public'))


def _safe_traceback_locations(exc: Exception) -> str:
    """Return traceback locations without source text or exception values."""

    frames = traceback.extract_tb(exc.__traceback__)
    return " > ".join(
        f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
        for frame in frames
    ) or "unavailable"

"""Tenant-scoped Telegram intake and deterministic Booking Agent bridge.

Phase 8A.2 stops at durable, pending outbound messages.  It deliberately has no
Telegram client, network call, LLM, or outbound delivery capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.appointment_tools import AppointmentTools
from app.ai.availability_tools import AvailabilityTools
from app.ai.booking_agent import BookingAgent, BookingConversationRequest, BookingConversationResult
from app.ai.payment_tools import PaymentTools
from app.ai.pricing_tools import PricingTools
from app.ai.service_tools import ServiceTools
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


class BookingAgentInvoker(Protocol):
    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> BookingConversationResult: ...


class DeterministicBookingAgentInvoker:
    """Build the strictly allow-listed 7A.9 request from backend-owned state."""

    _required_state = (
        "patient_id", "payer_type", "payer_name", "plan_name", "preferred_date",
        "preferred_modality", "payment_method",
    )

    def __init__(self, session: Session) -> None:
        self._session = session

    def invoke(
        self, *, tenant_id: UUID, conversation: ConversationSession, message_text: str
    ) -> BookingConversationResult:
        state = conversation.state or {}
        missing = [key for key in self._required_state if not state.get(key)]
        if missing:
            raise ValueError("booking context is incomplete")

        request = BookingConversationRequest(
            tenant_id=tenant_id,
            patient_id=UUID(str(state["patient_id"])),
            service_query=message_text,
            payer_type=str(state["payer_type"]),
            payer_name=str(state["payer_name"]),
            plan_name=str(state["plan_name"]),
            preferred_date=date.fromisoformat(str(state["preferred_date"])),
            preferred_modality=str(state["preferred_modality"]),
            payment_method=str(state["payment_method"]),
            practitioner_name=_optional_text(state.get("practitioner_name")),
            location_id=_optional_uuid(state.get("location_id")),
            room_id=_optional_uuid(state.get("room_id")),
        )
        agent = BookingAgent(
            tenant_id=tenant_id,
            service_tools=ServiceTools(tenant_id=tenant_id, session=self._session),
            pricing_tools=PricingTools(tenant_id=tenant_id, session=self._session),
            availability_tools=AvailabilityTools(tenant_id=tenant_id, session=self._session),
            appointment_tools=AppointmentTools(tenant_id=tenant_id, session=self._session),
            payment_tools=PaymentTools(tenant_id=tenant_id, session=self._session),
        )
        return agent.run(request)


def _optional_text(value: object) -> str | None:
    return str(value) if value is not None else None


def _optional_uuid(value: object) -> UUID | None:
    return UUID(str(value)) if value is not None else None


@dataclass(slots=True)
class TelegramWebhookService:
    session: Session
    agent_invoker: BookingAgentInvoker | None = None

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
            result = (self.agent_invoker or DeterministicBookingAgentInvoker(self.session)).invoke(
                tenant_id=tenant.tenant_id,
                conversation=conversation,
                message_text=update.message.text,
            )
            content = f"BookingAgent: {result.status}"
            agent_status = result.status
        except Exception:
            # The webhook is an acknowledgement boundary. Details are intentionally
            # not persisted because they could contain schema or secret material.
            self.session.rollback()
            self._select_tenant_schema(tenant.schema_name)
            conversation = self.session.execute(select(ConversationSession).where(
                ConversationSession.channel_type == "telegram",
                ConversationSession.external_user_id == external_user_id,
            )).scalar_one()
            content = "BookingAgent: unable_to_process"
            agent_status = "error"

        self.session.add(Message(
            conversation_session_id=conversation.id,
            channel_type="telegram",
            external_message_id=f"agent:{update.update_id}",
            direction="outgoing",
            message_type="text",
            content=content,
            raw_payload={"delivery_status": "pending", "agent_status": agent_status,
                         "source_update_id": update.update_id},
        ))
        self.session.commit()
        return TelegramIntakeResult(accepted=True)

    def _select_tenant_schema(self, schema_name: str) -> None:
        if self.session.get_bind().dialect.name != "sqlite":
            self.session.execute(text(f'SET LOCAL search_path TO "{schema_name}", public'))

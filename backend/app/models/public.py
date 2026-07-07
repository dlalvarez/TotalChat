import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    schema_name: Mapped[str] = mapped_column(String(63), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    plan_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    channels: Mapped[list["TenantChannel"]] = relationship(back_populates="tenant")
    user_links: Mapped[list["UserTenant"]] = relationship(back_populates="tenant")


class TenantChannel(TimestampMixin, Base):
    __tablename__ = "tenant_channels"
    __table_args__ = (
        UniqueConstraint("channel_type", "external_identifier", name="uq_tenant_channels_lookup"),
        Index("ix_tenant_channels_tenant_id", "tenant_id"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    webhook_secret_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    tenant: Mapped[Tenant] = relationship(back_populates="channels")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    tenant_links: Mapped[list["UserTenant"]] = relationship(back_populates="user")


class UserTenant(TimestampMixin, Base):
    __tablename__ = "user_tenants"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("public.users.id"), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("public.tenants.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    user: Mapped[User] = relationship(back_populates="tenant_links")
    tenant: Mapped[Tenant] = relationship(back_populates="user_links")

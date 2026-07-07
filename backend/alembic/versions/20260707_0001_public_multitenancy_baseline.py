"""public multitenancy baseline

Revision ID: 20260707_0001
Revises:
Create Date: 2026-07-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260707_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("schema_name", sa.String(length=63), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("plan_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="public",
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True, schema="public")
    op.create_index("ix_tenants_schema_name", "tenants", ["schema_name"], unique=True, schema="public")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="public",
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, schema="public")

    op.create_table(
        "tenant_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column("external_identifier", sa.String(length=255), nullable=False),
        sa.Column("webhook_secret_hash", sa.String(length=255), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"]),
        sa.UniqueConstraint("channel_type", "external_identifier", name="uq_tenant_channels_lookup"),
        schema="public",
    )
    op.create_index("ix_tenant_channels_tenant_id", "tenant_channels", ["tenant_id"], schema="public")

    op.create_table(
        "user_tenants",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["public.users.id"]),
        sa.PrimaryKeyConstraint("user_id", "tenant_id"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("user_tenants", schema="public")
    op.drop_index("ix_tenant_channels_tenant_id", table_name="tenant_channels", schema="public")
    op.drop_table("tenant_channels", schema="public")
    op.drop_index("ix_users_email", table_name="users", schema="public")
    op.drop_table("users", schema="public")
    op.drop_index("ix_tenants_schema_name", table_name="tenants", schema="public")
    op.drop_index("ix_tenants_slug", table_name="tenants", schema="public")
    op.drop_table("tenants", schema="public")

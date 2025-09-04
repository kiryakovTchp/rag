"""add users, oauth tables, and usage with RLS

Revision ID: 20250904_add_users_oauth_usage
Revises: 20250127_add_answer_feedback
Create Date: 2025-09-04 03:45:00

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20250904_add_users_oauth_usage"
down_revision: Union[str, Sequence[str], None] = "20250127_add_answer_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=50), server_default="user", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    # OAuth accounts
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("account_id", sa.String(length=255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_accounts_tenant", "oauth_accounts", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_oauth_accounts_provider_account",
        "oauth_accounts",
        ["provider", "account_id"],
        unique=True,
    )

    # OAuth tokens
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["oauth_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_tokens_account_active",
        "oauth_tokens",
        ["account_id", "revoked_at"],
        unique=False,
    )

    # usage table
    op.create_table(
        "usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("queries_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "documents_processed", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column("tokens_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_usage_tenant_date", "usage", ["tenant_id", "date"], unique=False
    )

    # Enable RLS and add basic tenant policies (COALESCE style)
    op.execute("ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS users_tenant_isolation ON users")
    op.execute(
        """
        CREATE POLICY users_tenant_isolation ON users
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )

    op.execute("ALTER TABLE IF EXISTS usage ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS usage_tenant_isolation ON usage")
    op.execute(
        """
        CREATE POLICY usage_tenant_isolation ON usage
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )


def downgrade() -> None:
    # RLS cleanup
    op.execute("DROP POLICY IF EXISTS usage_tenant_isolation ON usage")
    op.execute("ALTER TABLE IF EXISTS usage DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS users_tenant_isolation ON users")
    op.execute("ALTER TABLE IF EXISTS users DISABLE ROW LEVEL SECURITY")

    # Drop usage
    op.drop_index("ix_usage_tenant_date", table_name="usage")
    op.drop_table("usage")

    # Drop oauth tokens/accounts
    op.drop_index("ix_oauth_tokens_account_active", table_name="oauth_tokens")
    op.drop_table("oauth_tokens")
    op.drop_index("ix_oauth_accounts_provider_account", table_name="oauth_accounts")
    op.drop_index("ix_oauth_accounts_tenant", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    # Drop users
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

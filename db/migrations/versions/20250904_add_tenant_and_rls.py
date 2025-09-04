"""add tenant_id columns and basic RLS policies

Revision ID: 20250904_add_tenant_and_rls
Revises: 33699f75c48d
Create Date: 2025-09-04 00:00:00

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250904_add_tenant_and_rls"
down_revision: Union[str, Sequence[str], None] = "20250904_add_users_oauth_usage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tenant_id columns
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
            sa.Column("tenant_id", sa.String(length=100), nullable=True)
        )
        batch_op.create_index("ix_documents_tenant_id", ["tenant_id"], unique=False)

    with op.batch_alter_table("elements") as batch_op:
        batch_op.add_column(
            sa.Column("tenant_id", sa.String(length=100), nullable=True)
        )
        batch_op.create_index("ix_elements_tenant_id", ["tenant_id"], unique=False)

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.add_column(
            sa.Column("tenant_id", sa.String(length=100), nullable=True)
        )
        batch_op.create_index("ix_chunks_tenant_id", ["tenant_id"], unique=False)

    # Enable RLS and add permissive policies (COALESCE-based) for multi-tenancy
    # Note: relies on app.current_tenant GUC set by application per-transaction
    op.execute("ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE IF EXISTS elements ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE IF EXISTS chunks ENABLE ROW LEVEL SECURITY")

    # Drop existing if any then create
    op.execute("DROP POLICY IF EXISTS documents_tenant_isolation ON documents")
    op.execute(
        """
        CREATE POLICY documents_tenant_isolation ON documents
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )

    op.execute("DROP POLICY IF EXISTS elements_tenant_isolation ON elements")
    op.execute(
        """
        CREATE POLICY elements_tenant_isolation ON elements
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )

    op.execute("DROP POLICY IF EXISTS chunks_tenant_isolation ON chunks")
    op.execute(
        """
        CREATE POLICY chunks_tenant_isolation ON chunks
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )


def downgrade() -> None:
    # Remove policies and disable RLS
    op.execute("DROP POLICY IF EXISTS chunks_tenant_isolation ON chunks")
    op.execute("DROP POLICY IF EXISTS elements_tenant_isolation ON elements")
    op.execute("DROP POLICY IF EXISTS documents_tenant_isolation ON documents")

    op.execute("ALTER TABLE IF EXISTS chunks DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE IF EXISTS elements DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE IF EXISTS documents DISABLE ROW LEVEL SECURITY")

    # Drop indexes and columns
    with op.batch_alter_table("chunks") as batch_op:
        batch_op.drop_index("ix_chunks_tenant_id")
        batch_op.drop_column("tenant_id")

    with op.batch_alter_table("elements") as batch_op:
        batch_op.drop_index("ix_elements_tenant_id")
        batch_op.drop_column("tenant_id")

    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_index("ix_documents_tenant_id")
        batch_op.drop_column("tenant_id")

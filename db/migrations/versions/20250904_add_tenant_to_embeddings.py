"""add tenant_id to embeddings and RLS

Revision ID: 20250904_add_tenant_to_embeddings
Revises: 20250904_add_tenant_and_rls
Create Date: 2025-09-04 00:15:00

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250904_add_tenant_to_embeddings"
down_revision: Union[str, Sequence[str], None] = "20250904_add_tenant_and_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("embeddings") as batch_op:
        batch_op.add_column(
            sa.Column("tenant_id", sa.String(length=100), nullable=True)
        )
        batch_op.create_index("ix_embeddings_tenant_id", ["tenant_id"], unique=False)

    # Enable RLS and add policy
    op.execute("ALTER TABLE IF EXISTS embeddings ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS embeddings_tenant_isolation ON embeddings")
    op.execute(
        """
        CREATE POLICY embeddings_tenant_isolation ON embeddings
        USING (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        WITH CHECK (COALESCE(tenant_id, '') = COALESCE(current_setting('app.current_tenant', true), ''))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS embeddings_tenant_isolation ON embeddings")
    op.execute("ALTER TABLE IF EXISTS embeddings DISABLE ROW LEVEL SECURITY")
    with op.batch_alter_table("embeddings") as batch_op:
        batch_op.drop_index("ix_embeddings_tenant_id")
        batch_op.drop_column("tenant_id")

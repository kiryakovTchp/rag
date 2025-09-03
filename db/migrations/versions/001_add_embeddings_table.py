"""add embeddings table

Revision ID: 001
Revises: 83821d6f3c19
Create Date: 2025-08-30 23:55:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = "83821d6f3c19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create embeddings table
    op.create_table(
        "embeddings",
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("vector", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )

    # Create index on provider for faster lookups
    op.create_index(
        op.f("ix_embeddings_provider"), "embeddings", ["provider"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_embeddings_provider"), table_name="embeddings")
    op.drop_table("embeddings")

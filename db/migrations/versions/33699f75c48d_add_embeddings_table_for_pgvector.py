"""add embeddings table for pgvector

Revision ID: 33699f75c48d
Revises: 6a53d52332f7
Create Date: 2025-08-31 01:24:48.801160

"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "33699f75c48d"
down_revision: Union[str, Sequence[str], None] = "6a53d52332f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure provider index exists
    # Create provider index if not exists (avoid transaction abort on duplicates)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_embeddings_provider ON embeddings(provider)"
    )

    # Convert vector column to proper pgvector type (with fallback)
    try:
        op.execute(
            "ALTER TABLE embeddings ALTER COLUMN vector TYPE vector(1024) USING (vector::vector)"
        )
    except Exception:
        # Fallback: recreate column if cast is not possible in current transaction
        op.execute("ALTER TABLE embeddings DROP COLUMN IF EXISTS vector")
        op.execute("ALTER TABLE embeddings ADD COLUMN vector vector(1024)")

    # Create vector index for similarity search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat
        ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop vector index
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_ivfflat")
    # Revert type back to text if needed
    try:
        op.execute("ALTER TABLE embeddings ALTER COLUMN vector TYPE text")
    except Exception:
        pass
    # Drop provider index if exists
    try:
        op.drop_index(op.f("ix_embeddings_provider"), table_name="embeddings")
    except Exception:
        pass

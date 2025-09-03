"""add pgvector extension

Revision ID: 6a53d52332f7
Revises: 001
Create Date: 2025-08-31 01:14:18.869405

"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a53d52332f7"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create index on embeddings vector column if table exists
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
        ON embeddings USING ivfflat (vector vector_cosine_ops)
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_embeddings_vector")

    # Note: We don't drop the vector extension as it might be used by other tables

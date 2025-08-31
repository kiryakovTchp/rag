"""add embeddings table for pgvector

Revision ID: 33699f75c48d
Revises: 6a53d52332f7
Create Date: 2025-08-31 01:24:48.801160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33699f75c48d'
down_revision: Union[str, Sequence[str], None] = '6a53d52332f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create embeddings table with proper vector type
    op.create_table('embeddings',
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('vector', sa.Text(), nullable=False),  # Will be converted to vector(1024)
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chunk_id')
    )

    # Create index on provider for faster lookups
    op.create_index(op.f('ix_embeddings_provider'), 'embeddings', ['provider'], unique=False)

    # Convert vector column to proper pgvector type
    op.execute("ALTER TABLE embeddings ALTER COLUMN vector TYPE vector(1024) USING (vector::vector)")

    # Create vector index for similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat
        ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop vector index
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_ivfflat")
    
    # Drop provider index
    op.drop_index(op.f('ix_embeddings_provider'), table_name='embeddings')
    
    # Drop table
    op.drop_table('embeddings')

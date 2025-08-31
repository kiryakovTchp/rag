"""add answer_logs table

Revision ID: 20250127_add_answer_logs
Revises: 33699f75c48d
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250127_add_answer_logs'
down_revision: Union[str, Sequence[str], None] = '33699f75c48d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('answer_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('in_tokens', sa.Integer(), nullable=True),
        sa.Column('out_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answer_logs_id'), 'answer_logs', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_answer_logs_id'), table_name='answer_logs')
    op.drop_table('answer_logs')

"""Add answer feedback table

Revision ID: 20250127_add_answer_feedback
Revises: 20250127_add_api_keys
Create Date: 2025-01-27 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250127_add_answer_feedback"
down_revision = "20250127_add_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create answer_feedback table
    op.create_table(
        "answer_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.String(length=100), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column(
            "rating", sa.Enum("up", "down", name="feedback_rating"), nullable=False
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "selected_citation_ids", postgresql.ARRAY(sa.Integer()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_answer_feedback_id"), "answer_feedback", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_answer_feedback_answer_id"),
        "answer_feedback",
        ["answer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_answer_feedback_tenant_id"),
        "answer_feedback",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_answer_feedback_user_id"), "answer_feedback", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_answer_feedback_user_id"), table_name="answer_feedback")
    op.drop_index(op.f("ix_answer_feedback_tenant_id"), table_name="answer_feedback")
    op.drop_index(op.f("ix_answer_feedback_answer_id"), table_name="answer_feedback")
    op.drop_index(op.f("ix_answer_feedback_id"), table_name="answer_feedback")

    # Drop table
    op.drop_table("answer_feedback")

    # Drop enum
    op.execute("DROP TYPE feedback_rating")

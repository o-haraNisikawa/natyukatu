"""Add participant count to participation history."""
from alembic import op
import sqlalchemy as sa

revision = "a3b7c91d42ef"
down_revision = "25c960cbd0dc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "participation_histories",
        sa.Column("participant_count", sa.Integer(), nullable=False, server_default="1")
    )


def downgrade():
    op.drop_column("participation_histories", "participant_count")

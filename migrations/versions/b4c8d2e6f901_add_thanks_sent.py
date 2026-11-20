"""Track whether a participant has received a thank-you point."""
from alembic import op
import sqlalchemy as sa

revision = "b4c8d2e6f901"
down_revision = "a3b7c91d42ef"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "participation_histories",
        sa.Column("thanks_sent", sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade():
    op.drop_column("participation_histories", "thanks_sent")

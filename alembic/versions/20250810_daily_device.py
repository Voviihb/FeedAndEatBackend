from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250810_daily_device"
down_revision = "20250810_tags"
branch_labels = None
depends_on = None

def upgrade():
    # daily_recipe
    op.create_table(
        "daily_recipe",
        sa.Column("day_of_year", sa.Integer(), primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # device_tokens
    op.create_table(
        "device_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_device_tokens_user", "device_tokens", ["user_id"])


def downgrade():
    op.drop_index("ix_device_tokens_user", table_name="device_tokens")
    op.drop_table("device_tokens")
    op.drop_table("daily_recipe") 
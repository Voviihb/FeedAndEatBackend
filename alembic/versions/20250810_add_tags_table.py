from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250810_tags"
down_revision = "20250810_trgm"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_tags_name_lower", "tags", [sa.text("lower(name)")], unique=True)


def downgrade():
    op.drop_index("ix_tags_name_lower", table_name="tags")
    op.drop_table("tags") 
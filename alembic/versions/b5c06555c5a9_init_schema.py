"""init schema

Revision ID: b5c06555c5a9
Revises: d444dd1117de
Create Date: 2025-08-10 12:01:55.835670

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b5c06555c5a9"
down_revision = "d444dd1117de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- recipes --------------------------------------------------------
    op.create_table(
        "recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("image_url", sa.String),

        sa.Column("instructions", postgresql.JSONB, nullable=False),
        sa.Column("servings",     postgresql.JSONB),
        sa.Column("ingredients",  postgresql.JSONB, nullable=False),
        sa.Column("tags",         postgresql.JSONB),
        sa.Column("nutrients",    postgresql.JSONB),

        sa.Column("rating",  sa.Float,   server_default="0"),
        sa.Column("cooked",  sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )

    # ---- association collection_recipes --------------------------------
    op.create_table(
        "collection_recipes",
        sa.Column("collection_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("collections.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recipes.id", ondelete="CASCADE"),
                  primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("collection_recipes")
    op.drop_table("recipes")
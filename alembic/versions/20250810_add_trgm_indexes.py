from alembic import op

# revision identifiers, used by Alembic.
revision = "20250810_trgm"
down_revision = "bbaa37c4e96b"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # pg_trgm для ILIKE
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # индекс по имени рецепта для ILIKE '%text%'
    op.execute("CREATE INDEX IF NOT EXISTS ix_recipes_name_trgm ON recipes USING gin (name gin_trgm_ops)")
    # индекс по тегам (GIN)
    op.execute("CREATE INDEX IF NOT EXISTS ix_recipes_tags_gin ON recipes USING gin (tags)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_recipes_tags_gin")
    op.execute("DROP INDEX IF EXISTS ix_recipes_name_trgm") 
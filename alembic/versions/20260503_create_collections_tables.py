"""create collections and collection_recipes tables

Revision ID: 20260503_collections
Revises: bbaa37c4e96b
Create Date: 2026-05-03 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260503_collections'
down_revision: Union[str, None] = '20250810_daily_device'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу collections только если её нет
    op.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            picture_url VARCHAR,
            created_at TIMESTAMP
        )
    """)

    # Создаём таблицу collection_recipes только если её нет
    op.execute("""
        CREATE TABLE IF NOT EXISTS collection_recipes (
            collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            PRIMARY KEY (collection_id, recipe_id)
        )
    """)


def downgrade() -> None:
    op.drop_table('collection_recipes')
    op.drop_table('collections')

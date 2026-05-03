"""collections

Revision ID: bbaa37c4e96b
Revises: b5c06555c5a9
Create Date: 2025-08-10 12:33:37.625137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bbaa37c4e96b'
down_revision: Union[str, None] = 'b5c06555c5a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('picture_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'collection_recipes',
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('collections.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('collection_recipes')
    op.drop_table('collections')

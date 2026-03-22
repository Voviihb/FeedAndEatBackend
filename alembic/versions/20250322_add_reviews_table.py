"""add reviews table

Revision ID: 20250322_add_reviews
Revises: 20250810_daily_device
Create Date: 2025-03-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250322_add_reviews'
down_revision = '20250810_daily_device'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mark', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recipe_id', 'user_id', name='uq_review_recipe_user'),
    )
    op.create_index('ix_reviews_recipe_id', 'reviews', ['recipe_id'])
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_reviews_user_id', table_name='reviews')
    op.drop_index('ix_reviews_recipe_id', table_name='reviews')
    op.drop_table('reviews')

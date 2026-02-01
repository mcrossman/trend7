"""Add section and confidence columns to trend tables

Revision ID: add_section_confidence_columns
Revises: d1fbc9bc34d5
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_section_confidence_columns'
down_revision = 'd1fbc9bc34d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to trend_article_matches table
    op.add_column('trend_article_matches', sa.Column('story_score', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('trend_article_matches', sa.Column('section', sa.String(length=50), nullable=True))
    
    # Add columns to proactive_feed_queue table
    op.add_column('proactive_feed_queue', sa.Column('overall_confidence', sa.Float(), nullable=True))
    op.add_column('proactive_feed_queue', sa.Column('confidence_level', sa.String(length=20), nullable=True))
    op.add_column('proactive_feed_queue', sa.Column('sections_involved', sa.Integer(), nullable=True))
    op.add_column('proactive_feed_queue', sa.Column('total_articles', sa.Integer(), nullable=True))
    
    # Create index on section column
    op.create_index('idx_matches_section', 'trend_article_matches', ['section'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_matches_section', table_name='trend_article_matches')
    
    # Drop columns from proactive_feed_queue
    op.drop_column('proactive_feed_queue', 'total_articles')
    op.drop_column('proactive_feed_queue', 'sections_involved')
    op.drop_column('proactive_feed_queue', 'confidence_level')
    op.drop_column('proactive_feed_queue', 'overall_confidence')
    
    # Drop columns from trend_article_matches
    op.drop_column('trend_article_matches', 'section')
    op.drop_column('trend_article_matches', 'story_score')

"""Add insights tracking tables for parent dashboard.

Revision ID: 005
Revises: 004
Create Date: 2025-01-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create message_insights table to track per-message analytics
    op.create_table(
        'message_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('topic', sa.String(100), nullable=True),  # Main topic of the message
        sa.Column('is_learning_question', sa.Boolean, nullable=False, default=False),  # True if why/how question
        sa.Column('estimated_time_seconds', sa.Integer, nullable=False, default=0),  # Estimated engagement time
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_message_insights_message_id', 'message_insights', ['message_id'])
    op.create_index('ix_message_insights_topic', 'message_insights', ['topic'])

    # Create child_topic_summary table for aggregated topic insights
    op.create_table(
        'child_topic_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('children.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('total_time_seconds', sa.Integer, nullable=False, default=0),
        sa.Column('message_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_accessed', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('child_id', 'topic', name='uix_child_topic')
    )
    op.create_index('ix_child_topic_summary_child_id', 'child_topic_summary', ['child_id'])
    op.create_index('ix_child_topic_summary_total_time', 'child_topic_summary', ['total_time_seconds'])

    # Create child_weekly_insights table for weekly highlights
    op.create_table(
        'child_weekly_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('children.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_start', sa.Date, nullable=False),  # Start of the week (Monday)
        sa.Column('top_topics', postgresql.JSONB, nullable=False, default=[]),  # List of {topic, time_seconds}
        sa.Column('total_learning_questions', sa.Integer, nullable=False, default=0),
        sa.Column('total_questions', sa.Integer, nullable=False, default=0),
        sa.Column('new_curiosities', postgresql.JSONB, nullable=False, default=[]),  # Topics accessed for first time
        sa.Column('needs_support_topics', postgresql.JSONB, nullable=False, default=[]),  # Topics with repeated questions
        sa.Column('suggested_discussion_topic', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('child_id', 'week_start', name='uix_child_week')
    )
    op.create_index('ix_child_weekly_insights_child_id', 'child_weekly_insights', ['child_id'])
    op.create_index('ix_child_weekly_insights_week_start', 'child_weekly_insights', ['week_start'])


def downgrade() -> None:
    op.drop_table('child_weekly_insights')
    op.drop_table('child_topic_summary')
    op.drop_table('message_insights')

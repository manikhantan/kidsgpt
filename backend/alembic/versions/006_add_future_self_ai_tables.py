"""Add Future Self AI tables for timeline tracking and future identity.

Revision ID: 006
Revises: 005
Create Date: 2025-11-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create future_identities table
    op.create_table(
        'future_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('children.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('future_identity', sa.String(100), nullable=False),
        sa.Column('breakthrough_age', sa.Integer, nullable=False),
        sa.Column('first_ambition', sa.String(500), nullable=False),
        sa.Column('timeline_compression', sa.Float, nullable=False, default=0.0),
        sa.Column('thinking_age', sa.Float, nullable=False),
        sa.Column('current_age', sa.Integer, nullable=False),
        sa.Column('trajectory', sa.String(20), nullable=False, default='steady'),
        sa.Column('revealed_achievements', postgresql.JSONB, nullable=False, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_future_identities_child_id', 'future_identities', ['child_id'])

    # Create timeline_events table
    op.create_table(
        'timeline_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('future_identity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('future_identities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_learned', sa.String(200), nullable=False),
        sa.Column('normal_learning_age', sa.Integer, nullable=False),
        sa.Column('actual_age', sa.Integer, nullable=False),
        sa.Column('years_compressed', sa.Float, nullable=False),
        sa.Column('complexity_score', sa.Float, nullable=True),
        sa.Column('context', sa.Text, nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_timeline_events_future_identity_id', 'timeline_events', ['future_identity_id'])
    op.create_index('ix_timeline_events_created_at', 'timeline_events', ['created_at'])

    # Create future_slip_type enum (if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE future_slip_type AS ENUM (
                'achievement', 'event', 'creation', 'ted_talk',
                'patent', 'company', 'breakthrough', 'innovation'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create future_slips table
    op.create_table(
        'future_slips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('future_identity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('future_identities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slip_type', sa.Enum('achievement', 'event', 'creation', 'ted_talk', 'patent', 'company', 'breakthrough', 'innovation', name='future_slip_type'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('supposed_year', sa.Integer, nullable=False),
        sa.Column('context', sa.Text, nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revealed_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_future_slips_future_identity_id', 'future_slips', ['future_identity_id'])
    op.create_index('ix_future_slips_revealed_at', 'future_slips', ['revealed_at'])


def downgrade() -> None:
    op.drop_table('future_slips')
    op.execute("DROP TYPE future_slip_type")
    op.drop_table('timeline_events')
    op.drop_table('future_identities')

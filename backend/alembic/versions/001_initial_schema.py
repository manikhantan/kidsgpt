"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create parents table
    op.create_table(
        'parents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parents_email'), 'parents', ['email'], unique=True)

    # Create children table
    op.create_table(
        'children',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_children_parent_id'), 'children', ['parent_id'], unique=False)
    op.create_index(op.f('ix_children_username'), 'children', ['username'], unique=True)

    # Create content_rules table
    op.create_table(
        'content_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.Enum('allowlist', 'blocklist', name='contentrulemode'), nullable=False),
        sa.Column('topics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_id')
    )

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_child_id'), 'chat_sessions', ['child_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('blocked', sa.Boolean(), nullable=False),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_session_id'), 'messages', ['session_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index(op.f('ix_messages_session_id'), table_name='messages')
    op.drop_table('messages')

    op.drop_index(op.f('ix_chat_sessions_child_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')

    op.drop_table('content_rules')

    op.drop_index(op.f('ix_children_username'), table_name='children')
    op.drop_index(op.f('ix_children_parent_id'), table_name='children')
    op.drop_table('children')

    op.drop_index(op.f('ix_parents_email'), table_name='parents')
    op.drop_table('parents')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS contentrulemode')
    op.execute('DROP TYPE IF EXISTS messagerole')

"""add_parent_chat_tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create parent_chat_sessions table
    op.create_table(
        'parent_chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('parents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=True, default='New Chat'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
    )

    # Create indexes for parent_chat_sessions
    op.create_index('ix_parent_chat_sessions_parent_id', 'parent_chat_sessions', ['parent_id'])
    op.create_index('ix_parent_chat_sessions_parent_last_message', 'parent_chat_sessions', ['parent_id', 'last_message_at'])

    # Create parent_messages table (this will auto-create the ENUM)
    op.create_table(
        'parent_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('parent_chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', postgresql.ENUM('user', 'assistant', name='messagerole', create_type=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create index for parent_messages
    op.create_index('ix_parent_messages_session_id', 'parent_messages', ['session_id'])


def downgrade() -> None:
    # Drop parent_messages table
    op.drop_index('ix_parent_messages_session_id', table_name='parent_messages')
    op.drop_table('parent_messages')

    # Drop parent_chat_sessions table
    op.drop_index('ix_parent_chat_sessions_parent_last_message', table_name='parent_chat_sessions')
    op.drop_index('ix_parent_chat_sessions_parent_id', table_name='parent_chat_sessions')
    op.drop_table('parent_chat_sessions')

    # Drop the ENUM type
    postgresql.ENUM(name='messagerole').drop(op.get_bind(), checkfirst=True)
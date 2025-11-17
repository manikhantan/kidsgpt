"""add_chat_session_title_and_tracking

Revision ID: 002
Revises: 0a98b73a47a7
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '0a98b73a47a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add title column to chat_sessions
    op.add_column('chat_sessions', sa.Column('title', sa.String(255), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE chat_sessions SET title = 'New Chat' WHERE title IS NULL")

    # Add last_message_at column
    op.add_column('chat_sessions', sa.Column('last_message_at', sa.DateTime(), nullable=True))

    # Add message_count column
    op.add_column('chat_sessions', sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'))

    # Update last_message_at and message_count for existing sessions
    op.execute("""
        UPDATE chat_sessions cs
        SET last_message_at = (
            SELECT MAX(created_at) FROM messages WHERE session_id = cs.id
        ),
        message_count = (
            SELECT COUNT(*) FROM messages WHERE session_id = cs.id
        )
    """)

    # Create composite index for efficient queries
    op.create_index(
        'ix_chat_sessions_child_last_message',
        'chat_sessions',
        ['child_id', 'last_message_at']
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index('ix_chat_sessions_child_last_message', table_name='chat_sessions')

    # Drop message_count column
    op.drop_column('chat_sessions', 'message_count')

    # Drop last_message_at column
    op.drop_column('chat_sessions', 'last_message_at')

    # Drop title column
    op.drop_column('chat_sessions', 'title')

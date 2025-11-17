"""Add role column to messages table

Revision ID: 004
Revises: 003
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the messagerole enum type if it doesn't exist
    # (it should already exist from initial migration, but we check to be safe)
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'messagerole'")
    )
    if result.fetchone() is None:
        op.execute("CREATE TYPE messagerole AS ENUM ('user', 'assistant')")

    # Add role column to messages table
    # First add as nullable, then update existing rows, then make not null
    op.add_column(
        'messages',
        sa.Column('role', sa.Enum('user', 'assistant', name='messagerole', create_type=False), nullable=True)
    )

    # Set default role for any existing messages without role
    # Assuming existing messages without a role were user messages
    op.execute("UPDATE messages SET role = 'user' WHERE role IS NULL")

    # Now make the column NOT NULL
    op.alter_column('messages', 'role', nullable=False)


def downgrade() -> None:
    op.drop_column('messages', 'role')

"""replace_username_with_email_in_children

Revision ID: 0a98b73a47a7
Revises: 001
Create Date: 2025-11-16 23:45:33.623344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a98b73a47a7'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the username index
    op.drop_index('ix_children_username', table_name='children')

    # Drop the username column
    op.drop_column('children', 'username')

    # Add email column
    op.add_column('children', sa.Column('email', sa.String(255), nullable=False))

    # Create unique index on email
    op.create_index(op.f('ix_children_email'), 'children', ['email'], unique=True)


def downgrade() -> None:
    # Drop email index
    op.drop_index(op.f('ix_children_email'), table_name='children')

    # Drop email column
    op.drop_column('children', 'email')

    # Add username column back
    op.add_column('children', sa.Column('username', sa.String(50), nullable=False))

    # Create username index back
    op.create_index(op.f('ix_children_username'), 'children', ['username'], unique=True)

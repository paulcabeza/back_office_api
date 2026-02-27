"""add_must_change_password_to_users

Revision ID: c9f3a5e71b24
Revises: b7e2d4f10a83
Create Date: 2026-02-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c9f3a5e71b24'
down_revision: Union[str, None] = 'b7e2d4f10a83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column with server_default so existing rows get a value
    op.add_column(
        'users',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='true'),
    )
    # Existing users already have a password, so set them to false
    op.execute("UPDATE users SET must_change_password = false")
    # Remove server_default so new inserts use the ORM default (True)
    op.alter_column('users', 'must_change_password', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'must_change_password')

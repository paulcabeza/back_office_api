"""add_username_to_users

Revision ID: b7e2d4f10a83
Revises: a3f1c8d92e01
Create Date: 2026-02-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7e2d4f10a83'
down_revision: Union[str, None] = 'a3f1c8d92e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_unique_constraint('uq_users_tenant_username', 'users', ['tenant_id', 'username'])


def downgrade() -> None:
    op.drop_constraint('uq_users_tenant_username', 'users', type_='unique')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'username')

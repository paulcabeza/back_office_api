"""add_created_by_user_id_to_affiliates

Revision ID: a3f1c8d92e01
Revises: 1a460bf62676
Create Date: 2026-02-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3f1c8d92e01'
down_revision: Union[str, None] = '1a460bf62676'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'affiliates',
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_affiliates_created_by_user',
        'affiliates',
        'users',
        ['created_by_user_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_affiliates_created_by_user', 'affiliates', type_='foreignkey')
    op.drop_column('affiliates', 'created_by_user_id')

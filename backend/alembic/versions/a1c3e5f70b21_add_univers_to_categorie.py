"""add univers to categorie

Revision ID: a1c3e5f70b21
Revises: 13f2b08e55ed
Create Date: 2026-11-10 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f70b21'
down_revision: Union[str, None] = '13f2b08e55ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

univers_enum = sa.Enum('meubles', 'ceramique', 'papeterie', name='univers_enum')


def upgrade() -> None:
    univers_enum.create(op.get_bind(), checkfirst=True)
    # server_default makes existing rows valid; every current category is furniture
    op.add_column(
        'categorie',
        sa.Column('univers', univers_enum, nullable=False, server_default='meubles'),
    )
    op.alter_column('categorie', 'univers', server_default=None)


def downgrade() -> None:
    op.drop_column('categorie', 'univers')
    univers_enum.drop(op.get_bind(), checkfirst=True)

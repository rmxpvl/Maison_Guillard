"""add dimensions and teinte_couleur to ligne_demande

Revision ID: f6b8d0e25a76
Revises: e5a7c9d14f65
Create Date: 2026-11-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6b8d0e25a76'
down_revision: Union[str, None] = 'e5a7c9d14f65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ligne_demande', sa.Column('dimensions', sa.String(), nullable=True))
    op.add_column('ligne_demande', sa.Column('teinte_couleur', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('ligne_demande', 'teinte_couleur')
    op.drop_column('ligne_demande', 'dimensions')

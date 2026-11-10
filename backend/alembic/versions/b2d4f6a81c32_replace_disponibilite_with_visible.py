"""replace disponibilite with visible

Revision ID: b2d4f6a81c32
Revises: a1c3e5f70b21
Create Date: 2026-11-10 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d4f6a81c32'
down_revision: Union[str, None] = 'a1c3e5f70b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

disponibilite_enum = sa.Enum('disponible', 'rupture', 'sur_commande', name='disponibilite_enum')


def upgrade() -> None:
    op.add_column(
        'produit',
        sa.Column('visible', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.drop_column('produit', 'disponibilite')
    disponibilite_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    disponibilite_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'produit',
        sa.Column('disponibilite', disponibilite_enum, nullable=False, server_default='disponible'),
    )
    op.drop_column('produit', 'visible')

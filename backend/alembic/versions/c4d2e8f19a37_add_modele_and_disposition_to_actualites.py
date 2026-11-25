"""add modele to actualite and disposition to photo_actualite

Revision ID: c4d2e8f19a37
Revises: b9e1a3b58da9
Create Date: 2026-11-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d2e8f19a37'
down_revision: Union[str, None] = 'b9e1a3b58da9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing posts keep the layout they had: cover on top, the other photos under it.
    op.add_column('actualite', sa.Column('modele', sa.String(), server_default='classique', nullable=False))
    op.add_column('photo_actualite', sa.Column('disposition', sa.String(), server_default='demi', nullable=False))


def downgrade() -> None:
    op.drop_column('photo_actualite', 'disposition')
    op.drop_column('actualite', 'modele')

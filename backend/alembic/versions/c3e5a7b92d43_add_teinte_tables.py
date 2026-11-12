"""add teinte tables

Revision ID: c3e5a7b92d43
Revises: b2d4f6a81c32
Create Date: 2026-11-10 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e5a7b92d43'
down_revision: Union[str, None] = 'b2d4f6a81c32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teinte',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('ordre', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_teinte_id'), 'teinte', ['id'], unique=False)
    op.create_table(
        'produit_teinte',
        sa.Column('produit_id', sa.Integer(), nullable=False),
        sa.Column('teinte_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['produit_id'], ['produit.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teinte_id'], ['teinte.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('produit_id', 'teinte_id'),
    )


def downgrade() -> None:
    op.drop_table('produit_teinte')
    op.drop_index(op.f('ix_teinte_id'), table_name='teinte')
    op.drop_table('teinte')

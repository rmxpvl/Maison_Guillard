"""add actualites, photo_actualite and contenu_site

Revision ID: b9e1a3b58da9
Revises: a8d0f2a47c98
Create Date: 2026-11-12 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9e1a3b58da9'
down_revision: Union[str, None] = 'a8d0f2a47c98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'actualite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titre', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('contenu', sa.Text(), nullable=False),
        sa.Column('publiee', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('date_publication', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_actualite_id'), 'actualite', ['id'], unique=False)
    op.create_index(op.f('ix_actualite_slug'), 'actualite', ['slug'], unique=True)
    op.create_table(
        'photo_actualite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actualite_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('legende', sa.String(), nullable=True),
        sa.Column('ordre', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['actualite_id'], ['actualite.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_photo_actualite_id'), 'photo_actualite', ['id'], unique=False)
    op.create_index(op.f('ix_photo_actualite_actualite_id'), 'photo_actualite', ['actualite_id'], unique=False)
    op.create_table(
        'contenu_site',
        sa.Column('cle', sa.String(), nullable=False),
        sa.Column('texte', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('cle'),
    )


def downgrade() -> None:
    op.drop_table('contenu_site')
    op.drop_index(op.f('ix_photo_actualite_actualite_id'), table_name='photo_actualite')
    op.drop_index(op.f('ix_photo_actualite_id'), table_name='photo_actualite')
    op.drop_table('photo_actualite')
    op.drop_index(op.f('ix_actualite_slug'), table_name='actualite')
    op.drop_index(op.f('ix_actualite_id'), table_name='actualite')
    op.drop_table('actualite')

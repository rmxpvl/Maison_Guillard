"""add reglages du devis, message_type and compteur_devis

Revision ID: e5a7c9d14f65
Revises: d4f6b8c03e54
Create Date: 2026-11-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a7c9d14f65'
down_revision: Union[str, None] = 'd4f6b8c03e54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'parametre',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom_commercial', sa.String(), nullable=False),
        sa.Column('nom_legal', sa.String(), nullable=False),
        sa.Column('adresse', sa.String(), nullable=False),
        sa.Column('siret', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('telephone', sa.String(), nullable=False),
        sa.Column('prenom_signature', sa.String(), nullable=False),
        sa.Column('mention_tva', sa.String(), nullable=False),
        sa.Column('validite_jours', sa.Integer(), nullable=False),
        sa.Column('frais_meubles', sa.Numeric(10, 2), nullable=False),
        sa.Column('frais_ceramique', sa.Numeric(10, 2), nullable=False),
        sa.Column('frais_papeterie', sa.Numeric(10, 2), nullable=False),
        sa.Column('cond_paiement', sa.Text(), nullable=False),
        sa.Column('cond_fabrication', sa.Text(), nullable=False),
        sa.Column('cond_annulation', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'message_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titre', sa.String(), nullable=False),
        sa.Column('texte', sa.Text(), nullable=False),
        sa.Column('ordre', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_message_type_id'), 'message_type', ['id'], unique=False)
    op.create_table(
        'compteur_devis',
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('dernier', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('annee'),
    )


def downgrade() -> None:
    op.drop_table('compteur_devis')
    op.drop_index(op.f('ix_message_type_id'), table_name='message_type')
    op.drop_table('message_type')
    op.drop_table('parametre')

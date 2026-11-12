"""replace commande and devis with demande

Revision ID: d4f6b8c03e54
Revises: c3e5a7b92d43
Create Date: 2026-11-10 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f6b8c03e54'
down_revision: Union[str, None] = 'c3e5a7b92d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

statut_demande_enum = sa.Enum(
    'nouvelle', 'devis_envoye', 'payee', 'en_fabrication', 'expediee', 'livree',
    'refusee', 'expiree', 'annulee', name='statut_demande_enum',
)


def upgrade() -> None:
    # No production data to carry over: v1 was never online (spec §6).
    op.drop_index(op.f('ix_ligne_commande_id'), table_name='ligne_commande')
    op.drop_table('ligne_commande')
    op.drop_index(op.f('ix_commande_id'), table_name='commande')
    op.drop_table('commande')
    op.drop_index(op.f('ix_devis_id'), table_name='devis')
    op.drop_table('devis')
    op.drop_table('parametre')
    sa.Enum(name='statut_commande_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='statut_devis_enum').drop(op.get_bind(), checkfirst=True)

    op.create_table(
        'demande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jeton', sa.String(), nullable=False),
        sa.Column('statut', statut_demande_enum, nullable=False),
        sa.Column('nom_client', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('adresse', sa.String(), nullable=True),
        sa.Column('message_client', sa.String(), nullable=True),
        sa.Column('description_projet', sa.String(), nullable=True),
        sa.Column('produit_reference_id', sa.Integer(), nullable=True),
        sa.Column('frais_livraison', sa.Numeric(10, 2), nullable=True),
        sa.Column('message_artisane', sa.String(), nullable=True),
        sa.Column('numero_devis', sa.String(), nullable=True),
        sa.Column('version_devis', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('devis_envoye_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expire_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('devis_snapshot', sa.JSON(), nullable=True),
        sa.Column('cgv_acceptees_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cgv_version', sa.String(), nullable=True),
        sa.Column('stripe_session_id', sa.String(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
        sa.Column('montant_paye', sa.Numeric(10, 2), nullable=True),
        sa.Column('payee_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_limite', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rembourse_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['produit_reference_id'], ['produit.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_devis'),
    )
    op.create_index(op.f('ix_demande_id'), 'demande', ['id'], unique=False)
    op.create_index(op.f('ix_demande_jeton'), 'demande', ['jeton'], unique=True)
    op.create_table(
        'ligne_demande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demande_id', sa.Integer(), nullable=False),
        sa.Column('produit_id', sa.Integer(), nullable=True),
        sa.Column('libelle', sa.String(), nullable=False),
        sa.Column('quantite', sa.Integer(), nullable=False),
        sa.Column('teinte_id', sa.Integer(), nullable=True),
        sa.Column('teinte_nom', sa.String(), nullable=True),
        sa.Column('souhait', sa.String(), nullable=True),
        sa.Column('prix_indicatif', sa.Numeric(10, 2), nullable=True),
        sa.Column('prix_final', sa.Numeric(10, 2), nullable=True),
        sa.ForeignKeyConstraint(['demande_id'], ['demande.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['produit_id'], ['produit.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['teinte_id'], ['teinte.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ligne_demande_id'), 'ligne_demande', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ligne_demande_id'), table_name='ligne_demande')
    op.drop_table('ligne_demande')
    op.drop_index(op.f('ix_demande_jeton'), table_name='demande')
    op.drop_index(op.f('ix_demande_id'), table_name='demande')
    op.drop_table('demande')
    statut_demande_enum.drop(op.get_bind(), checkfirst=True)

    op.create_table(
        'parametre',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_commande_actif', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'devis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom_client', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('produit_id', sa.Integer(), nullable=True),
        sa.Column('description_projet', sa.String(), nullable=False),
        sa.Column('statut', sa.Enum('nouveau', 'en_discussion', 'accepte', 'refuse', name='statut_devis_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['produit_id'], ['produit.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_devis_id'), 'devis', ['id'], unique=False)
    op.create_table(
        'commande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom_client', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('adresse', sa.String(), nullable=False),
        sa.Column('statut', sa.Enum('en_attente', 'confirmee', 'expediee', 'livree', 'annulee', name='statut_commande_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_commande_id'), 'commande', ['id'], unique=False)
    op.create_table(
        'ligne_commande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('commande_id', sa.Integer(), nullable=False),
        sa.Column('produit_id', sa.Integer(), nullable=False),
        sa.Column('quantite', sa.Integer(), nullable=False),
        sa.Column('prix_unitaire_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['commande_id'], ['commande.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['produit_id'], ['produit.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ligne_commande_id'), 'ligne_commande', ['id'], unique=False)

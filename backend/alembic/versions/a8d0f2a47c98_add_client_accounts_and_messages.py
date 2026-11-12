"""add client accounts, link tokens and message_demande

Revision ID: a8d0f2a47c98
Revises: f6b8d0e25a76
Create Date: 2026-11-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d0f2a47c98'
down_revision: Union[str, None] = 'f6b8d0e25a76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'client',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('email_verifie_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_client_id'), 'client', ['id'], unique=False)
    op.create_index(op.f('ix_client_email'), 'client', ['email'], unique=True)
    op.create_table(
        'jeton_client',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('activation', 'reinitialisation', name='type_jeton_enum'), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expire_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('utilise_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_jeton_client_id'), 'jeton_client', ['id'], unique=False)
    op.create_index(op.f('ix_jeton_client_token_hash'), 'jeton_client', ['token_hash'], unique=True)
    op.create_table(
        'message_demande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demande_id', sa.Integer(), nullable=False),
        sa.Column('auteur', sa.Enum('client', 'artisane', name='auteur_message_enum'), nullable=False),
        sa.Column('texte', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('lu_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['demande_id'], ['demande.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_message_demande_id'), 'message_demande', ['id'], unique=False)
    op.create_index(op.f('ix_message_demande_demande_id'), 'message_demande', ['demande_id'], unique=False)
    op.add_column('demande', sa.Column('client_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_demande_client_id'), 'demande', ['client_id'], unique=False)
    op.create_foreign_key('fk_demande_client_id', 'demande', 'client', ['client_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_demande_client_id', 'demande', type_='foreignkey')
    op.drop_index(op.f('ix_demande_client_id'), table_name='demande')
    op.drop_column('demande', 'client_id')
    op.drop_index(op.f('ix_message_demande_demande_id'), table_name='message_demande')
    op.drop_index(op.f('ix_message_demande_id'), table_name='message_demande')
    op.drop_table('message_demande')
    sa.Enum(name='auteur_message_enum').drop(op.get_bind(), checkfirst=True)
    op.drop_index(op.f('ix_jeton_client_token_hash'), table_name='jeton_client')
    op.drop_index(op.f('ix_jeton_client_id'), table_name='jeton_client')
    op.drop_table('jeton_client')
    sa.Enum(name='type_jeton_enum').drop(op.get_bind(), checkfirst=True)
    op.drop_index(op.f('ix_client_email'), table_name='client')
    op.drop_index(op.f('ix_client_id'), table_name='client')
    op.drop_table('client')

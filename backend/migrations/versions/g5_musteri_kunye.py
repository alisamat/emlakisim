"""musteri kunye alani

Revision ID: g5_musteri_kunye
Revises: g4_emlakci_profil
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'g5_musteri_kunye'
down_revision = 'g4_emlakci_profil'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('musteri', sa.Column('kunye', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('musteri', 'kunye')

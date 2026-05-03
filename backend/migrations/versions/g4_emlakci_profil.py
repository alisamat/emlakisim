"""emlakci profil bilgileri — unvan, slogan, logo, adres, gorunum

Revision ID: g4_emlakci_profil
Revises: g3_emlakci_slug
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'g4_emlakci_profil'
down_revision = 'g3_emlakci_slug'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('emlakci', sa.Column('unvan', sa.String(100), nullable=True))
    op.add_column('emlakci', sa.Column('slogan', sa.String(200), nullable=True))
    op.add_column('emlakci', sa.Column('logo_url', sa.Text(), nullable=True))
    op.add_column('emlakci', sa.Column('adres', sa.Text(), nullable=True))
    op.add_column('emlakci', sa.Column('telefon2', sa.String(20), nullable=True))
    op.add_column('emlakci', sa.Column('website', sa.String(200), nullable=True))
    op.add_column('emlakci', sa.Column('sosyal_medya', sa.JSON(), nullable=True))
    op.add_column('emlakci', sa.Column('ruhsat_no', sa.String(50), nullable=True))
    op.add_column('emlakci', sa.Column('vergi_no', sa.String(20), nullable=True))
    op.add_column('emlakci', sa.Column('profil_gorunum', sa.JSON(), nullable=True))


def downgrade():
    for col in ['unvan', 'slogan', 'logo_url', 'adres', 'telefon2', 'website', 'sosyal_medya', 'ruhsat_no', 'vergi_no', 'profil_gorunum']:
        op.drop_column('emlakci', col)

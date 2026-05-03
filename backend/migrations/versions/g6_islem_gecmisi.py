"""islem_gecmisi tablosu — geri alma destekli islem log

Revision ID: g6_islem_gecmisi
Revises: g5_musteri_kunye
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'g6_islem_gecmisi'
down_revision = 'g5_musteri_kunye'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('islem_gecmisi',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('emlakci_id', sa.Integer(), sa.ForeignKey('emlakci.id'), nullable=False),
        sa.Column('islem', sa.String(30), nullable=False),
        sa.Column('tablo', sa.String(30)),
        sa.Column('kayit_id', sa.Integer()),
        sa.Column('ozet', sa.String(300)),
        sa.Column('onceki_veri', sa.JSON()),
        sa.Column('yeni_veri', sa.JSON()),
        sa.Column('geri_alindi', sa.Boolean(), default=False),
        sa.Column('olusturma', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('islem_gecmisi')

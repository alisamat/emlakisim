"""talep tablosu — müşteri talebi ayrı modül

Revision ID: g7_talep
Revises: g6_islem_gecmisi
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'g7_talep'
down_revision = 'g6_islem_gecmisi'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('talep',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('emlakci_id', sa.Integer(), sa.ForeignKey('emlakci.id'), nullable=False),
        sa.Column('musteri_id', sa.Integer(), sa.ForeignKey('musteri.id'), nullable=True),
        sa.Column('yonu', sa.String(10), default='arayan'),
        sa.Column('islem_turu', sa.String(10)),
        sa.Column('butce_min', sa.Float(), nullable=True),
        sa.Column('butce_max', sa.Float(), nullable=True),
        sa.Column('tercih_oda', sa.String(10), nullable=True),
        sa.Column('tercih_sehir', sa.String(50), nullable=True),
        sa.Column('tercih_ilce', sa.String(50), nullable=True),
        sa.Column('tercih_tip', sa.String(20), nullable=True),
        sa.Column('istenen', sa.JSON(), nullable=True),
        sa.Column('istenmeyen', sa.JSON(), nullable=True),
        sa.Column('mulk_id', sa.Integer(), sa.ForeignKey('mulk.id'), nullable=True),
        sa.Column('durum', sa.String(15), default='aktif'),
        sa.Column('notlar', sa.Text(), nullable=True),
        sa.Column('olusturma', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('talep')

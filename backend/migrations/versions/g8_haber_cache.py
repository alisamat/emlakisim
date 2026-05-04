"""haber_cache tablosu — RSS haber cache

Revision ID: g8_haber_cache
Revises: g7_talep
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'g8_haber_cache'
down_revision = 'g7_talep'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('haber_cache',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('baslik', sa.String(500), nullable=False),
        sa.Column('kaynak', sa.String(100)),
        sa.Column('url', sa.Text()),
        sa.Column('ozet', sa.Text()),
        sa.Column('tarih', sa.DateTime()),
        sa.Column('kategori', sa.String(50)),
        sa.Column('olusturma', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('haber_cache')

"""mulk resimler ve musteri_id alanlari

Revision ID: g1_mulk_resimler
Revises: f68c57f4836b
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'g1_mulk_resimler'
down_revision = 'e7a0be6e1b05'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mulk', sa.Column('resimler', sa.JSON(), nullable=True))
    op.add_column('mulk', sa.Column('musteri_id', sa.Integer(), sa.ForeignKey('musteri.id'), nullable=True))


def downgrade():
    op.drop_column('mulk', 'resimler')
    op.drop_column('mulk', 'musteri_id')

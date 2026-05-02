"""teklif tablosu ve musteri dogum_tarihi

Revision ID: g2_teklif_dogum
Revises: g1_mulk_resimler
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'g2_teklif_dogum'
down_revision = 'g1_mulk_resimler'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('musteri', sa.Column('dogum_tarihi', sa.Date(), nullable=True))
    op.create_table('teklif',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('emlakci_id', sa.Integer(), sa.ForeignKey('emlakci.id'), nullable=False),
        sa.Column('mulk_id', sa.Integer(), sa.ForeignKey('mulk.id'), nullable=True),
        sa.Column('musteri_id', sa.Integer(), sa.ForeignKey('musteri.id'), nullable=True),
        sa.Column('teklif_tutar', sa.Float(), nullable=False),
        sa.Column('istenen_tutar', sa.Float(), nullable=True),
        sa.Column('durum', sa.String(20), default='bekliyor'),
        sa.Column('notlar', sa.Text(), nullable=True),
        sa.Column('olusturma', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('teklif')
    op.drop_column('musteri', 'dogum_tarihi')

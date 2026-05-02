"""emlakci slug alani

Revision ID: g3_emlakci_slug
Revises: g2_teklif_dogum
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'g3_emlakci_slug'
down_revision = 'g2_teklif_dogum'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('emlakci', sa.Column('slug', sa.String(100), nullable=True))
    # Mevcut kullanıcılar için slug oluştur
    conn = op.get_bind()
    emlakcilar = conn.execute(sa.text("SELECT id, ad_soyad FROM emlakci")).fetchall()
    for e in emlakcilar:
        import re
        slug = e[1].lower().strip()
        for tr, en in {'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u'}.items():
            slug = slug.replace(tr, en)
        slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
        conn.execute(sa.text("UPDATE emlakci SET slug = :slug WHERE id = :id"), {'slug': slug, 'id': e[0]})
    op.create_unique_constraint('uq_emlakci_slug', 'emlakci', ['slug'])


def downgrade():
    op.drop_constraint('uq_emlakci_slug', 'emlakci')
    op.drop_column('emlakci', 'slug')

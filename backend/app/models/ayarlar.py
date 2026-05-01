"""
AYARLAR MODELLERİ — Kullanıcı ayarları + Admin parametreleri
"""
from app import db
from datetime import datetime


class KullaniciAyar(db.Model):
    """Her emlakçının kişisel AI/uygulama ayarları"""
    __tablename__ = 'kullanici_ayar'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False, unique=True)
    ayarlar     = db.Column(db.JSON, default=dict)
    guncelleme  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SistemParametre(db.Model):
    """Admin tarafından yönetilen sistem parametreleri"""
    __tablename__ = 'sistem_parametre'

    id          = db.Column(db.Integer, primary_key=True)
    anahtar     = db.Column(db.String(100), unique=True, nullable=False)
    deger       = db.Column(db.Text)
    aciklama    = db.Column(db.String(200))
    kategori    = db.Column(db.String(50))    # vergi, hesaplama, belge, sistem
    guncelleme  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

"""
MUHASEBE MODELLERİ — Gelir/gider, cari hesap
Dinamik JSON detay stratejisi kullanır.
"""
from app import db
from datetime import datetime


class GelirGider(db.Model):
    """Gelir ve gider kayıtları"""
    __tablename__ = 'gelir_gider'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    tip         = db.Column(db.String(10), nullable=False)   # gelir / gider
    kategori    = db.Column(db.String(50))                   # komisyon, kira, ofis, personel, reklam...
    tutar       = db.Column(db.Float, nullable=False)
    aciklama    = db.Column(db.String(300))
    tarih       = db.Column(db.DateTime, default=datetime.utcnow)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class Cari(db.Model):
    """Cari hesap (müşteri/tedarikçi borç-alacak)"""
    __tablename__ = 'cari'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    ad          = db.Column(db.String(120), nullable=False)
    tip         = db.Column(db.String(20))                   # musteri, tedarikci, mal_sahibi
    telefon     = db.Column(db.String(20))
    bakiye      = db.Column(db.Float, default=0)             # + alacak, - borç
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)
    hareketler  = db.relationship('CariHareket', backref='cari', lazy=True)


class CariHareket(db.Model):
    """Cari hesap hareketleri"""
    __tablename__ = 'cari_hareket'

    id          = db.Column(db.Integer, primary_key=True)
    cari_id     = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=False)
    tip         = db.Column(db.String(10))                   # borc / alacak
    tutar       = db.Column(db.Float, nullable=False)
    aciklama    = db.Column(db.String(200))
    tarih       = db.Column(db.DateTime, default=datetime.utcnow)

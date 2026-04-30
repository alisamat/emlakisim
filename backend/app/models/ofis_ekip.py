"""
OFİS EKİP — Çoklu danışman desteği
Bir emlakçı birden fazla danışman yönetebilir.
"""
from app import db
from datetime import datetime


class Danisман(db.Model):
    """Ofisteki emlak danışmanları"""
    __tablename__ = 'danisman'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)  # ofis sahibi
    ad_soyad    = db.Column(db.String(120), nullable=False)
    telefon     = db.Column(db.String(20))
    email       = db.Column(db.String(120))
    uzmanlik    = db.Column(db.String(100))     # kiralık, satılık, arsa, ticari
    aktif       = db.Column(db.Boolean, default=True)
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class MusteriAtama(db.Model):
    """Müşteri → danışman ataması"""
    __tablename__ = 'musteri_atama'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    danisman_id = db.Column(db.Integer, db.ForeignKey('danisman.id'), nullable=False)
    notlar      = db.Column(db.Text)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

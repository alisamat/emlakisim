"""
İLETİŞİM GEÇMİŞİ — Müşteri ile yapılan tüm iletişimlerin kaydı
"""
from app import db
from datetime import datetime


class IletisimKayit(db.Model):
    """Her müşteri ile yapılan iletişim kaydı"""
    __tablename__ = 'iletisim_kayit'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    tip         = db.Column(db.String(20))       # telefon, whatsapp, email, yuz_yuze, yer_gosterme
    yon         = db.Column(db.String(10))       # gelen, giden
    ozet        = db.Column(db.Text)             # kısa not
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

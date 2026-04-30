"""
İŞLEM TAKİP — Tapu, kredi, ekspertiz süreç takibi + Evrak arşivi
"""
from app import db
from datetime import datetime


class SurecTakip(db.Model):
    """Tapu devri, kredi, ekspertiz gibi süreçlerin takibi"""
    __tablename__ = 'surec_takip'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    tip         = db.Column(db.String(30))           # tapu_devri, kredi, ekspertiz, iskan, imar
    baslik      = db.Column(db.String(200))
    durum       = db.Column(db.String(20), default='basladi')  # basladi, devam, bekliyor, tamamlandi
    adimlar     = db.Column(db.JSON, default=list)   # [{ad, durum, tarih, not}]
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)
    guncelleme  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Evrak(db.Model):
    """Evrak arşivi — sözleşme, tapu, ekspertiz raporu vb."""
    __tablename__ = 'evrak'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    baslik      = db.Column(db.String(200))
    tip         = db.Column(db.String(30))           # sozlesme, tapu, ekspertiz, kontrat, diger
    etiketler   = db.Column(db.String(200))          # virgülle ayrılmış etiketler
    notlar      = db.Column(db.Text)
    dosya_url   = db.Column(db.Text)                 # ileride storage URL
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

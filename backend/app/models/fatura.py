"""
FATURA MODELİ
"""
from app import db
from datetime import datetime


class Fatura(db.Model):
    __tablename__ = 'fatura'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    fatura_no   = db.Column(db.String(50))
    tip         = db.Column(db.String(20))           # satis, kiralama, hizmet, komisyon
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    alici_ad    = db.Column(db.String(120))
    alici_adres = db.Column(db.Text)
    tutar       = db.Column(db.Float, default=0)
    kdv_oran    = db.Column(db.Integer, default=20)
    kdv_tutar   = db.Column(db.Float, default=0)
    toplam      = db.Column(db.Float, default=0)
    durum       = db.Column(db.String(15), default='bekliyor')  # bekliyor, odendi, gecikti, iptal
    vade_tarihi = db.Column(db.DateTime)
    odeme_tarihi = db.Column(db.DateTime)
    kalemler    = db.Column(db.JSON, default=list)    # [{aciklama, miktar, birim_fiyat, tutar}]
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

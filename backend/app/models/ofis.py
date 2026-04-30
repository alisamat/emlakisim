"""
OFİS YÖNETİM MODELLERİ — Envanter, geri bildirim
"""
from app import db
from datetime import datetime


class Envanter(db.Model):
    """Ofis malzeme/ihtiyaç takibi"""
    __tablename__ = 'envanter'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    ad          = db.Column(db.String(120), nullable=False)
    kategori    = db.Column(db.String(50))       # kirtasiye, temizlik, teknoloji, mobilya
    miktar      = db.Column(db.Integer, default=0)
    min_miktar  = db.Column(db.Integer, default=0)  # bu altına düşünce uyarı
    birim       = db.Column(db.String(20))       # adet, paket, kutu
    notlar      = db.Column(db.Text)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class GeriBildirim(db.Model):
    """Yer gösterme / görüşme sonrası geri bildirim"""
    __tablename__ = 'geri_bildirim'

    id               = db.Column(db.Integer, primary_key=True)
    emlakci_id       = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id       = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id          = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    yer_gosterme_id  = db.Column(db.Integer, db.ForeignKey('yer_gosterme.id'), nullable=True)
    puan             = db.Column(db.Integer)          # 1-5
    yorum            = db.Column(db.Text)
    ilgi_durumu      = db.Column(db.String(20))       # cok_ilgili, ilgili, kararsiz, ilgisiz
    sonraki_adim     = db.Column(db.String(50))       # tekrar_gosterme, teklif, vazgecti, dusunuyor
    olusturma        = db.Column(db.DateTime, default=datetime.utcnow)

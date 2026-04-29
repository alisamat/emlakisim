"""
LEAD & ÇAĞRI MODELLERİ
"""
from app import db
from datetime import datetime


class Lead(db.Model):
    """Potansiyel müşteri (lead) takibi"""
    __tablename__ = 'lead'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    ad_soyad    = db.Column(db.String(120))
    telefon     = db.Column(db.String(20))
    email       = db.Column(db.String(120))
    kaynak      = db.Column(db.String(30))          # whatsapp, web, telefon, referans, ilan
    sicaklik    = db.Column(db.String(10), default='sicak')  # sicak, ilgili, soguk
    durum       = db.Column(db.String(20), default='yeni')   # yeni, iletisimde, musteri_oldu, kayip
    ilk_mesaj   = db.Column(db.Text)
    son_iletisim = db.Column(db.DateTime)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class CagriKayit(db.Model):
    """Telefon çağrı kaydı"""
    __tablename__ = 'cagri_kayit'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    telefon     = db.Column(db.String(20))
    yon         = db.Column(db.String(10))           # gelen, giden, kacirilmis
    sure_sn     = db.Column(db.Integer)              # saniye
    notlar      = db.Column(db.Text)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    lead_id     = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

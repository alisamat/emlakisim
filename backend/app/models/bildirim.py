"""
BİLDİRİM MODELİ
"""
from app import db
from datetime import datetime


class Bildirim(db.Model):
    __tablename__ = 'bildirim'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    tip         = db.Column(db.String(30))      # lead, hatirlatma, yedek, gorev, kredi, sistem
    baslik      = db.Column(db.String(200))
    icerik      = db.Column(db.Text)
    okundu      = db.Column(db.Boolean, default=False)
    link        = db.Column(db.String(100))     # tıklanınca gidilecek tab
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

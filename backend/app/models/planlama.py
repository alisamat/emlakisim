"""
PLANLAMA MODELLERİ — Görev, hatırlatma, takvim
"""
from app import db
from datetime import datetime


class Gorev(db.Model):
    """Görev ve hatırlatmalar"""
    __tablename__ = 'gorev'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    baslik      = db.Column(db.String(200), nullable=False)
    aciklama    = db.Column(db.Text)
    tip         = db.Column(db.String(20), default='gorev')   # gorev, hatirlatma, yer_gosterme, toplanti
    oncelik     = db.Column(db.String(10), default='orta')    # dusuk, orta, yuksek, acil
    durum       = db.Column(db.String(15), default='bekliyor') # bekliyor, devam, tamamlandi, iptal
    baslangic   = db.Column(db.DateTime)
    bitis       = db.Column(db.DateTime)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

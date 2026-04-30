"""
KALICI HAFIZA MODELLERİ — Müşteri bazlı + konuşma state
Günler arası bağlam korunur. AI gerçekten hatırlar.
"""
from app import db
from datetime import datetime


class MusteriHafiza(db.Model):
    """Müşteri bazlı kalıcı hafıza — tercihler, kararlar, geçmiş"""
    __tablename__ = 'musteri_hafiza'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    tip         = db.Column(db.String(20))     # tercih, karar, gozlem, onemli
    icerik      = db.Column(db.Text, nullable=False)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class KonusmaState(db.Model):
    """Konuşma durumu — multi-turn context"""
    __tablename__ = 'konusma_state'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False, unique=True)
    son_islem   = db.Column(db.String(50))      # son yapılan işlem tipi
    son_musteri_id = db.Column(db.Integer)       # son bahsedilen müşteri
    son_mulk_id = db.Column(db.Integer)          # son bahsedilen mülk
    son_arama   = db.Column(db.JSON)             # son arama kriterleri
    bekleyen    = db.Column(db.JSON)             # bekleyen adımlı işlem
    baglam      = db.Column(db.JSON)             # ek bağlam bilgisi
    guncelleme  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

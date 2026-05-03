"""
TALEP MODELİ — Müşterinin ne istediği
Arayan (kiralık/satılık arıyor) veya Veren (kiraya vermek/satmak istiyor)
"""
from app import db
from datetime import datetime


class Talep(db.Model):
    """Müşteri talebi — ayrı modül, müşteriye opsiyonel bağlı."""
    __tablename__ = 'talep'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id    = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)  # opsiyonel — isimsiz olabilir

    # Talep yönü ve türü
    yonu          = db.Column(db.String(10), default='arayan')  # 'arayan' veya 'veren'
    islem_turu    = db.Column(db.String(10))                     # 'kira' veya 'satis'
    # arayan + kira = kiralık daire ARIYOR
    # arayan + satis = satın almak İSTİYOR
    # veren + kira = mülkünü kiraya VERMEK istiyor
    # veren + satis = mülkünü SATMAK istiyor

    # Bütçe / Fiyat
    butce_min     = db.Column(db.Float)
    butce_max     = db.Column(db.Float)

    # Tercihler (arayan için)
    tercih_oda    = db.Column(db.String(10))       # 2+1, 3+1
    tercih_sehir  = db.Column(db.String(50))
    tercih_ilce   = db.Column(db.String(50))
    tercih_tip    = db.Column(db.String(20))       # daire, villa, arsa
    istenen       = db.Column(db.JSON, default=list)    # ["asansör", "balkon"]
    istenmeyen    = db.Column(db.JSON, default=list)    # ["açık mutfak"]

    # Bağlantı (veren için — hangi mülk)
    mulk_id       = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)

    # Durum
    durum         = db.Column(db.String(15), default='aktif')  # aktif, pasif, tamamlandi
    notlar        = db.Column(db.Text)
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)

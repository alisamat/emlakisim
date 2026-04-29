"""
DİYALOG EĞİTİM MODELLERİ — Başarılı diyalog-işlem çiftleri + öğrenilen pattern'lar
"""
from app import db
from datetime import datetime


class DiyalogKayit(db.Model):
    """Her başarılı diyalog-işlem çifti"""
    __tablename__ = 'diyalog_kayit'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    mesaj       = db.Column(db.Text, nullable=False)        # kullanıcının yazdığı
    mesaj_norm  = db.Column(db.Text)                        # normalleştirilmiş hali
    islem       = db.Column(db.String(50), nullable=False)  # musteri_ekle, mulk_liste, rapor, ai_sohbet...
    basarili    = db.Column(db.Boolean, default=True)
    model       = db.Column(db.String(30))                  # pattern, gemini, openai, claude
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class OgrenilenPattern(db.Model):
    """Admin tarafından veya otomatik eklenen pattern'lar"""
    __tablename__ = 'ogrenilen_pattern'

    id          = db.Column(db.Integer, primary_key=True)
    pattern     = db.Column(db.String(200), nullable=False)  # regex pattern
    islem       = db.Column(db.String(50), nullable=False)   # hedef komut
    kaynak      = db.Column(db.String(20), default='manuel') # manuel, otomatik
    kullanim    = db.Column(db.Integer, default=0)           # kaç kez eşleşti
    aktif       = db.Column(db.Boolean, default=True)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

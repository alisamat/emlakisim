"""
İŞLEM TAKİP + GERİ ALMA SİSTEMİ
Her yazma işlemini loglar, geri alma için eski veriyi saklar.
"""
import json
import logging
from datetime import datetime
from app import db

logger = logging.getLogger(__name__)


class IslemGecmisi(db.Model):
    """Her yazma işleminin kaydı — geri alma destekli."""
    __tablename__ = 'islem_gecmisi'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    islem       = db.Column(db.String(30), nullable=False)   # musteri_ekle, mulk_guncelle, not_sil...
    tablo       = db.Column(db.String(30))                   # musteri, mulk, gorev, not, fatura, teklif
    kayit_id    = db.Column(db.Integer)                      # ilgili kaydın ID'si
    ozet        = db.Column(db.String(300))                  # "Ahmet Eker müşteriye eklendi"
    onceki_veri = db.Column(db.JSON)                         # geri alma için eski hali (null=yeni kayıt)
    yeni_veri   = db.Column(db.JSON)                         # yapılan değişiklik
    geri_alindi = db.Column(db.Boolean, default=False)       # geri alındı mı
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


def islem_kaydet(emlakci_id, islem, tablo, kayit_id, ozet, onceki_veri=None, yeni_veri=None):
    """İşlemi logla."""
    try:
        log = IslemGecmisi(
            emlakci_id=emlakci_id, islem=islem, tablo=tablo,
            kayit_id=kayit_id, ozet=ozet,
            onceki_veri=onceki_veri, yeni_veri=yeni_veri,
        )
        db.session.add(log)
        db.session.commit()
        logger.info(f'[İşlem] {islem}: {ozet}')
        return log.id
    except Exception as e:
        logger.error(f'[İşlem] Kayıt hata: {e}')
        return None


def son_islemler(emlakci_id, limit=20):
    """Son işlemleri getir."""
    return IslemGecmisi.query.filter_by(emlakci_id=emlakci_id)\
        .order_by(IslemGecmisi.olusturma.desc()).limit(limit).all()


def islem_geri_al(emlakci_id, islem_id=None):
    """Son işlemi veya belirli işlemi geri al."""
    from app.models import Musteri, Mulk, Not
    from app.models.planlama import Gorev
    from app.models.fatura import Fatura

    if islem_id:
        log = IslemGecmisi.query.filter_by(id=islem_id, emlakci_id=emlakci_id, geri_alindi=False).first()
    else:
        # Son geri alınmamış işlem
        log = IslemGecmisi.query.filter_by(emlakci_id=emlakci_id, geri_alindi=False)\
            .order_by(IslemGecmisi.olusturma.desc()).first()

    if not log:
        return None, 'Geri alınacak işlem bulunamadı.'

    tablo_model = {
        'musteri': Musteri, 'mulk': Mulk, 'not': Not, 'gorev': Gorev, 'fatura': Fatura,
        'gorev': Gorev, 'fatura': Fatura,
    }

    try:
        model = tablo_model.get(log.tablo)
        if not model:
            return None, f'"{log.tablo}" tablosu geri alma desteklemiyor.'

        if log.islem.endswith('_ekle') or log.islem.endswith('_olustur'):
            # Ekleme geri al → sil
            kayit = model.query.get(log.kayit_id)
            if kayit:
                db.session.delete(kayit)
                log.geri_alindi = True
                db.session.commit()
                return log, f'↩️ *Geri alındı:* {log.ozet}'
            return None, 'Kayıt zaten silinmiş.'

        elif log.islem.endswith('_guncelle'):
            # Güncelleme geri al → eski veriyi geri yükle
            if not log.onceki_veri:
                return None, 'Eski veri kaydedilmemiş, geri alınamıyor.'
            kayit = model.query.get(log.kayit_id)
            if kayit:
                for alan, deger in log.onceki_veri.items():
                    if hasattr(kayit, alan):
                        setattr(kayit, alan, deger)
                log.geri_alindi = True
                db.session.commit()
                return log, f'↩️ *Geri alındı:* {log.ozet}'
            return None, 'Kayıt bulunamadı.'

        elif log.islem.endswith('_sil'):
            # Silme geri al → eski veriyi tekrar ekle
            if not log.onceki_veri:
                return None, 'Eski veri kaydedilmemiş, geri alınamıyor.'
            yeni = model(**{k: v for k, v in log.onceki_veri.items() if hasattr(model, k) and k != 'id'})
            db.session.add(yeni)
            log.geri_alindi = True
            db.session.commit()
            return log, f'↩️ *Geri alındı:* {log.ozet} (yeni ID: {yeni.id})'

        return None, f'"{log.islem}" işlemi geri alma desteklemiyor.'

    except Exception as e:
        logger.error(f'[GeriAl] Hata: {e}')
        db.session.rollback()
        return None, f'Geri alma hatası: {str(e)}'


def islem_formatla(islemler):
    """İşlem listesini sohbet mesajına çevir."""
    if not islemler:
        return '📋 Henüz işlem kaydı yok.'

    islem_ikon = {
        'musteri_ekle': '👤+', 'musteri_guncelle': '👤✏️', 'musteri_sil': '👤🗑',
        'mulk_ekle': '🏢+', 'mulk_guncelle': '🏢✏️', 'mulk_sil': '🏢🗑',
        'gorev_ekle': '📌+', 'gorev_guncelle': '📌✏️', 'gorev_sil': '📌🗑',
        'not_ekle': '📝+', 'not_guncelle': '📝✏️', 'not_sil': '📝🗑',
        'fatura_ekle': '🧾+', 'fatura_guncelle': '🧾✏️', 'fatura_sil': '🧾🗑',
        'teklif_ekle': '💰+', 'teklif_guncelle': '💰✏️', 'teklif_sil': '💰🗑',
    }

    satirlar = []
    for i, log in enumerate(islemler):
        ikon = islem_ikon.get(log.islem, '📋')
        tarih = log.olusturma.strftime('%d.%m %H:%M') if log.olusturma else ''
        geri = ' _(geri alındı)_' if log.geri_alindi else ''
        satirlar.append(f'*{i+1}.* {ikon} {log.ozet}{geri} _{tarih}_')

    return f'📋 *Son İşlemler ({len(islemler)}):*\n\n' + '\n'.join(satirlar)

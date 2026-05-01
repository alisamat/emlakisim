"""
KREDİ SİSTEMİ — Tek noktadan maliyet yönetimi
Her işlem log'lanır, kredi düşülür.
"""
import logging
from app.models import db, IslemLog

logger = logging.getLogger(__name__)

# İşlem başına kredi maliyeti
KREDI_TABLOSU = {
    'pattern':       0,       # pattern matching → bedava
    'yardim':        0,       # yardım mesajı → bedava
    'rapor':         0,       # basit rapor → bedava
    'not_ekle':      0,       # not → bedava
    'ai_sohbet':     1,       # AI sohbet mesajı
    'musteri_ekle':  0.5,     # müşteri ekleme
    'mulk_ekle':     0.5,     # mülk ekleme
    'musteri_liste': 0,       # listeleme → bedava
    'mulk_liste':    0,       # listeleme → bedava
    'belge':         2,       # PDF oluşturma
    'sms':           1,       # SMS gönderim
    'email':         1,       # email gönderim
}

# AI model fiyatları ($/1M token)
AI_FIYAT = {
    'gemini-1.5-flash':          {'input': 0.075, 'output': 0.30},
    'gpt-4o-mini':               {'input': 0.15,  'output': 0.60},
    'claude-haiku-4-5-20251001': {'input': 0.25,  'output': 1.25},
}

def _kar_marji():
    try:
        from app.routes.ayarlar import parametre_al
        val = parametre_al('kredi_kar_marji', '3.0')
        return float(val)
    except Exception:
        return 3.0

KAR_MARJI = 3.0  # varsayılan, runtime'da _kar_marji() kullanılır


def kredi_kontrol(emlakci, tutar=1):
    """Kredi yeterli mi?"""
    return (emlakci.kredi or 0) >= tutar


def kredi_dus(emlakci, islem_tipi, aciklama='', model=None, token_input=0, token_output=0):
    """Kredi düş + log kaydet. Döndürür: kalan kredi."""
    # Kredi tutarını hesapla
    if model and model in AI_FIYAT:
        maliyet_usd, kredi_tutar = ai_maliyet_hesapla(model, token_input, token_output)
    else:
        maliyet_usd = 0
        kredi_tutar = KREDI_TABLOSU.get(islem_tipi, 0)

    # Kredi düş
    if kredi_tutar > 0:
        emlakci.kredi = max(0, (emlakci.kredi or 0) - kredi_tutar)

    # Log kaydet
    log = IslemLog(
        emlakci_id=emlakci.id,
        islem_tipi=islem_tipi,
        model=model,
        token_input=token_input or None,
        token_output=token_output or None,
        maliyet_usd=maliyet_usd,
        kredi_tutar=kredi_tutar,
        aciklama=aciklama[:200] if aciklama else None,
    )
    db.session.add(log)
    db.session.commit()

    logger.info(f'[Kredi] {emlakci.ad_soyad}: {islem_tipi} → -{kredi_tutar} kredi (kalan: {emlakci.kredi})')
    return emlakci.kredi


def ai_maliyet_hesapla(model, token_input, token_output):
    """AI token maliyetini hesapla → (usd, kredi)."""
    fiyat = AI_FIYAT.get(model, {'input': 0.15, 'output': 0.60})
    usd = (token_input * fiyat['input'] / 1_000_000) + (token_output * fiyat['output'] / 1_000_000)
    kredi = max(0.5, usd * _kar_marji() * 1000)  # minimum 0.5 kredi, aksi halde çok düşük kalır
    return round(usd, 6), round(kredi, 2)

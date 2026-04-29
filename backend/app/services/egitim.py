"""
DİYALOG EĞİTİM SERVİSİ
- Her diyaloğu kaydet (eğitim verisi)
- Öğrenilen pattern'larla eşleştir (DB'den)
- Zaman içinde AI'ya daha az ihtiyaç → maliyet düşer
"""
import re
import logging
from app.models import db
from app.models.egitim import DiyalogKayit, OgrenilenPattern

logger = logging.getLogger(__name__)

# Bellekte cache (startup'ta DB'den yüklenir)
_pattern_cache = None


def diyalog_kaydet(emlakci_id, mesaj, mesaj_norm, islem, basarili=True, model=None):
    """Her başarılı diyaloğu kaydet."""
    try:
        kayit = DiyalogKayit(
            emlakci_id=emlakci_id,
            mesaj=mesaj[:500],
            mesaj_norm=mesaj_norm[:500] if mesaj_norm else None,
            islem=islem,
            basarili=basarili,
            model=model,
        )
        db.session.add(kayit)
        db.session.commit()
    except Exception as e:
        logger.error(f'[Egitim] Kayıt hatası: {e}')
        db.session.rollback()


def ogrenilen_pattern_esle(metin_norm):
    """DB'deki öğrenilen pattern'larla eşleştir. Bulursa komut döndür."""
    global _pattern_cache

    # Cache'i yükle
    if _pattern_cache is None:
        _pattern_yukle()

    for pattern, islem in _pattern_cache:
        try:
            if re.search(pattern, metin_norm):
                # Kullanım sayısını artır (async yapılabilir)
                _kullanim_artir(pattern)
                return islem
        except re.error:
            continue

    return None


def _pattern_yukle():
    """DB'den aktif pattern'ları cache'e yükle."""
    global _pattern_cache
    try:
        patterns = OgrenilenPattern.query.filter_by(aktif=True).order_by(OgrenilenPattern.kullanim.desc()).all()
        _pattern_cache = [(p.pattern, p.islem) for p in patterns]
        logger.info(f'[Egitim] {len(_pattern_cache)} öğrenilen pattern yüklendi')
    except:
        _pattern_cache = []


def _kullanim_artir(pattern_str):
    """Pattern kullanım sayısını artır."""
    try:
        p = OgrenilenPattern.query.filter_by(pattern=pattern_str, aktif=True).first()
        if p:
            p.kullanim = (p.kullanim or 0) + 1
            db.session.commit()
    except:
        db.session.rollback()


def cache_yenile():
    """Pattern cache'ini yenile (yeni pattern eklendiğinde çağrılır)."""
    global _pattern_cache
    _pattern_cache = None


def anlasilamayan_listele(limit=50):
    """AI'ya giden ama pattern'a dönüştürülebilecek diyalogları listele."""
    kayitlar = DiyalogKayit.query.filter_by(
        islem='ai_sohbet', basarili=True
    ).order_by(DiyalogKayit.olusturma.desc()).limit(limit).all()
    return kayitlar


def istatistik():
    """Eğitim istatistikleri."""
    toplam = DiyalogKayit.query.count()
    pattern_hit = DiyalogKayit.query.filter_by(model='pattern').count()
    ai_hit = DiyalogKayit.query.filter(DiyalogKayit.model != 'pattern', DiyalogKayit.model.isnot(None)).count()
    ogrenilen = OgrenilenPattern.query.filter_by(aktif=True).count()

    return {
        'toplam_diyalog': toplam,
        'pattern_hit': pattern_hit,
        'ai_hit': ai_hit,
        'pattern_oran': round(pattern_hit / toplam * 100, 1) if toplam else 0,
        'ogrenilen_pattern': ogrenilen,
    }

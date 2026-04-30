"""
İŞLEM ZİNCİRLEME — Tek komutla birden fazla işlem tetikleme
"Müşteri ekle ve uygun mülk bul" → müşteri kaydı + eşleştirme
"""
import logging
from app.models import db, Musteri, Mulk
from app.routes.bildirim import bildirim_olustur

logger = logging.getLogger(__name__)


def musteri_eklendi_sonrasi(emlakci, musteri):
    """Müşteri eklendikten sonra otomatik işlemler."""
    sonuclar = []

    # 1. Uygun mülk var mı kontrol et
    uygun = _uygun_mulk_bul(emlakci.id, musteri)
    if uygun:
        mulk_listesi = ', '.join([m.baslik or m.adres or '?' for m in uygun[:3]])
        bildirim_olustur(
            emlakci.id, 'eslestirme',
            f'🔗 {musteri.ad_soyad} için {len(uygun)} uygun mülk!',
            f'{mulk_listesi}', link='eslestirme'
        )
        sonuclar.append(f'🔗 {len(uygun)} uygun mülk bulundu')

    # 2. Sıcak müşteriyse hatırlatma oluştur
    if musteri.sicaklik == 'sicak':
        from app.models import Not
        not_obj = Not(
            emlakci_id=emlakci.id, musteri_id=musteri.id,
            icerik=f'{musteri.ad_soyad} sıcak müşteri — hızlı dönüş yap!',
            etiket='hatirlatici',
        )
        db.session.add(not_obj)
        db.session.commit()
        sonuclar.append('🔔 Sıcak müşteri hatırlatması eklendi')

    return sonuclar


def mulk_eklendi_sonrasi(emlakci, mulk):
    """Mülk eklendikten sonra otomatik işlemler."""
    sonuclar = []

    # 1. Bu mülke uygun müşteri var mı
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id, islem_turu=mulk.islem_turu).all()
    uygun = []
    for m in musteriler:
        if m.butce_max and mulk.fiyat and mulk.fiyat <= m.butce_max:
            uygun.append(m)

    if uygun:
        musteri_listesi = ', '.join([m.ad_soyad for m in uygun[:3]])
        bildirim_olustur(
            emlakci.id, 'eslestirme',
            f'👥 Yeni mülk için {len(uygun)} potansiyel müşteri!',
            f'{mulk.baslik or mulk.adres}: {musteri_listesi}', link='eslestirme'
        )
        sonuclar.append(f'👥 {len(uygun)} potansiyel müşteri bildirildi')

    return sonuclar


def _uygun_mulk_bul(emlakci_id, musteri, limit=5):
    """Müşteriye uygun mülkleri bul."""
    q = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True, islem_turu=musteri.islem_turu)
    if musteri.butce_max:
        q = q.filter(Mulk.fiyat <= musteri.butce_max)
    if musteri.butce_min:
        q = q.filter(Mulk.fiyat >= musteri.butce_min)
    return q.limit(limit).all()

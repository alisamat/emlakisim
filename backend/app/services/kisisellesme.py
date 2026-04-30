"""
KİŞİSELLEŞME MOTORU — Her emlakçıya özgü asistan davranışı
Zamanla emlakçının çalışma tarzını öğrenir ve adapte olur.

Öğrenilen:
1. En çok hangi işlemleri yapıyor
2. Hangi saatlerde aktif
3. Hangi müşteri segmentine odaklı (kiralık/satılık, bütçe aralığı)
4. Portföy odağı (hangi tip, hangi bölge)
5. İletişim tarzı (resmi/samimi)
6. Sık kullandığı komutlar → hızlı erişim önerileri
"""
import logging
from datetime import datetime, timedelta
from collections import Counter
from app.models import db, Musteri, Mulk
from app.models.egitim import DiyalogKayit

logger = logging.getLogger(__name__)


def profil_cikart(emlakci_id):
    """Emlakçının çalışma profilini çıkart — kişiselleşme için."""
    profil = {}

    # 1. En çok yapılan işlemler (son 30 gün)
    son30 = datetime.utcnow() - timedelta(days=30)
    diyaloglar = DiyalogKayit.query.filter(
        DiyalogKayit.emlakci_id == emlakci_id,
        DiyalogKayit.olusturma >= son30
    ).all()

    islem_sayac = Counter()
    saat_sayac = Counter()
    for d in diyaloglar:
        if d.islem:
            islem_sayac[d.islem] += 1
        if d.olusturma:
            saat_sayac[d.olusturma.hour] += 1

    profil['en_cok_islem'] = islem_sayac.most_common(5)
    profil['aktif_saatler'] = sorted(saat_sayac.most_common(3), key=lambda x: x[0])
    profil['toplam_diyalog'] = len(diyaloglar)

    # 2. Müşteri segmenti
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
    kira_sayi = sum(1 for m in musteriler if m.islem_turu == 'kira')
    satis_sayi = sum(1 for m in musteriler if m.islem_turu == 'satis')
    profil['musteri_odak'] = 'kiralık' if kira_sayi > satis_sayi else 'satılık' if satis_sayi > kira_sayi else 'karma'

    butceler = [m.butce_max for m in musteriler if m.butce_max]
    if butceler:
        profil['ort_butce'] = round(sum(butceler) / len(butceler))
    else:
        profil['ort_butce'] = 0

    # 3. Portföy odağı
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()
    tip_sayac = Counter(m.tip for m in mulkler if m.tip)
    bolge_sayac = Counter(m.ilce for m in mulkler if m.ilce)
    profil['portfoy_tip'] = tip_sayac.most_common(3)
    profil['portfoy_bolge'] = bolge_sayac.most_common(3)

    fiyatlar = [m.fiyat for m in mulkler if m.fiyat]
    if fiyatlar:
        profil['ort_fiyat'] = round(sum(fiyatlar) / len(fiyatlar))
        profil['min_fiyat'] = min(fiyatlar)
        profil['max_fiyat'] = max(fiyatlar)

    # 4. Çalışma yoğunluğu
    profil['musteri_sayisi'] = len(musteriler)
    profil['portfoy_sayisi'] = len(mulkler)

    return profil


def kisisellesmis_prompt_eki(emlakci_id):
    """Sistem prompt'a eklenmek üzere kişiselleşmiş bağlam."""
    try:
        profil = profil_cikart(emlakci_id)
    except Exception:
        return ''

    ek = '\n[KİŞİSELLEŞME]'

    if profil.get('musteri_odak'):
        ek += f' Odak: {profil["musteri_odak"]}.'

    if profil.get('portfoy_bolge'):
        bolgeler = ', '.join([b[0] for b in profil['portfoy_bolge'][:2]])
        ek += f' Bölge: {bolgeler}.'

    if profil.get('portfoy_tip'):
        tipler = ', '.join([t[0] for t in profil['portfoy_tip'][:2]])
        ek += f' Tip: {tipler}.'

    if profil.get('en_cok_islem'):
        islemler = ', '.join([i[0] for i in profil['en_cok_islem'][:3]])
        ek += f' Sık: {islemler}.'

    return ek


def hizli_erisim_onerileri(emlakci_id):
    """Emlakçının en çok kullandığı 5 işlem — hızlı erişim için."""
    profil = profil_cikart(emlakci_id)
    islemler = profil.get('en_cok_islem', [])

    islem_komut = {
        'musteri_ekle': 'müşteri ekle',
        'musteri_liste': 'müşteri listele',
        'mulk_ekle': 'mülk ekle',
        'mulk_liste': 'portföy listele',
        'rapor': 'rapor',
        'bugun_ozet': 'bugün özet',
        'gorev_ekle': 'görev ekle',
        'muhasebe_rapor': 'kar zarar',
        'yardim': 'yardım',
        'performans': 'performans',
    }

    oneriler = []
    for islem, sayi in islemler:
        if islem in islem_komut:
            oneriler.append({'komut': islem_komut[islem], 'sayi': sayi})

    return oneriler[:5]

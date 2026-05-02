"""
SATICI TAHMİN MOTORU — Kural tabanlı satış olasılığı tahmini
Portföydeki mülk sahiplerinin satma ihtimalini puanlar.
"""
from datetime import datetime, timedelta
from app.models import Musteri, Mulk
from app import db


def satici_tahmin(emlakci_id):
    """
    Tüm müşterilerin satış olasılığını hesapla.
    Kural tabanlı scoring (0-100):
    - Sahiplik süresi (uzun = satma ihtimali yüksek)
    - Etkileşim sıklığı (çok konuşan = ilgili)
    - Son iletişim zamanı (yakın = aktif)
    - Müşteri sıcaklığı
    - Bölge fiyat trendi (portföy ortalamasıyla karşılaştır)
    """
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()

    # Bölge fiyat ortalaması
    fiyat_ort = {}
    for m in mulkler:
        if m.ilce and m.fiyat:
            fiyat_ort.setdefault(m.ilce, []).append(m.fiyat)
    for k in fiyat_ort:
        fiyat_ort[k] = sum(fiyat_ort[k]) / len(fiyat_ort[k])

    sonuclar = []
    for musteri in musteriler:
        puan = 0
        detaylar = []

        # 1. Kayıt süresi (eski müşteri = satma ihtimali yüksek)
        gun = (datetime.utcnow() - musteri.olusturma).days if musteri.olusturma else 0
        if gun > 365:
            puan += 20
            detaylar.append(f'📅 {gun} gündür kayıtlı (+20)')
        elif gun > 180:
            puan += 15
            detaylar.append(f'📅 {gun} gündür kayıtlı (+15)')
        elif gun > 90:
            puan += 10
            detaylar.append(f'📅 {gun} gündür kayıtlı (+10)')

        # 2. Etkileşim sıklığı
        try:
            from app.models.iletisim_gecmisi import IletisimKayit
            iletisim_sayi = IletisimKayit.query.filter_by(
                emlakci_id=emlakci_id, musteri_id=musteri.id
            ).count()
            if iletisim_sayi > 10:
                puan += 15
                detaylar.append(f'📞 {iletisim_sayi} iletişim (+15)')
            elif iletisim_sayi > 5:
                puan += 10
                detaylar.append(f'📞 {iletisim_sayi} iletişim (+10)')
            elif iletisim_sayi > 0:
                puan += 5
                detaylar.append(f'📞 {iletisim_sayi} iletişim (+5)')
        except Exception:
            pass

        # 3. Son iletişim zamanı
        try:
            from app.models.iletisim_gecmisi import IletisimKayit
            son = IletisimKayit.query.filter_by(
                emlakci_id=emlakci_id, musteri_id=musteri.id
            ).order_by(IletisimKayit.olusturma.desc()).first()
            if son:
                gun_once = (datetime.utcnow() - son.olusturma).days
                if gun_once <= 7:
                    puan += 20
                    detaylar.append(f'🕐 Son iletişim {gun_once} gün önce (+20)')
                elif gun_once <= 30:
                    puan += 10
                    detaylar.append(f'🕐 Son iletişim {gun_once} gün önce (+10)')
        except Exception:
            pass

        # 4. Müşteri sıcaklığı
        if musteri.sicaklik == 'sicak':
            puan += 25
            detaylar.append('🔥 Sıcak müşteri (+25)')
        elif musteri.sicaklik == 'ilgili':
            puan += 15
            detaylar.append('🟡 İlgili müşteri (+15)')

        # 5. İşlem türü (satılık arayanlar)
        if musteri.islem_turu == 'satis':
            puan += 10
            detaylar.append('🏷 Satış arıyor (+10)')

        # 6. Bütçe belirli (ciddi alıcı sinyali)
        if musteri.butce_max and musteri.butce_max > 0:
            puan += 10
            detaylar.append('💰 Bütçe belirlemiş (+10)')

        # Puan sınırla
        puan = min(puan, 100)

        # Yorum
        if puan >= 75:
            yorum = '🟢 Çok yüksek — hemen iletişime geçin'
        elif puan >= 50:
            yorum = '🟡 Yüksek — takip edin'
        elif puan >= 25:
            yorum = '🟠 Orta — izleyin'
        else:
            yorum = '⚪ Düşük — bekleyin'

        sonuclar.append({
            'musteri_id': musteri.id,
            'ad_soyad': musteri.ad_soyad,
            'telefon': musteri.telefon,
            'islem_turu': musteri.islem_turu,
            'sicaklik': musteri.sicaklik,
            'puan': puan,
            'yorum': yorum,
            'detaylar': detaylar,
        })

    # Puana göre sırala
    sonuclar.sort(key=lambda x: x['puan'], reverse=True)
    return sonuclar


def isi_haritasi(emlakci_id):
    """
    İlçe bazında portföy ısı haritası.
    Kendi portföy verilerinden istatistik çıkar.
    """
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()

    ilce_veri = {}

    # Portföy verileri
    for m in mulkler:
        ilce = m.ilce or 'Bilinmiyor'
        if ilce not in ilce_veri:
            ilce_veri[ilce] = {
                'mulk_sayisi': 0, 'talep_sayisi': 0,
                'fiyatlar_satis': [], 'fiyatlar_kira': [],
                'metrekareler': [],
            }
        ilce_veri[ilce]['mulk_sayisi'] += 1
        if m.fiyat:
            if m.islem_turu == 'kira':
                ilce_veri[ilce]['fiyatlar_kira'].append(m.fiyat)
            else:
                ilce_veri[ilce]['fiyatlar_satis'].append(m.fiyat)
        if m.metrekare:
            ilce_veri[ilce]['metrekareler'].append(m.metrekare)

    # Talep verileri (müşteri tercihlerinden)
    for m in musteriler:
        tercih = m.tercih_notlar or ''
        for ilce in ilce_veri:
            if ilce.lower() in tercih.lower():
                ilce_veri[ilce]['talep_sayisi'] += 1

    # İstatistik hesapla
    sonuc = []
    for ilce, v in ilce_veri.items():
        ort_satis = sum(v['fiyatlar_satis']) / len(v['fiyatlar_satis']) if v['fiyatlar_satis'] else 0
        ort_kira = sum(v['fiyatlar_kira']) / len(v['fiyatlar_kira']) if v['fiyatlar_kira'] else 0
        ort_m2 = sum(v['metrekareler']) / len(v['metrekareler']) if v['metrekareler'] else 0
        m2_fiyat = ort_satis / ort_m2 if ort_m2 and ort_satis else 0
        getiri = (ort_kira * 12 / ort_satis * 100) if ort_satis and ort_kira else 0

        # Isı skoru: mülk sayısı + talep = sıcak bölge
        isi = min(100, (v['mulk_sayisi'] * 15) + (v['talep_sayisi'] * 20))

        sonuc.append({
            'ilce': ilce,
            'mulk_sayisi': v['mulk_sayisi'],
            'talep_sayisi': v['talep_sayisi'],
            'ort_satis_fiyat': round(ort_satis),
            'ort_kira_fiyat': round(ort_kira),
            'ort_m2': round(ort_m2, 1),
            'm2_fiyat': round(m2_fiyat),
            'kira_getirisi': round(getiri, 1),
            'isi_skoru': isi,
        })

    sonuc.sort(key=lambda x: x['isi_skoru'], reverse=True)
    return sonuc

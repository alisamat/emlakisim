"""
HESAPLAMA SERVİSİ — Emlak sektörü hesaplamaları
Kira vergisi, değer artış kazancı, kira getirisi (ROI), aidat analizi
"""


def kira_vergisi(yillik_kira, istisna_tutari=33000, vergi_dilimleri=None):
    """
    Kira geliri vergisi hesaplama (2026 tahmini).
    yillik_kira: Yıllık toplam kira geliri (TL)
    istisna_tutari: Yıllık istisna (2026: ~33.000 TL tahmini)
    """
    if vergi_dilimleri is None:
        # 2026 tahmini gelir vergisi dilimleri
        vergi_dilimleri = [
            (110000, 0.15),
            (230000, 0.20),
            (580000, 0.27),
            (3000000, 0.35),
            (float('inf'), 0.40),
        ]

    matrah = max(0, yillik_kira - istisna_tutari)
    if matrah == 0:
        return {
            'yillik_kira': yillik_kira,
            'istisna': istisna_tutari,
            'matrah': 0,
            'vergi': 0,
            'net_gelir': yillik_kira,
            'efektif_oran': 0,
            'dilimler': [],
        }

    toplam_vergi = 0
    kalan = matrah
    dilimler = []
    onceki_sinir = 0

    for sinir, oran in vergi_dilimleri:
        dilim_tutar = min(kalan, sinir - onceki_sinir)
        if dilim_tutar <= 0:
            break
        vergi = dilim_tutar * oran
        toplam_vergi += vergi
        dilimler.append({
            'aralik': f'{onceki_sinir:,.0f} - {sinir:,.0f} TL'.replace(',', '.'),
            'oran': f'%{int(oran*100)}',
            'matrah': round(dilim_tutar, 2),
            'vergi': round(vergi, 2),
        })
        kalan -= dilim_tutar
        onceki_sinir = sinir

    return {
        'yillik_kira': yillik_kira,
        'istisna': istisna_tutari,
        'matrah': round(matrah, 2),
        'vergi': round(toplam_vergi, 2),
        'net_gelir': round(yillik_kira - toplam_vergi, 2),
        'efektif_oran': round(toplam_vergi / yillik_kira * 100, 1) if yillik_kira else 0,
        'dilimler': dilimler,
    }


def deger_artis_kazanci(alis_fiyati, satis_fiyati, alis_yili, satis_yili, yeniden_degerleme=None):
    """
    Değer artış kazancı vergisi hesaplama.
    5 yıl içinde satışlarda uygulanır.
    """
    elde_tutma = satis_yili - alis_yili

    if elde_tutma >= 5:
        return {
            'alis_fiyati': alis_fiyati,
            'satis_fiyati': satis_fiyati,
            'elde_tutma_yil': elde_tutma,
            'vergi_var_mi': False,
            'aciklama': '5 yıldan fazla elde tutulduğu için değer artış kazancı vergisi yok.',
            'kazanc': satis_fiyati - alis_fiyati,
            'vergi': 0,
        }

    # Yeniden değerleme oranı tahmini (yıllık %30 ortalama)
    if yeniden_degerleme is None:
        yeniden_degerleme = 1.30 ** elde_tutma

    degerlendirilmis_maliyet = alis_fiyati * yeniden_degerleme
    kazanc = max(0, satis_fiyati - degerlendirilmis_maliyet)

    # İstisna (2026 tahmini ~87.000 TL)
    istisna = 87000
    matrah = max(0, kazanc - istisna)

    # Gelir vergisi dilimleri ile hesapla
    sonuc = kira_vergisi(matrah + istisna, istisna)

    return {
        'alis_fiyati': alis_fiyati,
        'satis_fiyati': satis_fiyati,
        'elde_tutma_yil': elde_tutma,
        'vergi_var_mi': True,
        'degerlendirilmis_maliyet': round(degerlendirilmis_maliyet, 2),
        'brut_kazanc': satis_fiyati - alis_fiyati,
        'net_kazanc': round(kazanc, 2),
        'istisna': istisna,
        'matrah': round(matrah, 2),
        'vergi': sonuc['vergi'],
        'aciklama': f'{elde_tutma} yıl elde tutuldu. Değer artış vergisi uygulanır.',
    }


def kira_getirisi(mulk_fiyati, aylik_kira, yillik_gider=0):
    """
    Kira getirisi (ROI) hesaplama.
    Brüt ve net getiri oranı.
    """
    yillik_kira = aylik_kira * 12
    yillik_net = yillik_kira - yillik_gider

    brut_getiri = (yillik_kira / mulk_fiyati * 100) if mulk_fiyati else 0
    net_getiri = (yillik_net / mulk_fiyati * 100) if mulk_fiyati else 0
    geri_donus_yil = (mulk_fiyati / yillik_net) if yillik_net > 0 else 0

    return {
        'mulk_fiyati': mulk_fiyati,
        'aylik_kira': aylik_kira,
        'yillik_kira': yillik_kira,
        'yillik_gider': yillik_gider,
        'yillik_net': round(yillik_net, 2),
        'brut_getiri': round(brut_getiri, 2),
        'net_getiri': round(net_getiri, 2),
        'geri_donus_yil': round(geri_donus_yil, 1),
        'degerlendirme': _getiri_degerlendirme(net_getiri),
    }


def _getiri_degerlendirme(oran):
    if oran >= 8: return '🟢 Çok iyi yatırım'
    if oran >= 5: return '🟡 Makul yatırım'
    if oran >= 3: return '🟠 Düşük getiri'
    return '🔴 Yatırıma uygun değil'


def tapu_masrafi(satis_bedeli, dask_bedeli=1500, doner_sermaye=1000):
    """Tapu devir masrafı hesaplama."""
    tapu_harci = satis_bedeli * 0.04  # %4 (alıcı+satıcı)
    alici_harci = satis_bedeli * 0.02
    satici_harci = satis_bedeli * 0.02
    toplam = tapu_harci + dask_bedeli + doner_sermaye

    return {
        'satis_bedeli': satis_bedeli,
        'tapu_harci': round(tapu_harci, 2),
        'alici_harci': round(alici_harci, 2),
        'satici_harci': round(satici_harci, 2),
        'dask': dask_bedeli,
        'doner_sermaye': doner_sermaye,
        'toplam_masraf': round(toplam, 2),
    }


def komisyon_hesapla(islem_turu, bedel, oran=None):
    """Emlakçı komisyon hesaplama."""
    if islem_turu == 'satis':
        oran = oran or 0.02  # %2
        komisyon = bedel * oran
        kdv = komisyon * 0.20
        return {
            'islem': 'Satış', 'bedel': bedel, 'oran': f'%{oran*100:.0f}',
            'komisyon': round(komisyon, 2), 'kdv': round(kdv, 2),
            'toplam': round(komisyon + kdv, 2),
            'aciklama': f'Alıcıdan %{oran*100:.0f} + satıcıdan %{oran*100:.0f} (ayrı ayrı)',
        }
    else:
        komisyon = bedel  # 1 aylık kira
        kdv = komisyon * 0.20
        return {
            'islem': 'Kiralama', 'bedel': bedel, 'oran': '1 aylık kira',
            'komisyon': round(komisyon, 2), 'kdv': round(kdv, 2),
            'toplam': round(komisyon + kdv, 2),
        }


def aidat_analizi(aidat, kira, mulk_fiyati):
    """Aidat/kira ve aidat/fiyat oranı analizi."""
    kira_orani = (aidat / kira * 100) if kira else 0
    fiyat_orani = (aidat * 12 / mulk_fiyati * 100) if mulk_fiyati else 0

    return {
        'aidat': aidat,
        'kira': kira,
        'aidat_kira_orani': round(kira_orani, 1),
        'aidat_fiyat_orani': round(fiyat_orani, 2),
        'degerlendirme': '🟢 Normal' if kira_orani < 15 else '🟡 Yüksek' if kira_orani < 25 else '🔴 Çok yüksek',
    }

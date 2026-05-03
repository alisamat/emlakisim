"""
DİNAMİK TOOL YÜKLEME — Kategoriye göre fonksiyon seçimi
40 fonksiyonun hepsini göndermek yerine sadece ilgili 4-5'ini gönderir.
Token tasarrufu: ~%80
"""

# Kategori → fonksiyon isimleri
KATEGORI_TOOLS = {
    'musteri': [
        'musteri_ekle', 'musteri_guncelle', 'musteri_sil', 'musteri_listele',
        'gelismis_musteri_ara', 'musteri_analiz', 'musteri_eslesme_bul',
        'dogum_gunu_kaydet', 'yaklasan_dogum_gunleri',
    ],
    'mulk': [
        'mulk_ekle', 'mulk_guncelle', 'mulk_sil', 'mulk_goruntule', 'mulk_listele', 'gelismis_mulk_ara',
    ],
    'eslestirme': [
        'eslestir', 'musteri_eslesme_bul', 'gelismis_mulk_ara', 'gelismis_musteri_ara',
    ],
    'finans': [
        'fatura_olustur', 'fatura_guncelle', 'fatura_sil', 'fatura_listele', 'gelir_gider_ozet',
        'cari_ozet', 'muhasebe_donem', 'komisyon_hesapla', 'tapu_masrafi_hesapla',
        'kira_vergisi_hesapla', 'kira_getirisi_hesapla',
    ],
    'planlama': [
        'gorev_ekle', 'gorev_listele', 'gorev_guncelle', 'gorev_sil', 'rapor',
    ],
    'not': [
        'not_ekle', 'not_guncelle', 'not_sil', 'not_ara', 'not_goreve_donustur',
    ],
    'iletisim': [
        'whatsapp_mesaj_gonder', 'toplu_mesaj_gonder', 'gosterim_geri_bildirim',
    ],
    'teklif': [
        'teklif_kaydet', 'teklif_guncelle', 'teklif_sil', 'teklif_listele', 'satis_kapandi',
    ],
    'analiz': [
        'mahalle_analiz', 'hava_durumu', 'emlak_haberleri',
    ],
    'arac': [
        'qr_kod_olustur', 'cevir', 'web_sayfa_bilgi', 'veri_indir',
        'yedek_durumu_sorgula', 'asistan_ismi_degistir',
        'son_islemler_getir', 'islem_geri_al',
    ],
    'navigasyon': [
        'sayfa_ac',
    ],
    'sohbet': [
        'rapor',  # sohbette rapor isteyebilir
    ],
}


def tools_yukle(kategoriler, tum_fonksiyonlar):
    """
    Kategorilere göre ilgili fonksiyon tanımlarını döndür.

    Args:
        kategoriler: ['musteri', 'planlama'] gibi
        tum_fonksiyonlar: _FUNCTIONS listesi

    Returns:
        Filtrelenmiş fonksiyon listesi (4-10 arası)
    """
    if not kategoriler:
        # Kategori belirlenemedi — en sık kullanılan 8 tool'u gönder
        varsayilan = [
            'musteri_ekle', 'musteri_listele', 'mulk_ekle', 'mulk_listele',
            'gorev_ekle', 'not_ekle', 'rapor', 'sayfa_ac',
        ]
        return [f for f in tum_fonksiyonlar if f['name'] in varsayilan]

    # İlgili tool isimlerini topla
    tool_isimleri = set()
    for kat in kategoriler:
        for isim in KATEGORI_TOOLS.get(kat, []):
            tool_isimleri.add(isim)

    # Fonksiyon tanımlarını filtrele
    secilen = [f for f in tum_fonksiyonlar if f['name'] in tool_isimleri]

    # Çok az tool seçildiyse varsayılanları ekle
    if len(secilen) < 3:
        for f in tum_fonksiyonlar:
            if f['name'] in ('rapor', 'sayfa_ac') and f not in secilen:
                secilen.append(f)

    return secilen

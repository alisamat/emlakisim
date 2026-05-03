"""
KATMANLI PROMPT OLUŞTURMA — Token tasarrufu
Tier 1 (çekirdek, ~200 token) + Tier 2 (kategoriye göre, ~300 token) + Tier 3 (bağlam)
Toplam: 500-700 token (eskisi 3000+)
"""
from datetime import datetime


def prompt_olustur(emlakci, kategoriler, metin=''):
    """Katmanlı sistem prompt oluştur."""
    # Asistan ismi
    asistan_ismi = 'Emlakisim AI'
    try:
        from app.models.ayarlar import KullaniciAyar
        k = KullaniciAyar.query.filter_by(emlakci_id=emlakci.id).first()
        if k and k.ayarlar and k.ayarlar.get('asistan_ismi'):
            asistan_ismi = k.ayarlar['asistan_ismi']
    except Exception:
        pass

    # AI tonu
    ton = ''
    try:
        from app.models.ayarlar import KullaniciAyar
        k = KullaniciAyar.query.filter_by(emlakci_id=emlakci.id).first()
        if k and k.ayarlar:
            t = k.ayarlar.get('ai_tonu', 'samimi')
            if t == 'resmi':
                ton = 'Resmi ve profesyonel konuş, "siz" hitabı kullan.'
            elif t == 'kisa':
                ton = 'Çok kısa ve öz cevap ver.'
            else:
                ton = 'Samimi ve yardımsever ol.'
    except Exception:
        ton = 'Samimi ve yardımsever ol.'

    # ═══ TIER 1: Çekirdek (~200 token) ═══
    tier1 = f"""Sen {asistan_ismi} — emlak profesyonelleri için AI asistan.
Kullanıcı: {emlakci.ad_soyad}. Kredi: {emlakci.kredi}. Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}.
{ton}
Türkçe konuş. *bold* ve _italic_ kullan.
Selamlama + komut birlikte gelirse: kısa selamla + komutu yap.
Çoklu istek varsa hepsini yap. Koşullu istek varsa önce kontrol et.
İşlem sonucunda eklenen TÜM bilgileri detaylı göster.
Bilgi yeterliyse hemen yap, gereksiz soru sorma."""

    # ═══ TIER 2: Kategoriye göre (~300 token) ═══
    tier2 = ''
    for kat in kategoriler:
        tier2 += KATEGORI_PROMPTLARI.get(kat, '')

    # ═══ TIER 3: Bağlam (~100 token) ═══
    tier3 = ''
    try:
        from app.services.hafiza import baglam_olustur
        tier3 = baglam_olustur(emlakci, metin) or ''
    except Exception:
        pass

    return f'{tier1}\n\n{tier2}\n\n{tier3}'.strip()


KATEGORI_PROMPTLARI = {
    'musteri': """
MÜŞTERİ İŞLEMLERİ:
DİKKAT: "müşterimize ekle", "müşteri kaydet", "arıyor", "arayışı var", "talep ediyor" → MÜŞTERİ ekle (mulk_ekle DEĞİL!).
"kiralık daire arıyor" = müşteri talebi. "kiralık daire ilan ekle" = mülk ekle. Farkı anla.
Müşteri eklerken şu alanları doğal dilden çıkar:
- ad_soyad (zorunlu), telefon, islem_turu (kira/satis)
- butce_min, butce_max (TL — "30K"=30000, "1.5M"=1500000)
- tercih_oda ("2+1", "3+1"), tercih_sehir, tercih_ilce
- istenen_ozellikler: ["asansör", "balkon", "site içi", "otopark"]
- istenmeyen_ozellikler: ["açık mutfak", "zemin kat", "bodrum"]
- kunye: ayırt edici lakap ("Eyyüpteki", "mimar")
Aynı isimde müşteri varsa uyar. "Elimizde ne var" = portföy, müşteri DEĞİL.
""",

    'mulk': """
MÜLK İŞLEMLERİ:
Mülk eklerken şu alanları çıkar:
- baslik (zorunlu), adres, sehir, ilce
- tip (daire/villa/arsa/dukkan/ofis), islem_turu (kira/satis)
- fiyat (TL), metrekare, oda_sayisi ("2+1")
- kat, bina_yasi, isitma, mutfak (açık/kapalı)
- esyali, asansor, otopark, balkon, site_ici
"Elimizde kiralık ne var" = portföydeki kiralık mülkler.
Mülk güncelleme: kullanıcı portföy listeledikten sonra "şuna ısıtma ekle", "fiyatı güncelle" derse → bağlamdan hangi mülk olduğunu anla, mulk_guncelle çağır.
Portföyde tek mülk varsa otomatik onu güncelle, sormaya gerek yok.
"İlanı göster", "ilanı görüntüle", "ilan sayfası" → web_sayfa_bilgi fonksiyonunu çağır, kendi metin çıktısı oluşturma. Asla mülk bilgilerini metin olarak tekrar yazma — sayfa linki ver.
""",

    'eslestirme': """
EŞLEŞTIRME: Müşteri tercihleri × mülk özellikleri çapraz karşılaştırma.
İşlem türü, fiyat, lokasyon, oda sayısı, özellikler puanlanır.
""",

    'finans': """
FİNANS: Fatura, gelir/gider, cari, komisyon, tapu, vergi, ROI hesaplama.
Dönem: bu_ay, gecen_ay, bu_yil, son_3_ay filtreleri var.
""",

    'planlama': """
PLANLAMA: Görev/toplantı/hatırlatma oluştur.
tarih: "bugun", "yarin", "haftaya", "onumuzdeki cuma"
saat: "sabah"(09), "ogleden_sonra"(14), "aksam"(18), "14:00"
""",

    'not': """
NOT: Not ekle/ara/listele/göreve dönüştür. Tipler: not, hatirlatici, gosterim, sesli_not.
""",

    'iletisim': """
İLETİŞİM: WhatsApp mesaj gönder (müşteri adından telefon bulunur), toplu mesaj, gösterim anketi.
""",

    'teklif': """
TEKLİF: Teklif kaydet (tutar, mülk, müşteri), listele, satış kapandı zincirleme süreç.
""",

    'analiz': """
ANALİZ: Mahalle puanlama, hava durumu, emlak haberleri, satıcı tahmin, ısı haritası.
""",

    'arac': """
ARAÇLAR: QR kod, çeviri (9 dil), web sayfa linki, Excel/ZIP export, yedek durumu, döviz kuru.
""",

    'navigasyon': """
NAVİGASYON: sayfa_ac(sayfa) — musteriler, mulkler, muhasebe, planlama, takvim, ayarlar, notlar, faturalar, cariler, leadler, eslestirme, gruplar, emlakcilar, hesaplamalar, isi_haritasi, gorsel_analiz, sanal_staging, belgeler, yedekleme, performans, kredi.
""",

    'sohbet': """
Doğal konuşma. Emlak sektörü bilgisi ver: tapu masrafı, kira artışı, DASK, iskan, komisyon oranları.
"Kredi" = uygulama kredisi (panel aç), "konut kredisi" = banka kredisi bilgisi.
""",
}

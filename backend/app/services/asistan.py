"""
AI ASISTAN — Function calling ile DB işlemleri + çok modelli + pattern matching
Öncelik: Pattern → Direkt DB → AI (ucuzdan pahalıya)
"""
import os
import re
import json
import logging
from datetime import datetime
from app.models import db, Musteri, Mulk, YerGosterme, Not
from app.services import whatsapp as wa

logger = logging.getLogger(__name__)

# ─── Türkçe normalleştirme ─────────────────────────────────
_TR_MAP = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')

def _normalize(metin):
    """Türkçe karakterleri ASCII'ye çevir, küçük harf yap."""
    return metin.lower().translate(_TR_MAP).strip()


# ─── Pattern Matching (sıfır maliyet) ──────────────────────
_PATTERNS = [
    # ── Müşteri (10+ varyasyon) ──
    (r'(?:musteri|müşteri|müsteri)\s*(?:ekle|kayit|kaydet|olustur|gir|yaz)', 'musteri_ekle'),
    (r'(?:musteri|müşteri|müsteri)\s*(?:listele|göster|listesi|kimler|kac)', 'musteri_liste'),
    (r'(?:musteri|müşteri|müsteri)\s*(?:sil|kaldir|cikar)',   'musteri_sil'),
    (r'(?:yeni\s*musteri|yeni\s*müşteri)',                    'musteri_ekle'),
    (r'(?:kac|kaç)\s*(?:musteri|müşteri)',                    'musteri_liste'),
    (r'(?:sicak|sıcak)\s*(?:musteri|müşteri)',                'musteri_liste'),
    # ── Portföy (10+ varyasyon) ──
    (r'(?:portfoy|portföy|mulk|mülk|emlak|daire|villa|arsa)\s*(?:ekle|kayit|kaydet|olustur|gir)', 'mulk_ekle'),
    (r'(?:portfoy|portföy|mulk|mülk|emlak)\s*(?:listele|göster|listesi|kac)',    'mulk_liste'),
    (r'(?:yeni\s*(?:mulk|mülk|ilan|emlak|daire))',            'mulk_ekle'),
    (r'(?:kac|kaç)\s*(?:mulk|mülk|ilan|emlak)',               'mulk_liste'),
    (r'(?:kiralik|kiralık)(?:\s+\w+|\s*$)',                     'mulk_liste'),
    (r'(?:satilik|satılık)(?:\s+\w+|\s*$)',                     'mulk_liste'),
    # ── Not & Hatırlatma ──
    (r'(?:not)\s*(?:ekle|al|kaydet|yaz)',                     'not_ekle'),
    (r'(?:unutma|hatirla|hatırla|aklinda\s*tut|aklında\s*tut|sakla|kaydet\s*bunu)', 'unutma'),
    (r'(?:hatirlatmalar|hatırlatmalar|neler\s*unutmamam|neyi\s*hatirl)', 'hatirlatma_liste'),
    (r'(?:bunu\s*hatirla|bunu\s*unutma)',                     'unutma'),
    # ── Rapor & Özet ──
    (r'(?:rapor|özet|durum|nasil\s*gidiyor|ne\s*durumda)',            'rapor'),
    (r'(?:istatistik|dagilim|dağılım|segment)',                      'istatistik'),
    (r'(?:genel\s*durum|genel\s*ozet|genel\s*bakis)',         'rapor'),
    # ── Muhasebe (15+ varyasyon) ──
    (r'(?:kar\s*zarar|kâr\s*zarar|kar.zarar|gelir\s*gider)',  'muhasebe_rapor'),
    (r'(?:gelir|kazanc|kazanç)\s*(?:ne\s*kadar|toplam)',      'muhasebe_rapor'),
    (r'(?:gider|masraf|harcama)\s*(?:ne\s*kadar|toplam)',     'muhasebe_rapor'),
    (r'(?:cari|alacak|borc|borç)\s*(?:durum|listele|göster|ne\s*kadar)', 'cari_rapor'),
    (r'(?:ne\s*kadar\s*(?:borcum|alacagim|alacağım))',        'cari_rapor'),
    (r'(?:gelir\s*ekle|kazanc\s*ekle)',                       'muhasebe_rapor'),
    (r'(?:gider\s*ekle|masraf\s*ekle|harcama\s*ekle)',        'muhasebe_rapor'),
    # ── Planlama (10+ varyasyon) ──
    (r'(?:gorev|görev)\s*(?:ekle|olustur|kaydet|yaz)',        'gorev_ekle'),
    (r'(?:gorev|görev)\s*(?:listele|göster|ne\s*var)',        'gorev_liste'),
    (r'(?:bugun|bugün|gunluk|günlük)\s*(?:plan|görev|ozet|ne\s*var)', 'bugun_ozet'),
    (r'(?:yarin|yarın)\s*(?:ne\s*var|plan)',                  'bugun_ozet'),
    (r'(?:randevu|toplanti|toplantı)\s*(?:ekle|planla)',      'gorev_ekle'),
    (r'(?:hatırlat|hatırlat.*bana)',                          'gorev_ekle'),
    # ── Eşleştirme ──
    (r'(?:esles|eşleş|eslestir|eşleştir|uygun\s*mulk|uygun\s*mülk)', 'eslestirme'),
    (r'(?:kimler?\s*(?:uygun|ilgili|bakiyor))',               'eslestirme'),
    (r'(?:bu\s*(?:mulk|mülk).*(?:kime|kim))',                 'eslestirme'),
    # ── Fatura ──
    (r'(?:fatura)\s*(?:olustur|ekle|kaydet|kes|hazirla)',     'fatura_ekle'),
    (r'(?:fatura)\s*(?:listele|göster|son)',                  'fatura_liste'),
    # ── İlan & Reklam ──
    (r'(?:ilan)\s*(?:metni|yaz|olustur|hazirla)',             'ilan_olustur'),
    (r'(?:reklam|tanitim|tanıtım)\s*(?:yaz|hazirla|olustur)', 'ilan_olustur'),
    (r'(?:sosyal\s*medya|instagram|facebook)\s*(?:icerik|paylas)', 'ilan_olustur'),
    # ── Belge ──
    (r'(?:yer\s*goster|yer\s*göster)\s*(?:belgesi|tutanak|olustur)', 'rapor'),
    (r'(?:kontrat|sozlesme|sözleşme)\s*(?:olustur|hazirla)',  'rapor'),
    (r'(?:brosur|broşür)\s*(?:olustur|hazirla|indir)',        'rapor'),
    # ── Hesaplama ──
    (r'(?:kira\s*vergisi|vergi\s*hesapla)',                   'rapor'),
    (r'(?:kira\s*getiri|roi|yatirim\s*getiri|yatırım)',       'rapor'),
    (r'(?:deger\s*artis|değer\s*artış|kazanc\s*vergisi)',     'rapor'),
    # ── Sektörel ──
    (r'(?:sektor|sektör|haber|piyasa|trend|gelisme|gelişme|ekonomi)', 'sektor_bilgi'),
    (r'(?:fiyat|m2|metrekare)\s*(?:ne\s*kadar|ortalama)',     'sektor_bilgi'),
    # ── Performans ──
    (r'(?:performans|kpi|verimlilik|ozet\s*rapor|nasil\s*gidiyorum)', 'performans'),
    (r'(?:strateji|oneri|öner|ne\s*yapmaliyim|tavsiye|yol\s*harita)', 'strateji'),
    # ── Yardım ──
    # ── Müşteri detay ──
    (r'(?:musteri|müşteri).*(?:bilgi|detay|profil)',          'musteri_liste'),
    (r'(?:musteri|müşteri)(?:ler)?(?:de|da|den|dan|i|ı|m|mda)?\s+(?:ara|bul)\s+\S', 'musteri_ara'),
    (r'(\S+)\s+(?:isminde|adında|adlı|isimli|diye)\s*(?:musteri|müşteri)', 'musteri_ara'),
    (r'(?:musteri|müşteri).*(?:var\s*m[ıi]|olmal)',           'musteri_ara'),
    (r'(\w)\s*(?:ile|harfi|harfiyle)\s*(?:basla|başla)',      'harf_filtre'),
    (r'(?:bas|baş)\s*(?:harf|harfi)\s*(\w)',                  'harf_filtre'),
    (r'(\w)\s*ile\s*baslayan|(\w)\s*ile\s*başlayan',          'harf_filtre'),
    (r'(?:mulk|mülk|portfoy|portföy)(?:te|da|de)?\s+(?:ara|bul)\s+\S',    'mulk_ara'),
    (r'(?:musteri|müşteri).*(?:ara|bul|sec|seç)',             'musteri_liste'),
    (r'(?:musteri|müşteri).*(?:grup|etiket|filtre)',          'musteri_liste'),
    (r'(?:musteri|müşteri).*(?:mail|email|gonder)',           'musteri_liste'),
    (r'(?:telefon\s*rehber|rehber.*ekle)',                    'musteri_ekle'),
    (r'(?:excel.*musteri|excel.*müşteri)',                    'musteri_ekle'),
    # ── Portföy detay ──
    (r'(?:mulk|mülk|emlak).*(?:detay|bilgi|özellik)',        'mulk_liste'),
    (r'(?:mulk|mülk).*(?:brosur|broşür|pdf)',                'mulk_liste'),
    (r'(?:mulk|mülk).*(?:mail|email|gonder|paylas)',         'mulk_liste'),
    (r'(?:excel.*(?:mulk|mülk|portfoy|portföy))',            'mulk_ekle'),
    (r'(?:sahibinden|hepsiemlak).*(?:ekle|import|aktar)',     'mulk_ekle'),
    # ── Belge detay ──
    (r'(?:pdf|belge|evrak)\s*(?:olustur|hazirla|indir)',     'rapor'),
    (r'(?:yer\s*gosterme|yer\s*gösterme)',                   'rapor'),
    (r'(?:kira\s*kontrat|kira\s*sozlesme|kira\s*sözleşme)',  'rapor'),
    (r'(?:yonlendirme|yönlendirme)\s*(?:belgesi|formu)',     'rapor'),
    # ── Muhasebe detay ──
    (r'(?:fis|fiş)\s*(?:oku|tara|okut)',                     'muhasebe_rapor'),
    (r'(?:banka.*excel|hesap\s*ozeti|hesap\s*özeti)',         'muhasebe_rapor'),
    (r'(?:butce|bütçe)\s*(?:planla|hazirla|göster)',          'muhasebe_rapor'),
    (r'(?:ne\s*kadar\s*(?:kazandim|kazandım|harcadim|harcadım))', 'muhasebe_rapor'),
    # ── Planlama detay ──
    (r'(?:plan|planlama)\s*(?:yap|göster|listele)',           'gorev_liste'),
    (r'(?:takvim|ajanda)\s*(?:göster|aç)',                    'gorev_liste'),
    (r'(?:ne\s*zaman|saat\s*kac|saat\s*kaç)',                'bugun_ozet'),
    (r'(?:bu\s*hafta|gelecek\s*hafta)\s*(?:ne\s*var|plan)',   'bugun_ozet'),
    # ── Lead detay ──
    (r'(?:lead|potansiyel)\s*(?:ekle|listele|göster|kac)',    'eslestirme'),
    (r'(?:yeni\s*lead|yeni\s*potansiyel)',                    'eslestirme'),
    (r'(?:kacirilmis|kaçırılmış)\s*(?:cagri|çağrı|arama)',   'eslestirme'),
    # ── Hesaplama detay ──
    (r'(?:ne\s*kadar\s*vergi|vergi\s*ne\s*kadar)',           'rapor'),
    (r'(?:kira\s*ne\s*kadar|kira\s*fiyat)',                  'sektor_bilgi'),
    (r'(?:m2|metrekare)\s*(?:fiyat|ne\s*kadar)',             'sektor_bilgi'),
    # ── Envanter ──
    (r'(?:malzeme|envanter|stok)\s*(?:ekle|listele|kontrol)', 'rapor'),
    # ── Ekip ──
    (r'(?:danisman|danışman)\s*(?:ekle|listele|göster)',      'rapor'),
    (r'(?:ekip|takim|takım)\s*(?:göster|listele)',            'rapor'),
    # ── Yedek ──
    (r'(?:yedek|backup)\s*(?:al|indir|gonder)',               'rapor'),
    (r'(?:veri.*(?:export|indir|gonder))',                    'rapor'),
    # ── Ayarlar ──
    (r'(?:ayar|setting|profil)\s*(?:degistir|değiştir|güncelle)', 'rapor'),
    (r'(?:sifre|şifre)\s*(?:degistir|değiştir)',              'rapor'),
    (r'(?:logo)\s*(?:degistir|değiştir|yukle|yükle)',         'rapor'),
    (r'(?:karanlik|karanlık|gece)\s*(?:mod|tema)',            'rapor'),
    # ── Genel arama ──
    (r'(?:ara|bul)\s+(.+)',                                   'genel_ara'),
    (r'(.+)\s+(?:ara|bul)$',                                  'genel_ara'),
    (r'(?:onu|ona)\s*(?:ara|ula)',                             'genel_ara'),
    # ── Tapu & Komisyon hesapla ──
    (r'(?:tapu)\s*(?:masraf|harç|harc|maliyet|ne\s*kadar)',   'rapor'),
    (r'(?:komisyon)\s*(?:hesapla|ne\s*kadar)',                 'rapor'),
    # ── Ayar/şifre ──
    (r'(?:sifre|şifre|sifremi|şifremi)',                       'rapor'),
    (r'(?:ayar|tema|logo)\s*(?:degistir|değiştir|ac|aç)',     'rapor'),
    # ── Döviz & Altın ──
    (r'(?:doviz|döviz|kur|dolar|euro|sterlin)',                  'doviz_kuru'),
    (r'(?:altin|altın|gram\s*fiyat)',                            'altin_fiyat'),
    (r'(\d[\d.,]*)\s*(?:tl|lira).*(?:dolar|euro|doviz|döviz)',   'fiyat_cevir'),
    # ── Yasal & Piyasa & Süreç ──
    (r'(?:yasal|hukuki|ipotek|haciz|iskan)\s*(?:durum|kontrol|risk)', 'yasal_bilgi'),
    (r'(?:piyasa|deger|değer)\s*(?:analiz|rapor|karsilastir)',        'piyasa_bilgi'),
    (r'(?:surec|süreç)\s*(?:durum|ozet|ne\s*durumda)',               'surec_ozet_cmd'),
    # ── Yardım & Yetenek ──
    (r'(?:yardim|yardım|neler?\s*yapabilirsin|merhaba|selam|hey)', 'yardim'),
    (r'(?:bunu\s*yapabilir\s*mi|yapabilir\s*misin|mumkun\s*mu|mümkün\s*mü)', 'yetenek_sor'),
    (r'(?:ne\s*yapabilirsin|yeteneklerin|ozelliklerin|özellikler)', 'yardim'),
    (r'(?:nasil\s*kullan|nasıl\s*kullan|nasil\s*yap|nasıl\s*yap)', 'yardim'),
    (r'(?:tesekkur|teşekkür|sagol|sağol|eyv)',                'tesekkur'),
    (r'(?:gunayd|günayd|iyi\s*sabah)',                       'gunaydin'),
    (r'(?:iyi\s*aksamlar|iyi\s*geceler)',                    'iyi_aksam'),
    # ── Excel Export ──
    (r'(?:portfoy|portföy|mulk|mülk)\s*(?:.*excel|.*indir|.*liste.*ver)', 'portfoy_excel'),
    (r'(?:excel)\s*(?:.*portfoy|.*portföy|.*mulk|.*mülk)',               'portfoy_excel'),
    (r'(?:musteri|müşteri)\s*(?:.*excel|.*indir|.*liste.*ver)',           'musteri_excel'),
    (r'(?:excel)\s*(?:.*musteri|.*müşteri)',                              'musteri_excel'),
    (r'(?:tum|tüm|hep).*(?:zip)',                                        'tum_zip'),
    (r'(?:zip).*(?:indir|ver|export)',                                    'tum_zip'),
    (r'(?:tum|tüm|hep).*(?:excel|indir|export)',                         'tum_excel'),
    # ── Tahmin & Analiz ──
    (r'(?:satici|satıcı)\s*(?:tahmin|olasil|olasıl|ihtimal)', 'satici_tahmin'),
    (r'(?:kim)\s*(?:sat|alacak|ilgili)',                     'satici_tahmin'),
    (r'(?:isi|ısı)\s*(?:harita|haritas)',                    'isi_haritasi'),
    (r'(?:ilce|ilçe)\s*(?:analiz|istatistik|karsilastir)',   'isi_haritasi'),
    (r'(?:piyasa|market)\s*(?:isi|ısı|sicak|sıcak|hareket)', 'isi_haritasi'),
    # ── Emlakçı Dizini ──
    (r'(?:emlakci|emlakçı)\s*(?:ekle|kaydet|kayıt)',          'emlakci_ekle'),
    (r'(?:emlakci|emlakçı)\s*(?:liste|listele|rehber|dizin|göster|goster)', 'emlakci_liste'),
    (r'(?:emlakci|emlakçı)\s*(?:ara|bul)',                    'emlakci_ara'),
    (r'(?:emlakci|emlakçı)\s*(?:sil|kaldir|kaldır)',          'emlakci_sil'),
    (r'kac\s*(?:emlakci|emlakçı)|(?:emlakci|emlakçı)\s*(?:kac|kaç|sayı|sayi)', 'emlakci_sayisi'),
    (r'(?:emlakci|emlakçı)\s*(?:dizin|rehber)',               'emlakci_liste'),
    # ── Grup Yönetimi ──
    (r'grup\s*(?:kur|olustur|oluştur|ac|aç|yeni)',           'grup_kur'),
    (r'grup(?:lar)?\s*(?:liste|listele|göster|goster|neler)', 'grup_liste'),
    (r'(?:kac|kaç)\s*grup|grup\s*(?:kac|kaç|sayı|sayi)',    'grup_sayisi'),
    (r'grup\s*(?:esles|eşleş|eslestir|eşleştir)',            'grup_esles'),
    (r'grup\s*(?:uye|üye)(?:ler|leri)?',                     'grup_uyeleri'),
    (r'grup\s*(?:davet|teklif)',                              'grup_davet'),
    (r'grup.*(?:cik|çık|ayril|ayrıl)',                        'grup_cik'),
    (r'grup\s*(?:ayar|setting)',                              'grup_ayar'),
    (r'(?:portfoy|portföy)\s*(?:ac|aç|paylas|paylaş).*grup', 'grup_portfoy_ac'),
    (r'grup.*(?:portfoy|portföy)\s*(?:ac|aç|paylas|paylaş)', 'grup_portfoy_ac'),
    (r'(?:portfoy|portföy)\s*(?:kapat|kapa).*grup',          'grup_portfoy_kapat'),
    (r'grup.*(?:portfoy|portföy)\s*(?:kapat|kapa)',           'grup_portfoy_kapat'),
    (r'(?:talep)\s*(?:ac|aç|paylas|paylaş).*grup',           'grup_talep_ac'),
    (r'grup.*(?:talep)\s*(?:ac|aç|paylas|paylaş)',            'grup_talep_ac'),
    (r'(?:talep)\s*(?:kapat|kapa).*grup',                    'grup_talep_kapat'),
    (r'grup.*(?:talep)\s*(?:kapat|kapa)',                     'grup_talep_kapat'),
    (r'grup\s*(?:bildirim|aktivite|hareket)',                 'grup_bildirim'),
    (r'(?:grub|grup).*(?:davet\s*et|ekle).*(?:uye|üye)',     'grup_uye_davet'),
    (r'(?:grub|grup).*(?:yonetici|yönetici)\s*(?:ata|yap)',  'grup_yonetici_ata'),
]

def _pattern_isle(metin_norm, emlakci, metin_raw):
    """Pattern matching ile komut bul. Bulursa (komut, args) döndür, bulamazsa None."""
    for pattern, komut in _PATTERNS:
        if re.search(pattern, metin_norm):
            return komut
    return None


# ─── Sayfa Navigasyon Haritası ────────────────────────────
_NAVIGASYON_PATTERNS = [
    # (regex, tab_key, cevap_mesaj)
    (r'(?:müşteri|musteri)\s*(?:sayfa|ekran|git|aç|ac|göster|goster)',   'musteriler',  '👥 Müşteriler sayfası açılıyor...'),
    (r'(?:mulk|mülk|portfoy|portföy)\s*(?:sayfa|ekran|git|aç|ac|göster|goster)', 'mulkler', '🏢 Portföy sayfası açılıyor...'),
    (r'(?:yer\s*goster|yer\s*göster)\s*(?:sayfa|git|aç|ac)',            'kayitlar',    '📋 Yer gösterme kayıtları açılıyor...'),
    (r'(?:belge|dokuman|doküman)\s*(?:sayfa|git|aç|ac|göster|goster)',   'belgeler',    '📄 Belgeler sayfası açılıyor...'),
    (r'(?:muhasebe)\s*(?:sayfa|git|aç|ac|göster|goster)',               'muhasebe',    '💰 Muhasebe sayfası açılıyor...'),
    (r'(?:hesaplama|hesap)\s*(?:sayfa|git|aç|ac|göster|goster)',        'hesaplamalar','🧮 Hesaplama araçları açılıyor...'),
    (r'(?:planlama|gorev|görev)\s*(?:sayfa|git|aç|ac|göster|goster)',   'planlama',    '📅 Planlama sayfası açılıyor...'),
    (r'(?:yedek|yedekleme|backup)\s*(?:sayfa|git|aç|ac|göster|goster)', 'yedekleme',   '💾 Yedekleme sayfası açılıyor...'),
    (r'(?:toplu)\s*(?:sayfa|git|aç|ac|göster|goster|islem|işlem)',      'toplu',       '📦 Toplu işlemler açılıyor...'),
    (r'(?:lead)\s*(?:sayfa|git|aç|ac|göster|goster)',                   'leadler',     '🎯 Lead yönetimi açılıyor...'),
    (r'(?:esles|eşleş)\s*(?:sayfa|git|aç|ac)',                          'eslestirme',  '🔗 Eşleştirme sayfası açılıyor...'),
    (r'(?:takvim|kalendar)\s*(?:sayfa|git|aç|ac|göster|goster)',        'takvim',      '📅 Takvim açılıyor...'),
    (r'(?:tanitim|tanıtım|sosyal)\s*(?:sayfa|git|aç|ac|göster|goster)','tanitim',     '🌐 Tanıtım sayfası açılıyor...'),
    (r'(?:fatura)\s*(?:sayfa|git|aç|ac|göster|goster)',                 'faturalar',   '🧾 Faturalar açılıyor...'),
    (r'(?:cagri|çağrı|arama)\s*(?:kayit|kayıt|sayfa|git|aç|ac)',       'cagrilar',    '📞 Çağrı kayıtları açılıyor...'),
    (r'(?:kar\s*zarar|kâr\s*zarar)\s*(?:sayfa|git|aç|ac|göster)',      'karzarar',    '📈 Kâr/Zarar sayfası açılıyor...'),
    (r'(?:cari)\s*(?:sayfa|git|aç|ac|göster|goster)',                   'cariler',     '📒 Cari hesaplar açılıyor...'),
    (r'(?:ayar)\s*(?:sayfa|git|aç|ac|göster|goster)',                   'ayarlar',     '⚙️ Ayarlar sayfası açılıyor...'),
    (r'(?:muhasebe\s*rapor)\s*(?:sayfa|git|aç|ac)',                     'muhrapor',    '📊 Muhasebe raporu açılıyor...'),
    (r'(?:butce|bütçe)\s*(?:sayfa|git|aç|ac|göster|goster)',           'butce',       '💼 Bütçe planlama açılıyor...'),
    (r'(?:surec|süreç)\s*(?:sayfa|git|aç|ac|takip|göster)',            'surec',       '📋 Süreç takip açılıyor...'),
    (r'(?:talep)\s*(?:sayfa|git|aç|ac|göster|goster)',                  'talepler',    '📝 Talepler sayfası açılıyor...'),
    (r'(?:ekip|danisman|danışman)\s*(?:sayfa|git|aç|ac|göster)',       'ekip',        '👔 Ekip yönetimi açılıyor...'),
    (r'(?:performans|kpi)\s*(?:sayfa|git|aç|ac|göster)',               'performans',  '🏆 Performans sayfası açılıyor...'),
    (r'(?:iletisim|iletişim)\s*(?:gecmis|geçmiş|sayfa|git|aç|ac)',    'iletisim',    '📞 İletişim geçmişi açılıyor...'),
    (r'(?:envanter|malzeme|stok)\s*(?:sayfa|git|aç|ac|göster)',        'envanter',    '📦 Ofis envanter açılıyor...'),
    (r'(?:admin|yonetim|yönetim)\s*(?:panel|sayfa|git|aç|ac)',        'admin_dash',  '🛡 Admin paneli açılıyor...'),
    (r'(?:ilan\s*ocr|ocr)\s*(?:sayfa|git|aç|ac)',                      'ilan_ocr',    '📸 İlan OCR açılıyor...'),
    (r'(?:isaretleme|işaretleme|resim\s*isaret)\s*(?:sayfa|git|aç|ac)','isaretleme', '🖊 Resim işaretleme açılıyor...'),
    (r'(?:gorsel|görsel)\s*(?:analiz|değerleme|sayfa|git|aç|ac)',     'gorsel_analiz', '📸 AI Görsel Analiz açılıyor...'),
    (r'(?:sanal|staging|düzenleme)\s*(?:sayfa|git|aç|ac)',            'sanal_staging', '🪑 Sanal Ev Düzenleme açılıyor...'),
    (r'(?:mahalle|semt)\s*(?:analiz|rapor|puan|sayfa)',               'gorsel_analiz', '📍 Mahalle analizi — sohbetten "Kadıköy Moda nasıl?" yazın'),
    (r'(?:isi|ısı)\s*(?:harita|sayfa|git|aç|ac)',                   'isi_haritasi',  '🗺 Isı Haritası açılıyor...'),
    (r'(?:tahmin|prediction)\s*(?:sayfa|git|aç|ac)',                'isi_haritasi',  '🔮 Tahmin sayfası açılıyor...'),
    (r'(?:emlakci|emlakçı)\s*(?:dizin|sayfa|git|aç|ac)\s*(?:sayfa|git|aç|ac)?', 'emlakcilar', '📒 Emlakçı dizini açılıyor...'),
    (r'(?:grup)\s*(?:sayfa|git|aç|ac|göster|goster)',                   'gruplar',     '👥 Gruplar sayfası açılıyor...'),
    (r'(?:profil)\s*(?:sayfa|git|aç|ac|göster|goster)',                'profil',      '👤 Profil sayfası açılıyor...'),
    (r'(?:kredi)\s*(?:sayfa|git|aç|ac|göster|goster|satin|satın)',     'kredi',       '💎 Kredi paneli açılıyor...'),
    # Kısa navigasyonlar — "X aç" / "X'e git" / "X göster"
    (r'müsterilere?\s*git',           'musteriler',  '👥 Müşteriler sayfası açılıyor...'),
    (r'portföye?\s*git',              'mulkler',     '🏢 Portföy sayfası açılıyor...'),
    (r'muhasebeye?\s*git',            'muhasebe',    '💰 Muhasebe sayfası açılıyor...'),
    (r'takvi?me?\s*git',              'takvim',      '📅 Takvim açılıyor...'),
    (r'ayarlara?\s*git',              'ayarlar',     '⚙️ Ayarlar sayfası açılıyor...'),
    (r'gruplara?\s*git',              'gruplar',     '👥 Gruplar sayfası açılıyor...'),
    (r'leadlere?\s*git',              'leadler',     '🎯 Lead yönetimi açılıyor...'),
    (r'faturalara?\s*git',            'faturalar',   '🧾 Faturalar açılıyor...'),
    (r'carilere?\s*git',              'cariler',     '📒 Cari hesaplar açılıyor...'),
    (r'ekibe?\s*git',                 'ekip',        '👔 Ekip yönetimi açılıyor...'),
    (r'profile?\s*git',               'profil',      '👤 Profil sayfası açılıyor...'),
    # "X'i aç" / "X aç"
    (r'musterileri?\s*ac',            'musteriler',  '👥 Müşteriler sayfası açılıyor...'),
    (r'(?:portfoy|portföy)u?\s*ac',   'mulkler',     '🏢 Portföy sayfası açılıyor...'),
    (r'muhasebeyi?\s*ac',             'muhasebe',    '💰 Muhasebe sayfası açılıyor...'),
    (r'takvimi?\s*ac',                'takvim',      '📅 Takvim açılıyor...'),
    (r'ayarlari?\s*ac',               'ayarlar',     '⚙️ Ayarlar sayfası açılıyor...'),
    (r'gruplari?\s*ac',               'gruplar',     '👥 Gruplar sayfası açılıyor...'),
    (r'faturalari?\s*ac',             'faturalar',   '🧾 Faturalar açılıyor...'),
    (r'belgeleri?\s*ac',              'belgeler',    '📄 Belgeler sayfası açılıyor...'),
]


def _navigasyon_kontrol(metin_norm):
    """Navigasyon komutu mu kontrol et. (tab, mesaj) veya None döndür."""
    for pattern, tab, mesaj in _NAVIGASYON_PATTERNS:
        if re.search(pattern, metin_norm):
            return tab, mesaj
    return None


# ─── Bağlam Takip Filtreleri ─────────────────────────────
_BAGLAM_PATTERNS = [
    # (regex, filtre_tipi)
    (r'(?:bunlardan|onlardan|icinden|içinden|listeden)\s*(?:sicak|sıcak)',  'sicaklik_sicak'),
    (r'(?:bunlardan|onlardan|icinden|içinden|listeden)\s*(?:soguk|soğuk)',  'sicaklik_soguk'),
    (r'(?:bunlardan|onlardan|icinden|içinden|listeden)\s*(?:ilgili)',       'sicaklik_ilgili'),
    (r'(?:sicak|sıcak)\s*(?:olan|musteri|müşteri)',                        'sicaklik_sicak'),
    (r'(?:soguk|soğuk)\s*(?:olan|musteri|müşteri)',                        'sicaklik_soguk'),
    (r'(?:kiralik|kiralık)\s*(?:olan|arayan)',                             'islem_kira'),
    (r'(?:satilik|satılık)\s*(?:olan|arayan)',                             'islem_satis'),
    (r'(?:bunlardan|onlardan)?\s*(?:kiralik|kiralık)',                     'islem_kira'),
    (r'(?:bunlardan|onlardan)?\s*(?:satilik|satılık)',                     'islem_satis'),
    (r'(\d+)\.\s*(?:numaray[ıi]|siray[ıi]|kisiyi|kişiyi|mulku|mülkü)?\s*(?:goster|göster|sec|seç|detay|ac|aç)', 'numara_sec'),
    (r'(\d+)\.\s*(?:si|sı|ci|cı|nu|nolu)',                                'numara_sec'),
    (r'(?:ilk|son|en\s*son)\s*(\d+)',                                      'limit_sec'),
    (r'(?:daha\s*fazla|devam|geri\s*kalan)',                               'devam'),
]


def _baglam_filtre(metin_norm, emlakci, session):
    """Bağlamsal takip filtresi — önceki listeyi filtrele."""
    son_liste = session.get('son_liste')  # [{id, tip, ...}]
    son_komut = session.get('son_komut')  # 'musteri' veya 'mulk'
    if not son_liste:
        return None

    for pattern, filtre in _BAGLAM_PATTERNS:
        m = re.search(pattern, metin_norm)
        if not m:
            continue

        ids = [s['id'] for s in son_liste]

        if filtre == 'numara_sec':
            idx = int(m.group(1)) - 1
            if idx < 0 or idx >= len(son_liste):
                return f'⚠️ {idx+1}. sırada kayıt yok. Listede {len(son_liste)} kayıt var.'
            secilen = son_liste[idx]
            if son_komut == 'musteri':
                mus = Musteri.query.get(secilen['id'])
                if mus:
                    session['son_musteri_id'] = mus.id
                    butce = ''
                    if mus.butce_min or mus.butce_max:
                        f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '?'
                        butce = f'\n💰 Bütçe: {f_tl(mus.butce_min)} - {f_tl(mus.butce_max)} TL'
                    return (f'👤 *{mus.ad_soyad}*\n\n'
                            f'📞 {mus.telefon or "—"}\n'
                            f'📧 {mus.email or "—"}\n'
                            f'🏷 {mus.islem_turu or "?"} · {"🔥" if mus.sicaklik == "sicak" else "🟡" if mus.sicaklik == "ilgili" else "❄️"} {mus.sicaklik or "?"}'
                            f'{butce}'
                            + (f'\n📝 {mus.tercih_notlar[:100]}' if mus.tercih_notlar else ''))
            elif son_komut == 'mulk':
                mulk = Mulk.query.get(secilen['id'])
                if mulk:
                    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
                    det = mulk.detaylar or {}
                    return (f'🏢 *{mulk.baslik or mulk.adres or "—"}*\n\n'
                            f'📍 {mulk.ilce or "?"}, {mulk.sehir or "?"}\n'
                            f'💰 {f_tl(mulk.fiyat)}\n'
                            f'🏷 {mulk.islem_turu or "?"} · {mulk.tip or "?"}\n'
                            f'🛏 {mulk.oda_sayisi or "?"} · {mulk.metrekare or "?"}m²'
                            + (f'\n🏗 Bina yaşı: {det.get("bina_yasi")}' if det.get("bina_yasi") else '')
                            + (f'\n🔥 Isıtma: {det.get("isinma")}' if det.get("isinma") else ''))
            elif son_komut == 'gorev':
                from app.models.planlama import Gorev
                g = Gorev.query.get(secilen['id'])
                if g:
                    return (f'📌 *{g.baslik}*\n\n'
                            f'🏷 Tip: {g.tip or "görev"}\n'
                            f'📊 Durum: {g.durum or "bekliyor"}\n'
                            f'⭐ Öncelik: {g.oncelik or "normal"}'
                            + (f'\n📅 Başlangıç: {g.baslangic.strftime("%d.%m.%Y %H:%M") if g.baslangic else "—"}')
                            + (f'\n📝 {g.aciklama[:100]}' if g.aciklama else ''))
            elif son_komut == 'fatura':
                from app.models.fatura import Fatura
                f = Fatura.query.get(secilen['id'])
                if f:
                    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '?'
                    return (f'🧾 *Fatura: {f.fatura_no}*\n\n'
                            f'👤 Alıcı: {f.alici_ad or "—"}\n'
                            f'💰 Tutar: {f_tl(f.tutar)} TL\n'
                            f'📊 KDV: {f_tl(f.kdv_tutar)} TL (%{f.kdv_oran or 20})\n'
                            f'💵 Toplam: {f_tl(f.toplam)} TL\n'
                            f'📋 Durum: {f.durum or "taslak"}\n'
                            f'🏷 Tip: {f.tip or "—"}')
            elif son_komut == 'hatirlatma':
                n = Not.query.get(secilen['id'])
                if n:
                    return (f'🧠 *Hatırlatma*\n\n'
                            f'📝 {n.icerik}\n'
                            f'📅 {n.olusturma.strftime("%d.%m.%Y %H:%M") if n.olusturma else "—"}')

        if filtre.startswith('sicaklik_') and son_komut == 'musteri':
            hedef = filtre.split('_')[1]
            sonuclar = Musteri.query.filter(Musteri.id.in_(ids), Musteri.sicaklik == hedef).all()
            if not sonuclar:
                return f'📭 Listede {hedef} müşteri yok.'
            satirlar = [f'*{i+1}.* {"🔥" if hedef == "sicak" else "🟡" if hedef == "ilgili" else "❄️"} {m.ad_soyad} — {m.telefon or "—"} ({m.islem_turu or "?"})' for i, m in enumerate(sonuclar)]
            session['son_liste'] = [{'id': m.id} for m in sonuclar]
            return f'👥 *{hedef.capitalize()} müşteriler ({len(sonuclar)}):*\n\n' + '\n'.join(satirlar)

        if filtre.startswith('islem_'):
            hedef_islem = 'kira' if 'kira' in filtre else 'satis'
            hedef_label = 'Kiralık' if hedef_islem == 'kira' else 'Satılık'
            if son_komut == 'musteri':
                sonuclar = Musteri.query.filter(Musteri.id.in_(ids), Musteri.islem_turu == hedef_islem).all()
                if not sonuclar:
                    return f'📭 Listede {hedef_label.lower()} arayan müşteri yok.'
                satirlar = [f'*{i+1}.* {m.ad_soyad} — {m.telefon or "—"}' for i, m in enumerate(sonuclar)]
                session['son_liste'] = [{'id': m.id} for m in sonuclar]
                return f'👥 *{hedef_label} arayan müşteriler ({len(sonuclar)}):*\n\n' + '\n'.join(satirlar)
            elif son_komut == 'mulk':
                sonuclar = Mulk.query.filter(Mulk.id.in_(ids), Mulk.islem_turu == hedef_islem).all()
                if not sonuclar:
                    return f'📭 Listede {hedef_label.lower()} mülk yok.'
                f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
                satirlar = [f'*{i+1}.* {m.baslik or "—"} — {f_tl(m.fiyat)}' for i, m in enumerate(sonuclar)]
                session['son_liste'] = [{'id': m.id} for m in sonuclar]
                return f'🏢 *{hedef_label} mülkler ({len(sonuclar)}):*\n\n' + '\n'.join(satirlar)

        if filtre == 'devam':
            offset = session.get('son_offset', 10)
            if son_komut == 'musteri':
                sonuclar = Musteri.query.filter_by(emlakci_id=emlakci.id).order_by(Musteri.olusturma.desc()).offset(offset).limit(10).all()
                if not sonuclar:
                    return '📭 Daha fazla müşteri yok.'
                satirlar = [f'*{offset+i+1}.* {m.ad_soyad} — {m.telefon or "—"} ({m.islem_turu or "?"})' for i, m in enumerate(sonuclar)]
                session['son_liste'] = [{'id': m.id} for m in sonuclar]
                session['son_offset'] = offset + 10
                return f'👥 *Müşteriler (devam):*\n\n' + '\n'.join(satirlar)
            elif son_komut == 'mulk':
                sonuclar = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).order_by(Mulk.olusturma.desc()).offset(offset).limit(10).all()
                if not sonuclar:
                    return '📭 Daha fazla mülk yok.'
                f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
                satirlar = [f'*{offset+i+1}.* {m.baslik or "—"} — {f_tl(m.fiyat)}' for i, m in enumerate(sonuclar)]
                session['son_liste'] = [{'id': m.id} for m in sonuclar]
                session['son_offset'] = offset + 10
                return f'🏢 *Portföy (devam):*\n\n' + '\n'.join(satirlar)
            elif son_komut == 'gorev':
                from app.models.planlama import Gorev
                sonuclar = Gorev.query.filter_by(emlakci_id=emlakci.id).filter(Gorev.durum != 'tamamlandi').offset(offset).limit(10).all()
                if not sonuclar:
                    return '📭 Daha fazla görev yok.'
                satirlar = [f'*{offset+i+1}.* {"📌"} {g.baslik}' for i, g in enumerate(sonuclar)]
                session['son_liste'] = [{'id': g.id, 'tip': 'gorev'} for g in sonuclar]
                session['son_offset'] = offset + 10
                return f'📅 *Görevler (devam):*\n\n' + '\n'.join(satirlar)
            elif son_komut == 'fatura':
                from app.models.fatura import Fatura
                sonuclar = Fatura.query.filter_by(emlakci_id=emlakci.id).order_by(Fatura.olusturma.desc()).offset(offset).limit(10).all()
                if not sonuclar:
                    return '📭 Daha fazla fatura yok.'
                satirlar = [f'*{offset+i+1}.* {f.fatura_no} — {f.alici_ad or "?"} — {int(f.toplam):,} TL'.replace(',', '.') for i, f in enumerate(sonuclar)]
                session['son_liste'] = [{'id': f.id, 'tip': 'fatura'} for f in sonuclar]
                session['son_offset'] = offset + 10
                return f'🧾 *Faturalar (devam):*\n\n' + '\n'.join(satirlar)

    return None


# ─── Direkt DB İşlemleri (sıfır AI maliyeti) ──────────────
def _komut_calistir(komut, emlakci, metin, session):
    """Pattern ile eşleşen komutu çalıştır."""

    if komut == 'yardim':
        return _yardim_mesaji(emlakci)

    if komut == 'tesekkur':
        return f'😊 Rica ederim {emlakci.ad_soyad.split(" ")[0]}! Başka bir konuda yardımcı olabilir miyim?'

    if komut == 'gunaydin':
        return _yardim_mesaji(emlakci)  # Günaydın = hoşgeldin + özet

    if komut == 'iyi_aksam':
        return f'🌙 İyi akşamlar {emlakci.ad_soyad.split(" ")[0]}! Yarın için bir şey planlamak ister misiniz?'

    if komut == 'musteri_ara':
        session['son_komut'] = 'musteri'
        return _musteri_ara(emlakci, metin)

    if komut == 'mulk_ara':
        session['son_komut'] = 'mulk'
        return _mulk_ara(emlakci, metin)

    if komut == 'harf_filtre':
        return _harf_filtre(emlakci, metin, session)

    if komut == 'musteri_liste':
        session['son_komut'] = 'musteri'
        session['son_offset'] = 10
        sonuc, liste = _musteri_listele(emlakci, session)
        return sonuc

    if komut == 'mulk_liste':
        session['son_komut'] = 'mulk'
        session['son_offset'] = 10
        sonuc, liste = _mulk_listele(emlakci, session)
        return sonuc

    if komut == 'rapor':
        session['son_komut'] = 'rapor'
        return _rapor(emlakci)

    if komut == 'musteri_ekle':
        session['bekleyen_islem'] = 'musteri_ekle'
        return ('*Yeni müşteri eklemek için bilgileri girin:*\n\n'
                'Ad Soyad, Telefon, İşlem türü (kiralık/satılık)\n\n'
                '_Örnek: Ali Yılmaz, 05321234567, kiralık_')

    if komut == 'mulk_ekle':
        session['bekleyen_islem'] = 'mulk_ekle'
        return ('*Yeni mülk eklemek için bilgileri girin:*\n\n'
                'Başlık, Adres, Tip (daire/villa/arsa), İşlem (kiralık/satılık), Fiyat\n\n'
                '_Örnek: Kadıköy 3+1 Daire, Moda Cad. No:5, daire, kiralık, 25000_')

    if komut == 'muhasebe_rapor':
        return _muhasebe_rapor(emlakci)

    if komut == 'cari_rapor':
        return _cari_rapor(emlakci)

    if komut == 'gorev_ekle':
        session['bekleyen_islem'] = 'gorev_ekle'
        return '*Görev başlığını yazın:*\n\n_Örnek: "Ahmet beye yarın saat 3te dönüş yap"_'

    if komut == 'gorev_liste':
        session['son_komut'] = 'gorev'
        return _gorev_listele(emlakci, session)

    if komut == 'bugun_ozet':
        return _bugun_ozet(emlakci)

    if komut == 'eslestirme':
        session['son_komut'] = 'eslestirme'
        return _eslestirme_ozet(emlakci)

    if komut == 'fatura_ekle':
        session['bekleyen_islem'] = 'fatura_ekle'
        return '*Fatura bilgileri:*\n\nAlıcı adı, tutar (TL), açıklama\n_Örnek: "Ali Yılmaz, 15000, komisyon"_'

    if komut == 'fatura_liste':
        session['son_komut'] = 'fatura'
        return _fatura_listele(emlakci, session)

    if komut == 'doviz_kuru':
        return _doviz_goster()

    if komut == 'altin_fiyat':
        return _doviz_goster()

    if komut == 'fiyat_cevir':
        return _fiyat_cevir(metin)

    if komut == 'yasal_bilgi':
        return ('⚖️ *Yasal durum kontrolü için:*\n\n'
                'Portföy sayfasında mülkün ⋮ menüsünden *"Yasal Durum"* butonuna tıklayın.\n'
                '10 kontrol noktası: iskan, ipotek, haciz, DASK, imar, deprem, aidat, kira, vekaletname\n\n'
                '_Veya doğrudan hangi mülk için kontrol istediğinizi yazın._')

    if komut == 'piyasa_bilgi':
        return ('📊 *Piyasa değeri analizi için:*\n\n'
                'Portföy sayfasında mülkün ⋮ menüsünden *"Piyasa Değeri"* butonuna tıklayın.\n'
                'Portföy ortalaması, ilçe karşılaştırması, m² fiyat ve değerlendirme göreceksiniz.\n'
                'PDF rapor da indirebilirsiniz.')

    # ── Excel Export ──
    if komut == 'portfoy_excel':
        sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
        if sayi == 0:
            return '📭 Portföyünüzde henüz mülk yok.'
        return ('📥 *Portföy Excel dosyanız hazır!*\n\n'
                f'🏢 {sayi} mülk · Başlık, adres, şehir, ilçe, tip, fiyat, m², oda, kat, ısıtma, eşyalı, sahibi...\n\n'
                '[📥 Excel İndir](/api/panel/yedek/portfoy-excel)\n\n'
                '_Dosya otomatik indirilecek._')

    if komut == 'musteri_excel':
        sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
        if sayi == 0:
            return '📭 Henüz müşteriniz yok.'
        return ('📥 *Müşteri Excel dosyanız hazır!*\n\n'
                f'👥 {sayi} müşteri · Ad soyad, telefon, email, TC, işlem türü, bütçe, sıcaklık, tercihler...\n\n'
                '[📥 Excel İndir](/api/panel/yedek/musteri-excel)\n\n'
                '_Dosya otomatik indirilecek._')

    if komut == 'tum_zip':
        return ('📥 *Tüm veriniz ZIP olarak hazır!*\n\n'
                '10 ayrı CSV dosyası, tek ZIP:\n'
                'musteriler.csv · portfoy.csv · gelir_gider.csv\n'
                'gorevler.csv · notlar.csv · yer_gostermeler.csv\n'
                'faturalar.csv · cariler.csv · leadler.csv · iletisim_gecmisi.csv\n\n'
                '[📥 ZIP İndir](/api/panel/yedek/indir?format=zip)\n\n'
                '_Her tablo ayrı dosya — başka sisteme aktarım için ideal._')

    if komut == 'tum_excel':
        return ('📥 *Tüm veriniz Excel olarak hazır!*\n\n'
                '10 sheet, tek dosya:\n'
                '👥 Müşteriler · 🏢 Portföy · 💰 Gelir/Gider\n'
                '📅 Görevler · 📝 Notlar · 📋 Yer Göstermeler\n'
                '🧾 Faturalar · 📒 Cariler · 🎯 Leadler · 📞 İletişim Geçmişi\n\n'
                '[📥 Tümünü İndir](/api/panel/yedek/indir)\n\n'
                '_Tüm sütunlar dahil — yedek veya taşıma için tam veri._')

    # ── Tahmin & Analiz ──
    if komut == 'satici_tahmin':
        from app.services.tahmin_motoru import satici_tahmin
        sonuclar = satici_tahmin(emlakci.id)
        if not sonuclar:
            return '🔮 Henüz yeterli veri yok. Müşteri ekledikçe tahminler oluşacak.'
        satirlar = []
        for t in sonuclar[:8]:
            ikon = '🟢' if t['puan'] >= 75 else '🟡' if t['puan'] >= 50 else '🟠' if t['puan'] >= 25 else '⚪'
            satirlar.append(f'{ikon} *{t["ad_soyad"]}* — %{t["puan"]} ({t["yorum"].split("—")[0].strip()})')
        return f'🔮 *Satıcı/Alıcı Tahmin Raporu:*\n\n' + '\n'.join(satirlar) + '\n\n_Detaylar için Isı Haritası sayfasını açın._'

    if komut == 'isi_haritasi':
        from app.services.tahmin_motoru import isi_haritasi
        sonuc = isi_haritasi(emlakci.id)
        if not sonuc:
            return '🗺 Henüz portföyünüzde yeterli veri yok. Mülk ekledikçe harita oluşacak.'
        f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '—'
        satirlar = []
        for h in sonuc[:8]:
            isi = '🔴' if h['isi_skoru'] >= 70 else '🟡' if h['isi_skoru'] >= 50 else '🔵'
            satirlar.append(f'{isi} *{h["ilce"]}* — {h["mulk_sayisi"]} mülk · {f_tl(h["m2_fiyat"])} TL/m² · %{h["kira_getirisi"]} getiri')
        return ('🗺 *Piyasa Isı Haritası:*\n\n' + '\n'.join(satirlar),  'isi_haritasi')

    # ── Emlakçı Dizini ──
    if komut in ('emlakci_ekle', 'emlakci_sil', 'emlakci_liste', 'emlakci_ara', 'emlakci_sayisi'):
        return _emlakci_komut(komut, emlakci, metin, session)

    # ── Grup Yönetimi ──
    if komut and komut.startswith('grup_'):
        return _grup_komut(komut, emlakci, metin, session)

    if komut == 'surec_ozet_cmd':
        from app.services.surec_bildirim import surec_ozet_rapor
        rapor = surec_ozet_rapor(emlakci.id)
        if not rapor:
            return '📋 Aktif süreç yok.'
        satirlar = [f'• *{s["baslik"]}* — {s["ilerleme"]} (%{s["yuzde"]})' + (f' ⚠️ {s["gun_gecti"]} gün' if s["uyari"] else '') for s in rapor]
        return f'📋 *Aktif Süreçler:*\n\n' + '\n'.join(satirlar)

    if komut == 'istatistik':
        return _istatistik_detay(emlakci)

    if komut == 'strateji':
        from app.services.akilli_oneri import stratejik_oneriler
        oneriler = stratejik_oneriler(emlakci.id)
        if not oneriler:
            return '✅ *Harika gidiyorsun!* Şu an stratejik bir sorun görünmüyor.'
        satirlar = [f'• *{o["baslik"]}*\n  {o["mesaj"]}' for o in oneriler[:5]]
        return f'🎯 *Stratejik Öneriler:*\n\n' + '\n\n'.join(satirlar)

    if komut == 'genel_ara':
        return _genel_ara(emlakci, metin)

    if komut == 'yetenek_sor':
        return ('🤖 *Evet, büyük ihtimalle yapabilirim!*\n\n'
                'Ben 100+ farklı işlem yapabilen AI emlak asistanıyım:\n\n'
                '👥 Müşteri yönetimi (ekle, düzenle, ara, grupla, eşleştir)\n'
                '🏢 Portföy yönetimi (ekle, detay, broşür, ilan, reklam)\n'
                '💰 Muhasebe (gelir/gider, cari, fatura, fiş OCR, banka import)\n'
                '📋 Planlama (görev, takvim, hatırlatma)\n'
                '📄 Belgeler (yer gösterme, kontrat, yönlendirme, sunum PDF)\n'
                '🧮 Hesaplama (kira vergisi, ROI, değer artış)\n'
                '📊 Rapor & analiz (performans, sektör, piyasa)\n'
                '📦 Toplu işlem (Excel, OCR, rehber import)\n\n'
                '_Doğrudan ne istediğinizi yazın, yapayım!_')

    if komut == 'ilan_olustur':
        return ('📝 *İlan metni oluşturmak için:*\n\n'
                'Portföy sayfasında mülkün ⋮ menüsünden *"İlan Metni"* butonuna tıklayın.\n'
                'AI otomatik olarak profesyonel ilan metni oluşturup kopyalayacak.\n\n'
                '_Veya doğrudan hangi mülk için ilan istediğinizi yazın._')

    if komut == 'sektor_bilgi':
        return ('📰 *Sektörel bilgi için:*\n\n'
                '• Uygulama menüsünden *Performans & Analiz* sayfasını açın\n'
                '• "Sektör Haberleri" veya "Piyasa Analizi" butonuna tıklayın\n'
                '• AI güncel bilgileri özetleyecek\n\n'
                '_Veya doğrudan sorunuzu yazın, AI cevaplasın._')

    if komut == 'performans':
        return _performans_ozet(emlakci)

    if komut == 'not_ekle':
        session['bekleyen_islem'] = 'not_ekle'
        return '*Not yazın:*'

    if komut == 'unutma':
        session['bekleyen_islem'] = 'unutma'
        return '*Neyi hatırlamamı istiyorsunuz?*\n\n_Örnek: "Ahmet beye yarın dönüş yap" veya "Kadıköy dairesi 25.000 TL ye düştü"_'

    if komut == 'hatirlatma_liste':
        session['son_komut'] = 'hatirlatma'
        return _hatirlatma_listele(emlakci, session)

    return None


def _musteri_listele(emlakci, session=None):
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).order_by(Musteri.olusturma.desc()).limit(10).all()
    if not musteriler:
        return '📭 Henüz müşteriniz yok.\n\n_"Müşteri ekle" yazarak yeni müşteri ekleyebilirsiniz._', []
    if session is not None:
        session['son_liste'] = [{'id': m.id} for m in musteriler]
    satirlar = [f'*{i+1}.* {m.ad_soyad} — {m.telefon or "tel yok"} ({m.islem_turu or "?"})' for i, m in enumerate(musteriler)]
    toplam = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    ek = f'\n\n_Toplam {toplam} müşteri. "devam" yazarak daha fazla görebilirsiniz._' if toplam > 10 else ''
    return f'👥 *Müşterileriniz* ({toplam})\n\n' + '\n'.join(satirlar) + ek, musteriler


def _harf_filtre(emlakci, metin, session):
    """'A ile başlayanlar', 'baş harfi M' gibi bağlamsal filtreleme."""
    # Harfi çıkar
    m = re.search(r'(\w)\s*(?:ile|harfi|harfiyle)\s*(?:basla|başla)', metin.lower())
    if not m:
        m = re.search(r'(?:bas|baş)\s*(?:harf|harfi)\s*(\w)', metin.lower())
    if not m:
        m = re.search(r'(\w)\s*ile\s*(?:basla|başla)yan', metin.lower())
    harf = m.group(1).upper() if m else metin.strip()[0].upper()

    # Bağlamdan ne aradığını anla
    metin_lower = metin.lower()
    if 'müşteri' in metin_lower or 'musteri' in metin_lower:
        hedef = 'musteri'
    elif 'mülk' in metin_lower or 'mulk' in metin_lower or 'portföy' in metin_lower or 'portfoy' in metin_lower:
        hedef = 'mulk'
    else:
        # Bağlamdan: son komut ne idi?
        hedef = session.get('son_komut', 'musteri')

    if hedef == 'mulk':
        sonuclar = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).filter(
            Mulk.baslik.ilike(f'{harf}%')
        ).limit(10).all()
        if not sonuclar:
            return f'🔍 "{harf}" harfi ile başlayan mülk bulunamadı.'
        f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
        satirlar = [f'*{i+1}.* {m.baslik or "—"} — {f_tl(m.fiyat)} ({m.islem_turu or "?"})' for i, m in enumerate(sonuclar)]
        return f'🏢 *"{harf}" ile başlayan mülkler ({len(sonuclar)}):*\n\n' + '\n'.join(satirlar)
    else:
        sonuclar = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(
            Musteri.ad_soyad.ilike(f'{harf}%')
        ).limit(10).all()
        if not sonuclar:
            return f'🔍 "{harf}" harfi ile başlayan müşteri bulunamadı.'
        satirlar = [f'*{i+1}.* {m.ad_soyad} — {m.telefon or "tel yok"} ({m.islem_turu or "?"})' for i, m in enumerate(sonuclar)]
        return f'👥 *"{harf}" ile başlayan müşteriler ({len(sonuclar)}):*\n\n' + '\n'.join(satirlar)


def _musteri_ara(emlakci, metin):
    """İsim/telefon ile müşteri ara."""
    # Arama kelimesini çıkar
    metin_lower = metin.lower()
    # "müşterilerde ara Ali" → "ali"
    # "Ali isminde müşteri var mı" → "ali"
    # "müşterilerde Ali ara" → "ali"
    sorgu = re.sub(r'(?:musteri|müşteri)(?:ler)?(?:de|da|den|dan|i|ı|m|mda)?\s*(?:ara|bul)?\s*', '', metin_lower).strip()
    sorgu = re.sub(r'\s*(?:ara|bul|var\s*m[ıi]|olmal[ıi]|isminde|adında|adlı|isimli|diye)\s*', ' ', sorgu).strip()
    sorgu = re.sub(r'(?:musteri|müşteri)\s*', '', sorgu).strip()
    if not sorgu or len(sorgu) < 2:
        return '🔍 Kimi aramak istiyorsunuz? Örnek: "müşterilerde Ali ara"'

    sonuclar = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(
        db.or_(
            Musteri.ad_soyad.ilike(f'%{sorgu}%'),
            Musteri.telefon.ilike(f'%{sorgu}%'),
            Musteri.tercih_notlar.ilike(f'%{sorgu}%'),
        )
    ).limit(10).all()

    if not sonuclar:
        return f'🔍 "{sorgu}" ile eşleşen müşteri bulunamadı.\n\n_Toplam {Musteri.query.filter_by(emlakci_id=emlakci.id).count()} müşteriniz var._'

    satirlar = []
    for i, m in enumerate(sonuclar):
        sicaklik_ikon = {'sicak': '🔥', 'ilgili': '🟡', 'soguk': '❄️'}.get(m.sicaklik, '⚪')
        satirlar.append(f'*{i+1}.* {sicaklik_ikon} {m.ad_soyad} — {m.telefon or "tel yok"} ({m.islem_turu or "?"})')
    return f'🔍 *"{sorgu}" arama sonuçları:* ({len(sonuclar)})\n\n' + '\n'.join(satirlar)


def _mulk_ara(emlakci, metin):
    """İsim/adres/ilçe ile mülk ara."""
    metin_lower = metin.lower()
    sorgu = re.sub(r'(?:mulk|mülk|portfoy|portföy)(?:te|da|de)?\s*(?:ara|bul)?\s*', '', metin_lower).strip()
    sorgu = re.sub(r'\s*(?:ara|bul)\s*', ' ', sorgu).strip()
    if not sorgu or len(sorgu) < 2:
        return '🔍 Ne aramak istiyorsunuz? Örnek: "portföyde Kadıköy ara"'

    sonuclar = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).filter(
        db.or_(
            Mulk.baslik.ilike(f'%{sorgu}%'),
            Mulk.adres.ilike(f'%{sorgu}%'),
            Mulk.sehir.ilike(f'%{sorgu}%'),
            Mulk.ilce.ilike(f'%{sorgu}%'),
        )
    ).limit(10).all()

    if not sonuclar:
        return f'🔍 "{sorgu}" ile eşleşen mülk bulunamadı.\n\n_Portföyünüzde {Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()} mülk var._'

    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
    satirlar = []
    for i, m in enumerate(sonuclar):
        satirlar.append(f'*{i+1}.* {m.baslik or m.adres or "—"} — {f_tl(m.fiyat)} ({m.islem_turu or "?"})')
    return f'🔍 *"{sorgu}" arama sonuçları:* ({len(sonuclar)})\n\n' + '\n'.join(satirlar)


def _mulk_listele(emlakci, session=None):
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).order_by(Mulk.olusturma.desc()).limit(10).all()
    if not mulkler:
        return '📭 Henüz portföyünüzde mülk yok.\n\n_"Mülk ekle" yazarak yeni mülk ekleyebilirsiniz._', []
    if session is not None:
        session['son_liste'] = [{'id': m.id} for m in mulkler]
    satirlar = []
    for i, m in enumerate(mulkler):
        fiyat = f'{int(m.fiyat):,}'.replace(',', '.') + ' TL' if m.fiyat else '?'
        satirlar.append(f'*{i+1}.* {m.baslik or m.adres or "—"} — {fiyat} ({m.islem_turu or "?"})')
    toplam = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    ek = f'\n\n_Toplam {toplam} mülk. "devam" yazarak daha fazla görebilirsiniz._' if toplam > 10 else ''
    return f'🏢 *Portföyünüz* ({toplam})\n\n' + '\n'.join(satirlar) + ek, mulkler


def _rapor(emlakci):
    m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    yg_sayi = YerGosterme.query.filter_by(emlakci_id=emlakci.id).count()
    return (f'📊 *Genel Durum*\n\n'
            f'👥 Müşteriler: *{m_sayi}*\n'
            f'🏢 Portföy: *{p_sayi}*\n'
            f'📋 Yer gösterme: *{yg_sayi}*\n'
            f'💎 Kredi: *{emlakci.kredi}*')


def _yardim_mesaji(emlakci):
    # Proaktif günlük özet
    ozet_ek = ''
    try:
        from app.models.planlama import Gorev
        from app.models.lead import Lead
        from datetime import timedelta
        bugun = datetime.now().replace(hour=0, minute=0, second=0)
        yarin = bugun + timedelta(days=1)
        gorev_sayi = Gorev.query.filter(Gorev.emlakci_id == emlakci.id, Gorev.baslangic >= bugun, Gorev.baslangic < yarin, Gorev.durum != 'iptal').count()
        yeni_lead = Lead.query.filter_by(emlakci_id=emlakci.id, durum='yeni').count()
        if gorev_sayi or yeni_lead:
            ozet_ek = f'\n📅 Bugün *{gorev_sayi}* görev · 🎯 *{yeni_lead}* yeni lead\n'
    except Exception:
        pass

    # Proaktif uyarılar
    uyarilar = ''
    try:
        from app.models.lead import Lead
        from app.services.yedekleme import yedek_durumu
        soguk_lead = Lead.query.filter_by(emlakci_id=emlakci.id, durum='yeni').count()
        yd = yedek_durumu(emlakci)
        if soguk_lead > 0:
            uyarilar += f'\n⚠️ *{soguk_lead} yeni lead* — dönüş yapılmadı!'
        if yd.get('uyari'):
            uyarilar += f'\n💾 {yd["mesaj"]}'
        if emlakci.kredi and emlakci.kredi < 5:
            uyarilar += f'\n💎 Krediniz düşük: *{emlakci.kredi}*'
    except Exception:
        pass

    return (f'👋 *Merhaba {emlakci.ad_soyad.split(" ")[0]}!*\n{ozet_ek}{uyarilar}\n'
            'Ben Emlakisim AI Asistanınızım. İşte yapabileceklerim:\n\n'
            '👥 *Müşteri:* "müşteri ekle", "müşteri listele"\n'
            '🏢 *Portföy:* "mülk ekle", "portföy listele"\n'
            '📋 *Belgeler:* "yer gösterme oluştur"\n'
            '📊 *Rapor:* "rapor", "özet"\n'
            '📝 *Not:* "not ekle"\n'
            '📅 *Planlama:* "görev ekle", "bugün özet"\n'
            '🔗 *Eşleştirme:* "eşleştir"\n'
            '🧾 *Fatura:* "fatura ekle", "fatura listele"\n'
            '💰 *Muhasebe:* "kar zarar", "cari"\n'
            '🧠 *Unutma:* "unutma: Ahmet beye yarın dönüş yap"\n'
            '💡 *Hesaplama:* "kira vergisi hesapla"\n'
            '📒 *Emlakçı Dizini:* "emlakçı ekle", "emlakçı listele", "emlakçı ara"\n'
            '👥 *Gruplar:* "grup kur", "gruplarım", "grup eşleştir", "portföyü gruba aç"\n\n'
            '💡 *İpucu:* Excel\'den toplu müşteri/portföy ekleyebilirsiniz!\n'
            'Fotoğraf çekerek sahibinden ilanlarını portföye aktarabilirsiniz!\n\n'
            + _hizli_erisim_mesaji(emlakci) +
            '_Doğal dille yazın, anlayacağım._')


def _hizli_erisim_mesaji(emlakci):
    """Kişiselleşmiş hızlı erişim önerileri."""
    try:
        from app.services.kisisellesme import hizli_erisim_onerileri
        oneriler = hizli_erisim_onerileri(emlakci.id)
        if oneriler:
            komutlar = ', '.join([f'"{o["komut"]}"' for o in oneriler[:4]])
            return f'⚡ *Sık kullandıkların:* {komutlar}\n\n'
    except Exception:
        pass
    return ''


# ─── Bekleyen İşlem Yürütme ────────────────────────────────
def _bekleyen_isle(session, emlakci, metin):
    """Adımlı komut tamamlama (kullanıcı bilgi girdikten sonra)."""
    islem = session.pop('bekleyen_islem', None)
    if not islem:
        return None

    if islem == 'musteri_ekle':
        return _musteri_kaydet(emlakci, metin)
    if islem == 'mulk_ekle':
        return _mulk_kaydet(emlakci, metin)
    if islem == 'not_ekle':
        return _not_kaydet(emlakci, metin)
    if islem == 'unutma':
        return _unutma_kaydet(emlakci, metin)
    if islem == 'gorev_ekle':
        return _gorev_kaydet(emlakci, metin)
    if islem == 'fatura_ekle':
        return _fatura_kaydet(emlakci, metin)
    if islem == 'emlakci_ekle_bilgi':
        return _emlakci_kaydet(emlakci, metin)
    if islem == 'grup_kur_bilgi':
        return _grup_kaydet(emlakci, metin)
    if islem == 'grup_uye_davet_bilgi':
        return _grup_uye_davet_isle(emlakci, metin, session)
    return None


def _musteri_kaydet(emlakci, metin):
    """Serbest metinden müşteri bilgisi çıkar ve kaydet."""
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    ad = parcalar[0] if parcalar else metin.strip()
    telefon = parcalar[1] if len(parcalar) > 1 else ''
    islem = 'kira' if len(parcalar) > 2 and 'kira' in parcalar[2].lower() else 'satis'

    musteri = Musteri(
        emlakci_id=emlakci.id,
        ad_soyad=ad,
        telefon=telefon,
        islem_turu=islem,
    )
    db.session.add(musteri)
    db.session.commit()

    # Konuşma state güncelle
    from app.services.hafiza import state_guncelle_islem
    state_guncelle_islem(emlakci.id, 'musteri_ekle', musteri_id=musteri.id)

    # Akıllı eşleştirme
    from app.services.eslestirme import eslesdir
    eslesimler = eslesdir(emlakci.id, musteri_id=musteri.id, limit=3)
    eslesme_mesaj = ''
    if eslesimler:
        eslesme_mesaj = f'\n\n🔗 *{len(eslesimler)} uygun mülk bulundu:*'
        for e in eslesimler[:3]:
            eslesme_mesaj += f'\n  • {e["baslik"]} — {e["fiyat_str"]} (%{e["puan"]})'

    # Zincirleme
    from app.services.zincirleme import musteri_eklendi_sonrasi
    try:
        zincir = musteri_eklendi_sonrasi(emlakci, musteri)
        zincir_mesaj = '\n'.join(zincir) if zincir else ''
    except Exception:
        zincir_mesaj = ''

    return f'✅ *Müşteri eklendi!*\n\n👤 {ad}\n📞 {telefon or "—"}\n🏷 {islem.capitalize()}' + eslesme_mesaj + (f'\n\n{zincir_mesaj}' if zincir_mesaj else '')


def _mulk_kaydet(emlakci, metin):
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    baslik = parcalar[0] if parcalar else metin.strip()
    adres = parcalar[1] if len(parcalar) > 1 else ''
    tip = parcalar[2] if len(parcalar) > 2 else 'daire'
    islem = 'kira' if len(parcalar) > 3 and 'kira' in parcalar[3].lower() else 'satis'
    fiyat = None
    if len(parcalar) > 4:
        try: fiyat = float(re.sub(r'[^\d.]', '', parcalar[4]))
        except: pass

    mulk = Mulk(
        emlakci_id=emlakci.id,
        baslik=baslik,
        adres=adres,
        tip=tip,
        islem_turu=islem,
        fiyat=fiyat,
    )
    db.session.add(mulk)
    db.session.commit()

    from app.services.zincirleme import mulk_eklendi_sonrasi
    try:
        zincir = mulk_eklendi_sonrasi(emlakci, mulk)
        zincir_mesaj = '\n'.join(zincir) if zincir else ''
    except Exception:
        zincir_mesaj = ''

    fiyat_str = f'{int(fiyat):,}'.replace(',', '.') + ' TL' if fiyat else '—'
    return f'✅ *Mülk eklendi!*\n\n🏢 {baslik}\n📍 {adres or "—"}\n💰 {fiyat_str}' + (f'\n\n{zincir_mesaj}' if zincir_mesaj else '')


def _not_kaydet(emlakci, metin):
    not_obj = Not(emlakci_id=emlakci.id, icerik=metin, etiket='not')
    db.session.add(not_obj)
    db.session.commit()
    return f'✅ *Not kaydedildi.*\n\n📝 {metin[:100]}'


def _muhasebe_rapor(emlakci):
    """Muhasebe özet raporu."""
    from app.models.muhasebe import GelirGider
    kayitlar = GelirGider.query.filter_by(emlakci_id=emlakci.id).all()
    gelir = sum(k.tutar for k in kayitlar if k.tip == 'gelir')
    gider = sum(k.tutar for k in kayitlar if k.tip == 'gider')
    kar = gelir - gider
    f = lambda v: f'{int(v):,}'.replace(',', '.')
    return (f'💰 *Muhasebe Özeti*\n\n'
            f'📈 Gelir: *{f(gelir)} TL*\n'
            f'📉 Gider: *{f(gider)} TL*\n'
            f'{"🟢" if kar >= 0 else "🔴"} {"Kâr" if kar >= 0 else "Zarar"}: *{f(abs(kar))} TL*\n'
            f'📊 Kâr marjı: *%{(kar/gelir*100):.1f}*\n' if gelir > 0 else
            f'💰 *Muhasebe Özeti*\n\nHenüz gelir/gider kaydı yok.')


def _cari_rapor(emlakci):
    """Cari hesap özeti."""
    from app.models.muhasebe import Cari
    cariler = Cari.query.filter_by(emlakci_id=emlakci.id).all()
    if not cariler:
        return '📒 Henüz cari hesap yok.\n\n_Muhasebe menüsünden cari hesap ekleyebilirsiniz._'
    alacak = sum(c.bakiye for c in cariler if c.bakiye > 0)
    borc = sum(abs(c.bakiye) for c in cariler if c.bakiye < 0)
    f = lambda v: f'{int(v):,}'.replace(',', '.')
    satirlar = [f'  *{c.ad}*: {"+" if c.bakiye >= 0 else ""}{f(c.bakiye)} TL' for c in cariler[:8]]
    return (f'📒 *Cari Hesaplar*\n\n'
            f'🟢 Toplam Alacak: *{f(alacak)} TL*\n'
            f'🔴 Toplam Borç: *{f(borc)} TL*\n\n'
            + '\n'.join(satirlar))


def _doviz_goster():
    """Döviz + altın kurları göster."""
    from app.services.doviz import kurlari_getir
    k = kurlari_getir()
    f = lambda v: f'{v:,.2f}'.replace(',', '.') if v else '—'
    usd = k.get('USD', {})
    eur = k.get('EUR', {})
    gbp = k.get('GBP', {})
    altin = k.get('ALTIN_GRAM')
    return (f'💱 *Güncel Kurlar* ({k.get("tarih", "?")})\n\n'
            f'🇺🇸 Dolar: *{f(usd.get("satis"))} TL*\n'
            f'🇪🇺 Euro: *{f(eur.get("satis"))} TL*\n'
            f'🇬🇧 Sterlin: *{f(gbp.get("satis"))} TL*\n'
            f'🥇 Altın (gram): *{f(altin)} TL*\n\n'
            f'_Kaynak: {k.get("kaynak", "?")}_')


def _fiyat_cevir(metin):
    """Metindeki TL tutarı dövize çevir."""
    import re as _re
    m = _re.search(r'([\d.,]+)', metin.replace('.', '').replace(',', '.'))
    if not m:
        return 'Tutar bulunamadı. Örnek: "5000000 TL dolar"'
    try:
        tutar = float(m.group(1))
    except ValueError:
        return 'Geçersiz tutar.'

    from app.services.doviz import fiyat_donustur
    s = fiyat_donustur(tutar)
    f_n = lambda v: f'{v:,.2f}'.replace(',', '.')
    f_tl = lambda v: f'{int(v):,}'.replace(',', '.')

    return (f'💱 *{f_tl(tutar)} TL =*\n\n'
            f'🇺🇸 ${f_n(s.get("USD", 0))}\n'
            f'🇪🇺 €{f_n(s.get("EUR", 0))}\n'
            f'🇬🇧 £{f_n(s.get("GBP", 0))}\n'
            f'🥇 {f_n(s.get("ALTIN_GRAM", 0))} gram altın\n\n'
            f'_Kur: ${s.get("kurlar", {}).get("USD", "?")} · {s.get("tarih", "")}_')


def _istatistik_detay(emlakci):
    """Detaylı istatistik — müşteri + portföy dağılım."""
    from collections import Counter
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).all()
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).all()

    m_sic = Counter(m.sicaklik or 'orta' for m in musteriler)
    m_isl = Counter(m.islem_turu or '?' for m in musteriler)
    p_tip = Counter(m.tip or '?' for m in mulkler)
    p_isl = Counter(m.islem_turu or '?' for m in mulkler)

    f = lambda d: ', '.join([f'{k}: {v}' for k, v in d.most_common(5)])

    return (f'📊 *Detaylı İstatistik*\n\n'
            f'👥 *Müşteriler ({len(musteriler)}):*\n'
            f'  Sıcaklık: {f(m_sic)}\n'
            f'  İşlem: {f(m_isl)}\n\n'
            f'🏢 *Portföy ({len(mulkler)}):*\n'
            f'  Tip: {f(p_tip)}\n'
            f'  İşlem: {f(p_isl)}')


def _genel_ara(emlakci, metin):
    """Sohbetten genel arama."""
    import re as _re
    m = _re.search(r'(?:ara|bul)\s+(.+)', metin.lower())
    sorgu = m.group(1).strip() if m else metin.strip()
    from app.services.akilli_arama import genel_arama
    sonuc = genel_arama(emlakci.id, sorgu)
    if not sonuc['sonuclar']:
        return f'🔍 "{sorgu}" için sonuç bulunamadı.'
    satirlar = [f'{s["ikon"]} *{s["baslik"]}* — {s["detay"]}' for s in sonuc['sonuclar'][:8]]
    return f'🔍 *"{sorgu}" arama sonuçları:*\n\n' + '\n'.join(satirlar)


def _performans_ozet(emlakci):
    """Genel performans özeti."""
    from app.models.muhasebe import GelirGider
    from app.models.lead import Lead
    m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    yg_sayi = YerGosterme.query.filter_by(emlakci_id=emlakci.id).count()
    lead_yeni = Lead.query.filter_by(emlakci_id=emlakci.id, durum='yeni').count()
    kayitlar = GelirGider.query.filter_by(emlakci_id=emlakci.id).all()
    gelir = sum(k.tutar for k in kayitlar if k.tip == 'gelir')
    gider = sum(k.tutar for k in kayitlar if k.tip == 'gider')
    f = lambda v: f'{int(v):,}'.replace(',', '.')

    return (f'🏆 *Performans Özeti*\n\n'
            f'👥 Müşteri: *{m_sayi}*\n'
            f'🏢 Portföy: *{p_sayi}*\n'
            f'📋 Yer gösterme: *{yg_sayi}*\n'
            f'🎯 Yeni lead: *{lead_yeni}*\n'
            f'📈 Gelir: *{f(gelir)} TL*\n'
            f'📉 Gider: *{f(gider)} TL*\n'
            f'{"🟢" if gelir >= gider else "🔴"} Net: *{f(gelir - gider)} TL*\n'
            f'💎 Kredi: *{emlakci.kredi}*')


def _gorev_listele(emlakci, session=None):
    from app.models.planlama import Gorev
    gorevler = Gorev.query.filter_by(emlakci_id=emlakci.id).filter(Gorev.durum != 'tamamlandi').order_by(Gorev.olusturma.desc()).limit(10).all()
    if not gorevler:
        return '📅 Aktif görev yok.\n\n_"Görev ekle" yazarak yeni görev ekleyebilirsiniz._'
    if session is not None:
        session['son_liste'] = [{'id': g.id, 'tip': 'gorev'} for g in gorevler]
    satirlar = [f'*{i+1}.* {"✅" if g.durum == "tamamlandi" else "📌"} {g.baslik}' for i, g in enumerate(gorevler)]
    return f'📅 *Görevleriniz* ({len(gorevler)})\n\n' + '\n'.join(satirlar)


def _bugun_ozet(emlakci):
    from app.models.planlama import Gorev
    from datetime import datetime, timedelta
    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
    yarin = bugun + timedelta(days=1)
    gorevler = Gorev.query.filter(Gorev.emlakci_id == emlakci.id, Gorev.baslangic >= bugun, Gorev.baslangic < yarin, Gorev.durum != 'iptal').all()
    m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    mesaj = f'☀️ *Günlük Özet*\n\n👥 {m_sayi} müşteri · 🏢 {p_sayi} mülk\n'
    if gorevler:
        mesaj += f'\n📅 *Bugünkü görevler ({len(gorevler)}):*\n'
        for g in gorevler:
            saat = g.baslangic.strftime('%H:%M') if g.baslangic else ''
            mesaj += f'  • {g.baslik} {saat}\n'
    else:
        mesaj += '\n📅 Bugün planlanmış görev yok.'
    return mesaj


def _eslestirme_ozet(emlakci):
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).all()
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).all()
    eslesme = 0
    for m in musteriler:
        for p in mulkler:
            if m.islem_turu == p.islem_turu:
                if m.butce_max and p.fiyat and p.fiyat <= m.butce_max:
                    eslesme += 1
    return (f'🔗 *Eşleştirme Özeti*\n\n'
            f'👥 {len(musteriler)} müşteri · 🏢 {len(mulkler)} mülk\n'
            f'✅ {eslesme} potansiyel eşleşme\n\n'
            f'_Detaylı eşleştirme için uygulama menüsünden "Eşleştirme" sayfasını açın._')


def _gorev_kaydet(emlakci, metin):
    from app.models.planlama import Gorev
    g = Gorev(emlakci_id=emlakci.id, baslik=metin[:200], tip='gorev')
    db.session.add(g)
    db.session.commit()
    return f'✅ *Görev eklendi!*\n\n📌 {metin[:100]}'


def _fatura_kaydet(emlakci, metin):
    from app.models.fatura import Fatura
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    alici = parcalar[0] if parcalar else ''
    tutar = 0
    if len(parcalar) > 1:
        try: tutar = float(re.sub(r'[^\d.]', '', parcalar[1]))
        except: pass
    aciklama = parcalar[2] if len(parcalar) > 2 else 'hizmet'

    from datetime import datetime
    f = Fatura(
        emlakci_id=emlakci.id,
        fatura_no=f'F-{datetime.now().strftime("%Y%m%d%H%M")}',
        tip='hizmet', alici_ad=alici, tutar=tutar,
        kdv_oran=20, kdv_tutar=round(tutar * 0.2, 2),
        toplam=round(tutar * 1.2, 2),
    )
    db.session.add(f)
    db.session.commit()
    return f'✅ *Fatura oluşturuldu!*\n\n🧾 {f.fatura_no}\n👤 {alici}\n💰 {int(f.toplam):,} TL (KDV dahil)'.replace(',', '.')


def _fatura_listele(emlakci, session=None):
    from app.models.fatura import Fatura
    faturalar = Fatura.query.filter_by(emlakci_id=emlakci.id).order_by(Fatura.olusturma.desc()).limit(10).all()
    if not faturalar:
        return '🧾 Henüz fatura yok.'
    if session is not None:
        session['son_liste'] = [{'id': f.id, 'tip': 'fatura'} for f in faturalar]
    satirlar = [f'*{i+1}.* {f.fatura_no} — {f.alici_ad or "?"} — {int(f.toplam):,} TL — {f.durum}'.replace(',', '.') for i, f in enumerate(faturalar)]
    return f'🧾 *Son Faturalar ({len(faturalar)})*\n\n' + '\n'.join(satirlar)


def _unutma_kaydet(emlakci, metin):
    """'Unutma' komutu — önemli bilgiyi hatırlatma olarak kaydet."""
    not_obj = Not(emlakci_id=emlakci.id, icerik=metin, etiket='hatirlatici')
    db.session.add(not_obj)
    db.session.commit()
    return f'🧠 *Hatırladım!*\n\n📌 {metin[:150]}\n\n_"Hatırlatmalar" yazarak tüm kayıtları görebilirsiniz._'


def _hatirlatma_listele(emlakci, session=None):
    """Kaydedilmiş hatırlatmaları listele."""
    notlar = Not.query.filter_by(emlakci_id=emlakci.id, etiket='hatirlatici', tamamlandi=False)\
        .order_by(Not.olusturma.desc()).limit(10).all()
    if not notlar:
        return '📭 Henüz hatırlatma yok.\n\n_"Unutma: ..." yazarak hatırlatma ekleyebilirsiniz._'
    if session is not None:
        session['son_liste'] = [{'id': n.id, 'tip': 'not'} for n in notlar]
    satirlar = [f'*{i+1}.* {n.icerik[:80]}' for i, n in enumerate(notlar)]
    return f'🧠 *Hatırlatmalarınız* ({len(notlar)})\n\n' + '\n'.join(satirlar)


# ─── Emlakçı Dizini Komutları ─────────────────────────────
def _emlakci_komut(komut, emlakci, metin, session):
    """Emlakçı dizini sohbet komutları."""
    from app.models.grup import EmlakciDizin

    if komut == 'emlakci_ekle':
        session['bekleyen_islem'] = 'emlakci_ekle_bilgi'
        return ('📒 *Yeni emlakçı ekleyelim!*\n\n'
                'Bilgileri virgülle ayırarak yazın:\n'
                'Ad Soyad, Telefon, Bölge, Uzmanlık, Acente\n\n'
                '_Örnek: Mehmet Kaya, 05321234567, Kadıköy, Satılık Daire, ABC Emlak_\n'
                '_Sadece ad yazmanız da yeterli._')

    if komut == 'emlakci_sayisi':
        sayi = EmlakciDizin.query.filter_by(ekleyen_id=emlakci.id).count()
        return f'📒 Emlakçı dizininizde *{sayi}* kayıt var.'

    if komut == 'emlakci_liste':
        kayitlar = EmlakciDizin.query.filter_by(ekleyen_id=emlakci.id).order_by(EmlakciDizin.ad_soyad).limit(15).all()
        if not kayitlar:
            return ('📒 Emlakçı dizininiz henüz boş.\n\n'
                    '_"Emlakçı ekle" yazarak yeni emlakçı kaydedebilirsiniz._')
        satirlar = []
        for i, e in enumerate(kayitlar):
            detay = []
            if e.telefon:
                detay.append(f'📞 {e.telefon}')
            if e.bolge:
                detay.append(f'📍 {e.bolge}')
            if e.uzmanlik:
                detay.append(f'🏷 {e.uzmanlik}')
            if e.acente:
                detay.append(f'🏢 {e.acente}')
            satirlar.append(f'*{i+1}.* {e.ad_soyad}' + (f'\n   {" · ".join(detay)}' if detay else ''))
        toplam = EmlakciDizin.query.filter_by(ekleyen_id=emlakci.id).count()
        return f'📒 *Emlakçı Dizini* ({toplam} kayıt)\n\n' + '\n'.join(satirlar)

    if komut == 'emlakci_ara':
        sorgu = re.sub(r'(?:emlakci|emlakçı)\s*(?:ara|bul)\s*', '', metin.lower()).strip()
        if not sorgu:
            return '🔍 Kimi aramak istiyorsunuz? Örnek: "emlakçı ara Mehmet"'
        kayitlar = EmlakciDizin.query.filter_by(ekleyen_id=emlakci.id).filter(
            db.or_(
                EmlakciDizin.ad_soyad.ilike(f'%{sorgu}%'),
                EmlakciDizin.bolge.ilike(f'%{sorgu}%'),
                EmlakciDizin.acente.ilike(f'%{sorgu}%'),
                EmlakciDizin.telefon.ilike(f'%{sorgu}%'),
            )
        ).limit(10).all()
        if not kayitlar:
            return f'🔍 "{sorgu}" ile eşleşen emlakçı bulunamadı.'
        satirlar = []
        for i, e in enumerate(kayitlar):
            detay = []
            if e.telefon:
                detay.append(f'📞 {e.telefon}')
            if e.bolge:
                detay.append(f'📍 {e.bolge}')
            satirlar.append(f'*{i+1}.* {e.ad_soyad}' + (f' — {" · ".join(detay)}' if detay else ''))
        return f'🔍 *"{sorgu}" arama sonuçları:*\n\n' + '\n'.join(satirlar)

    if komut == 'emlakci_sil':
        return ('📒 Emlakçı silmek için dizin sayfasından ilerleyebilirsiniz.\n\n'
                '_Silmek istediğiniz emlakçının adını yazın, ben bulayım:_\n'
                'Örnek: "Mehmet Kaya sil"')

    return None


def _emlakci_kaydet(emlakci, metin):
    """Serbest metinden emlakçı bilgisi çıkar ve kaydet."""
    from app.models.grup import EmlakciDizin
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    ad = parcalar[0] if parcalar else metin.strip()
    telefon = parcalar[1] if len(parcalar) > 1 else None
    bolge = parcalar[2] if len(parcalar) > 2 else None
    uzmanlik = parcalar[3] if len(parcalar) > 3 else None
    acente = parcalar[4] if len(parcalar) > 4 else None

    e = EmlakciDizin(
        ekleyen_id=emlakci.id, ad_soyad=ad,
        telefon=telefon, bolge=bolge,
        uzmanlik=uzmanlik, acente=acente,
    )
    db.session.add(e)
    db.session.commit()

    detaylar = []
    if telefon:
        detaylar.append(f'📞 {telefon}')
    if bolge:
        detaylar.append(f'📍 {bolge}')
    if uzmanlik:
        detaylar.append(f'🏷 {uzmanlik}')
    if acente:
        detaylar.append(f'🏢 {acente}')

    return (f'✅ *Emlakçı kaydedildi!*\n\n'
            f'👤 {ad}\n'
            + '\n'.join(detaylar) +
            '\n\n_Başka emlakçı eklemek için "emlakçı ekle" yazın._')


# ─── Grup Yönetimi Komutları ──────────────────────────────
def _grup_komut(komut, emlakci, metin, session):
    """Grup yönetimi sohbet komutları."""
    from app.models.grup import Grup, GrupUyelik, GrupBildirim, EmlakciDizin
    from app.models import Emlakci as EmlakciModel, Mulk as MulkModel, Musteri as MusteriModel

    if komut == 'grup_kur':
        # Max 2 grup kontrolü
        aktif = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='aktif').count()
        if aktif >= 2:
            return '⚠️ En fazla *2 gruba* üye olabilirsiniz. Yeni grup kurmak için mevcut bir gruptan çıkmanız gerekiyor.'
        session['bekleyen_islem'] = 'grup_kur_bilgi'
        return ('👥 *Yeni grup kuralım!*\n\n'
                'Grup adı ve sloganı virgülle ayırarak yazın:\n\n'
                '_Örnek: Kadıköy Emlakçılar, Kadıköy bölgesinde işbirliği grubu_\n'
                '_Sadece grup adı yazmanız da yeterli._')

    if komut == 'grup_sayisi':
        aktif = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='aktif').count()
        bekleyen = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='bekliyor').count()
        mesaj = f'👥 *{aktif}* gruba üyesiniz.'
        if bekleyen:
            mesaj += f'\n📩 *{bekleyen}* bekleyen davetiniz var.'
        mesaj += f'\n_(Maksimum 2 grup üyeliği)_'
        return mesaj

    if komut == 'grup_liste':
        uyelikler = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='aktif').all()
        if not uyelikler:
            return ('👥 Henüz bir gruba üye değilsiniz.\n\n'
                    '_"Grup kur" yazarak yeni bir işbirliği grubu oluşturabilirsiniz._')
        satirlar = []
        for u in uyelikler:
            g = Grup.query.get(u.grup_id)
            if not g or not g.aktif:
                continue
            uye_sayisi = GrupUyelik.query.filter_by(grup_id=g.id, durum='aktif').count()
            rol_ikon = '👑' if u.rol == 'yonetici' else '👤'
            portfoy_durum = '🏢✅' if u.portfoy_acik else '🏢❌'
            talep_durum = '👥✅' if u.talep_acik else '👥❌'
            satirlar.append(
                f'{rol_ikon} *{g.ad}*\n'
                f'   {uye_sayisi} üye · {portfoy_durum} Portföy · {talep_durum} Talep'
                + (f'\n   _{g.slogan}_' if g.slogan else '')
            )
        return f'👥 *Gruplarınız:*\n\n' + '\n\n'.join(satirlar)

    if komut == 'grup_uyeleri':
        # İlk aktif grubu bul (veya metinden grup adı çıkar)
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.\n\n_"Grup kur" yazarak yeni grup oluşturabilirsiniz._'
        uyeler = GrupUyelik.query.filter_by(grup_id=grup.id, durum='aktif').all()
        satirlar = []
        for u in uyeler:
            e = EmlakciModel.query.get(u.emlakci_id)
            if not e:
                continue
            rol_ikon = '👑' if u.rol == 'yonetici' else '👤'
            durum_detay = []
            if u.portfoy_acik:
                durum_detay.append('🏢 Portföy açık')
            if u.talep_acik:
                durum_detay.append('👥 Talep açık')
            satirlar.append(f'{rol_ikon} *{e.ad_soyad}*' + (f' — {", ".join(durum_detay)}' if durum_detay else ''))
        return f'👥 *{grup.ad} — Üyeler ({len(uyeler)}):*\n\n' + '\n'.join(satirlar)

    if komut == 'grup_davet':
        bekleyenler = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='bekliyor').all()
        if not bekleyenler:
            return '📩 Bekleyen grup davetiniz yok.'
        satirlar = []
        for u in bekleyenler:
            g = Grup.query.get(u.grup_id)
            if g:
                satirlar.append(f'• *{g.ad}*' + (f' — _{g.slogan}_' if g.slogan else ''))
        return (f'📩 *Bekleyen Davetler ({len(bekleyenler)}):*\n\n'
                + '\n'.join(satirlar) +
                '\n\n_Kabul etmek için "daveti kabul et" yazın.\nReddetmek için "daveti reddet" yazın._')

    if komut == 'grup_cik':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        if uyelik.rol == 'yonetici':
            baska_yonetici = GrupUyelik.query.filter(
                GrupUyelik.grup_id == grup.id, GrupUyelik.emlakci_id != emlakci.id,
                GrupUyelik.rol == 'yonetici', GrupUyelik.durum == 'aktif'
            ).first()
            aktif_uye = GrupUyelik.query.filter(
                GrupUyelik.grup_id == grup.id, GrupUyelik.emlakci_id != emlakci.id,
                GrupUyelik.durum == 'aktif'
            ).count()
            if aktif_uye > 0 and not baska_yonetici:
                return (f'⚠️ *{grup.ad}* grubunun tek yöneticisisiniz.\n'
                        'Çıkmak için önce başka birine yöneticilik verin:\n'
                        '_"grup yönetici ata [isim]" yazın._')
        uyelik.durum = 'cikti'
        GrupBildirim(grup_id=grup.id, emlakci_id=emlakci.id, tip='uye_cikti',
                     mesaj=f'{emlakci.ad_soyad} gruptan ayrıldı')
        kalan = GrupUyelik.query.filter_by(grup_id=grup.id, durum='aktif').count()
        if kalan <= 1:  # kendisi hala sayılıyor olabilir, commit sonrası 0 olur
            grup.aktif = False
        db.session.commit()
        return f'✅ *{grup.ad}* grubundan ayrıldınız.'

    if komut == 'grup_ayar':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        portfoy_durum = '✅ Açık' if uyelik.portfoy_acik else '❌ Kapalı'
        talep_durum = '✅ Açık' if uyelik.talep_acik else '❌ Kapalı'
        return (f'⚙️ *{grup.ad} — Paylaşım Ayarlarınız:*\n\n'
                f'🏢 Portföy paylaşımı: *{portfoy_durum}*\n'
                f'👥 Talep paylaşımı: *{talep_durum}*\n\n'
                '_Değiştirmek için:_\n'
                '• "portföyümü gruba aç"\n'
                '• "portföyümü gruba kapat"\n'
                '• "taleplerimizi gruba aç"\n'
                '• "taleplerimizi gruba kapat"')

    if komut == 'grup_portfoy_ac':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        uyelik.portfoy_acik = True
        db.session.commit()
        mulk_sayi = MulkModel.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
        return (f'✅ Portföyünüz *{grup.ad}* grubuna açıldı!\n\n'
                f'🏢 {mulk_sayi} mülk grup üyeleriyle paylaşılıyor.\n'
                '_Kişisel bilgiler (adres, müşteri adı) gizli kalır._')

    if komut == 'grup_portfoy_kapat':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        uyelik.portfoy_acik = False
        db.session.commit()
        return f'✅ Portföyünüz *{grup.ad}* grubunda artık gizli.'

    if komut == 'grup_talep_ac':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        uyelik.talep_acik = True
        db.session.commit()
        musteri_sayi = MusteriModel.query.filter_by(emlakci_id=emlakci.id).count()
        return (f'✅ Talepleriniz *{grup.ad}* grubuna açıldı!\n\n'
                f'👥 {musteri_sayi} müşteri talebi grup üyeleriyle paylaşılıyor.\n'
                '_Müşteri isimleri ve iletişim bilgileri gizli kalır._')

    if komut == 'grup_talep_kapat':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        uyelik.talep_acik = False
        db.session.commit()
        return f'✅ Talepleriniz *{grup.ad}* grubunda artık gizli.'

    if komut == 'grup_esles':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        # Eşleştirme yap
        acik_portfoy = GrupUyelik.query.filter_by(grup_id=grup.id, durum='aktif', portfoy_acik=True).all()
        acik_talep = GrupUyelik.query.filter_by(grup_id=grup.id, durum='aktif', talep_acik=True).all()
        portfoyler = []
        for u in acik_portfoy:
            mulkler = MulkModel.query.filter_by(emlakci_id=u.emlakci_id, aktif=True).all()
            for m in mulkler:
                portfoyler.append({
                    'tip': m.tip, 'islem': m.islem_turu, 'fiyat': m.fiyat,
                    'ilce': m.ilce, 'oda': m.oda_sayisi, 'uye': u.emlakci_id,
                })
        talepler = []
        for u in acik_talep:
            musteriler = MusteriModel.query.filter_by(emlakci_id=u.emlakci_id).all()
            for m in musteriler:
                talepler.append({
                    'islem': m.islem_turu, 'butce': m.butce_max,
                    'uye': u.emlakci_id,
                })
        eslesimler = []
        for t in talepler:
            for p in portfoyler:
                if t['islem'] == p['islem'] and t['uye'] != p['uye']:
                    if t['butce'] and p['fiyat'] and p['fiyat'] <= t['butce']:
                        eslesimler.append(p)
        if not eslesimler:
            return (f'🔗 *{grup.ad} — Eşleştirme Sonucu:*\n\n'
                    f'🏢 {len(portfoyler)} açık portföy · 👥 {len(talepler)} açık talep\n'
                    '❌ Henüz eşleşme bulunamadı.\n\n'
                    '_Daha fazla üyenin portföy/taleplerini açması gerekebilir._')
        satirlar = []
        for e in eslesimler[:10]:
            fiyat_str = f'{int(e["fiyat"]):,}'.replace(',', '.') + ' TL' if e['fiyat'] else '?'
            satirlar.append(f'• {e["tip"] or "?"} · {e["ilce"] or "?"} · {e["oda"] or "?"} · {fiyat_str}')
        return (f'🔗 *{grup.ad} — Eşleştirme Sonucu:*\n\n'
                f'🏢 {len(portfoyler)} portföy · 👥 {len(talepler)} talep · ✅ *{len(eslesimler)} eşleşme*\n\n'
                + '\n'.join(satirlar) +
                (f'\n\n_...ve {len(eslesimler) - 10} eşleşme daha_' if len(eslesimler) > 10 else ''))

    if komut == 'grup_bildirim':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        bildirimler = GrupBildirim.query.filter_by(grup_id=grup.id)\
            .order_by(GrupBildirim.olusturma.desc()).limit(10).all()
        if not bildirimler:
            return f'📢 *{grup.ad}* grubunda henüz aktivite yok.'
        satirlar = []
        for b in bildirimler:
            tarih = b.olusturma.strftime('%d.%m %H:%M') if b.olusturma else ''
            satirlar.append(f'• {b.mesaj} _{tarih}_')
        return f'📢 *{grup.ad} — Son Aktiviteler:*\n\n' + '\n'.join(satirlar)

    if komut == 'grup_uye_davet':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        if uyelik.rol != 'yonetici':
            return '⚠️ Üye davet etmek için *yönetici* yetkisi gerekli.'
        session['bekleyen_islem'] = 'grup_uye_davet_bilgi'
        session['davet_grup_id'] = grup.id
        return (f'👥 *{grup.ad}* grubuna üye davet edin.\n\n'
                'Davet etmek istediğiniz emlakçının adını veya ID\'sini yazın.\n'
                '_(Sadece uygulamayı kullanan emlakçılar davet edilebilir)_')

    if komut == 'grup_yonetici_ata':
        grup, uyelik = _grup_bul(emlakci, metin)
        if not grup:
            return '👥 Üye olduğunuz bir grup bulunamadı.'
        if uyelik.rol != 'yonetici':
            return '⚠️ Yönetici atamak için *yönetici* yetkisi gerekli.'
        return (f'👥 *{grup.ad}* grubuna yönetici atamak için üye listesini kontrol edin.\n\n'
                '_Grup üyelerini görmek için "grup üyeleri" yazın._')

    return None


def _grup_bul(emlakci, metin):
    """Metinden grup adı çıkarmaya çalış, bulamazsa ilk aktif grubu döndür."""
    from app.models.grup import Grup, GrupUyelik
    uyelikler = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='aktif').all()
    if not uyelikler:
        return None, None

    # Metinde grup adı geçiyor mu?
    metin_lower = metin.lower()
    for u in uyelikler:
        g = Grup.query.get(u.grup_id)
        if g and g.aktif and g.ad.lower() in metin_lower:
            return g, u

    # Bulamadıysa ilk grubu döndür
    for u in uyelikler:
        g = Grup.query.get(u.grup_id)
        if g and g.aktif:
            return g, u

    return None, None


def _grup_kaydet(emlakci, metin):
    """Serbest metinden grup bilgisi çıkar ve kur."""
    from app.models.grup import Grup, GrupUyelik, GrupBildirim
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    ad = parcalar[0] if parcalar else metin.strip()
    slogan = parcalar[1] if len(parcalar) > 1 else None

    g = Grup(ad=ad, slogan=slogan, kurucu_id=emlakci.id)
    db.session.add(g)
    db.session.flush()

    u = GrupUyelik(grup_id=g.id, emlakci_id=emlakci.id, rol='yonetici', durum='aktif')
    db.session.add(u)
    db.session.add(GrupBildirim(grup_id=g.id, emlakci_id=emlakci.id, tip='grup_kuruldu', mesaj=f'Grup "{g.ad}" kuruldu'))
    db.session.commit()

    return (f'✅ *Grup kuruldu!*\n\n'
            f'👥 *{g.ad}*\n'
            + (f'📝 {slogan}\n' if slogan else '') +
            f'👑 Yönetici: {emlakci.ad_soyad}\n\n'
            '_Üye davet etmek için "gruba üye ekle" yazın.\n'
            'Portföyünüzü açmak için "portföyümü gruba aç" yazın._')


def _grup_uye_davet_isle(emlakci, metin, session):
    """Gruba üye davet et."""
    from app.models.grup import Grup, GrupUyelik
    from app.models import Emlakci as EmlakciModel
    from app.routes.bildirim import bildirim_olustur

    grup_id = session.pop('davet_grup_id', None)
    if not grup_id:
        return '⚠️ Davet işlemi iptal edildi. Tekrar "gruba üye ekle" yazın.'

    grup = Grup.query.get(grup_id)
    if not grup:
        return '⚠️ Grup bulunamadı.'

    # İsimle emlakçı ara
    sorgu = metin.strip()
    hedef = EmlakciModel.query.filter(
        EmlakciModel.aktif == True,
        EmlakciModel.ad_soyad.ilike(f'%{sorgu}%')
    ).first()

    if not hedef:
        # ID ile dene
        try:
            hedef = EmlakciModel.query.filter_by(id=int(sorgu), aktif=True).first()
        except (ValueError, TypeError):
            pass

    if not hedef:
        return f'⚠️ "{sorgu}" adında aktif bir emlakçı bulunamadı.\n\n_Uygulamayı kullanan biri olmalı._'

    if hedef.id == emlakci.id:
        return '⚠️ Kendinizi davet edemezsiniz.'

    # Max 2 kontrol
    aktif = GrupUyelik.query.filter_by(emlakci_id=hedef.id, durum='aktif').count()
    if aktif >= 2:
        return f'⚠️ *{hedef.ad_soyad}* zaten 2 gruba üye, yeni davet gönderilemez.'

    # Teklif kapalı mı
    from app.models.ayarlar import KullaniciAyar
    ayar = KullaniciAyar.query.filter_by(emlakci_id=hedef.id).first()
    if ayar and ayar.ayarlar and ayar.ayarlar.get('grup_teklif_kapali'):
        return f'⚠️ *{hedef.ad_soyad}* grup tekliflerini kapatmış.'

    # Zaten üye/bekliyor mu
    mevcut = GrupUyelik.query.filter_by(grup_id=grup_id, emlakci_id=hedef.id).first()
    if mevcut and mevcut.durum in ('aktif', 'bekliyor'):
        return f'⚠️ *{hedef.ad_soyad}* zaten üye veya davet bekliyor.'

    # Davet oluştur
    if mevcut:
        mevcut.durum = 'bekliyor'
    else:
        u = GrupUyelik(grup_id=grup_id, emlakci_id=hedef.id, rol='uye', durum='bekliyor')
        db.session.add(u)

    bildirim_olustur(hedef.id, 'grup',
        f'📩 "{grup.ad}" grubuna üyelik davetiniz var',
        f'{emlakci.ad_soyad} sizi davet etti.', link='gruplar')

    db.session.commit()
    return f'✅ *{hedef.ad_soyad}* adlı emlakçıya *{grup.ad}* grubu için davet gönderildi!'


# ─── WhatsApp Mesaj Gönderme (sohbetten) ──────────────────
def _wa_mesaj_gonder(emlakci, args):
    """Sohbetten müşteriye WhatsApp mesajı gönder."""
    import os
    pid = os.environ.get('WA_PHONE_NUMBER_ID', '')
    tok = os.environ.get('WA_ACCESS_TOKEN', '')
    if not pid or not tok:
        return '⚠️ WhatsApp yapılandırması henüz aktif değil.'

    mesaj = args.get('mesaj', '')
    telefon = args.get('telefon', '')

    # Müşteri adından telefon bul
    if not telefon and args.get('musteri_adi'):
        mus = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(
            Musteri.ad_soyad.ilike(f'%{args["musteri_adi"]}%')
        ).first()
        if mus and mus.telefon:
            telefon = mus.telefon
        else:
            return f'⚠️ "{args["musteri_adi"]}" adında müşteri bulunamadı veya telefon numarası yok.'

    if not telefon:
        return '⚠️ Telefon numarası gerekli. Müşteri adı veya telefon belirtin.'

    # Telefon formatla
    telefon = telefon.replace('+', '').replace(' ', '').replace('-', '')
    if telefon.startswith('0'):
        telefon = '90' + telefon[1:]
    if not telefon.startswith('90'):
        telefon = '90' + telefon

    from app.services import whatsapp as wa
    basarili = wa.mesaj_gonder(pid, tok, telefon, mesaj)
    if basarili:
        return f'✅ WhatsApp mesajı gönderildi!\n📱 {telefon}\n💬 {mesaj[:100]}'
    return '❌ Mesaj gönderilemedi.'


def _wa_toplu_mesaj(emlakci, args):
    """Filtreye göre müşterilere toplu WhatsApp mesajı."""
    import os
    pid = os.environ.get('WA_PHONE_NUMBER_ID', '')
    tok = os.environ.get('WA_ACCESS_TOKEN', '')
    if not pid or not tok:
        return '⚠️ WhatsApp yapılandırması henüz aktif değil.'

    mesaj_sablon = args.get('mesaj', '')
    filtre = args.get('filtre', 'hepsi')

    sorgu = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(Musteri.telefon.isnot(None))
    if filtre == 'sicak':
        sorgu = sorgu.filter(Musteri.sicaklik == 'sicak')
    elif filtre == 'ilgili':
        sorgu = sorgu.filter(Musteri.sicaklik == 'ilgili')
    elif filtre == 'soguk':
        sorgu = sorgu.filter(Musteri.sicaklik == 'soguk')
    elif filtre == 'kira':
        sorgu = sorgu.filter(Musteri.islem_turu == 'kira')
    elif filtre == 'satis':
        sorgu = sorgu.filter(Musteri.islem_turu == 'satis')

    musteriler = sorgu.limit(50).all()
    if not musteriler:
        return f'📭 "{filtre}" filtresine uygun telefonu olan müşteri bulunamadı.'

    from app.services import whatsapp as wa
    gonderilen = 0
    for m in musteriler:
        tel = m.telefon.replace('+', '').replace(' ', '').replace('-', '')
        if tel.startswith('0'):
            tel = '90' + tel[1:]
        if not tel.startswith('90'):
            tel = '90' + tel
        kisi_mesaj = mesaj_sablon.replace('{isim}', m.ad_soyad.split(' ')[0])
        if wa.mesaj_gonder(pid, tok, tel, kisi_mesaj):
            gonderilen += 1

    return f'✅ *Toplu mesaj gönderildi!*\n\n📱 {gonderilen}/{len(musteriler)} kişiye ulaştı\n💬 {mesaj_sablon[:80]}'


# ─── Teklif / Pazarlık Takibi ─────────────────────────────
def _teklif_kaydet(emlakci, args):
    """Teklif kaydı oluştur."""
    from app.models import Teklif
    tutar = float(args.get('teklif_tutar', 0))

    # Mülk bul
    mulk_id = None
    if args.get('mulk_baslik'):
        mulk = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).filter(
            Mulk.baslik.ilike(f'%{args["mulk_baslik"]}%')
        ).first()
        if mulk:
            mulk_id = mulk.id

    # Müşteri bul
    musteri_id = None
    if args.get('musteri_adi'):
        mus = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(
            Musteri.ad_soyad.ilike(f'%{args["musteri_adi"]}%')
        ).first()
        if mus:
            musteri_id = mus.id

    t = Teklif(
        emlakci_id=emlakci.id, mulk_id=mulk_id, musteri_id=musteri_id,
        teklif_tutar=tutar, istenen_tutar=args.get('istenen_tutar'),
        notlar=args.get('notlar'),
    )
    db.session.add(t)
    db.session.commit()

    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '?'
    return (f'✅ *Teklif kaydedildi!*\n\n'
            f'💰 Teklif: {f_tl(tutar)} TL\n'
            + (f'🏷 İstenen: {f_tl(args.get("istenen_tutar"))} TL\n' if args.get('istenen_tutar') else '')
            + (f'🏢 Mülk: {args.get("mulk_baslik", "—")}\n' if args.get('mulk_baslik') else '')
            + (f'👤 Müşteri: {args.get("musteri_adi", "—")}' if args.get('musteri_adi') else ''))


def _teklif_listele(emlakci, args):
    """Teklif geçmişini listele."""
    from app.models import Teklif
    sorgu = Teklif.query.filter_by(emlakci_id=emlakci.id)
    if args.get('durum'):
        sorgu = sorgu.filter(Teklif.durum == args['durum'])
    if args.get('mulk_baslik'):
        mulk = Mulk.query.filter_by(emlakci_id=emlakci.id).filter(Mulk.baslik.ilike(f'%{args["mulk_baslik"]}%')).first()
        if mulk:
            sorgu = sorgu.filter(Teklif.mulk_id == mulk.id)

    teklifler = sorgu.order_by(Teklif.olusturma.desc()).limit(15).all()
    if not teklifler:
        return '📭 Teklif kaydı bulunamadı.'

    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '?'
    satirlar = []
    for i, t in enumerate(teklifler):
        mulk_ad = Mulk.query.get(t.mulk_id).baslik if t.mulk_id and Mulk.query.get(t.mulk_id) else '—'
        mus_ad = Musteri.query.get(t.musteri_id).ad_soyad if t.musteri_id and Musteri.query.get(t.musteri_id) else '—'
        durum_ikon = {'bekliyor': '⏳', 'kabul': '✅', 'red': '❌', 'karsi_teklif': '🔄'}.get(t.durum, '⏳')
        tarih = t.olusturma.strftime('%d.%m') if t.olusturma else ''
        satirlar.append(f'*{i+1}.* {durum_ikon} {f_tl(t.teklif_tutar)} TL — {mus_ad} → {mulk_ad} _{tarih}_')

    return f'💰 *Teklif Geçmişi ({len(teklifler)}):*\n\n' + '\n'.join(satirlar)


# ─── Doğum Günü Takibi ────────────────────────────────────
def _dogum_gunu_kaydet(emlakci, args):
    """Müşterinin doğum tarihini kaydet."""
    from datetime import datetime as dt
    mus = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(
        Musteri.ad_soyad.ilike(f'%{args.get("musteri_adi", "")}%')
    ).first()
    if not mus:
        return f'⚠️ "{args.get("musteri_adi")}" adında müşteri bulunamadı.'

    tarih_str = args.get('tarih', '')
    tarih = None
    for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m'):
        try:
            tarih = dt.strptime(tarih_str, fmt).date()
            if tarih.year == 1900:  # sadece gün-ay verildi
                tarih = tarih.replace(year=2000)
            break
        except ValueError:
            continue

    if not tarih:
        # Ay ismiyle dene: "15 Mart"
        ay_map = {'ocak': 1, 'subat': 2, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayis': 5, 'mayıs': 5,
                  'haziran': 6, 'temmuz': 7, 'agustos': 8, 'ağustos': 8, 'eylul': 9, 'eylül': 9,
                  'ekim': 10, 'kasim': 11, 'kasım': 11, 'aralik': 12, 'aralık': 12}
        import re as _re
        m = _re.search(r'(\d{1,2})\s*(\w+)', tarih_str.lower())
        if m and m.group(2) in ay_map:
            from datetime import date
            tarih = date(2000, ay_map[m.group(2)], int(m.group(1)))

    if not tarih:
        return '⚠️ Tarih anlaşılamadı. Örnek: "15.03.1990" veya "15 Mart"'

    mus.dogum_tarihi = tarih
    db.session.commit()
    return f'✅ *{mus.ad_soyad}* doğum tarihi kaydedildi: {tarih.strftime("%d %B").replace("January","Ocak").replace("February","Şubat").replace("March","Mart").replace("April","Nisan").replace("May","Mayıs").replace("June","Haziran").replace("July","Temmuz").replace("August","Ağustos").replace("September","Eylül").replace("October","Ekim").replace("November","Kasım").replace("December","Aralık")}'


def _yaklasan_dogum_gunleri(emlakci):
    """Yaklaşan 30 gün içindeki doğum günlerini listele."""
    from datetime import date, timedelta
    bugun = date.today()
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).filter(Musteri.dogum_tarihi.isnot(None)).all()

    yaklasan = []
    for m in musteriler:
        dg = m.dogum_tarihi.replace(year=bugun.year)
        if dg < bugun:
            dg = dg.replace(year=bugun.year + 1)
        kalan = (dg - bugun).days
        if kalan <= 30:
            yaklasan.append((m, kalan, dg))

    yaklasan.sort(key=lambda x: x[1])

    if not yaklasan:
        return '🎂 Önümüzdeki 30 gün içinde doğum günü olan müşteri yok.\n\n_Doğum tarihi kaydetmek için: "Ahmet Beyin doğum günü 15 Mart"_'

    satirlar = []
    for m, kalan, dg in yaklasan:
        if kalan == 0:
            satirlar.append(f'🎉 *BUGÜN!* {m.ad_soyad} — {m.telefon or ""}')
        elif kalan <= 3:
            satirlar.append(f'🎂 *{kalan} gün sonra!* {m.ad_soyad} — {dg.strftime("%d.%m")}')
        else:
            satirlar.append(f'📅 {kalan} gün — {m.ad_soyad} — {dg.strftime("%d.%m")}')

    return f'🎂 *Yaklaşan Doğum Günleri:*\n\n' + '\n'.join(satirlar)


# ─── Satış Kapandı — Zincirleme Süreç ─────────────────────
def _satis_kapandi(emlakci, args):
    """Satış kapandığında zincirleme işlem: komisyon hesapla, fatura kes, ilan kaldır, mesaj hazırla."""
    satis_bedeli = float(args.get('satis_bedeli', 0))
    komisyon_oran = float(args.get('komisyon_oran', 0.02))
    komisyon = satis_bedeli * komisyon_oran
    kdv = komisyon * 0.20
    toplam = komisyon + kdv
    f_tl = lambda v: f'{int(v):,}'.replace(',', '.')

    sonuclar = [f'🎉 *Satış Kapandı — Tebrikler!*\n']

    # 1. Komisyon hesapla
    sonuclar.append(f'💰 *Komisyon:*\n  Bedel: {f_tl(satis_bedeli)} TL\n  Komisyon (%{int(komisyon_oran*100)}): {f_tl(komisyon)} TL\n  KDV: {f_tl(kdv)} TL\n  *Toplam: {f_tl(toplam)} TL*')

    # 2. Fatura oluştur
    try:
        from app.models.fatura import Fatura
        fatura = Fatura(
            emlakci_id=emlakci.id, alici_ad=args.get('musteri_adi', ''),
            tutar=komisyon, kdv_oran=20, kdv_tutar=round(kdv, 2), toplam=round(toplam, 2),
            tip='komisyon', fatura_no=f'F-{datetime.now().strftime("%Y%m%d%H%M")}',
        )
        db.session.add(fatura)
        sonuclar.append(f'\n🧾 *Fatura:* {fatura.fatura_no} — {f_tl(toplam)} TL oluşturuldu')
    except Exception:
        sonuclar.append('\n⚠️ Fatura oluşturulamadı')

    # 3. İlanı kaldır
    if args.get('mulk_baslik'):
        mulk = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).filter(
            Mulk.baslik.ilike(f'%{args["mulk_baslik"]}%')
        ).first()
        if mulk:
            mulk.aktif = False
            sonuclar.append(f'\n🏢 *İlan kaldırıldı:* {mulk.baslik}')

    # 4. Müşteriye teşekkür mesajı hazırla
    musteri_adi = args.get('musteri_adi', 'Müşterimiz')
    tesekkur = f'Sayın {musteri_adi}, emlak alım süreciniz başarıyla tamamlanmıştır. Bizi tercih ettiğiniz için teşekkür ederiz. Herhangi bir konuda yardıma ihtiyacınız olursa lütfen bize ulaşın. — {emlakci.ad_soyad}'
    sonuclar.append(f'\n💬 *Teşekkür mesajı hazırlandı:*\n_{tesekkur}_')

    # 5. Tapu randevusu hatırlatması
    sonuclar.append('\n📋 *Yapılacaklar:*\n  • Tapu randevusu alın\n  • DASK poliçesi kontrol edin\n  • Gerekli belgeleri toplayın')

    db.session.commit()
    return '\n'.join(sonuclar)


# ─── AI Fonksiyonları (function calling) ───────────────────
_FUNCTIONS = [
    {
        'name': 'musteri_ekle',
        'description': 'Yeni müşteri ekler',
        'parameters': {
            'type': 'object',
            'properties': {
                'ad_soyad': {'type': 'string', 'description': 'Müşterinin adı soyadı'},
                'telefon': {'type': 'string', 'description': 'Telefon numarası'},
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis']},
                'butce_min': {'type': 'number', 'description': 'Minimum bütçe TL'},
                'butce_max': {'type': 'number', 'description': 'Maksimum bütçe TL'},
                'tercih_notlar': {'type': 'string', 'description': 'Müşteri tercihleri'},
            },
            'required': ['ad_soyad'],
        },
    },
    {
        'name': 'musteri_listele',
        'description': 'Müşteri listesini getirir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'mulk_ekle',
        'description': 'Portföye yeni mülk ekler',
        'parameters': {
            'type': 'object',
            'properties': {
                'baslik': {'type': 'string'},
                'adres': {'type': 'string'},
                'sehir': {'type': 'string'},
                'ilce': {'type': 'string'},
                'tip': {'type': 'string', 'enum': ['daire', 'villa', 'arsa', 'dukkan', 'ofis']},
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis']},
                'fiyat': {'type': 'number'},
                'metrekare': {'type': 'number'},
                'oda_sayisi': {'type': 'string'},
            },
            'required': ['baslik'],
        },
    },
    {
        'name': 'mulk_listele',
        'description': 'Portföy listesini getirir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'rapor',
        'description': 'Genel durum raporu verir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'not_ekle',
        'description': 'Not kaydeder',
        'parameters': {
            'type': 'object',
            'properties': {
                'icerik': {'type': 'string', 'description': 'Not içeriği'},
            },
            'required': ['icerik'],
        },
    },
    {
        'name': 'gorev_ekle',
        'description': 'Görev veya hatırlatma oluşturur',
        'parameters': {
            'type': 'object',
            'properties': {
                'baslik': {'type': 'string', 'description': 'Görev başlığı'},
                'aciklama': {'type': 'string'},
                'tip': {'type': 'string', 'enum': ['gorev', 'hatirlatma', 'yer_gosterme', 'toplanti']},
            },
            'required': ['baslik'],
        },
    },
    {
        'name': 'fatura_olustur',
        'description': 'Fatura oluşturur',
        'parameters': {
            'type': 'object',
            'properties': {
                'alici_ad': {'type': 'string'},
                'tutar': {'type': 'number'},
                'tip': {'type': 'string', 'enum': ['hizmet', 'komisyon', 'satis', 'kiralama']},
            },
            'required': ['alici_ad', 'tutar'],
        },
    },
    {
        'name': 'eslestir',
        'description': 'Müşteriye uygun mülkleri bulur',
        'parameters': {
            'type': 'object',
            'properties': {
                'musteri_id': {'type': 'integer', 'description': 'Müşteri ID'},
            },
            'required': ['musteri_id'],
        },
    },
    {
        'name': 'kira_vergisi_hesapla',
        'description': 'Kira vergisi hesaplar',
        'parameters': {
            'type': 'object',
            'properties': {
                'yillik_kira': {'type': 'number', 'description': 'Yıllık kira geliri TL'},
            },
            'required': ['yillik_kira'],
        },
    },
    {
        'name': 'kira_getirisi_hesapla',
        'description': 'Kira getirisi ROI hesaplar',
        'parameters': {
            'type': 'object',
            'properties': {
                'mulk_fiyati': {'type': 'number'},
                'aylik_kira': {'type': 'number'},
            },
            'required': ['mulk_fiyati', 'aylik_kira'],
        },
    },
    {
        'name': 'genel_arama',
        'description': 'Müşteri, mülk, görev, lead, fatura arar',
        'parameters': {
            'type': 'object',
            'properties': {
                'sorgu': {'type': 'string', 'description': 'Arama kelimesi'},
            },
            'required': ['sorgu'],
        },
    },
    {
        'name': 'gelismis_mulk_ara',
        'description': 'Portföydeki mülkleri doğal dil ile arar ve filtreler. Kullanıcı "Kadıköy\'de 3+1 kiralık 15bin altı daire" gibi konuşunca bu fonksiyon çağrılır.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sehir': {'type': 'string', 'description': 'Şehir adı (İstanbul, Ankara vb.)'},
                'ilce': {'type': 'string', 'description': 'İlçe adı (Kadıköy, Beşiktaş vb.)'},
                'tip': {'type': 'string', 'enum': ['daire', 'villa', 'arsa', 'dukkan', 'ofis', 'mustakil'], 'description': 'Mülk tipi'},
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis'], 'description': 'kiralık=kira, satılık=satis'},
                'fiyat_min': {'type': 'number', 'description': 'Minimum fiyat TL'},
                'fiyat_max': {'type': 'number', 'description': 'Maksimum fiyat TL'},
                'oda_sayisi': {'type': 'string', 'description': 'Oda sayısı: 1+1, 2+1, 3+1, 4+1 vb.'},
                'metrekare_min': {'type': 'number', 'description': 'Minimum metrekare'},
                'ozellikler': {'type': 'string', 'description': 'Ek özellikler: deniz manzaralı, asansörlü, eşyalı, krediye uygun vb.'},
            },
        },
    },
    {
        'name': 'gelismis_musteri_ara',
        'description': 'Müşterileri doğal dil ile arar ve filtreler. "Satılık arayan sıcak müşteriler" veya "bütçesi 1 milyon üstü kiracılar" gibi sorgular.',
        'parameters': {
            'type': 'object',
            'properties': {
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis'], 'description': 'kiralık=kira, satılık=satis'},
                'butce_min': {'type': 'number', 'description': 'Minimum bütçe TL'},
                'butce_max': {'type': 'number', 'description': 'Maksimum bütçe TL'},
                'sicaklik': {'type': 'string', 'enum': ['sicak', 'ilgili', 'soguk'], 'description': 'Müşteri sıcaklığı'},
                'sorgu': {'type': 'string', 'description': 'İsim veya not içinde arama'},
            },
        },
    },
    {
        'name': 'mahalle_analiz',
        'description': 'Bir ilçe veya mahallenin detaylı analizini yapar. Güvenlik, ulaşım, eğitim, sağlık, sosyal tesis puanları ve yatırım önerisi verir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sehir': {'type': 'string', 'description': 'Şehir adı'},
                'ilce': {'type': 'string', 'description': 'İlçe adı'},
                'mahalle': {'type': 'string', 'description': 'Mahalle adı (opsiyonel)'},
            },
            'required': ['ilce'],
        },
    },
    # ── Görev Yönetimi ──
    {
        'name': 'gorev_listele',
        'description': 'Aktif görevleri, hatırlatmaları ve planları listeler. Filtreleme yapılabilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'durum': {'type': 'string', 'enum': ['bekliyor', 'devam', 'tamamlandi', 'iptal'], 'description': 'Görev durumuna göre filtrele'},
                'tip': {'type': 'string', 'enum': ['gorev', 'hatirlatma', 'yer_gosterme', 'toplanti'], 'description': 'Görev tipine göre filtrele'},
            },
        },
    },
    {
        'name': 'gorev_guncelle',
        'description': 'Mevcut görevi günceller — durumunu değiştirir (tamamla, iptal et), başlık düzenler.',
        'parameters': {
            'type': 'object',
            'properties': {
                'gorev_id': {'type': 'integer', 'description': 'Görev ID'},
                'durum': {'type': 'string', 'enum': ['bekliyor', 'devam', 'tamamlandi', 'iptal']},
                'baslik': {'type': 'string', 'description': 'Yeni başlık (opsiyonel)'},
            },
            'required': ['gorev_id'],
        },
    },
    # ── Fatura ──
    {
        'name': 'fatura_listele',
        'description': 'Faturaları listeler. Duruma göre filtrelenebilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'durum': {'type': 'string', 'enum': ['taslak', 'gonderildi', 'odendi', 'iptal'], 'description': 'Fatura durumu filtresi'},
            },
        },
    },
    # ── Muhasebe ──
    {
        'name': 'gelir_gider_ozet',
        'description': 'Gelir/gider muhasebe özetini verir. Toplam gelir, gider, kâr/zarar.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'cari_ozet',
        'description': 'Cari hesap özetini verir. Alacak, borç bakiyeleri.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    # ── Lead Yönetimi ──
    {
        'name': 'lead_listele',
        'description': 'Potansiyel müşteri (lead) listesini getirir. Duruma ve kaynağa göre filtrelenebilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'durum': {'type': 'string', 'enum': ['yeni', 'iletisimde', 'gorusmede', 'kazanildi', 'kaybedildi'], 'description': 'Lead durumu'},
                'kaynak': {'type': 'string', 'description': 'Lead kaynağı (whatsapp, web, referans vb.)'},
            },
        },
    },
    # ── Emlakçı Dizini ──
    {
        'name': 'emlakci_dizin_ara',
        'description': 'Emlakçı dizininde arama yapar. İsim, bölge, uzmanlık veya acente ile aranabilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sorgu': {'type': 'string', 'description': 'Arama kelimesi (isim, bölge, acente)'},
            },
            'required': ['sorgu'],
        },
    },
    # ── Grup ──
    {
        'name': 'grup_bilgi',
        'description': 'Grup bilgilerini, üyelerini, ayarlarını veya eşleştirme sonuçlarını getirir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'islem': {'type': 'string', 'enum': ['liste', 'uyeler', 'ayarlar', 'eslestirme', 'davetler'], 'description': 'İstenen bilgi türü'},
            },
            'required': ['islem'],
        },
    },
    # ── Export ──
    {
        'name': 'veri_indir',
        'description': 'Veriyi Excel veya ZIP olarak indirme linki verir. Portföy, müşteri veya tüm veri indirilebilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tip': {'type': 'string', 'enum': ['portfoy', 'musteri', 'tumu'], 'description': 'İndirilecek veri tipi'},
                'format': {'type': 'string', 'enum': ['excel', 'zip'], 'description': 'Dosya formatı'},
            },
            'required': ['tip'],
        },
    },
    # ── Hesaplamalar ──
    {
        'name': 'tapu_masrafi_hesapla',
        'description': 'Tapu devir masrafını hesaplar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'satis_bedeli': {'type': 'number', 'description': 'Satış bedeli TL'},
            },
            'required': ['satis_bedeli'],
        },
    },
    {
        'name': 'komisyon_hesapla',
        'description': 'Emlakçı komisyonu hesaplar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'islem_turu': {'type': 'string', 'enum': ['satis', 'kira'], 'description': 'İşlem türü'},
                'bedel': {'type': 'number', 'description': 'Satış bedeli veya kira tutarı TL'},
            },
            'required': ['islem_turu', 'bedel'],
        },
    },
    # ── WhatsApp Mesaj Gönderme ──
    {
        'name': 'whatsapp_mesaj_gonder',
        'description': 'Müşteriye WhatsApp mesajı gönderir. "Ahmet Beye yaz: fiyat düştü" gibi komutlarda kullanılır.',
        'parameters': {
            'type': 'object',
            'properties': {
                'musteri_adi': {'type': 'string', 'description': 'Müşterinin adı (veritabanından telefon bulunur)'},
                'telefon': {'type': 'string', 'description': 'Telefon numarası (müşteri adı bilinmiyorsa)'},
                'mesaj': {'type': 'string', 'description': 'Gönderilecek mesaj metni'},
            },
            'required': ['mesaj'],
        },
    },
    {
        'name': 'toplu_mesaj_gonder',
        'description': 'Birden fazla müşteriye WhatsApp mesajı gönderir. "Tüm sıcak müşterilere yaz" gibi komutlarda.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filtre': {'type': 'string', 'enum': ['hepsi', 'sicak', 'ilgili', 'soguk', 'kira', 'satis'], 'description': 'Müşteri filtresi'},
                'mesaj': {'type': 'string', 'description': 'Gönderilecek mesaj (isim otomatik kişiselleştirilir)'},
            },
            'required': ['mesaj'],
        },
    },
    # ── Teklif / Pazarlık ──
    {
        'name': 'teklif_kaydet',
        'description': 'Bir mülk için gelen teklifi kaydeder. Pazarlık takibi.',
        'parameters': {
            'type': 'object',
            'properties': {
                'mulk_baslik': {'type': 'string', 'description': 'Mülkün başlığı veya tanımı'},
                'musteri_adi': {'type': 'string', 'description': 'Teklif veren müşterinin adı'},
                'teklif_tutar': {'type': 'number', 'description': 'Teklif tutarı TL'},
                'istenen_tutar': {'type': 'number', 'description': 'Mal sahibinin istediği tutar TL'},
                'notlar': {'type': 'string', 'description': 'Ek notlar'},
            },
            'required': ['teklif_tutar'],
        },
    },
    {
        'name': 'teklif_listele',
        'description': 'Teklif geçmişini listeler. Mülk veya müşteri bazında filtrelenebilir.',
        'parameters': {
            'type': 'object',
            'properties': {
                'mulk_baslik': {'type': 'string', 'description': 'Mülk başlığı ile filtrele'},
                'durum': {'type': 'string', 'enum': ['bekliyor', 'kabul', 'red', 'karsi_teklif'], 'description': 'Teklif durumu'},
            },
        },
    },
    # ── Doğum Günü ──
    {
        'name': 'dogum_gunu_kaydet',
        'description': 'Müşterinin doğum tarihini kaydeder. "Ahmet Beyin doğum günü 15 Mart" gibi.',
        'parameters': {
            'type': 'object',
            'properties': {
                'musteri_adi': {'type': 'string', 'description': 'Müşteri adı'},
                'tarih': {'type': 'string', 'description': 'Doğum tarihi (GG.AA.YYYY veya GG Ay)'},
            },
            'required': ['musteri_adi', 'tarih'],
        },
    },
    {
        'name': 'yaklasan_dogum_gunleri',
        'description': 'Yaklaşan doğum günlerini listeler.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    # ── Satış Süreci ──
    {
        'name': 'satis_kapandi',
        'description': 'Satış kapandığında zincirleme süreç başlatır: komisyon hesapla, fatura oluştur, ilanı kaldır, müşteriye teşekkür mesajı hazırla.',
        'parameters': {
            'type': 'object',
            'properties': {
                'mulk_baslik': {'type': 'string', 'description': 'Satılan mülkün başlığı'},
                'musteri_adi': {'type': 'string', 'description': 'Alan müşterinin adı'},
                'satis_bedeli': {'type': 'number', 'description': 'Satış bedeli TL'},
                'komisyon_oran': {'type': 'number', 'description': 'Komisyon oranı (varsayılan 0.02 = %2)'},
            },
            'required': ['satis_bedeli'],
        },
    },
    # ── Kişiselleştirme ──
    {
        'name': 'asistan_ismi_degistir',
        'description': 'Asistanın ismini değiştirir. Kullanıcı "sana Asis diyelim", "ismini X koy", "sana X diye sesleneyim" gibi söylediğinde çağrılır.',
        'parameters': {
            'type': 'object',
            'properties': {
                'isim': {'type': 'string', 'description': 'Yeni asistan ismi'},
            },
            'required': ['isim'],
        },
    },
    # ── Sayfa Navigasyonu ──
    {
        'name': 'sayfa_ac',
        'description': 'Uygulama içinde bir sayfayı açar. Müşteriler, portföy, muhasebe, takvim, ayarlar vb.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sayfa': {'type': 'string', 'enum': ['musteriler', 'mulkler', 'muhasebe', 'planlama', 'takvim', 'ayarlar', 'faturalar', 'cariler', 'leadler', 'eslestirme', 'gruplar', 'emlakcilar', 'hesaplamalar', 'isi_haritasi', 'gorsel_analiz', 'sanal_staging', 'belgeler', 'toplu', 'yedekleme', 'ekip', 'performans'], 'description': 'Açılacak sayfa'},
            },
            'required': ['sayfa'],
        },
    },
]

def _ai_function_call(fonksiyon_adi, args, emlakci):
    """AI'nın çağırdığı fonksiyonu yürüt."""
    if fonksiyon_adi == 'musteri_ekle':
        m = Musteri(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('ad_soyad', 'telefon', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Müşteri eklendi: {args.get("ad_soyad")}'

    if fonksiyon_adi == 'musteri_listele':
        sonuc, _ = _musteri_listele(emlakci)
        return sonuc

    if fonksiyon_adi == 'mulk_ekle':
        m = Mulk(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Mülk eklendi: {args.get("baslik")}'

    if fonksiyon_adi == 'mulk_listele':
        sonuc, _ = _mulk_listele(emlakci)
        return sonuc

    if fonksiyon_adi == 'rapor':
        return _rapor(emlakci)

    if fonksiyon_adi == 'not_ekle':
        n = Not(emlakci_id=emlakci.id, icerik=args.get('icerik', ''), etiket='not')
        db.session.add(n)
        db.session.commit()
        return '✅ Not kaydedildi.'

    if fonksiyon_adi == 'gorev_ekle':
        from app.models.planlama import Gorev
        g = Gorev(emlakci_id=emlakci.id, baslik=args.get('baslik', ''), aciklama=args.get('aciklama'), tip=args.get('tip', 'gorev'))
        db.session.add(g); db.session.commit()
        return f'✅ Görev eklendi: {args.get("baslik")}'

    if fonksiyon_adi == 'fatura_olustur':
        from app.models.fatura import Fatura
        tutar = float(args.get('tutar', 0))
        f = Fatura(emlakci_id=emlakci.id, alici_ad=args.get('alici_ad', ''), tutar=tutar,
                   tip=args.get('tip', 'hizmet'), kdv_oran=20, kdv_tutar=round(tutar*0.2, 2),
                   toplam=round(tutar*1.2, 2), fatura_no=f'F-{datetime.now().strftime("%Y%m%d%H%M")}')
        db.session.add(f); db.session.commit()
        return f'✅ Fatura oluşturuldu: {f.fatura_no} — {int(f.toplam):,} TL'.replace(',', '.')

    if fonksiyon_adi == 'eslestir':
        from app.services.eslestirme import eslesdir
        sonuclar = eslesdir(emlakci.id, musteri_id=args.get('musteri_id'), limit=5)
        if not sonuclar:
            return '📭 Uygun mülk bulunamadı.'
        satirlar = [f'• {s["baslik"]} — {s["fiyat_str"]} (%{s["puan"]})' for s in sonuclar]
        return f'🔗 *{len(sonuclar)} uygun mülk:*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'kira_vergisi_hesapla':
        from app.services.hesaplama import kira_vergisi
        s = kira_vergisi(float(args.get('yillik_kira', 0)))
        f = lambda v: f'{int(v):,}'.replace(',', '.')
        return f'🧾 *Kira Vergisi*\nGelir: {f(s["yillik_kira"])} TL\nVergi: {f(s["vergi"])} TL\nNet: {f(s["net_gelir"])} TL\nOran: %{s["efektif_oran"]}'

    if fonksiyon_adi == 'kira_getirisi_hesapla':
        from app.services.hesaplama import kira_getirisi
        s = kira_getirisi(float(args.get('mulk_fiyati', 0)), float(args.get('aylik_kira', 0)))
        return f'💰 *Kira Getirisi*\nBrüt: %{s["brut_getiri"]}\nNet: %{s["net_getiri"]}\nGeri dönüş: {s["geri_donus_yil"]} yıl\n{s["degerlendirme"]}'

    if fonksiyon_adi == 'genel_arama':
        from app.services.akilli_arama import genel_arama
        sonuc = genel_arama(emlakci.id, args.get('sorgu', ''))
        if not sonuc['sonuclar']:
            return f'🔍 Sonuç bulunamadı.'
        satirlar = [f'{s["ikon"]} *{s["baslik"]}* — {s["detay"]}' for s in sonuc['sonuclar'][:8]]
        return f'🔍 *Arama sonuçları:*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'gelismis_mulk_ara':
        return _gelismis_mulk_ara(emlakci, args)

    if fonksiyon_adi == 'gelismis_musteri_ara':
        return _gelismis_musteri_ara(emlakci, args)

    if fonksiyon_adi == 'mahalle_analiz':
        return _mahalle_analiz(args)

    if fonksiyon_adi == 'gorev_listele':
        from app.models.planlama import Gorev
        sorgu = Gorev.query.filter_by(emlakci_id=emlakci.id)
        if args.get('durum'):
            sorgu = sorgu.filter(Gorev.durum == args['durum'])
        else:
            sorgu = sorgu.filter(Gorev.durum != 'tamamlandi')
        if args.get('tip'):
            sorgu = sorgu.filter(Gorev.tip == args['tip'])
        gorevler = sorgu.order_by(Gorev.olusturma.desc()).limit(15).all()
        if not gorevler:
            return '📅 Görev bulunamadı.'
        satirlar = [f'*{i+1}.* {"✅" if g.durum == "tamamlandi" else "📌"} {g.baslik} — {g.durum or "bekliyor"}' for i, g in enumerate(gorevler)]
        return f'📅 *Görevler ({len(gorevler)}):*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'gorev_guncelle':
        from app.models.planlama import Gorev
        g = Gorev.query.filter_by(id=args.get('gorev_id'), emlakci_id=emlakci.id).first()
        if not g:
            return '⚠️ Görev bulunamadı.'
        if args.get('durum'):
            g.durum = args['durum']
        if args.get('baslik'):
            g.baslik = args['baslik']
        db.session.commit()
        return f'✅ Görev güncellendi: {g.baslik} → {g.durum}'

    if fonksiyon_adi == 'fatura_listele':
        from app.models.fatura import Fatura
        sorgu = Fatura.query.filter_by(emlakci_id=emlakci.id)
        if args.get('durum'):
            sorgu = sorgu.filter(Fatura.durum == args['durum'])
        faturalar = sorgu.order_by(Fatura.olusturma.desc()).limit(10).all()
        if not faturalar:
            return '🧾 Fatura bulunamadı.'
        satirlar = [f'*{i+1}.* {f.fatura_no} — {f.alici_ad or "?"} — {int(f.toplam):,} TL — {f.durum}'.replace(',', '.') for i, f in enumerate(faturalar)]
        return f'🧾 *Faturalar ({len(faturalar)}):*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'gelir_gider_ozet':
        return _muhasebe_rapor(emlakci)

    if fonksiyon_adi == 'cari_ozet':
        return _cari_rapor(emlakci)

    if fonksiyon_adi == 'lead_listele':
        from app.models.lead import Lead
        sorgu = Lead.query.filter_by(emlakci_id=emlakci.id)
        if args.get('durum'):
            sorgu = sorgu.filter(Lead.durum == args['durum'])
        if args.get('kaynak'):
            sorgu = sorgu.filter(Lead.kaynak.ilike(f'%{args["kaynak"]}%'))
        leadler = sorgu.order_by(Lead.olusturma.desc()).limit(10).all()
        if not leadler:
            return '🎯 Lead bulunamadı.'
        satirlar = [f'*{i+1}.* {l.ad_soyad} — {l.telefon or "?"} · {l.durum} · {l.kaynak or "?"}' for i, l in enumerate(leadler)]
        return f'🎯 *Leadler ({len(leadler)}):*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'emlakci_dizin_ara':
        from app.models.grup import EmlakciDizin
        s = args.get('sorgu', '')
        kayitlar = EmlakciDizin.query.filter_by(ekleyen_id=emlakci.id).filter(
            db.or_(EmlakciDizin.ad_soyad.ilike(f'%{s}%'), EmlakciDizin.bolge.ilike(f'%{s}%'), EmlakciDizin.acente.ilike(f'%{s}%'))
        ).limit(10).all()
        if not kayitlar:
            return f'📒 "{s}" ile eşleşen emlakçı bulunamadı.'
        satirlar = [f'*{i+1}.* {e.ad_soyad} — {e.telefon or "?"} · {e.bolge or "?"}' for i, e in enumerate(kayitlar)]
        return f'📒 *Emlakçı Dizini — "{s}":*\n\n' + '\n'.join(satirlar)

    if fonksiyon_adi == 'grup_bilgi':
        islem = args.get('islem', 'liste')
        if islem == 'liste':
            return _grup_komut('grup_liste', emlakci, '', {})
        elif islem == 'uyeler':
            return _grup_komut('grup_uyeleri', emlakci, '', {})
        elif islem == 'ayarlar':
            return _grup_komut('grup_ayar', emlakci, '', {})
        elif islem == 'eslestirme':
            return _grup_komut('grup_esles', emlakci, '', {})
        elif islem == 'davetler':
            return _grup_komut('grup_davet', emlakci, '', {})
        return _grup_komut('grup_liste', emlakci, '', {})

    if fonksiyon_adi == 'veri_indir':
        tip = args.get('tip', 'tumu')
        fmt = args.get('format', 'excel')
        if tip == 'portfoy':
            sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
            return f'📥 *Portföy Excel hazır!* ({sayi} mülk)\n\n[📥 İndir](/api/panel/yedek/portfoy-excel)'
        elif tip == 'musteri':
            sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
            return f'📥 *Müşteri Excel hazır!* ({sayi} müşteri)\n\n[📥 İndir](/api/panel/yedek/musteri-excel)'
        else:
            url = '/api/panel/yedek/indir' + ('?format=zip' if fmt == 'zip' else '')
            return f'📥 *Tüm veri {"ZIP" if fmt == "zip" else "Excel"} hazır!*\n\n[📥 İndir]({url})'

    if fonksiyon_adi == 'tapu_masrafi_hesapla':
        from app.services.hesaplama import tapu_masrafi
        s = tapu_masrafi(float(args.get('satis_bedeli', 0)))
        f_tl = lambda v: f'{int(v):,}'.replace(',', '.')
        return (f'🏛 *Tapu Masrafı*\n\n'
                f'Satış bedeli: {f_tl(s["satis_bedeli"])} TL\n'
                f'Alıcı harcı: {f_tl(s["alici_harci"])} TL\n'
                f'Satıcı harcı: {f_tl(s["satici_harci"])} TL\n'
                f'DASK: {f_tl(s["dask"])} TL\n'
                f'Döner sermaye: {f_tl(s["doner_sermaye"])} TL\n'
                f'*Toplam: {f_tl(s["toplam_masraf"])} TL*')

    if fonksiyon_adi == 'komisyon_hesapla':
        from app.services.hesaplama import komisyon_hesapla
        s = komisyon_hesapla(args.get('islem_turu', 'satis'), float(args.get('bedel', 0)))
        f_tl = lambda v: f'{int(v):,}'.replace(',', '.')
        return (f'💰 *{s["islem"]} Komisyonu*\n\n'
                f'Bedel: {f_tl(s["bedel"])} TL\n'
                f'Oran: {s["oran"]}\n'
                f'Komisyon: {f_tl(s["komisyon"])} TL\n'
                f'KDV: {f_tl(s["kdv"])} TL\n'
                f'*Toplam: {f_tl(s["toplam"])} TL*')

    # ── WhatsApp Mesaj ──
    if fonksiyon_adi == 'whatsapp_mesaj_gonder':
        return _wa_mesaj_gonder(emlakci, args)

    if fonksiyon_adi == 'toplu_mesaj_gonder':
        return _wa_toplu_mesaj(emlakci, args)

    # ── Teklif / Pazarlık ──
    if fonksiyon_adi == 'teklif_kaydet':
        return _teklif_kaydet(emlakci, args)

    if fonksiyon_adi == 'teklif_listele':
        return _teklif_listele(emlakci, args)

    # ── Doğum Günü ──
    if fonksiyon_adi == 'dogum_gunu_kaydet':
        return _dogum_gunu_kaydet(emlakci, args)

    if fonksiyon_adi == 'yaklasan_dogum_gunleri':
        return _yaklasan_dogum_gunleri(emlakci)

    # ── Satış Süreci ──
    if fonksiyon_adi == 'satis_kapandi':
        return _satis_kapandi(emlakci, args)

    if fonksiyon_adi == 'asistan_ismi_degistir':
        yeni_isim = args.get('isim', '').strip()
        if not yeni_isim or len(yeni_isim) > 30:
            return '⚠️ Geçersiz isim. 1-30 karakter olmalı.'
        from app.models.ayarlar import KullaniciAyar
        kayit = KullaniciAyar.query.filter_by(emlakci_id=emlakci.id).first()
        if kayit:
            ayarlar = kayit.ayarlar or {}
            ayarlar['asistan_ismi'] = yeni_isim
            kayit.ayarlar = ayarlar
        else:
            kayit = KullaniciAyar(emlakci_id=emlakci.id, ayarlar={'asistan_ismi': yeni_isim})
            db.session.add(kayit)
        db.session.commit()
        return f'✅ Artık bana *{yeni_isim}* diye seslenebilirsin! 😊'

    if fonksiyon_adi == 'sayfa_ac':
        sayfa = args.get('sayfa', 'musteriler')
        sayfa_adlari = {
            'musteriler': '👥 Müşteriler', 'mulkler': '🏢 Portföy', 'muhasebe': '💰 Muhasebe',
            'planlama': '📅 Planlama', 'takvim': '📅 Takvim', 'ayarlar': '⚙️ Ayarlar',
            'faturalar': '🧾 Faturalar', 'cariler': '📒 Cariler', 'leadler': '🎯 Leadler',
            'eslestirme': '🔗 Eşleştirme', 'gruplar': '👥 Gruplar', 'emlakcilar': '📒 Emlakçı Dizini',
            'hesaplamalar': '🧮 Hesaplamalar', 'isi_haritasi': '🗺 Isı Haritası',
            'gorsel_analiz': '📸 Görsel Analiz', 'sanal_staging': '🪑 Sanal Staging',
            'belgeler': '📄 Belgeler', 'toplu': '📦 Toplu İşlem', 'yedekleme': '💾 Yedekleme',
            'ekip': '👔 Ekip', 'performans': '🏆 Performans',
        }
        ad = sayfa_adlari.get(sayfa, sayfa)
        return (f'{ad} sayfası açılıyor...', sayfa)

    return None


def _gelismis_mulk_ara(emlakci, args):
    """Doğal dil ile portföy arama — AI function calling handler."""
    sorgu = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True)

    if args.get('sehir'):
        sorgu = sorgu.filter(Mulk.sehir.ilike(f'%{args["sehir"]}%'))
    if args.get('ilce'):
        sorgu = sorgu.filter(Mulk.ilce.ilike(f'%{args["ilce"]}%'))
    if args.get('tip'):
        sorgu = sorgu.filter(Mulk.tip.ilike(f'%{args["tip"]}%'))
    if args.get('islem_turu'):
        sorgu = sorgu.filter(Mulk.islem_turu == args['islem_turu'])
    if args.get('fiyat_min'):
        sorgu = sorgu.filter(Mulk.fiyat >= float(args['fiyat_min']))
    if args.get('fiyat_max'):
        sorgu = sorgu.filter(Mulk.fiyat <= float(args['fiyat_max']))
    if args.get('oda_sayisi'):
        sorgu = sorgu.filter(Mulk.oda_sayisi.ilike(f'%{args["oda_sayisi"]}%'))
    if args.get('metrekare_min'):
        sorgu = sorgu.filter(Mulk.metrekare >= float(args['metrekare_min']))
    if args.get('ozellikler'):
        # Detaylar JSON alanında veya başlık/adreste ara
        ozel = args['ozellikler']
        sorgu = sorgu.filter(db.or_(
            Mulk.baslik.ilike(f'%{ozel}%'),
            Mulk.adres.ilike(f'%{ozel}%'),
            db.cast(Mulk.detaylar, db.String).ilike(f'%{ozel}%'),
        ))

    # Grup portföylerinden de ara
    from app.models.grup import GrupUyelik
    grup_mulkler = []
    uyelikler = GrupUyelik.query.filter_by(emlakci_id=emlakci.id, durum='aktif').all()
    for u in uyelikler:
        acik_uyeler = GrupUyelik.query.filter(
            GrupUyelik.grup_id == u.grup_id,
            GrupUyelik.emlakci_id != emlakci.id,
            GrupUyelik.durum == 'aktif',
            GrupUyelik.portfoy_acik == True,
        ).all()
        for au in acik_uyeler:
            g_sorgu = Mulk.query.filter_by(emlakci_id=au.emlakci_id, aktif=True)
            if args.get('islem_turu'):
                g_sorgu = g_sorgu.filter(Mulk.islem_turu == args['islem_turu'])
            if args.get('fiyat_max'):
                g_sorgu = g_sorgu.filter(Mulk.fiyat <= float(args['fiyat_max']))
            if args.get('ilce'):
                g_sorgu = g_sorgu.filter(Mulk.ilce.ilike(f'%{args["ilce"]}%'))
            grup_mulkler.extend(g_sorgu.limit(5).all())

    sonuclar = sorgu.order_by(Mulk.fiyat.asc()).limit(10).all()

    if not sonuclar and not grup_mulkler:
        filtreler = []
        if args.get('ilce'): filtreler.append(args['ilce'])
        if args.get('tip'): filtreler.append(args['tip'])
        if args.get('islem_turu'): filtreler.append('kiralık' if args['islem_turu'] == 'kira' else 'satılık')
        return f'📭 {" ".join(filtreler)} aramasında sonuç bulunamadı.\n\n_Portföyünüzde {Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()} mülk var._'

    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
    satirlar = []
    for m in sonuclar:
        satirlar.append(
            f'🏢 *{m.baslik or m.adres or "—"}*\n'
            f'   📍 {m.ilce or "?"}, {m.sehir or "?"} · {m.oda_sayisi or "?"} · {m.metrekare or "?"}m²\n'
            f'   💰 {f_tl(m.fiyat)} · {m.islem_turu or "?"}'
        )
    # Grup sonuçları
    if grup_mulkler:
        satirlar.append(f'\n👥 *Grup portföylerinden ({len(grup_mulkler)}):*')
        for m in grup_mulkler[:5]:
            satirlar.append(
                f'   🏢 {m.tip or "?"} · {m.ilce or "?"} · {m.oda_sayisi or "?"} · {f_tl(m.fiyat)}'
            )

    return f'🔍 *{len(sonuclar)} mülk bulundu:*\n\n' + '\n'.join(satirlar)


def _gelismis_musteri_ara(emlakci, args):
    """Doğal dil ile müşteri arama — AI function calling handler."""
    sorgu = Musteri.query.filter_by(emlakci_id=emlakci.id)

    if args.get('islem_turu'):
        sorgu = sorgu.filter(Musteri.islem_turu == args['islem_turu'])
    if args.get('butce_min'):
        sorgu = sorgu.filter(Musteri.butce_max >= float(args['butce_min']))
    if args.get('butce_max'):
        sorgu = sorgu.filter(Musteri.butce_min <= float(args['butce_max']))
    if args.get('sicaklik'):
        sorgu = sorgu.filter(Musteri.sicaklik == args['sicaklik'])
    if args.get('sorgu'):
        s = args['sorgu']
        sorgu = sorgu.filter(db.or_(
            Musteri.ad_soyad.ilike(f'%{s}%'),
            Musteri.tercih_notlar.ilike(f'%{s}%'),
            Musteri.telefon.ilike(f'%{s}%'),
        ))

    sonuclar = sorgu.order_by(Musteri.olusturma.desc()).limit(10).all()

    if not sonuclar:
        return '📭 Arama kriterlerinize uygun müşteri bulunamadı.'

    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') + ' TL' if v else '?'
    sicaklik_ikon = {'sicak': '🔥', 'ilgili': '🟡', 'soguk': '❄️'}
    satirlar = []
    for m in sonuclar:
        ikon = sicaklik_ikon.get(m.sicaklik, '⚪')
        butce = ''
        if m.butce_min or m.butce_max:
            butce = f' · Bütçe: {f_tl(m.butce_min)}-{f_tl(m.butce_max)}'
        satirlar.append(
            f'{ikon} *{m.ad_soyad}* — {m.telefon or "tel yok"}\n'
            f'   {m.islem_turu or "?"}{butce}'
            + (f'\n   📝 {m.tercih_notlar[:60]}' if m.tercih_notlar else '')
        )

    return f'👥 *{len(sonuclar)} müşteri bulundu:*\n\n' + '\n'.join(satirlar)


def _mahalle_analiz(args):
    """Mahalle/ilçe analizi — Gemini ile."""
    sehir = args.get('sehir', 'İstanbul')
    ilce = args.get('ilce', '')
    mahalle = args.get('mahalle', '')
    konum = f'{mahalle + ", " if mahalle else ""}{ilce}, {sehir}'

    # Cache kontrol
    cache_key = f'mahalle_{sehir}_{ilce}_{mahalle}'.lower().replace(' ', '_')
    try:
        from app.models.ayarlar import SistemParametre
        cached = SistemParametre.query.filter_by(anahtar=cache_key).first()
        if cached and cached.deger:
            import json
            data = json.loads(cached.deger)
            # 24 saat cache
            from datetime import datetime, timedelta
            if cached.guncelleme and (datetime.utcnow() - cached.guncelleme) < timedelta(hours=24):
                return _mahalle_format(data, konum)
    except Exception:
        pass

    # Gemini API ile analiz
    import os, requests
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return f'📍 *{konum}* analizi için AI API anahtarı gerekli.'

    prompt = f"""Türkiye {konum} bölgesini emlak yatırımı perspektifinden analiz et.

Aşağıdaki JSON formatında cevap ver (Türkçe):
{{
    "guvenlik": 1-10 arası puan,
    "ulasim": 1-10 arası puan,
    "egitim": 1-10 arası puan,
    "saglik": 1-10 arası puan,
    "sosyal_tesis": 1-10 arası puan,
    "yesil_alan": 1-10 arası puan,
    "genel_puan": 1-10 arası ortalama,
    "ortalama_m2_fiyat_satis": tahmini TL,
    "ortalama_m2_fiyat_kira": tahmini TL,
    "trend": "yukseliyor" veya "stabil" veya "dususte",
    "yatirim_onerisi": kısa yatırım tavsiyesi,
    "one_cikan_ozellik": bölgenin en güçlü yanı,
    "dikkat_edilecek": bölgenin zayıf yanı
}}

Sadece JSON döndür, açıklama yazma."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 1024},
        }, timeout=15)
        metin = r.json()['candidates'][0]['content']['parts'][0]['text']
        metin = metin.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        import json
        data = json.loads(metin)

        # Cache kaydet
        try:
            from app.models.ayarlar import SistemParametre
            param = SistemParametre.query.filter_by(anahtar=cache_key).first()
            if param:
                param.deger = json.dumps(data)
            else:
                param = SistemParametre(anahtar=cache_key, deger=json.dumps(data), aciklama=f'Mahalle analizi: {konum}')
                db.session.add(param)
            db.session.commit()
        except Exception:
            pass

        return _mahalle_format(data, konum)
    except Exception:
        return f'📍 *{konum}* analizi şu an yapılamadı. Lütfen tekrar deneyin.'


def _mahalle_format(data, konum):
    """Mahalle analiz verilerini formatlı mesaja çevir."""
    puan_bar = lambda p: '🟢' if p >= 7 else '🟡' if p >= 5 else '🔴'
    trend_ikon = {'yukseliyor': '📈', 'stabil': '➡️', 'dususte': '📉'}
    f_tl = lambda v: f'{int(v):,}'.replace(',', '.') if v else '?'

    return (
        f'📍 *{konum} — Bölge Analizi*\n\n'
        f'{puan_bar(data.get("guvenlik", 0))} Güvenlik: *{data.get("guvenlik", "?")}/10*\n'
        f'{puan_bar(data.get("ulasim", 0))} Ulaşım: *{data.get("ulasim", "?")}/10*\n'
        f'{puan_bar(data.get("egitim", 0))} Eğitim: *{data.get("egitim", "?")}/10*\n'
        f'{puan_bar(data.get("saglik", 0))} Sağlık: *{data.get("saglik", "?")}/10*\n'
        f'{puan_bar(data.get("sosyal_tesis", 0))} Sosyal Tesis: *{data.get("sosyal_tesis", "?")}/10*\n'
        f'{puan_bar(data.get("yesil_alan", 0))} Yeşil Alan: *{data.get("yesil_alan", "?")}/10*\n\n'
        f'⭐ Genel Puan: *{data.get("genel_puan", "?")}/10*\n'
        f'{trend_ikon.get(data.get("trend", ""), "❓")} Trend: *{data.get("trend", "?")}*\n\n'
        f'💰 Satış m²: ~{f_tl(data.get("ortalama_m2_fiyat_satis"))} TL\n'
        f'💰 Kira m²: ~{f_tl(data.get("ortalama_m2_fiyat_kira"))} TL\n\n'
        f'✅ *Güçlü:* {data.get("one_cikan_ozellik", "—")}\n'
        f'⚠️ *Dikkat:* {data.get("dikkat_edilecek", "—")}\n\n'
        f'💡 *Yatırım:* {data.get("yatirim_onerisi", "—")}'
    )


# ─── AI Model Çağrıları ───────────────────────────────────
def _ai_cevap(metin: str, gecmis: list, sistem: str) -> str:
    """Model seçimi: önce Gemini (function calling), yedekte Claude."""
    metin_lower = metin.lower()
    analiz_kelimeler = ['eşleştir', 'karşılaştır', 'analiz', 'tavsiye', 'öneri', 'uygun mu', 'karsilastir']

    if any(k in metin_lower for k in analiz_kelimeler):
        kategori = 'analiz'
    else:
        kategori = 'basit'

    # Gemini Flash — basit (en ucuz)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key and kategori == 'basit':
        try:
            return _gemini(gemini_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] Gemini başarısız: {e}')

    # GPT-4o mini — yedek
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        try:
            return _openai(openai_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] OpenAI başarısız: {e}')

    # Claude Haiku — analiz veya son yedek
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if anthropic_key:
        return _claude(anthropic_key, sistem, gecmis)

    raise RuntimeError('Hiçbir AI anahtarı tanımlı değil')


def _gemini(api_key, sistem, gecmis):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=sistem)
    history = [{'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]} for m in gecmis[:-1]]
    chat = model.start_chat(history=history)
    return chat.send_message(gecmis[-1]['content']).text


def _gemini_with_functions(api_key, sistem, gecmis, emlakci):
    """Gemini ile function calling — AI doğrudan DB işlemi yapar."""
    import google.generativeai as genai
    import json as _json
    genai.configure(api_key=api_key)

    # Gemini function declarations
    tools = [{
        'function_declarations': [{
            'name': f['name'],
            'description': f['description'],
            'parameters': f['parameters'],
        } for f in _FUNCTIONS]
    }]

    model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=sistem, tools=tools)
    history = [{'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]} for m in gecmis[:-1]]
    chat = model.start_chat(history=history)
    response = chat.send_message(gecmis[-1]['content'])

    # Function call kontrolü — çoklu komut desteği
    sonuclar = []
    nav = None
    for part in response.parts:
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            args = dict(fc.args) if fc.args else {}
            sonuc = _ai_function_call(fc.name, args, emlakci)
            if isinstance(sonuc, tuple):
                sonuclar.append(sonuc[0])
                nav = sonuc[1]
            elif sonuc:
                sonuclar.append(sonuc)
    if sonuclar:
        birlesik = '\n\n'.join(sonuclar)
        return (birlesik, nav) if nav else birlesik

    return response.text


def _openai(api_key, sistem, gecmis):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'system', 'content': sistem}] + gecmis,
        max_tokens=1024,
    )
    return r.choices[0].message.content


def _claude(api_key, sistem, gecmis):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    r = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=sistem,
        messages=gecmis,
    )
    return r.content[0].text


# ─── OpenAI Function Calling (akıllı mod) ──────────────────
def _openai_with_functions(api_key, sistem, gecmis, emlakci):
    """OpenAI ile function calling — AI doğrudan DB işlemi yapar."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    tools = [{'type': 'function', 'function': f} for f in _FUNCTIONS]
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'system', 'content': sistem}] + gecmis,
        tools=tools,
        tool_choice='auto',
        max_tokens=1024,
    )

    msg = r.choices[0].message
    if msg.tool_calls:
        sonuclar = []
        nav = None
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            sonuc = _ai_function_call(tc.function.name, args, emlakci)
            if isinstance(sonuc, tuple):
                sonuclar.append(sonuc[0])
                nav = sonuc[1]
            elif sonuc:
                sonuclar.append(sonuc)
        if nav:
            return ('\n\n'.join(sonuclar), nav) if sonuclar else ('İşlem tamamlandı.', nav)
        return '\n\n'.join(sonuclar) if sonuclar else msg.content or 'İşlem tamamlandı.'

    return msg.content


# ─── Sistem Prompt ─────────────────────────────────────────
def _sistem_prompt(emlakci, metin=''):
    from app.services.hafiza import baglam_olustur
    from app.services.kisisellesme import kisisellesmis_prompt_eki
    try:
        baglam = baglam_olustur(emlakci, metin)
    except Exception:
        baglam = ''
    try:
        baglam += kisisellesmis_prompt_eki(emlakci.id)
    except Exception:
        pass

    # Kullanıcı ayarlarını oku
    ton_talimat = ''
    try:
        from app.models.ayarlar import KullaniciAyar
        kayit = KullaniciAyar.query.filter_by(emlakci_id=emlakci.id).first()
        if kayit and kayit.ayarlar:
            ton = kayit.ayarlar.get('ai_tonu', 'samimi')
            if ton == 'resmi':
                ton_talimat = '\n- Resmi ve profesyonel bir dil kullan, "siz" hitabı kullan'
            elif ton == 'kisa':
                ton_talimat = '\n- Çok kısa ve öz cevap ver, gereksiz detay verme'
            else:
                ton_talimat = '\n- Samimi ve yardımsever ol, "sen" hitabı kullan'
    except Exception:
        pass

    # Asistan ismi
    asistan_ismi = 'Emlakisim AI'
    try:
        from app.models.ayarlar import KullaniciAyar
        k = KullaniciAyar.query.filter_by(emlakci_id=emlakci.id).first()
        if k and k.ayarlar and k.ayarlar.get('asistan_ismi'):
            asistan_ismi = k.ayarlar['asistan_ismi']
    except Exception:
        pass

    return f"""Sen {asistan_ismi} — emlak profesyonelleri için geliştirilmiş üst segment yapay zeka asistanısın.
{f'Kullanıcı sana "{asistan_ismi}" diye hitap ediyor. Bu ismi kullan.' if asistan_ismi != 'Emlakisim AI' else ''}
Sen basit bir chatbot DEĞİLSİN. Sen gerçek bir emlak ofisi asistanı gibi düşünen, planlayan, hatırlayan, öneren, analiz eden akıllı bir sistemsin.

══════════════════════════════════════
GÜNCEL BAĞLAM (şu anda bildiklerin):
══════════════════════════════════════
{baglam}

══════════════════════════════════════
YETENEKLERİN (function calling ile yapabileceklerin):
══════════════════════════════════════
DB İŞLEMLERİ — doğrudan yapabilirsin:
• musteri_ekle(ad_soyad, telefon, islem_turu, butce_min/max, tercih) — müşteri kaydet
• musteri_listele() — tüm müşterileri getir
• gelismis_musteri_ara(islem_turu, butce_min/max, sicaklik, sorgu) — filtreleyerek müşteri ara
• mulk_ekle(baslik, adres, sehir, ilce, tip, islem_turu, fiyat, oda) — mülk ekle
• mulk_listele() — portföyü getir
• gelismis_mulk_ara(sehir, ilce, tip, islem_turu, fiyat_min/max, oda, ozellikler) — filtreleyerek mülk ara
• gorev_ekle(baslik, tip, aciklama) — görev/hatırlatma oluştur
• gorev_listele(durum, tip) — görevleri filtrele
• gorev_guncelle(gorev_id, durum, baslik) — görev güncelle/tamamla
• fatura_olustur(alici_ad, tutar, tip) — fatura kes
• fatura_listele(durum) — faturaları listele
• lead_listele(durum, kaynak) — leadleri listele
• gelir_gider_ozet() — muhasebe raporu
• cari_ozet() — cari hesap özeti
• eslestir(musteri_id) — müşteriye uygun mülkleri bul
• kira_vergisi_hesapla(yillik_kira) — vergi hesapla
• kira_getirisi_hesapla(mulk_fiyati, aylik_kira) — ROI hesapla
• tapu_masrafi_hesapla(satis_bedeli) — tapu masrafı hesapla
• komisyon_hesapla(islem_turu, bedel) — komisyon hesapla
• mahalle_analiz(sehir, ilce, mahalle) — bölge analizi
• emlakci_dizin_ara(sorgu) — emlakçı rehberinde ara
• grup_bilgi(islem) — grup bilgileri
• veri_indir(tip, format) — Excel/ZIP indirme linki
• genel_arama(sorgu) — tüm verilerde ara
• not_ekle(icerik) — not kaydet
• rapor() — genel durum raporu
• sayfa_ac(sayfa) — uygulama sayfası aç

BİLGİ BANKASI — sıfır maliyetle cevap verebileceğin konular:
• Tapu masrafları, tapu devir süreci (8 adım), tapu çeşitleri (kat mülkiyeti vs irtifakı)
• Kira artış oranı (TÜFE), depozito kuralları, kira sözleşmesi, tahliye sebepleri
• Emlakçı komisyon oranları (%2+KDV satış, 1 aylık kira), yetki belgesi
• DASK sigortası, iskan belgesi, imar durumu (TAKS/KAKS/gabari)
• Emlak vergisi oranları, vergi muafiyetleri, değer artış kazancı
• Konut kredisi süreci, ekspertiz raporu
• Alım-satım süreci (10 adım), gayrimenkul yatırım rehberi
• Apartman/site yönetimi, aidat kuralları

HESAPLAMA — yapabildiğin hesaplar:
• Kira vergisi (dilimli, istisna, efektif oran)
• Değer artış kazancı (5 yıl kuralı, yeniden değerleme)
• Kira getirisi ROI (brüt/net, geri dönüş süresi)
• Tapu masrafı (%4 harç + DASK + döner sermaye)
• Komisyon hesaplama (satış %2+KDV, kira 1 aylık+KDV)
• Aidat analizi (aidat/kira oranı)

BELGE ÜRETİMİ — oluşturabildiğin belgeler:
• Yer gösterme tutanağı PDF
• Kira kontratı PDF
• Alıcı/satıcı yönlendirme belgesi PDF
• Mülk broşürü PDF
• Fatura PDF
• İlan metni (sahibinden, sosyal medya)
• Reklam metni (profesyonel/samimi/lüks/yatırımcı)
• Sunum PDF

══════════════════════════════════════
DAVRANIŞ KURALLARI:
══════════════════════════════════════
{ton_talimat}
• Türkçe konuş. WhatsApp formatı kullan: *kalın*, _italik_
• BAĞLAMI KORU: yukarıdaki "GÜNCEL BAĞLAM" bilgisini kullan. Müşteri adı geçiyorsa detaylarını bil.
• PROAKTİF OL: sadece sorulan cevapla yetinme. "Bu müşteriye uygun 3 mülk var" gibi önerilerde bulun.
• HATIRLA: önceki konuşmalardan bilgi kullan. "Geçen sefer bahsettiğimiz daire" gibi ifadeleri anla.
• ZAMİR ÇÖZ: "onu ara" → yukarıda SON MÜŞTERİ kimse onun telefonunu ver. "bunu ekle" → son mülkü portföye ekle.
• ÇOKLU KOMUT: Tek mesajda birden fazla istek varsa HEPSİNİ yap.
  Örnek: "Adnan beyi müşterilere ekle numarası 02123221722, ayrıca saat 14'te toplantı görevi oluştur"
  → 1. musteri_ekle(ad_soyad="Adnan Bey", telefon="02123221722")
  → 2. gorev_ekle(baslik="Adnan Bey ile toplantı saat 14:00", tip="toplanti")
  İKİ fonksiyonu da çağır, ikisinin sonucunu da raporla.
• DOĞAL DİLDEN BİLGİ ÇIKAR: Kullanıcı bilgiyi doğal cümle içinde verirse, bilgiyi çıkar ve direkt işlemi yap.
  Örnek: "saat 14'te Adnan bey ile toplantımız var" → gorev_ekle(baslik="Adnan Bey ile toplantı - 14:00", tip="toplanti")
  Geri soru SORMA, bilgi yeterliyse hemen yap.
• AKILLI OL: "ara" kelimesi bağlama göre farklı anlam taşır:
  - Müşteri ile konuşuluyorsa → telefon ile ara
  - Mülk aranıyorsa → portföyde ara
  - Genel soruysa → veritabanında ara
• BİLGİ EKSİKSE SOR, tahmin etme. Ama bilgi yeterliyse hemen yap, gereksiz soru sorma.
• GÜVENLİ OL: silme/toplu değişiklik işlemlerinde önce onay iste.
• ÖNERİ SUN: "Excel'den toplu ekleyebilirsiniz", "Fotoğraf çekerek sahibinden ilanlarını aktarabilirsiniz" gibi proaktif önerilerde bulun.
• HATA YAPMA: müşteri bilgisi yanlışsa düzelt, tutarsızlık varsa uyar.
• HER ZAMAN ÇÖZÜM ODAKLI OL.
"""


# ─── ANA İŞLEM FONKSİYONU ─────────────────────────────────
def isle(emlakci, mesaj: dict, session: dict, pid: str, tok: str) -> bool:
    """WhatsApp mesajını işle: pattern → bekleyen → AI."""
    tip = mesaj.get('type', 'text')
    telefon = mesaj.get('from', '')

    if tip == 'text':
        metin = mesaj.get('text', {}).get('body', '').strip()
    elif tip == 'location':
        loc = mesaj.get('location', {})
        metin = f'[Konum: {loc.get("latitude")}, {loc.get("longitude")} — {loc.get("name", "")} {loc.get("address", "")}]'
    elif tip == 'image':
        metin = '[Fotoğraf gönderildi]'
    elif tip == 'contacts':
        k = mesaj.get('contacts', [{}])[0]
        ad = f'{k.get("name", {}).get("first_name", "")} {k.get("name", {}).get("last_name", "")}'.strip()
        tel = k.get('phones', [{}])[0].get('phone', '') if k.get('phones') else ''
        metin = f'[Kişi kartı: {ad} — {tel}]'
    else:
        metin = f'[{tip}]'

    gecmis = session.setdefault('gecmis', [])
    gecmis.append({'role': 'user', 'content': metin})
    if len(gecmis) > 20:
        gecmis[:] = gecmis[-20:]

    try:
        from app.services.egitim import diyalog_kaydet, ogrenilen_pattern_esle
        metin_norm = _normalize(metin)
        kullanilan_model = None
        kullanilan_islem = None

        # 1. Bekleyen adımlı işlem varsa tamamla
        bekleyen = _bekleyen_isle(session, emlakci, metin)
        if bekleyen:
            cevap = bekleyen
            kullanilan_islem = 'bekleyen'
            kullanilan_model = 'pattern'
        else:
            # 2. BAĞLAMSAL KARAR MOTORU (pattern'dan önce)
            from app.services.karar import baglam_karar
            try:
                karar = baglam_karar(emlakci.id, metin, metin_norm)
            except Exception:
                karar = None

            if karar:
                komut_adi, args = karar
                if komut_adi == 'telefon_ara':
                    cevap = args['mesaj']
                elif komut_adi == 'musteri_bilgi':
                    cevap = args['mesaj']
                elif komut_adi == 'musteri_iletisim':
                    cevap = args['mesaj']
                elif komut_adi == 'eslestirme_musteri':
                    from app.services.eslestirme import eslesdir
                    sonuclar = eslesdir(emlakci.id, musteri_id=args['musteri_id'], limit=5)
                    if sonuclar:
                        satirlar = [f'• {s["baslik"]} — {s["fiyat_str"]} (%{s["puan"]})' for s in sonuclar]
                        cevap = f'🔗 *Uygun mülkler:*\n\n' + '\n'.join(satirlar)
                    else:
                        cevap = '📭 Şu an uygun mülk bulunamadı.'
                elif komut_adi in ('fiyat_filtre', 'boyut_filtre', 'alternatif'):
                    cevap = args['mesaj']
                else:
                    cevap = args.get('mesaj', 'İşlem tamamlandı.')
                kullanilan_islem = komut_adi
                kullanilan_model = 'baglam'
            else:
                # 3. Öğrenilen pattern'lar (DB'den)
                ogrenilen = ogrenilen_pattern_esle(metin_norm)
                if ogrenilen:
                    cevap = _komut_calistir(ogrenilen, emlakci, metin, session)
                    kullanilan_islem = ogrenilen
                    kullanilan_model = 'ogrenilen'
                else:
                    # 3. Danışmanlık bilgi bankası (sıfır maliyet)
                    from app.services.danismanlik import danismanlik_cevapla
                    danismanlik = danismanlik_cevapla(metin_norm)
                    if danismanlik:
                        cevap = danismanlik
                        kullanilan_islem = 'danismanlik'
                        kullanilan_model = 'pattern'
                    else:
                        # 4. Sabit pattern matching (sıfır maliyet)
                        komut = _pattern_isle(metin_norm, emlakci, metin)
                        if komut:
                            cevap = _komut_calistir(komut, emlakci, metin, session)
                            kullanilan_islem = komut
                            kullanilan_model = 'pattern'
                        else:
                            # 5. AI (function calling — tüm modellerde)
                            sistem = _sistem_prompt(emlakci, metin)
                            openai_key = os.environ.get('OPENAI_API_KEY', '')
                            gemini_key = os.environ.get('GEMINI_API_KEY', '')
                            if openai_key:
                                cevap = _openai_with_functions(openai_key, sistem, gecmis, emlakci)
                                kullanilan_model = 'openai'
                            elif gemini_key:
                                try:
                                    cevap = _gemini_with_functions(gemini_key, sistem, gecmis, emlakci)
                                    kullanilan_model = 'gemini'
                                except Exception:
                                    cevap = _ai_cevap(metin, gecmis, sistem)
                                    kullanilan_model = 'gemini'
                            else:
                                cevap = _ai_cevap(metin, gecmis, sistem)
                                kullanilan_model = 'claude'
                            kullanilan_islem = 'ai_sohbet'

        # Zeka motoru — cevabı zenginleştir
        try:
            from app.services.zeka import mesaj_zenginlestir
            cevap = mesaj_zenginlestir(emlakci, metin, cevap)
        except Exception:
            pass

        # Müşteri hafızasına otomatik kaydet (etkileşim)
        try:
            from app.services.hafiza import _musteri_bul, musteri_hafiza_ekle
            bahsedilen = _musteri_bul(emlakci.id, metin)
            if bahsedilen and kullanilan_islem not in ('yardim', 'rapor', 'performans'):
                musteri_hafiza_ekle(emlakci.id, bahsedilen.id, 'etkilesim', metin[:200])
        except Exception:
            pass

        # Diyaloğu kaydet (eğitim verisi)
        diyalog_kaydet(emlakci.id, metin, metin_norm, kullanilan_islem or 'bilinmeyen', model=kullanilan_model)

        gecmis.append({'role': 'assistant', 'content': cevap})
        wa.mesaj_gonder(pid, tok, telefon, cevap)
    except Exception as e:
        logger.error(f'[Asistan] Hata: {e}', exc_info=True)
        wa.mesaj_gonder(pid, tok, telefon, 'Bir hata oluştu, lütfen tekrar deneyin.')

    return False

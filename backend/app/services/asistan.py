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
    (r'(?:rapor|özet|istatistik|durum|nasil\s*gidiyor|ne\s*durumda)', 'rapor'),
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
    # ── Yardım ──
    # ── Müşteri detay ──
    (r'(?:musteri|müşteri).*(?:bilgi|detay|profil)',          'musteri_liste'),
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
    # ── Yardım & Yetenek ──
    (r'(?:yardim|yardım|neler?\s*yapabilirsin|merhaba|selam|hey)', 'yardim'),
    (r'(?:bunu\s*yapabilir\s*mi|yapabilir\s*misin|mumkun\s*mu|mümkün\s*mü)', 'yetenek_sor'),
    (r'(?:ne\s*yapabilirsin|yeteneklerin|ozelliklerin|özellikler)', 'yardim'),
    (r'(?:nasil\s*kullan|nasıl\s*kullan|nasil\s*yap|nasıl\s*yap)', 'yardim'),
    (r'(?:tesekkur|teşekkür|sagol|sağol|eyv)',                'yardim'),
]

def _pattern_isle(metin_norm, emlakci, metin_raw):
    """Pattern matching ile komut bul. Bulursa (komut, args) döndür, bulamazsa None."""
    for pattern, komut in _PATTERNS:
        if re.search(pattern, metin_norm):
            return komut
    return None


# ─── Direkt DB İşlemleri (sıfır AI maliyeti) ──────────────
def _komut_calistir(komut, emlakci, metin, session):
    """Pattern ile eşleşen komutu çalıştır."""

    if komut == 'yardim':
        return _yardim_mesaji(emlakci)

    if komut == 'musteri_liste':
        return _musteri_listele(emlakci)

    if komut == 'mulk_liste':
        return _mulk_listele(emlakci)

    if komut == 'rapor':
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
        return _gorev_listele(emlakci)

    if komut == 'bugun_ozet':
        return _bugun_ozet(emlakci)

    if komut == 'eslestirme':
        return _eslestirme_ozet(emlakci)

    if komut == 'fatura_ekle':
        session['bekleyen_islem'] = 'fatura_ekle'
        return '*Fatura bilgileri:*\n\nAlıcı adı, tutar (TL), açıklama\n_Örnek: "Ali Yılmaz, 15000, komisyon"_'

    if komut == 'fatura_liste':
        return _fatura_listele(emlakci)

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
        return _hatirlatma_listele(emlakci)

    return None


def _musteri_listele(emlakci):
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).order_by(Musteri.olusturma.desc()).limit(10).all()
    if not musteriler:
        return '📭 Henüz müşteriniz yok.\n\n_"Müşteri ekle" yazarak yeni müşteri ekleyebilirsiniz._'
    satirlar = [f'*{i+1}.* {m.ad_soyad} — {m.telefon or "tel yok"} ({m.islem_turu or "?"})' for i, m in enumerate(musteriler)]
    return f'👥 *Müşterileriniz* ({len(musteriler)})\n\n' + '\n'.join(satirlar)


def _mulk_listele(emlakci):
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).order_by(Mulk.olusturma.desc()).limit(10).all()
    if not mulkler:
        return '📭 Henüz portföyünüzde mülk yok.\n\n_"Mülk ekle" yazarak yeni mülk ekleyebilirsiniz._'
    satirlar = []
    for i, m in enumerate(mulkler):
        fiyat = f'{int(m.fiyat):,}'.replace(',', '.') + ' TL' if m.fiyat else '?'
        satirlar.append(f'*{i+1}.* {m.baslik or m.adres or "—"} — {fiyat} ({m.islem_turu or "?"})')
    return f'🏢 *Portföyünüz* ({len(mulkler)})\n\n' + '\n'.join(satirlar)


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
    except:
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
    except:
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
            '💡 *Hesaplama:* "kira vergisi hesapla"\n\n'
            '💡 *İpucu:* Excel\'den toplu müşteri/portföy ekleyebilirsiniz!\n'
            'Fotoğraf çekerek sahibinden ilanlarını portföye aktarabilirsiniz!\n\n'
            '_Doğal dille yazın, anlayacağım._')


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
    except:
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
    except:
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


def _gorev_listele(emlakci):
    from app.models.planlama import Gorev
    gorevler = Gorev.query.filter_by(emlakci_id=emlakci.id).filter(Gorev.durum != 'tamamlandi').order_by(Gorev.olusturma.desc()).limit(10).all()
    if not gorevler:
        return '📅 Aktif görev yok.\n\n_"Görev ekle" yazarak yeni görev ekleyebilirsiniz._'
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


def _fatura_listele(emlakci):
    from app.models.fatura import Fatura
    faturalar = Fatura.query.filter_by(emlakci_id=emlakci.id).order_by(Fatura.olusturma.desc()).limit(10).all()
    if not faturalar:
        return '🧾 Henüz fatura yok.'
    satirlar = [f'*{f.fatura_no}* — {f.alici_ad or "?"} — {int(f.toplam):,} TL — {f.durum}'.replace(',', '.') for f in faturalar]
    return f'🧾 *Son Faturalar*\n\n' + '\n'.join(satirlar)


def _unutma_kaydet(emlakci, metin):
    """'Unutma' komutu — önemli bilgiyi hatırlatma olarak kaydet."""
    not_obj = Not(emlakci_id=emlakci.id, icerik=metin, etiket='hatirlatici')
    db.session.add(not_obj)
    db.session.commit()
    return f'🧠 *Hatırladım!*\n\n📌 {metin[:150]}\n\n_"Hatırlatmalar" yazarak tüm kayıtları görebilirsiniz._'


def _hatirlatma_listele(emlakci):
    """Kaydedilmiş hatırlatmaları listele."""
    notlar = Not.query.filter_by(emlakci_id=emlakci.id, etiket='hatirlatici', tamamlandi=False)\
        .order_by(Not.olusturma.desc()).limit(10).all()
    if not notlar:
        return '📭 Henüz hatırlatma yok.\n\n_"Unutma: ..." yazarak hatırlatma ekleyebilirsiniz._'
    satirlar = [f'*{i+1}.* {n.icerik[:80]}' for i, n in enumerate(notlar)]
    return f'🧠 *Hatırlatmalarınız* ({len(notlar)})\n\n' + '\n'.join(satirlar)


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
]

def _ai_function_call(fonksiyon_adi, args, emlakci):
    """AI'nın çağırdığı fonksiyonu yürüt."""
    if fonksiyon_adi == 'musteri_ekle':
        m = Musteri(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('ad_soyad', 'telefon', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Müşteri eklendi: {args.get("ad_soyad")}'

    if fonksiyon_adi == 'musteri_listele':
        return _musteri_listele(emlakci)

    if fonksiyon_adi == 'mulk_ekle':
        m = Mulk(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Mülk eklendi: {args.get("baslik")}'

    if fonksiyon_adi == 'mulk_listele':
        return _mulk_listele(emlakci)

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

    return None


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

    # Function call kontrolü
    for part in response.parts:
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            args = dict(fc.args) if fc.args else {}
            sonuc = _ai_function_call(fc.name, args, emlakci)
            if sonuc:
                return sonuc

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
        tc = msg.tool_calls[0]
        args = json.loads(tc.function.arguments)
        sonuc = _ai_function_call(tc.function.name, args, emlakci)
        return sonuc or msg.content or 'İşlem tamamlandı.'

    return msg.content


# ─── Sistem Prompt ─────────────────────────────────────────
def _sistem_prompt(emlakci, metin=''):
    from app.services.hafiza import baglam_olustur
    from app.services.kisisellesme import kisisellesmis_prompt_eki
    try:
        baglam = baglam_olustur(emlakci, metin)
    except:
        baglam = ''
    try:
        baglam += kisisellesmis_prompt_eki(emlakci.id)
    except:
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
    except:
        pass

    return f"""Sen Emlakisim'in yapay zeka destekli emlak asistanısın. Gerçek bir emlak ofisi asistanı gibi davran.

{baglam}

Görevlerin:
- Müşteri bilgilerini kaydet ve yönet (ad, telefon, TC, bütçe, tercih)
- Portföy mülklerini kaydet ve yönet (detaylı bilgi: kat, ısınma, m², her şey)
- Yer gösterme belgesi ve kira kontratı oluştur
- Müşteri-mülk eşleştirmesi yap ve öner
- Not, plan ve hatırlatma al
- Rapor sun, hesaplama yap (kira vergisi, ROI, değer artış)
- Fatura oluştur ve takip et
- Cari hesap takibi yap
- Tapu süreçleri, kredi işlemleri hakkında bilgi ver
- Sosyal medya paylaşım metni oluştur
- Randevu ve takvim yönet
- Sektörel bilgi ver (mevzuat, vergi, piyasa)

Kurallar:
- Türkçe konuş, kısa ve net ol{ton_talimat}
- Bilgi eksikse sor, tahmin etme
- İşlem yaptıktan sonra onay mesajı ver
- Proaktif ol: yapılabilecekleri öner, hatırlat, uyar
- Bağlamı koru: önceki konuşmalardan bilgi kullan
- Müşteri adı geçtiğinde ilgili bilgileri hatırla ve kullan
- WhatsApp formatı kullan (*kalın*, _italik_)
- Güvenli ol: silme/değiştirme işlemlerinde onay iste
- Her zaman çözüm odaklı ol
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

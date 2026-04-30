"""
ZEKA MOTORU — Kimsenin öngörmediği akıllı davranışlar
Proaktif, öngörücü, kişiselleşmiş, bağlamsal.

Bu modül asistanı gerçek bir "düşünen" asistana dönüştürür:
1. Niyet analizi — kullanıcı ne istiyor gerçekten?
2. Proaktif öneriler — sorulmadan önce faydalı bilgi sun
3. Müşteri davranış analizi — kim ne zaman harekete geçer?
4. Akıllı zamanlama — doğru zamanda doğru öneri
5. Bağlam zincirleme — "önceki" "sonraki" "diğer" anlar
6. Duygu/aciliyet algılama — "acil" "hemen" "kritik" fark edilir
"""
import re
import logging
from datetime import datetime, timedelta
from app.models import db, Musteri, Mulk, Not
from app.models.planlama import Gorev
from app.models.lead import Lead
from app.models.muhasebe import GelirGider
from app.models.hafiza_model import MusteriHafiza, KonusmaState

logger = logging.getLogger(__name__)


# ── 1. NİYET ANALİZİ ──────────────────────────────────────
def niyet_analiz(metin):
    """Kullanıcının gerçek niyetini anla — sadece kelimeler değil, bağlam."""
    metin_lower = metin.lower()
    niyet = {
        'aciliyet': 0,      # 0-10 aciliyet skoru
        'duygu': 'normal',  # normal, olumlu, olumsuz, acil
        'islem_tipi': None, # sorgu, islem, rapor, sohbet
        'hedef': None,      # musteri, mulk, muhasebe, genel
        'alt_niyet': None,  # "karşılaştır", "en ucuz", "yakın"
    }

    # Aciliyet tespiti
    acil_kelimeler = ['acil', 'hemen', 'simdi', 'şimdi', 'derhal', 'bekleyemez', 'çok önemli', 'kritik', 'ivedi']
    for k in acil_kelimeler:
        if k in metin_lower:
            niyet['aciliyet'] = 8
            niyet['duygu'] = 'acil'
            break

    # Duygu tespiti
    olumlu = ['teşekkür', 'harika', 'mükemmel', 'süper', 'güzel', 'bravo', 'iyi']
    olumsuz = ['kötü', 'berbat', 'sorun', 'hata', 'yanlış', 'problem', 'şikayet']
    for k in olumlu:
        if k in metin_lower:
            niyet['duygu'] = 'olumlu'
    for k in olumsuz:
        if k in metin_lower:
            niyet['duygu'] = 'olumsuz'

    # İşlem tipi
    sorgu_kelimeler = ['kaç', 'ne kadar', 'listele', 'göster', 'bul', 'ara', 'var mı', 'hangi']
    islem_kelimeler = ['ekle', 'oluştur', 'kaydet', 'sil', 'değiştir', 'güncelle']
    rapor_kelimeler = ['rapor', 'özet', 'analiz', 'karşılaştır', 'hesapla']
    for k in islem_kelimeler:
        if k in metin_lower:
            niyet['islem_tipi'] = 'islem'
            break
    if not niyet['islem_tipi']:
        for k in rapor_kelimeler:
            if k in metin_lower:
                niyet['islem_tipi'] = 'rapor'
                break
    if not niyet['islem_tipi']:
        for k in sorgu_kelimeler:
            if k in metin_lower:
                niyet['islem_tipi'] = 'sorgu'
                break
    if not niyet['islem_tipi']:
        niyet['islem_tipi'] = 'sohbet'

    # Hedef
    if re.search(r'müşteri|musteri|alıcı|alici|kiracı|kiraci', metin_lower):
        niyet['hedef'] = 'musteri'
    elif re.search(r'mülk|mulk|portföy|portfoy|daire|ev|arsa|villa', metin_lower):
        niyet['hedef'] = 'mulk'
    elif re.search(r'fatura|gelir|gider|muhasebe|cari|borç|alacak', metin_lower):
        niyet['hedef'] = 'muhasebe'

    # Alt niyet
    if 'en ucuz' in metin_lower or 'en uygun' in metin_lower:
        niyet['alt_niyet'] = 'en_ucuz'
    elif 'karşılaştır' in metin_lower or 'kıyasla' in metin_lower:
        niyet['alt_niyet'] = 'karsilastir'
    elif 'yakın' in metin_lower or 'civardaki' in metin_lower:
        niyet['alt_niyet'] = 'yakin'
    elif 'daha ucuz' in metin_lower or 'daha pahalı' in metin_lower:
        niyet['alt_niyet'] = 'fiyat_filtre'
    elif 'başka' in metin_lower or 'diğer' in metin_lower or 'alternatif' in metin_lower:
        niyet['alt_niyet'] = 'alternatif'

    return niyet


# ── 2. PROAKTİF ÖNERİLER ──────────────────────────────────
def proaktif_oneriler(emlakci):
    """Asistanın sorulmadan sunacağı akıllı öneriler."""
    oneriler = []

    # Dönüş yapılmamış sıcak müşteriler
    sicak = Musteri.query.filter_by(emlakci_id=emlakci.id, sicaklik='sicak').all()
    for m in sicak:
        son_etkilesim = MusteriHafiza.query.filter_by(
            emlakci_id=emlakci.id, musteri_id=m.id
        ).order_by(MusteriHafiza.olusturma.desc()).first()
        if not son_etkilesim or (datetime.utcnow() - son_etkilesim.olusturma).days >= 2:
            oneriler.append({
                'tip': 'musteri_donus',
                'oncelik': 'yuksek',
                'mesaj': f'🔥 {m.ad_soyad} sıcak müşteri — {2 if not son_etkilesim else (datetime.utcnow() - son_etkilesim.olusturma).days}+ gündür dönüş yok',
                'aksiyon': f'musteri_id:{m.id}',
            })

    # Eşleşmeyen müşteriler (portföyde uygun mülk yok)
    from app.services.eslestirme import eslesdir
    for m in Musteri.query.filter_by(emlakci_id=emlakci.id).limit(20).all():
        eslesim = eslesdir(emlakci.id, musteri_id=m.id, limit=1)
        if not eslesim and m.butce_max:
            oneriler.append({
                'tip': 'portfoy_eksik',
                'oncelik': 'orta',
                'mesaj': f'📭 {m.ad_soyad} için portföyde uygun mülk yok ({m.islem_turu})',
            })

    # Geciken faturalar
    from app.models.fatura import Fatura
    geciken = Fatura.query.filter_by(emlakci_id=emlakci.id, durum='bekliyor').filter(
        Fatura.vade_tarihi < datetime.utcnow()
    ).all()
    if geciken:
        oneriler.append({
            'tip': 'geciken_fatura',
            'oncelik': 'yuksek',
            'mesaj': f'⚠️ {len(geciken)} geciken fatura var!',
        })

    # Haftalık performans trendi
    bu_hafta = datetime.utcnow() - timedelta(days=7)
    yeni_musteri = Musteri.query.filter(
        Musteri.emlakci_id == emlakci.id, Musteri.olusturma >= bu_hafta
    ).count()
    yeni_mulk = Mulk.query.filter(
        Mulk.emlakci_id == emlakci.id, Mulk.olusturma >= bu_hafta
    ).count()
    if yeni_musteri == 0 and yeni_mulk == 0:
        oneriler.append({
            'tip': 'aktivite_dusuk',
            'oncelik': 'dusuk',
            'mesaj': '📉 Bu hafta yeni müşteri veya mülk eklenmedi. Aktif olmanız önerilir.',
        })

    return oneriler[:5]  # max 5 öneri


# ── 3. MÜŞTERİ DAVRANIŞ ANALİZİ ──────────────────────────
def musteri_analiz(emlakci_id, musteri_id):
    """Müşterinin davranış analizi — ne zaman harekete geçer?"""
    m = Musteri.query.get(musteri_id)
    if not m:
        return {}

    hafizalar = MusteriHafiza.query.filter_by(
        emlakci_id=emlakci_id, musteri_id=musteri_id
    ).order_by(MusteriHafiza.olusturma).all()

    # İletişim sıklığı
    from app.models.iletisim_gecmisi import IletisimKayit
    iletisimler = IletisimKayit.query.filter_by(
        emlakci_id=emlakci_id, musteri_id=musteri_id
    ).order_by(IletisimKayit.olusturma).all()

    son_iletisim = iletisimler[-1].olusturma if iletisimler else None
    gun_gecti = (datetime.utcnow() - son_iletisim).days if son_iletisim else 999

    return {
        'musteri': m.ad_soyad,
        'sicaklik': m.sicaklik,
        'iletisim_sayisi': len(iletisimler),
        'hafiza_sayisi': len(hafizalar),
        'son_iletisim_gun': gun_gecti,
        'risk': 'yuksek' if gun_gecti > 7 and m.sicaklik == 'sicak' else 'orta' if gun_gecti > 14 else 'dusuk',
        'oneri': _musteri_oneri(m, gun_gecti, len(iletisimler)),
    }


def _musteri_oneri(musteri, gun_gecti, iletisim_sayisi):
    """Müşteri için akıllı öneri."""
    if musteri.sicaklik == 'sicak' and gun_gecti > 3:
        return f'🔥 ACİL: {musteri.ad_soyad} sıcak müşteri, {gun_gecti} gündür dönüş yok. Hemen arayın!'
    if gun_gecti > 14:
        return f'⚠️ {musteri.ad_soyad} ile {gun_gecti} gündür iletişim yok. Soğuyor olabilir.'
    if iletisim_sayisi > 5 and musteri.sicaklik != 'sicak':
        return f'💡 {musteri.ad_soyad} ile {iletisim_sayisi} görüşme yapıldı ama hala sıcak değil. Strateji değişikliği önerilir.'
    return None


# ── 4. AKILLI MESAJ ZENGINLEŞTIRME ─────────────────────────
def mesaj_zenginlestir(emlakci, metin, ai_cevap):
    """AI cevabına proaktif öneriler + bağlam ekle."""
    ek = ''

    niyet = niyet_analiz(metin)

    # Acil mesajlarda hızlı aksiyon öner
    if niyet['aciliyet'] >= 8:
        ek += '\n\n⚡ _Acil olarak işaretlendi._'

    # Müşteri sorgulandığında analiz ekle
    if niyet['hedef'] == 'musteri' and niyet['islem_tipi'] == 'sorgu':
        state = KonusmaState.query.filter_by(emlakci_id=emlakci.id).first()
        if state and state.son_musteri_id:
            analiz = musteri_analiz(emlakci.id, state.son_musteri_id)
            if analiz.get('oneri'):
                ek += f'\n\n💡 _{analiz["oneri"]}_'

    # "Daha ucuz" / "başka" deyince alternatif öner
    if niyet['alt_niyet'] in ('fiyat_filtre', 'alternatif'):
        ek += '\n\n💡 _Daha fazla seçenek için filtreleri değiştirin veya bütçeyi güncelleyin._'

    return ai_cevap + ek if ek else ai_cevap


# ── 5. GÜNLÜK ZEKA RAPORU ─────────────────────────────────
def gunluk_zeka_raporu(emlakci):
    """Her gün için akıllı özet + öneriler."""
    oneriler = proaktif_oneriler(emlakci)

    # İstatistikler
    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
    hafta = bugun - timedelta(days=7)
    ay = bugun - timedelta(days=30)

    haftalik_musteri = Musteri.query.filter(Musteri.emlakci_id == emlakci.id, Musteri.olusturma >= hafta).count()
    aylik_gelir = sum(k.tutar for k in GelirGider.query.filter(
        GelirGider.emlakci_id == emlakci.id, GelirGider.tip == 'gelir', GelirGider.tarih >= ay).all())

    rapor = {
        'tarih': bugun.isoformat(),
        'haftalik_musteri': haftalik_musteri,
        'aylik_gelir': round(aylik_gelir, 2),
        'oneriler': oneriler,
        'oneri_sayisi': len(oneriler),
    }

    return rapor

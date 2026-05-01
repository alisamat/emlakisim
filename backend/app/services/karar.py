"""
BAĞLAMSAL KARAR MOTORU — Aynı kelime farklı bağlamda farklı anlam
"ara" → telefon mu? DB arama mı? eşleştirme mi?
"onu" → son müşteri mi? son mülk mü?
"ekle" → müşteri mi? mülk mü? not mu?

Pattern matching'den ÖNCE çalışır, bağlama göre doğru işlemi seçer.
"""
import re
import logging
from app.models import Musteri, Mulk
from app.models.hafiza_model import KonusmaState

logger = logging.getLogger(__name__)


def baglam_karar(emlakci_id, metin, metin_norm):
    """
    Mesajı bağlam + niyet ile analiz et.
    Döndürür: (komut, args) veya None (pattern'a devret)
    """
    state = KonusmaState.query.filter_by(emlakci_id=emlakci_id).first()

    # 1. "ARA" bağlam çözme
    ara_sonuc = _ara_baglam(emlakci_id, metin, metin_norm, state)
    if ara_sonuc:
        return ara_sonuc

    # 2. "ONU / ONA / BUNU" zamir çözme + işlem
    zamir_sonuc = _zamir_islem(emlakci_id, metin, metin_norm, state)
    if zamir_sonuc:
        return zamir_sonuc

    # 3. "DAHA" bağlam (daha ucuz, daha büyük, başka)
    daha_sonuc = _daha_baglam(emlakci_id, metin, metin_norm, state)
    if daha_sonuc:
        return daha_sonuc

    return None


def _ara_baglam(emlakci_id, metin, metin_norm, state):
    """'ara' kelimesinin bağlamsal analizi."""
    if 'ara' not in metin_norm and 'bul' not in metin_norm:
        return None

    # "onu ara" / "ona ara" → son müşterinin telefonu
    if re.search(r'\b(onu|ona)\s*(ara|ula)', metin_norm):
        if state and state.son_musteri_id:
            m = Musteri.query.get(state.son_musteri_id)
            if m and m.telefon:
                return ('telefon_ara', {
                    'musteri': m.ad_soyad,
                    'telefon': m.telefon,
                    'mesaj': f'📞 *{m.ad_soyad}*\nTelefon: {m.telefon}\n\n[Aramak için tıklayın](tel:{m.telefon.replace(" ", "")})'
                })

    # Konuşmada müşteri adı geçiyor + "ara" → telefon
    if state and state.son_musteri_id:
        m = Musteri.query.get(state.son_musteri_id)
        if m:
            # "ara" kelimesi varsa ve son konuşma müşteri ile ilgiliyse
            # ve cümlede arama/bul anlamı varsa
            telefon_ipucu = re.search(r'(telefon|cep|numara|ula[sş]|ilet|haber\s*ver|donus|dönüş|ara\s*onu|onu\s*ara)', metin_norm)
            if telefon_ipucu and m.telefon:
                return ('telefon_ara', {
                    'musteri': m.ad_soyad,
                    'telefon': m.telefon,
                    'mesaj': f'📞 *{m.ad_soyad}*\nTelefon: {m.telefon}\n\n_Aramak için: tel:{m.telefon}_'
                })

    # İsim + ara → o kişiyi bul ve telefon ver
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
    for m in musteriler:
        if m.ad_soyad:
            ad_lower = m.ad_soyad.lower()
            parcalar = ad_lower.split()
            for parca in parcalar:
                if len(parca) > 2 and parca in metin_norm:
                    # Bu kişi hakkında "ara" denmiş
                    if m.telefon:
                        return ('telefon_ara', {
                            'musteri': m.ad_soyad,
                            'telefon': m.telefon,
                            'mesaj': f'📞 *{m.ad_soyad}*\nTelefon: {m.telefon}\n\n_Aramak için: tel:{m.telefon}_'
                        })
                    else:
                        return ('musteri_bilgi', {
                            'mesaj': f'👤 *{m.ad_soyad}* — telefon numarası kayıtlı değil.'
                        })

    # "Kadıköy ara" / "3+1 daire ara" → mülk arama
    # Bu durumda pattern'a devret (genel_ara çalışsın)
    return None


def _zamir_islem(emlakci_id, metin, metin_norm, state):
    """Zamir + işlem bağlamı."""
    if not state:
        return None

    # "ona mail at" / "ona mesaj gönder"
    if re.search(r'\b(ona|onun|musteri)\s*(mail|email|mesaj|gonder|yaz)', metin_norm):
        if state.son_musteri_id:
            m = Musteri.query.get(state.son_musteri_id)
            if m:
                det = m.detaylar or {}
                email = det.get('email', '')
                return ('musteri_iletisim', {
                    'musteri': m.ad_soyad,
                    'telefon': m.telefon,
                    'email': email,
                    'mesaj': (f'👤 *{m.ad_soyad}*\n'
                             f'📞 {m.telefon or "-"}\n'
                             f'📧 {email or "Email kayıtlı değil"}\n\n'
                             f'_İletişim kurmak için bilgileri kullanın._')
                })

    # "ona uygun mülk bul" / "ona göster"
    if re.search(r'\b(ona|onun|icin|için)\s*(uygun|mulk|mülk|daire|ev|göster|bul|esles|eşleş)', metin_norm):
        if state.son_musteri_id:
            return ('eslestirme_musteri', {
                'musteri_id': state.son_musteri_id,
            })

    # "bunu ekle" / "bunu kaydet" (son ilan OCR)
    if re.search(r'\b(bunu|buna)\s*(ekle|kaydet|portfoy|portföy)', metin_norm):
        if state.son_mulk_id:
            return ('mulk_detay', {
                'mulk_id': state.son_mulk_id,
                'mesaj': 'Son görüntülenen mülk zaten portföyde.'
            })

    return None


def _daha_baglam(emlakci_id, metin, metin_norm, state):
    """'daha' bağlamı — daha ucuz, daha büyük, başka."""
    if not state or not state.son_arama:
        return None

    if re.search(r'(daha\s*ucuz|daha\s*uygun|daha\s*hesapli)', metin_norm):
        return ('fiyat_filtre', {
            'yon': 'ucuz',
            'mesaj': '💰 Daha uygun fiyatlı seçenekler aranıyor...\n_Son aramanıza göre fiyat düşük olanlar filtreleniyor._'
        })

    if re.search(r'(daha\s*buyuk|daha\s*genis|daha\s*büyük)', metin_norm):
        return ('boyut_filtre', {
            'yon': 'buyuk',
            'mesaj': '📐 Daha büyük seçenekler aranıyor...'
        })

    if re.search(r'(baska|başka|diger|diğer|alternatif)', metin_norm):
        return ('alternatif', {
            'mesaj': '🔄 Alternatif seçenekler aranıyor...'
        })

    return None

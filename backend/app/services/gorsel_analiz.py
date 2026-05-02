"""
GÖRSEL ANALİZ & SANAL STAGING SERVİSİ
Fotoğraftan konut analizi, değerleme ve sanal ev düzenleme.
Gemini Vision API kullanır.
"""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)


def konut_analiz(image_base64, mulk_bilgi=None):
    """
    Fotoğraftan konut analizi yap.
    - Oda tipi tanıma
    - Durum puanlama (1-100)
    - Özellik tespiti
    - Renovasyon tahmini
    - Tahmini değerleme
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return {'hata': 'Gemini API anahtarı bulunamadı'}

    ek_bilgi = ''
    if mulk_bilgi:
        ek_bilgi = f"\nMülk bilgileri: {json.dumps(mulk_bilgi, ensure_ascii=False)}"

    prompt = f"""Bu emlak fotoğrafını profesyonel bir emlak değerleme uzmanı gözüyle analiz et.{ek_bilgi}

Aşağıdaki JSON formatında cevap ver (Türkçe):
{{
    "oda_tipi": "salon/yatak_odasi/mutfak/banyo/balkon/koridor/dis_mekan/otopark/bahce",
    "durum_puani": 1-100 arası (100=mükemmel, yeni bina kalitesi),
    "durum_aciklama": "kısa durum açıklaması",
    "tespit_edilen_ozellikler": ["özellik1", "özellik2"],
    "pozitif_ozellikler": ["güçlü yön1", "güçlü yön2"],
    "negatif_ozellikler": ["zayıf yön1", "zayıf yön2"],
    "renovasyon_onerileri": ["öneri1", "öneri2"],
    "tahmini_renovasyon_maliyeti": "düşük/orta/yüksek",
    "renovasyon_maliyet_tl": tahmini TL maliyet,
    "aydinlatma": "iyi/orta/kötü",
    "ferahlik": "ferah/orta/dar",
    "genel_izlenim": "kısa genel değerlendirme",
    "deger_etkisi": "bu oda değeri artırıyor/azaltıyor/nötr"
}}

Sadece JSON döndür."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
        r = requests.post(url, json={
            'contents': [{
                'parts': [
                    {'text': prompt},
                    {'inline_data': {'mime_type': 'image/jpeg', 'data': image_base64}},
                ]
            }],
            'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 1024},
        }, timeout=20)
        metin = r.json()['candidates'][0]['content']['parts'][0]['text']
        metin = metin.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        return json.loads(metin)
    except Exception as e:
        logger.error(f'[GörselAnaliz] Hata: {e}')
        return {'hata': str(e)}


def coklu_analiz(images_base64, mulk_bilgi=None):
    """
    Birden fazla fotoğrafı analiz et ve genel değerleme yap.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return {'hata': 'Gemini API anahtarı bulunamadı'}

    ek_bilgi = ''
    if mulk_bilgi:
        ek_bilgi = f"\nMülk bilgileri: {json.dumps(mulk_bilgi, ensure_ascii=False)}"

    parts = [{'text': f"""Bu mülkün {len(images_base64)} fotoğrafını analiz ederek kapsamlı değerleme yap.{ek_bilgi}

Aşağıdaki JSON formatında cevap ver (Türkçe):
{{
    "genel_durum_puani": 1-100,
    "odalar": [
        {{"tip": "oda tipi", "puan": 1-100, "not": "kısa açıklama"}}
    ],
    "genel_ozellikler": ["özellik1", "özellik2"],
    "guclu_yanlar": ["güçlü yön1", "güçlü yön2"],
    "zayif_yanlar": ["zayıf yön1", "zayıf yön2"],
    "renovasyon_onerileri": ["öneri1", "öneri2"],
    "tahmini_toplam_renovasyon_tl": tahmini toplam TL,
    "deger_sinifi": "A/B/C/D (A=lüks, D=bakımsız)",
    "tahmini_m2_fiyat_araligi": {{"min": TL, "max": TL}},
    "satis_potansiyeli": "yüksek/orta/düşük",
    "hedef_kitle": "aile/genç profesyonel/yatırımcı/öğrenci",
    "genel_degerlendirme": "2-3 cümlelik genel analiz"
}}

Sadece JSON döndür."""}]

    for img in images_base64[:5]:  # Max 5 fotoğraf
        parts.append({'inline_data': {'mime_type': 'image/jpeg', 'data': img}})

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
        r = requests.post(url, json={
            'contents': [{'parts': parts}],
            'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 2048},
        }, timeout=30)
        metin = r.json()['candidates'][0]['content']['parts'][0]['text']
        metin = metin.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        return json.loads(metin)
    except Exception as e:
        logger.error(f'[ÇokluAnaliz] Hata: {e}')
        return {'hata': str(e)}


def sanal_staging(image_base64, stil='modern', oda_tipi=None):
    """
    Sanal ev düzenleme — boş odayı mobilyalı hale getir.
    Faz 1: Gemini ile detaylı mobilyalı açıklama + öneriler.
    Faz 2: DALL-E / Stability AI ile gerçek görsel (API key gelince).
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return {'hata': 'Gemini API anahtarı bulunamadı'}

    stil_aciklama = {
        'modern': 'Modern minimalist Türk tarzı — açık renkler, temiz çizgiler, doğal ahşap',
        'klasik': 'Klasik Türk evi tarzı — sıcak renkler, geleneksel motifler, zarif mobilyalar',
        'minimalist': 'Ultra minimalist — beyaz/gri tonlar, az mobilya, geniş alanlar',
        'luks': 'Lüks segment — mermer, altın detaylar, tasarım mobilyalar',
        'genc': 'Genç profesyonel — renkli aksesuarlar, fonksiyonel, kompakt',
    }

    prompt = f"""Bu boş/az eşyalı oda fotoğrafını analiz et ve "{stil}" tarzında mobilyalı hale getirmek için detaylı plan oluştur.

Stil: {stil_aciklama.get(stil, stil)}
{f"Oda tipi: {oda_tipi}" if oda_tipi else "Oda tipini fotoğraftan belirle."}

Aşağıdaki JSON formatında cevap ver (Türkçe):
{{
    "oda_tipi": "tespit edilen oda tipi",
    "mevcut_durum": "odanın mevcut durumu kısa açıklama",
    "onerilen_mobilyalar": [
        {{"ad": "mobilya adı", "konum": "nereye konulacak", "renk": "renk önerisi", "tahmini_fiyat_tl": TL}}
    ],
    "dekorasyon_onerileri": [
        {{"ad": "dekorasyon öğesi", "aciklama": "detay", "tahmini_fiyat_tl": TL}}
    ],
    "renk_paleti": ["renk1", "renk2", "renk3"],
    "aydinlatma_onerileri": ["öneri1", "öneri2"],
    "toplam_tahmini_maliyet_tl": toplam TL,
    "sonuc_aciklama": "Bu düzenleme ile oda nasıl görünecek — 3-4 cümle detaylı açıklama",
    "deger_artisi_tahmini": "yüzde kaç değer artışı beklenir",
    "hedef_kitle_uyumu": "bu düzenleme hangi alıcı profiline hitap eder"
}}

Sadece JSON döndür."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
        r = requests.post(url, json={
            'contents': [{
                'parts': [
                    {'text': prompt},
                    {'inline_data': {'mime_type': 'image/jpeg', 'data': image_base64}},
                ]
            }],
            'generationConfig': {'temperature': 0.5, 'maxOutputTokens': 2048},
        }, timeout=20)
        metin = r.json()['candidates'][0]['content']['parts'][0]['text']
        metin = metin.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        return json.loads(metin)
    except Exception as e:
        logger.error(f'[SanalStaging] Hata: {e}')
        return {'hata': str(e)}

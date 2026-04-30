"""
İLAN OCR — İlan sitesi fotoğrafından bilgi çıkarma, karşılaştırma, telefon bulma
"""
import os
import json
import re
import logging
import requests

logger = logging.getLogger(__name__)

_ILAN_OCR_PROMPT = """Bu bir emlak ilan sayfasının ekran görüntüsü. Tüm bilgileri JSON olarak çıkar:

{
  "baslik": "ilan başlığı",
  "fiyat": 0,
  "adres": "konum/adres/mahalle",
  "sehir": "",
  "ilce": "",
  "oda_sayisi": "3+1",
  "brut_m2": 0,
  "net_m2": 0,
  "bina_yasi": 0,
  "kat": "",
  "kat_sayisi": 0,
  "isinma": "",
  "tip": "daire/villa/arsa/dukkan/ofis",
  "islem_turu": "kira/satis",
  "esyali": "",
  "site_icerisinde": "",
  "aidat": 0,
  "ilan_no": "",
  "ilan_tarihi": "",
  "emlakci_adi": "",
  "emlakci_telefon": "",
  "emlakci_firma": "",
  "aciklama": "ilan açıklaması (kısa)",
  "ozellikler": ["özellik1", "özellik2"],
  "guven_skoru": 85
}

Kurallar:
- Türkçe oku, TL kullan
- Fiyatı sayı olarak yaz
- Telefon numarasını bul (varsa)
- Emlakçı/ilan sahibi bilgisini çıkar
- Göremediğin alanları null yap
- Sadece JSON döndür"""


def ilan_fotograf_oku(image_base64):
    """İlan fotoğrafından tüm bilgileri çıkar."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [
                {'text': _ILAN_OCR_PROMPT},
                {'inline_data': {'mime_type': 'image/jpeg', 'data': image_base64}},
            ]}],
            'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 2048},
        }, timeout=30)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        sonuc = json.loads(text)

        # Telefon numarası temizle
        if sonuc.get('emlakci_telefon'):
            tel = re.sub(r'[^\d+]', '', sonuc['emlakci_telefon'])
            sonuc['emlakci_telefon'] = tel

        sonuc['model'] = 'gemini'
        return sonuc
    except Exception as e:
        logger.error(f'[İlan OCR] Hata: {e}')
        return {'hata': str(e)}


def ilanlari_karsilastir(ilanlar):
    """Birden fazla ilanı karşılaştır — farklar, ortaklar, fırsatlar."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return _basit_karsilastir(ilanlar)

    ilan_metin = '\n\n'.join([
        f"İlan {i+1}: {json.dumps(ilan, ensure_ascii=False)[:400]}"
        for i, ilan in enumerate(ilanlar)
    ])

    prompt = f"""Aşağıdaki emlak ilanlarını karşılaştır:

{ilan_metin}

Analiz et:
1. Ortak özellikler
2. Farklılıklar (tablo halinde)
3. Fiyat karşılaştırması (m² bazlı)
4. En iyi fırsat hangisi ve neden
5. Yatırım açısından değerlendirme

Türkçe, kısa ve öz yaz."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        return {'analiz': r.json()['candidates'][0]['content']['parts'][0]['text']}
    except Exception as e:
        return {'hata': str(e)}


def _basit_karsilastir(ilanlar):
    satirlar = []
    for i, ilan in enumerate(ilanlar):
        fiyat = ilan.get('fiyat', 0)
        m2 = ilan.get('brut_m2') or ilan.get('net_m2') or 0
        m2_fiyat = round(fiyat / m2) if m2 and fiyat else 0
        satirlar.append(f"İlan {i+1}: {ilan.get('baslik', '?')} — {fiyat:,} TL — {m2} m² — {m2_fiyat:,} TL/m²")
    return {'analiz': '\n'.join(satirlar)}

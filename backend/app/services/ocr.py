"""
OCR SERVİSİ — Fiş/fatura fotoğrafından gider çıkarma
Gemini Vision (ucuz) → OpenAI Vision (yedek)
OnMuhasebeci referans: onmuhFron-web/backend/app/services/gemini_fis_ocr_service.py
"""
import os
import json
import base64
import logging
import requests

logger = logging.getLogger(__name__)

_PROMPT = """Bu bir fiş veya fatura fotoğrafı. Lütfen aşağıdaki bilgileri JSON olarak çıkar:

{
  "belge_tipi": "fiş/fatura/e-fatura",
  "firma": "firma adı",
  "tarih": "GG.AA.YYYY",
  "toplam": 0.00,
  "kdv_tutar": 0.00,
  "kdv_oran": 0,
  "kalemler": [
    {"ad": "ürün adı", "tutar": 0.00}
  ],
  "kategori": "ofis/ulaşım/yemek/fatura/reklam/diğer",
  "guven_skoru": 85
}

Kurallar:
- Türkçe oku, Türk lirası (TL) kullan
- KDV oranlarını doğru tespit et (%1, %10, %20)
- Toplam tutarı doğru hesapla
- kategori: ofis malzemesi, ulaşım, yemek/restoran, fatura (elektrik/su/doğalgaz), reklam, diğer
- guven_skoru: 0-100 arası, okunabilirliğe göre
- Sadece JSON döndür, başka metin ekleme
"""


def fis_oku(image_base64: str) -> dict:
    """Fiş/fatura fotoğrafını oku → yapısal veri döndür."""

    # 1. Gemini Vision (en ucuz: ~$0.0003/fiş)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            sonuc = _gemini_vision(gemini_key, image_base64)
            if sonuc and sonuc.get('guven_skoru', 0) >= 60:
                sonuc['model'] = 'gemini'
                return sonuc
            logger.warning(f'[OCR] Gemini düşük güven: {sonuc.get("guven_skoru")}')
        except Exception as e:
            logger.warning(f'[OCR] Gemini hata: {e}')

    # 2. OpenAI Vision (yedek: ~$0.003/fiş)
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        try:
            sonuc = _openai_vision(openai_key, image_base64)
            if sonuc:
                sonuc['model'] = 'openai'
                return sonuc
        except Exception as e:
            logger.error(f'[OCR] OpenAI hata: {e}')

    return {'hata': 'OCR servisi çalışmadı', 'guven_skoru': 0}


def _gemini_vision(api_key: str, image_base64: str) -> dict:
    """Gemini 1.5 Flash Vision ile fiş oku."""
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
    payload = {
        'contents': [{
            'parts': [
                {'text': _PROMPT},
                {'inline_data': {'mime_type': 'image/jpeg', 'data': image_base64}},
            ]
        }],
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 1024},
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    text = r.json()['candidates'][0]['content']['parts'][0]['text']
    # JSON çıkar
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    return json.loads(text)


def _openai_vision(api_key: str, image_base64: str) -> dict:
    """OpenAI GPT-4o-mini Vision ile fiş oku."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': _PROMPT},
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}},
            ],
        }],
        max_tokens=1024,
    )
    text = r.choices[0].message.content.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    return json.loads(text)

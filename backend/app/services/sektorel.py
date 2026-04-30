"""
SEKTÖREL TAKİP — Emlak haberleri, mevzuat değişiklikleri, piyasa bilgisi
Gemini ile güncel bilgi çekme.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


def sektor_haberleri(konu='emlak piyasası'):
    """Sektörel gelişmeleri AI ile özetle."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    prompt = f"""Türkiye emlak sektöründe "{konu}" ile ilgili güncel bilgileri özetle.

Şunları içersin:
- Son gelişmeler ve trendler
- Önemli yasal düzenlemeler
- Piyasa durumu ve tahminler
- Emlakçılar için öneriler

Kısa ve öz Türkçe yaz, madde madde."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'icerik': text, 'konu': konu}
    except Exception as e:
        return {'hata': str(e)}


def piyasa_analizi(sehir='İstanbul', tip='daire'):
    """Bölge bazlı piyasa analizi."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    prompt = f"""Türkiye {sehir} ilinde {tip} tipi gayrimenkul piyasası hakkında bilgi ver:

- Ortalama m² fiyatları (kiralık ve satılık)
- Son dönem fiyat trendi (artış/düşüş)
- En çok talep gören ilçeler
- Yatırım için öneriler
- Dikkat edilmesi gereken riskler

Kısa ve öz Türkçe yaz."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'analiz': text, 'sehir': sehir, 'tip': tip}
    except Exception as e:
        return {'hata': str(e)}

"""
GELİŞMİŞ SERVİSLER — Web arama, metin okuma, sesli arama hazırlık
İleri seviye özellikler için temel altyapı.
"""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)


def web_arama(sorgu, max_sonuc=5):
    """Google Custom Search veya Gemini ile web araması."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    prompt = f"""Şu konuda kısa bir web araştırması yap ve Türkçe özetle:
"{sorgu}"

Sonuçları şu formatta ver:
- Kısa özet (2-3 cümle)
- Önemli bulgular (madde madde)
- Kaynak önerisi

Emlak sektörü bağlamında cevapla."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'sonuc': text, 'sorgu': sorgu}
    except Exception as e:
        return {'hata': str(e)}


def metin_analiz(metin):
    """Uzun metin analizi ve özetleme."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    prompt = f"""Aşağıdaki metni analiz et ve Türkçe özetle:

{metin[:3000]}

Çıkar:
1. Özet (2-3 cümle)
2. Önemli noktalar (madde madde)
3. Emlak ile ilgili bilgiler (varsa)"""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'analiz': text}
    except Exception as e:
        return {'hata': str(e)}


def sosyal_medya_icerik(mulk, platform='instagram'):
    """Mülk için sosyal medya paylaşım içeriği oluştur."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return {'hata': 'API anahtarı yok'}

    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''

    prompt = f"""Aşağıdaki emlak ilanı için {platform} paylaşım metni oluştur:

Başlık: {mulk.baslik or ''}
Adres: {mulk.adres or ''}, {mulk.sehir or ''} {mulk.ilce or ''}
Tip: {mulk.tip or ''} — {'Kiralık' if mulk.islem_turu == 'kira' else 'Satılık'}
Fiyat: {fiyat}
Oda: {mulk.oda_sayisi or ''}
Detaylar: {json.dumps(det, ensure_ascii=False)[:500]}

Platform: {platform}
- Instagram: emoji kullan, hashtag ekle, dikkat çekici
- Facebook: detaylı açıklama, iletişim bilgisi
- WhatsApp: kısa ve öz, emoji, fiyat vurgulu"""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 512},
        }, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return {'icerik': text, 'platform': platform}
    except Exception as e:
        return {'hata': str(e)}

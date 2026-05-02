"""
ÇEVİRİ SERVİSİ — Google Cloud Translation (500K karakter/ay ücretsiz)
Yabancı müşteriler için ilan çevirisi.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

DIL_KODLARI = {
    'ingilizce': 'en', 'english': 'en', 'en': 'en',
    'arapca': 'ar', 'arapça': 'ar', 'arabic': 'ar', 'ar': 'ar',
    'rusca': 'ru', 'rusça': 'ru', 'russian': 'ru', 'ru': 'ru',
    'almanca': 'de', 'german': 'de', 'de': 'de',
    'fransizca': 'fr', 'fransızca': 'fr', 'french': 'fr', 'fr': 'fr',
    'ispanyolca': 'es', 'spanish': 'es', 'es': 'es',
    'farsca': 'fa', 'farsça': 'fa', 'persian': 'fa', 'fa': 'fa',
    'turkce': 'tr', 'türkçe': 'tr', 'turkish': 'tr', 'tr': 'tr',
    'cince': 'zh', 'çince': 'zh', 'chinese': 'zh', 'zh': 'zh',
}

DIL_ADLARI = {
    'en': 'İngilizce', 'ar': 'Arapça', 'ru': 'Rusça', 'de': 'Almanca',
    'fr': 'Fransızca', 'es': 'İspanyolca', 'fa': 'Farsça', 'tr': 'Türkçe', 'zh': 'Çince',
}


def cevir(metin, hedef_dil='en', kaynak_dil='tr'):
    """Metni çevir — önce Google Translate, yedekte Gemini."""
    hedef = DIL_KODLARI.get(hedef_dil.lower(), hedef_dil)
    kaynak = DIL_KODLARI.get(kaynak_dil.lower(), kaynak_dil)

    # 1. Google Cloud Translation
    google_key = os.environ.get('GOOGLE_TRANSLATE_KEY', '')
    if google_key:
        try:
            r = requests.post('https://translation.googleapis.com/language/translate/v2', params={
                'key': google_key,
            }, json={
                'q': metin, 'target': hedef, 'source': kaynak, 'format': 'text',
            }, timeout=10)
            data = r.json()
            if 'data' in data:
                ceviri = data['data']['translations'][0]['translatedText']
                return {'basarili': True, 'ceviri': ceviri, 'kaynak': kaynak, 'hedef': hedef, 'motor': 'google'}
        except Exception as e:
            logger.error(f'[Çeviri] Google hata: {e}')

    # 2. Gemini ile çeviri (yedek)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            hedef_ad = DIL_ADLARI.get(hedef, hedef)
            prompt = f'Aşağıdaki Türkçe metni {hedef_ad} diline çevir. Sadece çeviriyi yaz, başka açıklama ekleme:\n\n{metin}'
            r = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}',
                json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.1}},
                timeout=15,
            )
            ceviri = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            return {'basarili': True, 'ceviri': ceviri, 'kaynak': kaynak, 'hedef': hedef, 'motor': 'gemini'}
        except Exception as e:
            logger.error(f'[Çeviri] Gemini hata: {e}')

    return {'basarili': False, 'hata': 'Çeviri servisi kullanılamıyor'}

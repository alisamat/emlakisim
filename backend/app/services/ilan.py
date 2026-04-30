"""
İLAN — Portföy için ilan metni oluşturma (sahibinden, hepsiemlak tarzı)
"""
import os
import json
import requests
import logging

logger = logging.getLogger(__name__)


def ilan_metni_olustur(mulk, platform='sahibinden'):
    """Mülk bilgilerinden ilan metni oluştur."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return _basit_ilan(mulk)

    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''

    prompt = f"""Aşağıdaki emlak bilgilerinden {platform} sitesi için profesyonel ilan metni oluştur:

Başlık: {mulk.baslik or ''}
Adres: {mulk.adres or ''}, {mulk.sehir or ''} {mulk.ilce or ''}
Tip: {mulk.tip or ''} — {'Kiralık' if mulk.islem_turu == 'kira' else 'Satılık'}
Fiyat: {fiyat}
Oda: {mulk.oda_sayisi or ''}
Detaylar: {json.dumps(det, ensure_ascii=False)[:800]}
Notlar: {mulk.notlar or ''}

Kurallar:
- Dikkat çekici başlık
- Detaylı açıklama (konum avantajları, özellikler, yakın çevre)
- Madde madde özellikler listesi
- Profesyonel ve ikna edici dil
- Türkçe yaz
- {platform} formatına uygun"""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.6, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f'[İlan] Hata: {e}')
        return _basit_ilan(mulk)


def _basit_ilan(mulk):
    """AI yoksa basit ilan metni."""
    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''
    islem = 'Kiralık' if mulk.islem_turu == 'kira' else 'Satılık'

    metin = f"""📌 {mulk.baslik or mulk.adres or 'Emlak İlanı'}

🏷 {islem} {mulk.tip or 'Daire'}
📍 {mulk.adres or ''} {mulk.sehir or ''} {mulk.ilce or ''}
💰 {fiyat}

📋 Özellikler:
"""
    if mulk.oda_sayisi: metin += f'• Oda: {mulk.oda_sayisi}\n'
    if det.get('brut_m2'): metin += f'• Brüt: {det["brut_m2"]} m²\n'
    if det.get('net_m2'): metin += f'• Net: {det["net_m2"]} m²\n'
    if det.get('bulundugu_kat'): metin += f'• Kat: {det["bulundugu_kat"]}\n'
    if det.get('isinma'): metin += f'• Isınma: {det["isinma"]}\n'

    if mulk.notlar:
        metin += f'\n📝 {mulk.notlar}\n'

    return metin

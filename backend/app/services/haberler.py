"""
HABER SERVİSİ — Gerçek emlak sektörü haberleri
NewsAPI.ai veya Gemini ile.
"""
import os
import requests
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def emlak_haberleri(konu='emlak piyasası türkiye'):
    """Gerçek emlak haberleri getir."""

    # 1. NewsAPI.ai (gerçek haberler)
    newsapi_key = os.environ.get('NEWSAPI_KEY', '')
    if newsapi_key:
        try:
            r = requests.post('https://newsapi.ai/api/v1/article/getArticles', json={
                'action': 'getArticles',
                'keyword': konu,
                'lang': 'tur',
                'articlesCount': 8,
                'articlesSortBy': 'date',
                'apiKey': newsapi_key,
            }, timeout=15)
            data = r.json()
            makaleler = data.get('articles', {}).get('results', [])
            if makaleler:
                haberler = []
                for m in makaleler[:8]:
                    haberler.append({
                        'baslik': m.get('title', ''),
                        'kaynak': m.get('source', {}).get('title', ''),
                        'tarih': m.get('dateTimePub', '')[:10],
                        'url': m.get('url', ''),
                        'ozet': m.get('body', '')[:150],
                    })
                return {'basarili': True, 'haberler': haberler, 'motor': 'newsapi'}
        except Exception as e:
            logger.error(f'[Haberler] NewsAPI hata: {e}')

    # 2. Gemini ile haber özeti
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            prompt = f"""Türkiye emlak sektöründe {konu} hakkında güncel bilgi ver.
5-6 madde halinde kısa özet yaz. Her madde için başlık ve 1-2 cümle açıklama.
Türkçe yaz, JSON formatı kullanma, düz metin olarak yaz."""

            r = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}',
                json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 1024}},
                timeout=15,
            )
            metin = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            # Düz metin olarak döndür — JSON parse gerekmez
            return {'basarili': True, 'metin': metin, 'motor': 'gemini', 'uyari': 'AI bilgisi — güncelliği garanti değil'}
        except Exception as e:
            logger.error(f'[Haberler] Gemini hata: {e}')

    # 3. OpenAI fallback
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            r = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': f'Türkiye emlak sektöründe {konu} hakkında güncel bilgi ver. 5-6 madde halinde kısa özet yaz. Türkçe.'}],
                max_tokens=500,
            )
            metin = r.choices[0].message.content.strip()
            return {'basarili': True, 'metin': metin, 'motor': 'openai', 'uyari': 'AI bilgisi — güncelliği garanti değil'}
        except Exception as e:
            logger.error(f'[Haberler] OpenAI hata: {e}')

    return {'basarili': False, 'hata': 'Haber servisi kullanılamıyor'}


def haber_formatla(sonuc):
    """Haberleri sohbet mesajına çevir."""
    if not sonuc.get('basarili'):
        return '⚠️ Haberler alınamadı.  Lütfen tekrar deneyin.'

    # Düz metin (Gemini)
    if sonuc.get('metin'):
        uyari = f'\n\n_⚠️ {sonuc["uyari"]}_' if sonuc.get('uyari') else ''
        return f'📰 *Emlak Sektörü*\n\n{sonuc["metin"]}{uyari}'

    satirlar = ['📰 *Emlak Sektörü Haberleri*\n']
    if sonuc.get('uyari'):
        satirlar.append(f'_⚠️ {sonuc["uyari"]}_\n')

    for i, h in enumerate(sonuc['haberler'][:6]):
        satirlar.append(
            f'*{i+1}.* {h["baslik"]}\n'
            + (f'   _{h.get("kaynak", "")}_ · {h.get("tarih", "")}\n' if h.get('kaynak') else '')
            + (f'   {h.get("ozet", "")[:100]}\n' if h.get('ozet') else '')
            + (f'   {h["url"]}\n' if h.get('url') else '')
        )

    return '\n'.join(satirlar)

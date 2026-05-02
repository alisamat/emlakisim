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

    # 2. Gemini ile haber özeti (yedek — ama halüsinasyon riski var)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            prompt = f"""Türkiye emlak sektöründe {konu} konusundaki son gelişmeleri listele.
Her haber için JSON formatında:
[{{"baslik": "haber başlığı", "ozet": "kısa özet", "kaynak": "muhtemel kaynak", "tarih": "tahmini tarih"}}]

NOT: Bunlar gerçek haberler olmalı, uydurma olmamalı. Emin olmadığın haberleri yazma.
Sadece JSON array döndür."""

            r = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}',
                json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 1024}},
                timeout=15,
            )
            metin = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            metin = metin.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
            haberler = json.loads(metin)
            return {'basarili': True, 'haberler': haberler[:8], 'motor': 'gemini', 'uyari': 'AI tahmini — doğruluğu garanti değil'}
        except Exception as e:
            logger.error(f'[Haberler] Gemini hata: {e}')

    return {'basarili': False, 'hata': 'Haber servisi kullanılamıyor'}


def haber_formatla(sonuc):
    """Haberleri sohbet mesajına çevir."""
    if not sonuc.get('basarili'):
        return '⚠️ Haberler alınamadı.'

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

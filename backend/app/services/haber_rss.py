"""
HABER RSS SERVİSİ — Gerçek emlak haberleri (ücretsiz, lisans yok)
Günde 1 kez çeker, DB'ye kaydeder, 10 günden eski siler.
"""
import os
import re
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from app import db

logger = logging.getLogger(__name__)

# RSS Kaynakları
RSS_KAYNAKLAR = [
    {
        'ad': 'Google News',
        'url': 'https://news.google.com/rss/search?q=emlak+gayrimenkul+konut+t%C3%BCrkiye&hl=tr&gl=TR&ceid=TR:tr',
        'tip': 'google',
    },
    {
        'ad': 'Google News Kira',
        'url': 'https://news.google.com/rss/search?q=kira+art%C4%B1%C5%9F+konut+fiyat&hl=tr&gl=TR&ceid=TR:tr',
        'tip': 'google',
    },
]


class HaberCache(db.Model):
    """Haber cache — RSS'den çekilen haberler."""
    __tablename__ = 'haber_cache'

    id          = db.Column(db.Integer, primary_key=True)
    baslik      = db.Column(db.String(500), nullable=False)
    kaynak      = db.Column(db.String(100))
    url         = db.Column(db.Text)
    ozet        = db.Column(db.Text)
    tarih       = db.Column(db.DateTime)
    kategori    = db.Column(db.String(50))     # emlak, kira, konut, yatirim
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


def _html_temizle(text):
    """HTML taglarını temizle."""
    if not text:
        return ''
    return re.sub(r'<[^>]+>', '', text).strip()


def _tarih_parse(tarih_str):
    """RSS tarihini datetime'a çevir."""
    if not tarih_str:
        return None
    for fmt in [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
    ]:
        try:
            return datetime.strptime(tarih_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def rss_cek():
    """Tüm RSS kaynaklarından haber çek ve DB'ye kaydet."""
    toplam = 0
    for kaynak in RSS_KAYNAKLAR:
        try:
            r = requests.get(kaynak['url'], timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Emlakisim/1.0)'
            })
            if r.status_code != 200:
                logger.warning(f'[RSS] {kaynak["ad"]} HTTP {r.status_code}')
                continue

            root = ET.fromstring(r.content)
            channel = root.find('channel')
            if channel is None:
                continue

            for item in channel.findall('item')[:15]:
                baslik = _html_temizle(item.findtext('title', ''))
                link = item.findtext('link', '')
                ozet = _html_temizle(item.findtext('description', ''))
                tarih_str = item.findtext('pubDate', '')
                kaynak_ad = item.findtext('source', kaynak['ad'])

                if not baslik:
                    continue

                # Zaten var mı kontrol
                mevcut = HaberCache.query.filter_by(baslik=baslik).first()
                if mevcut:
                    continue

                tarih = _tarih_parse(tarih_str)

                h = HaberCache(
                    baslik=baslik[:500],
                    kaynak=kaynak_ad[:100] if kaynak_ad else kaynak['ad'],
                    url=link,
                    ozet=ozet[:500] if ozet else '',
                    tarih=tarih,
                )
                db.session.add(h)
                toplam += 1

            db.session.commit()
            logger.info(f'[RSS] {kaynak["ad"]}: {toplam} yeni haber')
        except Exception as e:
            logger.error(f'[RSS] {kaynak["ad"]} hata: {e}')

    # 10 günden eski haberleri sil
    sinir = datetime.utcnow() - timedelta(days=10)
    eski = HaberCache.query.filter(HaberCache.olusturma < sinir).delete()
    db.session.commit()
    if eski:
        logger.info(f'[RSS] {eski} eski haber silindi')

    return toplam


def haberleri_getir(limit=10):
    """Cache'den haberleri getir."""
    haberler = HaberCache.query.order_by(HaberCache.tarih.desc().nullslast()).limit(limit).all()

    if not haberler:
        # Cache boşsa hemen çek
        rss_cek()
        haberler = HaberCache.query.order_by(HaberCache.tarih.desc().nullslast()).limit(limit).all()

    return [{
        'id': h.id,
        'baslik': h.baslik,
        'kaynak': h.kaynak,
        'url': h.url,
        'ozet': h.ozet,
        'tarih': h.tarih.strftime('%d.%m.%Y') if h.tarih else '',
    } for h in haberler]


def haber_formatla_rss(haberler):
    """Haberleri sohbet mesajına çevir."""
    if not haberler:
        return '📰 Henüz haber yok. Biraz sonra tekrar deneyin.'

    satirlar = ['📰 *Emlak Sektörü — Güncel Haberler*\n']
    for i, h in enumerate(haberler[:8]):
        satirlar.append(
            f'*{i+1}.* {h["baslik"]}\n'
            f'   _{h["kaynak"]}_ · {h["tarih"]}'
            + (f'\n   {h["url"]}' if h.get('url') else '')
        )

    return '\n\n'.join(satirlar)

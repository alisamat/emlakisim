"""
DÖVİZ & ALTIN KURLARI — TCMB + yedek kaynaklar
Günlük güncellenir, cache'lenir.
"""
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache
_kur_cache = {'tarih': None, 'kurlar': {}}


def kurlari_getir(yenile=False):
    """Günlük döviz + altın kurlarını getir."""
    global _kur_cache

    # Cache kontrolü (1 saat geçerli)
    if not yenile and _kur_cache['tarih'] and (datetime.utcnow() - _kur_cache['tarih']).seconds < 3600:
        return _kur_cache['kurlar']

    # 1. TCMB XML
    kurlar = _tcmb_kurlar()

    # 2. Yedek: API
    if not kurlar:
        kurlar = _yedek_kurlar()

    # 3. Son çare: sabit
    if not kurlar:
        kurlar = _sabit_kurlar()

    _kur_cache = {'tarih': datetime.utcnow(), 'kurlar': kurlar}
    return kurlar


def _tcmb_kurlar():
    """TCMB'den günlük kurları al."""
    try:
        url = 'https://www.tcmb.gov.tr/kurlar/today.xml'
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Emlakisim/1.0'})
        if r.status_code != 200:
            return None

        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)

        kurlar = {'tarih': datetime.utcnow().strftime('%d.%m.%Y'), 'kaynak': 'TCMB'}

        for currency in root.findall('.//Currency'):
            kod = currency.get('Kod', '')
            alis = currency.find('ForexBuying')
            satis = currency.find('ForexSelling')

            if kod == 'USD' and alis is not None and alis.text:
                kurlar['USD'] = {'alis': float(alis.text), 'satis': float(satis.text) if satis is not None and satis.text else float(alis.text)}
            elif kod == 'EUR' and alis is not None and alis.text:
                kurlar['EUR'] = {'alis': float(alis.text), 'satis': float(satis.text) if satis is not None and satis.text else float(alis.text)}
            elif kod == 'GBP' and alis is not None and alis.text:
                kurlar['GBP'] = {'alis': float(alis.text), 'satis': float(satis.text) if satis is not None and satis.text else float(alis.text)}

        # Altın
        for currency in root.findall('.//Currency'):
            kod = currency.get('Kod', '')
            if kod == 'XAU':
                alis = currency.find('ForexBuying')
                if alis is not None and alis.text:
                    # XAU ons fiyatı TRY — gram'a çevir (1 ons = 31.1035 gram)
                    ons_tl = float(alis.text)
                    kurlar['ALTIN_GRAM'] = round(ons_tl / 31.1035, 2)

        if 'USD' in kurlar:
            logger.info(f'[Döviz] TCMB kurları alındı: USD={kurlar["USD"]["satis"]}')
            return kurlar
        return None
    except Exception as e:
        logger.warning(f'[Döviz] TCMB hatası: {e}')
        return None


def _yedek_kurlar():
    """Yedek API — exchangerate veya benzeri."""
    try:
        r = requests.get('https://api.exchangerate-api.com/v4/latest/TRY', timeout=10)
        if r.status_code == 200:
            data = r.json()
            rates = data.get('rates', {})
            usd = 1 / rates.get('USD', 1) if rates.get('USD') else 37
            eur = 1 / rates.get('EUR', 1) if rates.get('EUR') else 40
            gbp = 1 / rates.get('GBP', 1) if rates.get('GBP') else 47
            return {
                'tarih': datetime.utcnow().strftime('%d.%m.%Y'),
                'kaynak': 'exchangerate-api',
                'USD': {'alis': round(usd, 4), 'satis': round(usd * 1.005, 4)},
                'EUR': {'alis': round(eur, 4), 'satis': round(eur * 1.005, 4)},
                'GBP': {'alis': round(gbp, 4), 'satis': round(gbp * 1.005, 4)},
            }
    except Exception as e:
        logger.warning(f'[Döviz] Yedek API hatası: {e}')
    return None


def _sabit_kurlar():
    """Son çare — sabit kurlar."""
    return {
        'tarih': datetime.utcnow().strftime('%d.%m.%Y'),
        'kaynak': 'sabit (güncel değil)',
        'USD': {'alis': 37.50, 'satis': 37.65},
        'EUR': {'alis': 40.20, 'satis': 40.40},
        'GBP': {'alis': 47.00, 'satis': 47.30},
        'ALTIN_GRAM': 3850.0,
    }


def fiyat_donustur(tutar_tl):
    """TL tutarı döviz + altın karşılığına çevir."""
    kurlar = kurlari_getir()

    sonuc = {'TL': tutar_tl}

    if 'USD' in kurlar:
        sonuc['USD'] = round(tutar_tl / kurlar['USD']['satis'], 2)
    if 'EUR' in kurlar:
        sonuc['EUR'] = round(tutar_tl / kurlar['EUR']['satis'], 2)
    if 'GBP' in kurlar:
        sonuc['GBP'] = round(tutar_tl / kurlar['GBP']['satis'], 2)
    if 'ALTIN_GRAM' in kurlar:
        sonuc['ALTIN_GRAM'] = round(tutar_tl / kurlar['ALTIN_GRAM'], 2)

    sonuc['kurlar'] = {
        'USD': kurlar.get('USD', {}).get('satis'),
        'EUR': kurlar.get('EUR', {}).get('satis'),
        'GBP': kurlar.get('GBP', {}).get('satis'),
        'ALTIN': kurlar.get('ALTIN_GRAM'),
    }
    sonuc['tarih'] = kurlar.get('tarih', '')
    sonuc['kaynak'] = kurlar.get('kaynak', '')

    return sonuc

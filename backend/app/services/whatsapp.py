import requests
import logging

logger = logging.getLogger(__name__)
BASE = 'https://graph.facebook.com/v19.0'


def mesaj_gonder(pid: str, tok: str, telefon: str, metin: str) -> bool:
    try:
        r = requests.post(
            f'{BASE}/{pid}/messages',
            headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'},
            json={'messaging_product': 'whatsapp', 'to': telefon,
                  'type': 'text', 'text': {'body': metin}},
            timeout=10
        )
        if not r.ok:
            logger.warning(f'[WA] {r.status_code} {r.text[:200]}')
        return r.ok
    except Exception as e:
        logger.error(f'[WA] Hata: {e}')
        return False

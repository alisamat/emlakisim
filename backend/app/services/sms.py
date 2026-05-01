"""
SMS SERVİSİ — Netgsm entegrasyonu (API key eklenince aktif olur)
Alternatif: Twilio

Kullanım:
  sms_gonder('05321234567', 'Merhaba, yer gösterme randevunuz yarın saat 14:00')

Gerekli env:
  NETGSM_USERCODE = kullanıcı kodu
  NETGSM_PASSWORD = şifre
  NETGSM_HEADER = başlık (onaylı gönderici adı)
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


def sms_gonder(telefon, mesaj, gonderen=None):
    """SMS gönder. Netgsm veya Twilio."""
    # Telefon formatı düzelt
    telefon = telefon.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if telefon.startswith('0'):
        telefon = '90' + telefon[1:]
    if not telefon.startswith('90'):
        telefon = '90' + telefon

    # 1. Netgsm
    netgsm_user = os.environ.get('NETGSM_USERCODE', '')
    netgsm_pass = os.environ.get('NETGSM_PASSWORD', '')
    if netgsm_user and netgsm_pass:
        return _netgsm_gonder(telefon, mesaj, netgsm_user, netgsm_pass)

    # 2. Twilio
    twilio_sid = os.environ.get('TWILIO_SID', '')
    twilio_token = os.environ.get('TWILIO_TOKEN', '')
    if twilio_sid and twilio_token:
        return _twilio_gonder(telefon, mesaj, twilio_sid, twilio_token)

    logger.warning('[SMS] API anahtarı tanımlı değil')
    return False, 'SMS servisi yapılandırılmamış'


def _netgsm_gonder(telefon, mesaj, usercode, password):
    """Netgsm API ile SMS gönder."""
    header = os.environ.get('NETGSM_HEADER', 'EMLAKISIM')
    try:
        url = 'https://api.netgsm.com.tr/sms/send/get'
        params = {
            'usercode': usercode,
            'password': password,
            'gsmno': telefon,
            'message': mesaj,
            'msgheader': header,
            'dil': 'TR',
        }
        r = requests.get(url, params=params, timeout=10)
        kod = r.text.strip().split()[0] if r.text else ''

        if kod in ('00', '01', '02'):
            logger.info(f'[SMS] Netgsm gönderildi: {telefon}')
            return True, 'Gönderildi'
        else:
            logger.error(f'[SMS] Netgsm hata: {r.text}')
            return False, f'Netgsm hata: {kod}'
    except Exception as e:
        logger.error(f'[SMS] Netgsm exception: {e}')
        return False, str(e)


def _twilio_gonder(telefon, mesaj, sid, token):
    """Twilio API ile SMS gönder."""
    twilio_from = os.environ.get('TWILIO_FROM', '')
    try:
        url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
        r = requests.post(url, auth=(sid, token), data={
            'To': f'+{telefon}',
            'From': twilio_from,
            'Body': mesaj,
        }, timeout=10)
        if r.status_code in (200, 201):
            logger.info(f'[SMS] Twilio gönderildi: {telefon}')
            return True, 'Gönderildi'
        else:
            logger.error(f'[SMS] Twilio hata: {r.text}')
            return False, f'Twilio hata: {r.status_code}'
    except Exception as e:
        logger.error(f'[SMS] Twilio exception: {e}')
        return False, str(e)


def sms_durum():
    """SMS servis durumu."""
    netgsm = bool(os.environ.get('NETGSM_USERCODE'))
    twilio = bool(os.environ.get('TWILIO_SID'))
    return {
        'aktif': netgsm or twilio,
        'servis': 'Netgsm' if netgsm else 'Twilio' if twilio else 'Yok',
    }

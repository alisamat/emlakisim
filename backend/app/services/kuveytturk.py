"""
KUVEYT TÜRK SANAL POS — 3D Secure Entegrasyonu
OnMuhasebeci'den adapte edilmiştir.

3D Secure Payment Flow:
1. start_3d_secure_payment() → XML oluştur + 3D Secure başlat
2. User → Bank 3D Secure sayfası
3. Bank → callback (AuthenticationResponse)
4. verify_3d_callback() → MD doğrula
5. provision_payment() → Final ödeme provizyon
"""
import os
import hashlib
import base64
import requests
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Config
def _cfg(key, default=''):
    return os.environ.get(key, default)

MERCHANT_ID = lambda: _cfg('KUVEYTTURK_MERCHANT_ID', '496')
CUSTOMER_ID = lambda: _cfg('KUVEYTTURK_CUSTOMER_ID', '400235')
USERNAME = lambda: _cfg('KUVEYTTURK_USERNAME', 'apitest')
PASSWORD = lambda: _cfg('KUVEYTTURK_PASSWORD', 'api123')
BASE_URL = lambda: _cfg('RAILWAY_PUBLIC_DOMAIN', 'backend-production-9ffc.up.railway.app')

# Kredi paketleri
from app.services.doviz import kurlari_getir

# Paketler USD bazlı — TRY fiyatı TCMB kuruyla dinamik hesaplanır
PAKETLER_USD = {
    'temel':        {'kredi': 3000,   'fiyat_usd': 8.00,   'aciklama': 'Temel Paket',        'populer': False},
    'standart':     {'kredi': 12000,  'fiyat_usd': 32.00,  'aciklama': 'Standart Paket',     'populer': True},
    'profesyonel':  {'kredi': 30000,  'fiyat_usd': 80.00,  'aciklama': 'Profesyonel Paket',  'populer': False},
    'kurumsal':     {'kredi': 120000, 'fiyat_usd': 320.00, 'aciklama': 'Kurumsal Paket',     'populer': False},
}

def _usd_kur():
    """TCMB USD satış kuru."""
    kurlar = kurlari_getir()
    return kurlar.get('USD', {}).get('satis', 38.00)

def paketleri_getir():
    """Paketleri güncel TRY fiyatıyla döndür (KDV %20 dahil)."""
    kur = _usd_kur()
    sonuc = {}
    for pid, p in PAKETLER_USD.items():
        fiyat_tl_net = round(p['fiyat_usd'] * kur, 2)
        fiyat_tl_kdv = round(fiyat_tl_net * 1.20, 2)
        sonuc[pid] = {
            'kredi': p['kredi'],
            'fiyat_usd': p['fiyat_usd'],
            'fiyat_tl': fiyat_tl_kdv,       # KDV dahil (ödeme tutarı)
            'fiyat_tl_net': fiyat_tl_net,    # KDV hariç
            'aciklama': p['aciklama'],
            'populer': p['populer'],
        }
    return sonuc, kur



def generate_hash_payment(merchant_id, order_id, amount, ok_url, fail_url, username, password):
    hashed_password = base64.b64encode(
        hashlib.sha1(password.encode('iso-8859-9')).digest()
    ).decode('utf-8')
    hash_str = f"{merchant_id}{order_id}{amount}{ok_url}{fail_url}{username}{hashed_password}"
    hash_bytes = hashlib.sha1(hash_str.encode('iso-8859-9')).digest()
    return base64.b64encode(hash_bytes).decode('utf-8')


def generate_hash_provision(merchant_id, order_id, amount, username, password):
    hashed_password = base64.b64encode(
        hashlib.sha1(password.encode('iso-8859-9')).digest()
    ).decode('utf-8')
    hash_str = f"{merchant_id}{order_id}{amount}{username}{hashed_password}"
    hash_bytes = hashlib.sha1(hash_str.encode('iso-8859-9')).digest()
    return base64.b64encode(hash_bytes).decode('utf-8')


def start_3d_secure_payment(card_holder_name, card_number, card_expire_month, card_expire_year,
                            card_cvv, amount, order_id, client_ip="127.0.0.1"):
    """3D Secure ödeme başlat → HTML döndür."""
    try:
        merchant_id = MERCHANT_ID()
        customer_id = CUSTOMER_ID()
        username = USERNAME()
        password = PASSWORD()

        base_url = f"https://{BASE_URL()}"
        ok_url = f"{base_url}/api/odeme/kuveytturk/callback"
        fail_url = f"{base_url}/api/odeme/kuveytturk/callback"

        if not all([merchant_id, username, password]):
            return {'success': False, 'error': 'Ödeme sistemi yapılandırması eksik'}

        # Türkçe karakter temizle
        for tr, en in {'Ç':'C','ç':'c','Ğ':'G','ğ':'g','İ':'I','ı':'i','Ö':'O','ö':'o','Ş':'S','ş':'s','Ü':'U','ü':'u'}.items():
            card_holder_name = card_holder_name.replace(tr, en)

        hash_data = generate_hash_payment(merchant_id, order_id, amount, ok_url, fail_url, username, password)

        xml = f'''<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <APIVersion>TDV2.0.0</APIVersion>
    <OkUrl>{ok_url}</OkUrl>
    <FailUrl>{fail_url}</FailUrl>
    <HashData>{hash_data}</HashData>
    <MerchantId>{merchant_id}</MerchantId>
    <CustomerId>{customer_id}</CustomerId>
    <UserName>{username}</UserName>
    <CardNumber>{card_number}</CardNumber>
    <CardExpireDateYear>{card_expire_year}</CardExpireDateYear>
    <CardExpireDateMonth>{card_expire_month}</CardExpireDateMonth>
    <CardCVV2>{card_cvv}</CardCVV2>
    <CardHolderName>{card_holder_name}</CardHolderName>
    <CardType>MasterCard</CardType>
    <BatchID>0</BatchID>
    <TransactionType>Sale</TransactionType>
    <InstallmentCount>0</InstallmentCount>
    <Amount>{amount}</Amount>
    <DisplayAmount>{amount}</DisplayAmount>
    <CurrencyCode>0949</CurrencyCode>
    <MerchantOrderId>{order_id}</MerchantOrderId>
    <TransactionSecurity>3</TransactionSecurity>
</KuveytTurkVPosMessage>'''

        api_url = "https://sanalpos.kuveytturk.com.tr/ServiceGateWay/Home/ThreeDModelPayGate"
        r = requests.post(api_url, data=xml, headers={'Content-Type': 'application/xml'}, verify=True, timeout=30)

        if r.status_code == 200:
            logger.info(f'[KuveytTürk] 3D Secure başlatıldı — OrderId: {order_id}')
            return {'success': True, 'html_content': r.text, 'order_id': order_id}
        return {'success': False, 'error': f'HTTP {r.status_code}'}
    except Exception as e:
        logger.error(f'[KuveytTürk] 3D Secure hata: {e}')
        return {'success': False, 'error': 'Ödeme başlatılamadı'}


def verify_3d_callback(authentication_response):
    """3D Secure callback doğrula."""
    try:
        from urllib.parse import unquote_plus
        xml_string = unquote_plus(authentication_response)

        root = ET.fromstring(xml_string)
        response_code = root.find('ResponseCode').text if root.find('ResponseCode') is not None else None
        response_message = root.find('ResponseMessage').text if root.find('ResponseMessage') is not None else ''

        vpos_msg = root.find('VPosMessage')
        md = root.find('MD').text if root.find('MD') is not None else None

        if response_code == '00' and md:
            order_id = vpos_msg.find('MerchantOrderId').text if vpos_msg is not None and vpos_msg.find('MerchantOrderId') is not None else None
            amount = vpos_msg.find('Amount').text if vpos_msg is not None and vpos_msg.find('Amount') is not None else None
            logger.info(f'[KuveytTürk] 3D doğrulama başarılı — OrderId: {order_id}')
            return {'success': True, 'order_id': order_id, 'amount': amount, 'md': md}
        else:
            logger.error(f'[KuveytTürk] 3D doğrulama başarısız — {response_code}: {response_message}')
            return {'success': False, 'error': f'3D doğrulama başarısız: {response_message}'}
    except Exception as e:
        logger.error(f'[KuveytTürk] Callback doğrulama hata: {e}')
        return {'success': False, 'error': 'Doğrulama hatası'}


def provision_payment(order_id, amount, md):
    """Final ödeme provizyon."""
    try:
        merchant_id = MERCHANT_ID()
        customer_id = CUSTOMER_ID()
        username = USERNAME()
        password = PASSWORD()

        hash_data = generate_hash_provision(merchant_id, order_id, amount, username, password)

        xml = f'''<KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <APIVersion>1.0.0</APIVersion>
    <HashData>{hash_data}</HashData>
    <MerchantId>{merchant_id}</MerchantId>
    <CustomerId>{customer_id}</CustomerId>
    <UserName>{username}</UserName>
    <TransactionType>Sale</TransactionType>
    <InstallmentCount>0</InstallmentCount>
    <CurrencyCode>0949</CurrencyCode>
    <Amount>{amount}</Amount>
    <MerchantOrderId>{order_id}</MerchantOrderId>
    <TransactionSecurity>3</TransactionSecurity>
    <KuveytTurkVPosAdditionalData>
        <AdditionalData>
            <Key>MD</Key>
            <Data>{md}</Data>
        </AdditionalData>
    </KuveytTurkVPosAdditionalData>
</KuveytTurkVPosMessage>'''

        api_url = "https://sanalpos.kuveytturk.com.tr/ServiceGateWay/Home/ThreeDModelProvisionGate"
        r = requests.post(api_url, data=xml, headers={'Content-Type': 'application/xml'}, verify=True, timeout=30)

        if r.status_code == 200:
            root = ET.fromstring(r.text)
            rc = root.find('.//ResponseCode').text if root.find('.//ResponseCode') is not None else None
            if rc == '00':
                prov = root.find('.//ProvisionNumber').text if root.find('.//ProvisionNumber') is not None else None
                rrn = root.find('.//RRN').text if root.find('.//RRN') is not None else None
                logger.info(f'[KuveytTürk] Provision başarılı — OrderId: {order_id}, Prov: {prov}')
                return {'success': True, 'provision_number': prov, 'rrn': rrn}
            msg = root.find('.//ResponseMessage').text if root.find('.//ResponseMessage') is not None else 'Bilinmeyen hata'
            return {'success': False, 'error': f'Ödeme alınamadı: {msg}'}
        return {'success': False, 'error': f'HTTP {r.status_code}'}
    except Exception as e:
        logger.error(f'[KuveytTürk] Provision hata: {e}')
        return {'success': False, 'error': 'Ödeme alınamadı'}

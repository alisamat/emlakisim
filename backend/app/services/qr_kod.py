"""
QR KOD SERVİSİ — Mülk linki, kartvizit, portföy QR
"""
import io
import base64
import logging

logger = logging.getLogger(__name__)


def qr_olustur(icerik, boyut=300):
    """QR kod oluştur → base64 PNG döndür."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(icerik)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return {'basarili': True, 'base64': b64, 'data_url': f'data:image/png;base64,{b64}'}
    except ImportError:
        # qrcode kütüphanesi yoksa Google Charts API (ücretsiz)
        url = f'https://chart.googleapis.com/chart?cht=qr&chs={boyut}x{boyut}&chl={icerik}'
        return {'basarili': True, 'url': url, 'data_url': url}
    except Exception as e:
        logger.error(f'[QR] Hata: {e}')
        return {'basarili': False, 'hata': str(e)}


def mulk_qr(emlakci, mulk_id=None):
    """Mülk veya portföy QR kodu oluştur."""
    import os
    frontend = os.environ.get('FRONTEND_URL', 'https://emlakisim.vercel.app')

    if mulk_id:
        url = f'{frontend}/sayfa/{emlakci.slug or emlakci.id}#mulk-{mulk_id}'
    else:
        url = f'{frontend}/sayfa/{emlakci.slug or emlakci.id}'

    return qr_olustur(url)


def kartvizit_qr(emlakci):
    """Emlakçı kartvizit QR — vCard formatı."""
    vcard = (
        f'BEGIN:VCARD\n'
        f'VERSION:3.0\n'
        f'FN:{emlakci.ad_soyad}\n'
        f'TEL:{emlakci.telefon or ""}\n'
        f'EMAIL:{emlakci.email or ""}\n'
        f'ORG:{emlakci.acente_adi or "Emlakisim"}\n'
        f'END:VCARD'
    )
    return qr_olustur(vcard)

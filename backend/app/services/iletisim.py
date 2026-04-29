"""
İLETİŞİM SERVİSİ — Email gönderme
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def email_gonder(alici_email, konu, icerik_html, gonderen_ad='Emlakisim'):
    """Email gönder. SMTP ayarları env'den alınır."""
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_pass = os.environ.get('SMTP_PASS', '')

    if not smtp_user or not smtp_pass:
        logger.warning('[Email] SMTP ayarları eksik')
        return False, 'SMTP ayarları tanımlı değil'

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = f'{gonderen_ad} <{smtp_user}>'
        msg['To'] = alici_email
        msg.attach(MIMEText(icerik_html, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f'[Email] Gönderildi: {alici_email}')
        return True, 'Gönderildi'
    except Exception as e:
        logger.error(f'[Email] Hata: {e}')
        return False, str(e)


def musteri_email_sablonu(emlakci, musteri, mulk=None, mesaj=''):
    """Müşteriye gönderilecek email HTML şablonu."""
    mulk_html = ''
    if mulk:
        fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''
        mulk_html = f'''
        <div style="background:#f8fafc;border-radius:8px;padding:16px;margin:16px 0;border-left:3px solid #16a34a">
            <strong>{mulk.baslik or mulk.adres or '-'}</strong><br>
            <span style="color:#64748b">{mulk.adres or ''} {mulk.sehir or ''} {mulk.ilce or ''}</span><br>
            <span style="color:#16a34a;font-weight:600">{fiyat}</span>
            {f' · {mulk.oda_sayisi}' if mulk.oda_sayisi else ''}
            {f' · {mulk.tip}' if mulk.tip else ''}
        </div>'''

    return f'''
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
        <div style="background:#16a34a;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0">
            <strong>🏠 Emlakisim</strong> — {emlakci.acente_adi or emlakci.ad_soyad}
        </div>
        <div style="padding:24px;background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <p>Sayın {musteri.ad_soyad if musteri else 'Müşterimiz'},</p>
            {f'<p>{mesaj}</p>' if mesaj else ''}
            {mulk_html}
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0">
            <p style="color:#64748b;font-size:13px">
                {emlakci.ad_soyad}<br>
                {emlakci.acente_adi or ''}<br>
                📞 {emlakci.telefon}
            </p>
        </div>
    </div>'''


def portfoy_email_sablonu(emlakci, mulkler):
    """Portföy listesi email şablonu."""
    items = ''
    for m in mulkler:
        fiyat = f'{int(m.fiyat):,}'.replace(',', '.') + ' TL' if m.fiyat else ''
        renk = '#3b82f6' if m.islem_turu == 'kira' else '#f59e0b'
        items += f'''
        <div style="padding:12px 0;border-bottom:1px solid #f1f5f9">
            <strong>{m.baslik or m.adres or '-'}</strong>
            <span style="background:{'#eff6ff' if m.islem_turu == 'kira' else '#fef3c7'};color:{renk};
                border-radius:4px;padding:2px 8px;font-size:11px;margin-left:8px">
                {'Kiralık' if m.islem_turu == 'kira' else 'Satılık'}
            </span><br>
            <span style="color:#64748b;font-size:13px">{m.adres or ''}</span><br>
            <span style="color:#16a34a;font-weight:600">{fiyat}</span>
            {f' · {m.oda_sayisi}' if m.oda_sayisi else ''}
        </div>'''

    return f'''
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
        <div style="background:#16a34a;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0">
            <strong>🏠 Emlakisim</strong> — Portföy Listesi
        </div>
        <div style="padding:24px;background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
            <p>Sayın ilgili,</p>
            <p>{emlakci.acente_adi or emlakci.ad_soyad} portföyünden seçme ilanlar:</p>
            {items}
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0">
            <p style="color:#64748b;font-size:13px">
                {emlakci.ad_soyad} · 📞 {emlakci.telefon}
            </p>
        </div>
    </div>'''

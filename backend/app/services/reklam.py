"""
REKLAM — AI ile mülk reklam metni + sunum PDF
"""
import os
import json
import requests
import logging
from datetime import datetime
# TurkPDF lazy import in sunum_pdf()

logger = logging.getLogger(__name__)


def reklam_metni_olustur(mulk, hedef='alici', stil='profesyonel'):
    """Mülk için hedef kitleye yönelik reklam metni."""
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return _basit_reklam(mulk)

    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''

    prompt = f"""Aşağıdaki emlak için {hedef} hedefli, {stil} tarzda bir reklam metni oluştur:

Başlık: {mulk.baslik or ''}
Adres: {mulk.adres or ''}, {mulk.sehir or ''} {mulk.ilce or ''}
Tip: {mulk.tip or ''} — {'Kiralık' if mulk.islem_turu == 'kira' else 'Satılık'}
Fiyat: {fiyat}
Oda: {mulk.oda_sayisi or ''}
Detaylar: {json.dumps(det, ensure_ascii=False)[:600]}

İçerik:
1. Dikkat çekici başlık
2. Ana metin (konum avantajları, özellikler, yaşam kalitesi)
3. Öne çıkan özellikler listesi
4. Çağrı ifadesi (CTA)

Stil: {stil} (profesyonel / samimi / lüks / yatırımcı)
Hedef: {hedef} (alıcı / kiracı / yatırımcı)
Türkçe yaz."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f'[Reklam] Hata: {e}')
        return _basit_reklam(mulk)


def _basit_reklam(mulk):
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''
    return f"🏠 {mulk.baslik or mulk.adres or 'Emlak'}\n📍 {mulk.adres or ''}\n💰 {fiyat}\n🏷 {'Kiralık' if mulk.islem_turu == 'kira' else 'Satılık'}"


def sunum_pdf(emlakci, mulk, reklam_metin=''):
    """Mülk sunum/reklam PDF."""
    from app.services.belge import TurkPDF
    pdf = TurkPDF()
    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''

    # Kapak
    pdf.set_font('Helvetica', 'B', 24)
    pdf.ln(30)
    pdf.cell(0, 14, mulk.baslik or mulk.adres or 'Emlak Sunumu', ln=True, align='C')
    pdf.set_font('Helvetica', '', 14)
    pdf.cell(0, 10, 'Kiralik' if mulk.islem_turu == 'kira' else 'Satilik', ln=True, align='C')
    if fiyat:
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 14, fiyat, ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # Konum
    if mulk.adres:
        pdf.alt_baslik('KONUM')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, f'{mulk.adres}, {mulk.ilce or ""} {mulk.sehir or ""}', ln=True)
        pdf.bos_satir()

    # Özellikler
    pdf.alt_baslik('OZELLIKLER')
    if mulk.tip: pdf.satir('Tip', mulk.tip.capitalize())
    if mulk.oda_sayisi: pdf.satir('Oda', mulk.oda_sayisi)
    if det.get('brut_m2'): pdf.satir('Brut m2', str(det['brut_m2']))
    if det.get('net_m2'): pdf.satir('Net m2', str(det['net_m2']))
    if det.get('bina_yasi'): pdf.satir('Bina Yasi', str(det['bina_yasi']))
    if det.get('bulundugu_kat'): pdf.satir('Kat', det['bulundugu_kat'])
    if det.get('isinma'): pdf.satir('Isinma', det['isinma'])
    pdf.bos_satir()

    # Reklam metni
    if reklam_metin:
        pdf.alt_baslik('ACIKLAMA')
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, reklam_metin[:1000])
        pdf.bos_satir()

    # İletişim
    pdf.alt_baslik('ILETISIM')
    pdf.satir('Danisnan', emlakci.ad_soyad)
    pdf.satir('Telefon', emlakci.telefon)
    if emlakci.acente_adi: pdf.satir('Acente', emlakci.acente_adi)

    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_y(-15)
    pdf.cell(0, 5, f'Emlakisim AI - {datetime.now().strftime("%d.%m.%Y")}', align='C')

    return pdf.output()

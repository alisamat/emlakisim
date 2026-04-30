"""
PDF OKUYUCU — PDF dosyasından metin çıkarma + AI analiz
"""
import os
import io
import base64
import logging
import requests

logger = logging.getLogger(__name__)


def pdf_metin_cikar(pdf_bytes):
    """PDF'den metin çıkar. Önce PyPDF2, sonra OCR fallback."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        metin = ''
        for page in reader.pages:
            metin += page.extract_text() or ''
        if metin.strip():
            return {'metin': metin.strip(), 'sayfa_sayisi': len(reader.pages), 'yontem': 'pypdf'}
    except Exception as e:
        logger.warning(f'[PDF] pypdf hatası: {e}')

    # OCR fallback — Gemini Vision ile
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            img_b64 = base64.b64encode(pdf_bytes).decode()
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
            r = requests.post(url, json={
                'contents': [{'parts': [
                    {'text': 'Bu PDF dosyasının tüm metnini çıkar ve Türkçe olarak döndür. Sadece metin döndür.'},
                    {'inline_data': {'mime_type': 'application/pdf', 'data': img_b64}},
                ]}],
                'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 4096},
            }, timeout=30)
            r.raise_for_status()
            metin = r.json()['candidates'][0]['content']['parts'][0]['text']
            return {'metin': metin, 'yontem': 'gemini_ocr'}
        except Exception as e:
            logger.error(f'[PDF] Gemini OCR hatası: {e}')

    return {'hata': 'PDF okunamadı', 'metin': ''}


def pdf_analiz(pdf_bytes, soru=''):
    """PDF'yi oku ve AI ile analiz et."""
    sonuc = pdf_metin_cikar(pdf_bytes)
    if sonuc.get('hata'):
        return sonuc

    metin = sonuc['metin'][:3000]
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        return sonuc

    prompt = f"""Aşağıdaki PDF metnini analiz et:

{metin}

{f'Soru: {soru}' if soru else 'Özet çıkar ve önemli noktaları listele.'}

Türkçe cevapla."""

    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        r = requests.post(url, json={
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 1024},
        }, timeout=15)
        r.raise_for_status()
        analiz = r.json()['candidates'][0]['content']['parts'][0]['text']
        sonuc['analiz'] = analiz
    except Exception as e:
        logger.error(f'[PDF] Analiz hatası: {e}')

    return sonuc

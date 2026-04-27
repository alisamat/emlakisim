"""
AI ASISTAN — Claude ile doğal dil anlama ve işleme
"""
import os
import logging
import anthropic
from app.services import whatsapp as wa

logger = logging.getLogger(__name__)


def isle(emlakci, mesaj: dict, session: dict, pid: str, tok: str) -> bool:
    """
    Gelen WhatsApp mesajını AI asistana ilet, cevabı gönder.
    True döndürürse session temizlenir.
    """
    tip   = mesaj.get('type', 'text')
    telefon = mesaj.get('from', '')

    if tip == 'text':
        metin = mesaj.get('text', {}).get('body', '').strip()
    elif tip == 'location':
        loc = mesaj.get('location', {})
        metin = f'[Konum: {loc.get("latitude")}, {loc.get("longitude")} — {loc.get("name", "")} {loc.get("address", "")}]'
    elif tip == 'image':
        metin = '[Fotoğraf gönderildi]'
    elif tip == 'contacts':
        k = mesaj.get('contacts', [{}])[0]
        ad = f'{k.get("name", {}).get("first_name", "")} {k.get("name", {}).get("last_name", "")}'.strip()
        tel = k.get('phones', [{}])[0].get('phone', '') if k.get('phones') else ''
        metin = f'[Kişi kartı: {ad} — {tel}]'
    else:
        metin = f'[{tip}]'

    # Geçmişe ekle
    gecmis = session.setdefault('gecmis', [])
    gecmis.append({'role': 'user', 'content': metin})

    # Son 20 mesajı tut
    if len(gecmis) > 20:
        gecmis[:] = gecmis[-20:]

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
        sistem = _sistem_prompt(emlakci)
        yanit  = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=1024,
            system=sistem,
            messages=gecmis,
        )
        cevap = yanit.content[0].text
        gecmis.append({'role': 'assistant', 'content': cevap})
        wa.mesaj_gonder(pid, tok, telefon, cevap)
    except Exception as e:
        logger.error(f'[Asistan] Claude hatası: {e}')
        wa.mesaj_gonder(pid, tok, telefon, 'Bir hata oluştu, lütfen tekrar deneyin.')

    return False


def _sistem_prompt(emlakci) -> str:
    return f"""Sen Emlakisim'in yapay zeka destekli emlak asistanısın.

Konuştuğun emlakçı: {emlakci.ad_soyad}
Acente: {emlakci.acente_adi or 'Belirtilmemiş'}

Görevlerin:
- Müşteri bilgilerini kaydet ve yönet (ad, telefon, TC, bütçe, tercih)
- Portföy mülklerini kaydet ve yönet
- Yer gösterme belgesi oluştur
- Müşteri-mülk eşleştirmesi yap
- Not ve plan al
- Kira/satış kontratı oluştur

Kurallar:
- Türkçe konuş, kısa ve net ol
- Bilgi eksikse sor
- Yapısal veriyi JSON formatında döndür (işlemler için)
- WhatsApp formatı kullan (*kalın*, _italik_)
"""

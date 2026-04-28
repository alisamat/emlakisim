"""
AI ASISTAN — Çok modelli: Gemini Flash (basit), GPT-4o mini (doküman), Claude Haiku (analiz)
"""
import os
import logging
from app.services import whatsapp as wa

logger = logging.getLogger(__name__)

# Görev kategorileri
_BASIT   = {'selamlama', 'soru', 'bilgi', 'genel'}
_DOKUMAN = {'kontrat', 'belge', 'pdf', 'yer_gosterme'}
_ANALIZ  = {'eslestirme', 'analiz', 'tavsiye', 'karsilastir'}


def isle(emlakci, mesaj: dict, session: dict, pid: str, tok: str) -> bool:
    tip     = mesaj.get('type', 'text')
    telefon = mesaj.get('from', '')

    if tip == 'text':
        metin = mesaj.get('text', {}).get('body', '').strip()
    elif tip == 'location':
        loc   = mesaj.get('location', {})
        metin = f'[Konum: {loc.get("latitude")}, {loc.get("longitude")} — {loc.get("name", "")} {loc.get("address", "")}]'
    elif tip == 'image':
        metin = '[Fotoğraf gönderildi]'
    elif tip == 'contacts':
        k   = mesaj.get('contacts', [{}])[0]
        ad  = f'{k.get("name", {}).get("first_name", "")} {k.get("name", {}).get("last_name", "")}'.strip()
        tel = k.get('phones', [{}])[0].get('phone', '') if k.get('phones') else ''
        metin = f'[Kişi kartı: {ad} — {tel}]'
    else:
        metin = f'[{tip}]'

    gecmis = session.setdefault('gecmis', [])
    gecmis.append({'role': 'user', 'content': metin})
    if len(gecmis) > 20:
        gecmis[:] = gecmis[-20:]

    sistem = _sistem_prompt(emlakci)

    try:
        cevap = _ai_cevap(metin, gecmis, sistem)
        gecmis.append({'role': 'assistant', 'content': cevap})
        wa.mesaj_gonder(pid, tok, telefon, cevap)
    except Exception as e:
        logger.error(f'[Asistan] AI hatası: {e}')
        wa.mesaj_gonder(pid, tok, telefon, 'Bir hata oluştu, lütfen tekrar deneyin.')

    return False


def _ai_cevap(metin: str, gecmis: list, sistem: str) -> str:
    """Model seçimi: önce ucuz Gemini, yedekte Claude."""
    # Anahtar kelime tespiti
    metin_lower = metin.lower()
    analiz_kelimeler = ['eşleştir', 'karşılaştır', 'analiz', 'tavsiye', 'öneri', 'uygun mu']
    dokuman_kelimeler = ['kontrat', 'sözleşme', 'belge', 'pdf', 'yer gösterme']

    if any(k in metin_lower for k in dokuman_kelimeler):
        kategori = 'dokuman'
    elif any(k in metin_lower for k in analiz_kelimeler):
        kategori = 'analiz'
    else:
        kategori = 'basit'

    # Gemini Flash — basit + doküman (en ucuz)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key and kategori in ('basit', 'dokuman'):
        try:
            return _gemini(gemini_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] Gemini başarısız, fallback: {e}')

    # GPT-4o mini — doküman (orta)
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key and kategori == 'dokuman':
        try:
            return _openai(openai_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] OpenAI başarısız, fallback: {e}')

    # Claude Haiku — analiz veya fallback
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if anthropic_key:
        return _claude(anthropic_key, sistem, gecmis)

    raise RuntimeError('Hiçbir AI anahtarı tanımlı değil')


def _gemini(api_key: str, sistem: str, gecmis: list) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=sistem,
    )
    history = []
    for m in gecmis[:-1]:
        role = 'user' if m['role'] == 'user' else 'model'
        history.append({'role': role, 'parts': [m['content']]})

    chat = model.start_chat(history=history)
    son_mesaj = gecmis[-1]['content']
    r = chat.send_message(son_mesaj)
    return r.text


def _openai(api_key: str, sistem: str, gecmis: list) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    mesajlar = [{'role': 'system', 'content': sistem}] + gecmis
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=mesajlar,
        max_tokens=1024,
    )
    return r.choices[0].message.content


def _claude(api_key: str, sistem: str, gecmis: list) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    r = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=sistem,
        messages=gecmis,
    )
    return r.content[0].text


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
- WhatsApp formatı kullan (*kalın*, _italik_)
"""

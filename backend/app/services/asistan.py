"""
AI ASISTAN — Function calling ile DB işlemleri + çok modelli + pattern matching
Öncelik: Pattern → Direkt DB → AI (ucuzdan pahalıya)
"""
import os
import re
import json
import logging
from datetime import datetime
from app.models import db, Musteri, Mulk, YerGosterme, Not
from app.services import whatsapp as wa

logger = logging.getLogger(__name__)

# ─── Türkçe normalleştirme ─────────────────────────────────
_TR_MAP = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')

def _normalize(metin):
    """Türkçe karakterleri ASCII'ye çevir, küçük harf yap."""
    return metin.lower().translate(_TR_MAP).strip()


# ─── Pattern Matching (sıfır maliyet) ──────────────────────
_PATTERNS = [
    # Müşteri ekleme
    (r'(?:musteri|müşteri)\s*(?:ekle|kayit|kaydet|olustur)',  'musteri_ekle'),
    (r'(?:musteri|müşteri)\s*(?:listele|göster|listesi)',     'musteri_liste'),
    (r'(?:musteri|müşteri)\s*(?:sil|kaldir)',                 'musteri_sil'),
    # Portföy
    (r'(?:portfoy|portföy|mulk|mülk|emlak)\s*(?:ekle|kayit|kaydet|olustur)', 'mulk_ekle'),
    (r'(?:portfoy|portföy|mulk|mülk|emlak)\s*(?:listele|göster|listesi)',    'mulk_liste'),
    # Not
    (r'(?:not)\s*(?:ekle|al|kaydet|yaz)',                     'not_ekle'),
    # Rapor
    (r'(?:rapor|özet|istatistik|durum)',                      'rapor'),
    # Yardım
    (r'(?:yardim|yardım|neler?\s*yapabilirsin|merhaba|selam|hey)', 'yardim'),
]

def _pattern_isle(metin_norm, emlakci, metin_raw):
    """Pattern matching ile komut bul. Bulursa (komut, args) döndür, bulamazsa None."""
    for pattern, komut in _PATTERNS:
        if re.search(pattern, metin_norm):
            return komut
    return None


# ─── Direkt DB İşlemleri (sıfır AI maliyeti) ──────────────
def _komut_calistir(komut, emlakci, metin, session):
    """Pattern ile eşleşen komutu çalıştır."""

    if komut == 'yardim':
        return _yardim_mesaji(emlakci)

    if komut == 'musteri_liste':
        return _musteri_listele(emlakci)

    if komut == 'mulk_liste':
        return _mulk_listele(emlakci)

    if komut == 'rapor':
        return _rapor(emlakci)

    if komut == 'musteri_ekle':
        session['bekleyen_islem'] = 'musteri_ekle'
        return ('*Yeni müşteri eklemek için bilgileri girin:*\n\n'
                'Ad Soyad, Telefon, İşlem türü (kiralık/satılık)\n\n'
                '_Örnek: Ali Yılmaz, 05321234567, kiralık_')

    if komut == 'mulk_ekle':
        session['bekleyen_islem'] = 'mulk_ekle'
        return ('*Yeni mülk eklemek için bilgileri girin:*\n\n'
                'Başlık, Adres, Tip (daire/villa/arsa), İşlem (kiralık/satılık), Fiyat\n\n'
                '_Örnek: Kadıköy 3+1 Daire, Moda Cad. No:5, daire, kiralık, 25000_')

    if komut == 'not_ekle':
        session['bekleyen_islem'] = 'not_ekle'
        return '*Not yazın:*'

    return None


def _musteri_listele(emlakci):
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci.id).order_by(Musteri.olusturma.desc()).limit(10).all()
    if not musteriler:
        return '📭 Henüz müşteriniz yok.\n\n_"Müşteri ekle" yazarak yeni müşteri ekleyebilirsiniz._'
    satirlar = [f'*{i+1}.* {m.ad_soyad} — {m.telefon or "tel yok"} ({m.islem_turu or "?"})' for i, m in enumerate(musteriler)]
    return f'👥 *Müşterileriniz* ({len(musteriler)})\n\n' + '\n'.join(satirlar)


def _mulk_listele(emlakci):
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).order_by(Mulk.olusturma.desc()).limit(10).all()
    if not mulkler:
        return '📭 Henüz portföyünüzde mülk yok.\n\n_"Mülk ekle" yazarak yeni mülk ekleyebilirsiniz._'
    satirlar = []
    for i, m in enumerate(mulkler):
        fiyat = f'{int(m.fiyat):,}'.replace(',', '.') + ' TL' if m.fiyat else '?'
        satirlar.append(f'*{i+1}.* {m.baslik or m.adres or "—"} — {fiyat} ({m.islem_turu or "?"})')
    return f'🏢 *Portföyünüz* ({len(mulkler)})\n\n' + '\n'.join(satirlar)


def _rapor(emlakci):
    m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    yg_sayi = YerGosterme.query.filter_by(emlakci_id=emlakci.id).count()
    return (f'📊 *Genel Durum*\n\n'
            f'👥 Müşteriler: *{m_sayi}*\n'
            f'🏢 Portföy: *{p_sayi}*\n'
            f'📋 Yer gösterme: *{yg_sayi}*\n'
            f'💎 Kredi: *{emlakci.kredi}*')


def _yardim_mesaji(emlakci):
    return (f'👋 *Merhaba {emlakci.ad_soyad.split(" ")[0]}!*\n\n'
            'Ben Emlakisim AI Asistanınızım. İşte yapabileceklerim:\n\n'
            '👥 *Müşteri:* "müşteri ekle", "müşteri listele"\n'
            '🏢 *Portföy:* "mülk ekle", "portföy listele"\n'
            '📋 *Belgeler:* "yer gösterme oluştur"\n'
            '📊 *Rapor:* "rapor", "özet"\n'
            '📝 *Not:* "not ekle"\n'
            '💰 *Hesaplama:* "kira vergisi hesapla"\n\n'
            '💡 *İpucu:* Excel\'den toplu müşteri/portföy ekleyebilirsiniz!\n'
            'Fotoğraf çekerek sahibinden ilanlarını portföye aktarabilirsiniz!\n\n'
            '_Doğal dille yazın, anlayacağım._')


# ─── Bekleyen İşlem Yürütme ────────────────────────────────
def _bekleyen_isle(session, emlakci, metin):
    """Adımlı komut tamamlama (kullanıcı bilgi girdikten sonra)."""
    islem = session.pop('bekleyen_islem', None)
    if not islem:
        return None

    if islem == 'musteri_ekle':
        return _musteri_kaydet(emlakci, metin)
    if islem == 'mulk_ekle':
        return _mulk_kaydet(emlakci, metin)
    if islem == 'not_ekle':
        return _not_kaydet(emlakci, metin)
    return None


def _musteri_kaydet(emlakci, metin):
    """Serbest metinden müşteri bilgisi çıkar ve kaydet."""
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    ad = parcalar[0] if parcalar else metin.strip()
    telefon = parcalar[1] if len(parcalar) > 1 else ''
    islem = 'kira' if len(parcalar) > 2 and 'kira' in parcalar[2].lower() else 'satis'

    musteri = Musteri(
        emlakci_id=emlakci.id,
        ad_soyad=ad,
        telefon=telefon,
        islem_turu=islem,
    )
    db.session.add(musteri)
    db.session.commit()
    return f'✅ *Müşteri eklendi!*\n\n👤 {ad}\n📞 {telefon or "—"}\n🏷 {islem.capitalize()}'


def _mulk_kaydet(emlakci, metin):
    parcalar = [p.strip() for p in metin.replace(';', ',').split(',')]
    baslik = parcalar[0] if parcalar else metin.strip()
    adres = parcalar[1] if len(parcalar) > 1 else ''
    tip = parcalar[2] if len(parcalar) > 2 else 'daire'
    islem = 'kira' if len(parcalar) > 3 and 'kira' in parcalar[3].lower() else 'satis'
    fiyat = None
    if len(parcalar) > 4:
        try: fiyat = float(re.sub(r'[^\d.]', '', parcalar[4]))
        except: pass

    mulk = Mulk(
        emlakci_id=emlakci.id,
        baslik=baslik,
        adres=adres,
        tip=tip,
        islem_turu=islem,
        fiyat=fiyat,
    )
    db.session.add(mulk)
    db.session.commit()
    fiyat_str = f'{int(fiyat):,}'.replace(',', '.') + ' TL' if fiyat else '—'
    return f'✅ *Mülk eklendi!*\n\n🏢 {baslik}\n📍 {adres or "—"}\n💰 {fiyat_str}'


def _not_kaydet(emlakci, metin):
    not_obj = Not(emlakci_id=emlakci.id, icerik=metin, etiket='not')
    db.session.add(not_obj)
    db.session.commit()
    return f'✅ *Not kaydedildi.*\n\n📝 {metin[:100]}'


# ─── AI Fonksiyonları (function calling) ───────────────────
_FUNCTIONS = [
    {
        'name': 'musteri_ekle',
        'description': 'Yeni müşteri ekler',
        'parameters': {
            'type': 'object',
            'properties': {
                'ad_soyad': {'type': 'string', 'description': 'Müşterinin adı soyadı'},
                'telefon': {'type': 'string', 'description': 'Telefon numarası'},
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis']},
                'butce_min': {'type': 'number', 'description': 'Minimum bütçe TL'},
                'butce_max': {'type': 'number', 'description': 'Maksimum bütçe TL'},
                'tercih_notlar': {'type': 'string', 'description': 'Müşteri tercihleri'},
            },
            'required': ['ad_soyad'],
        },
    },
    {
        'name': 'musteri_listele',
        'description': 'Müşteri listesini getirir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'mulk_ekle',
        'description': 'Portföye yeni mülk ekler',
        'parameters': {
            'type': 'object',
            'properties': {
                'baslik': {'type': 'string'},
                'adres': {'type': 'string'},
                'sehir': {'type': 'string'},
                'ilce': {'type': 'string'},
                'tip': {'type': 'string', 'enum': ['daire', 'villa', 'arsa', 'dukkan', 'ofis']},
                'islem_turu': {'type': 'string', 'enum': ['kira', 'satis']},
                'fiyat': {'type': 'number'},
                'metrekare': {'type': 'number'},
                'oda_sayisi': {'type': 'string'},
            },
            'required': ['baslik'],
        },
    },
    {
        'name': 'mulk_listele',
        'description': 'Portföy listesini getirir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'rapor',
        'description': 'Genel durum raporu verir',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'not_ekle',
        'description': 'Not kaydeder',
        'parameters': {
            'type': 'object',
            'properties': {
                'icerik': {'type': 'string', 'description': 'Not içeriği'},
            },
            'required': ['icerik'],
        },
    },
]

def _ai_function_call(fonksiyon_adi, args, emlakci):
    """AI'nın çağırdığı fonksiyonu yürüt."""
    if fonksiyon_adi == 'musteri_ekle':
        m = Musteri(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('ad_soyad', 'telefon', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Müşteri eklendi: {args.get("ad_soyad")}'

    if fonksiyon_adi == 'musteri_listele':
        return _musteri_listele(emlakci)

    if fonksiyon_adi == 'mulk_ekle':
        m = Mulk(emlakci_id=emlakci.id, **{k: v for k, v in args.items() if k in ('baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi')})
        db.session.add(m)
        db.session.commit()
        return f'✅ Mülk eklendi: {args.get("baslik")}'

    if fonksiyon_adi == 'mulk_listele':
        return _mulk_listele(emlakci)

    if fonksiyon_adi == 'rapor':
        return _rapor(emlakci)

    if fonksiyon_adi == 'not_ekle':
        n = Not(emlakci_id=emlakci.id, icerik=args.get('icerik', ''), etiket='not')
        db.session.add(n)
        db.session.commit()
        return '✅ Not kaydedildi.'

    return None


# ─── AI Model Çağrıları ───────────────────────────────────
def _ai_cevap(metin: str, gecmis: list, sistem: str) -> str:
    """Model seçimi: önce Gemini (function calling), yedekte Claude."""
    metin_lower = metin.lower()
    analiz_kelimeler = ['eşleştir', 'karşılaştır', 'analiz', 'tavsiye', 'öneri', 'uygun mu', 'karsilastir']

    if any(k in metin_lower for k in analiz_kelimeler):
        kategori = 'analiz'
    else:
        kategori = 'basit'

    # Gemini Flash — basit (en ucuz)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key and kategori == 'basit':
        try:
            return _gemini(gemini_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] Gemini başarısız: {e}')

    # GPT-4o mini — yedek
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key:
        try:
            return _openai(openai_key, sistem, gecmis)
        except Exception as e:
            logger.warning(f'[Asistan] OpenAI başarısız: {e}')

    # Claude Haiku — analiz veya son yedek
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if anthropic_key:
        return _claude(anthropic_key, sistem, gecmis)

    raise RuntimeError('Hiçbir AI anahtarı tanımlı değil')


def _gemini(api_key, sistem, gecmis):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=sistem)
    history = [{'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]} for m in gecmis[:-1]]
    chat = model.start_chat(history=history)
    return chat.send_message(gecmis[-1]['content']).text


def _openai(api_key, sistem, gecmis):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'system', 'content': sistem}] + gecmis,
        max_tokens=1024,
    )
    return r.choices[0].message.content


def _claude(api_key, sistem, gecmis):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    r = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=sistem,
        messages=gecmis,
    )
    return r.content[0].text


# ─── OpenAI Function Calling (akıllı mod) ──────────────────
def _openai_with_functions(api_key, sistem, gecmis, emlakci):
    """OpenAI ile function calling — AI doğrudan DB işlemi yapar."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    tools = [{'type': 'function', 'function': f} for f in _FUNCTIONS]
    r = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'system', 'content': sistem}] + gecmis,
        tools=tools,
        tool_choice='auto',
        max_tokens=1024,
    )

    msg = r.choices[0].message
    if msg.tool_calls:
        tc = msg.tool_calls[0]
        args = json.loads(tc.function.arguments)
        sonuc = _ai_function_call(tc.function.name, args, emlakci)
        return sonuc or msg.content or 'İşlem tamamlandı.'

    return msg.content


# ─── Sistem Prompt ─────────────────────────────────────────
def _sistem_prompt(emlakci):
    return f"""Sen Emlakisim'in yapay zeka destekli emlak asistanısın.

Konuştuğun emlakçı: {emlakci.ad_soyad}
Acente: {emlakci.acente_adi or 'Belirtilmemiş'}

Görevlerin:
- Müşteri bilgilerini kaydet ve yönet (ad, telefon, TC, bütçe, tercih)
- Portföy mülklerini kaydet ve yönet
- Yer gösterme belgesi oluştur
- Müşteri-mülk eşleştirmesi yap
- Not ve plan al
- Rapor sun, hesaplama yap
- Kira/satış kontratı oluştur

Kurallar:
- Türkçe konuş, kısa ve net ol
- Bilgi eksikse sor
- İşlem yaptıktan sonra onay mesajı ver
- Kullanıcıya yapabileceklerini proaktif olarak öner
- WhatsApp formatı kullan (*kalın*, _italik_)
- Güvenli ol: silme/değiştirme işlemlerinde onay iste
"""


# ─── ANA İŞLEM FONKSİYONU ─────────────────────────────────
def isle(emlakci, mesaj: dict, session: dict, pid: str, tok: str) -> bool:
    """WhatsApp mesajını işle: pattern → bekleyen → AI."""
    tip = mesaj.get('type', 'text')
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

    gecmis = session.setdefault('gecmis', [])
    gecmis.append({'role': 'user', 'content': metin})
    if len(gecmis) > 20:
        gecmis[:] = gecmis[-20:]

    try:
        from app.services.egitim import diyalog_kaydet, ogrenilen_pattern_esle
        metin_norm = _normalize(metin)
        kullanilan_model = None
        kullanilan_islem = None

        # 1. Bekleyen adımlı işlem varsa tamamla
        bekleyen = _bekleyen_isle(session, emlakci, metin)
        if bekleyen:
            cevap = bekleyen
            kullanilan_islem = 'bekleyen'
            kullanilan_model = 'pattern'
        else:
            # 2. Öğrenilen pattern'lar (DB'den)
            ogrenilen = ogrenilen_pattern_esle(metin_norm)
            if ogrenilen:
                cevap = _komut_calistir(ogrenilen, emlakci, metin, session)
                kullanilan_islem = ogrenilen
                kullanilan_model = 'ogrenilen'
            else:
                # 3. Sabit pattern matching (sıfır maliyet)
                komut = _pattern_isle(metin_norm, emlakci, metin)
                if komut:
                    cevap = _komut_calistir(komut, emlakci, metin, session)
                    kullanilan_islem = komut
                    kullanilan_model = 'pattern'
                else:
                    # 4. AI (function calling varsa)
                    openai_key = os.environ.get('OPENAI_API_KEY', '')
                    if openai_key:
                        cevap = _openai_with_functions(openai_key, _sistem_prompt(emlakci), gecmis, emlakci)
                    else:
                        cevap = _ai_cevap(metin, gecmis, _sistem_prompt(emlakci))
                    kullanilan_islem = 'ai_sohbet'
                    kullanilan_model = 'openai'

        # Diyaloğu kaydet (eğitim verisi)
        diyalog_kaydet(emlakci.id, metin, metin_norm, kullanilan_islem or 'bilinmeyen', model=kullanilan_model)

        gecmis.append({'role': 'assistant', 'content': cevap})
        wa.mesaj_gonder(pid, tok, telefon, cevap)
    except Exception as e:
        logger.error(f'[Asistan] Hata: {e}', exc_info=True)
        wa.mesaj_gonder(pid, tok, telefon, 'Bir hata oluştu, lütfen tekrar deneyin.')

    return False

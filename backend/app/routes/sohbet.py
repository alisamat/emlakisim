"""
PANEL SOHBET — Uygulama içi AI sohbet API + kredi sistemi
"""
import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Emlakci, PanelSohbet, PanelMesaj
from app.services.asistan import _ai_cevap, _sistem_prompt, _normalize, _pattern_isle, _komut_calistir, _openai_with_functions, _bekleyen_isle, _navigasyon_kontrol, _baglam_filtre
from app.services.kredi import kredi_kontrol, kredi_dus, KREDI_TABLOSU
from app.services.egitim import diyalog_kaydet, ogrenilen_pattern_esle

logger = logging.getLogger(__name__)
bp = Blueprint('sohbet', __name__, url_prefix='/api/panel')
_panel_sessions: dict[int, dict] = {}


@bp.route('/sohbet', methods=['POST'])
@jwt_required()
def mesaj_gonder():
    emlakci = Emlakci.query.get(get_jwt_identity())
    if not emlakci:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404

    data = request.get_json() or {}
    metin = (data.get('mesaj') or '').strip()
    if not metin:
        return jsonify({'message': 'Mesaj boş olamaz'}), 400

    sohbet_id = data.get('sohbet_id')

    # Sohbeti bul veya oluştur
    if sohbet_id:
        sohbet = PanelSohbet.query.filter_by(id=sohbet_id, emlakci_id=emlakci.id).first()
        if not sohbet:
            return jsonify({'message': 'Sohbet bulunamadı'}), 404
    else:
        sohbet = PanelSohbet(emlakci_id=emlakci.id, baslik=metin[:50])
        db.session.add(sohbet)
        db.session.flush()

    # Kullanıcı mesajını kaydet
    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='user', icerik=metin))

    # Geçmiş mesajları al
    gecmis = [{'role': m.rol, 'content': m.icerik}
              for m in PanelMesaj.query.filter_by(sohbet_id=sohbet.id).order_by(PanelMesaj.olusturma).all()]
    if len(gecmis) > 20:
        gecmis = gecmis[-20:]

    session = _panel_sessions.setdefault(emlakci.id, {})

    metin_norm = _normalize(metin)
    kullanilan_model = None
    nav_tab = None

    # ── LOG: Giriş ──
    logger.info(f'[SOHBET] ═══ YENİ MESAJ ═══')
    logger.info(f'[SOHBET] metin: "{metin}"')
    logger.info(f'[SOHBET] norm:  "{metin_norm}"')
    logger.info(f'[SOHBET] gecmis: {len(gecmis)} mesaj | session_keys: {list(session.keys())}')
    logger.info(f'[SOHBET] son_komut: {session.get("son_komut")} | son_liste: {len(session.get("son_liste", []))} kayıt')

    # 0. Navigasyon kontrolü
    nav = _navigasyon_kontrol(metin_norm)
    if nav:
        nav_tab, cevap = nav
        kullanilan_model = 'navigasyon'
        logger.info(f'[SOHBET] ✓ NAVİGASYON yakaladı → tab={nav_tab}')
        db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
        db.session.commit()
        return jsonify({'cevap': cevap, 'kredi_kalan': emlakci.kredi, 'sohbet_id': sohbet.id, 'tab': nav_tab})

    # 1. Bağlam filtresi
    baglam = _baglam_filtre(metin_norm, emlakci, session)
    if baglam:
        cevap = baglam
        kullanilan_model = 'baglam_filtre'
        logger.info(f'[SOHBET] ✓ BAĞLAM FİLTRE yakaladı → {cevap[:80]}...')
        db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
        db.session.commit()
        return jsonify({'cevap': cevap, 'kredi_kalan': emlakci.kredi, 'sohbet_id': sohbet.id})

    # 2. Pattern matching
    komut = _pattern_isle(metin_norm, emlakci, metin)
    if komut:
        logger.info(f'[SOHBET] ✓ PATTERN yakaladı → komut={komut}')
        sonuc = _komut_calistir(komut, emlakci, metin, session)
        if isinstance(sonuc, tuple):
            cevap, nav_tab = sonuc
        else:
            cevap = sonuc
        if komut == 'kredi_panel':
            nav_tab = 'kredi'
        kredi_dus(emlakci, komut, aciklama=metin[:100], model='pattern')
        kullanilan_model = 'pattern'

    # 3. AI — Semantic Router → Dinamik Tool → Katmanlı Prompt → LLM
    else:
        if not kredi_kontrol(emlakci, 1):
            cevap = '⚠️ *Krediniz yetersiz.*\n\nAI asistan kullanmak için kredi gereklidir.\nMevcut kredi: *0*'
            db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
            db.session.commit()
            return jsonify({'cevap': cevap, 'kredi_kalan': emlakci.kredi, 'sohbet_id': sohbet.id, 'kredi_yetersiz': True}), 200

        logger.info(f'[SOHBET] → NAVİGASYON: hayır | BAĞLAM: hayır | PATTERN: hayır → AI\'ya gidiyor')

        # 3a. Semantic Router
        from app.services.router import multi_route
        from app.services.tool_loader import tools_yukle
        from app.services.prompt_builder import prompt_olustur
        from app.services.asistan import _FUNCTIONS

        try:
            kategoriler = multi_route(metin)
        except Exception as e:
            logger.error(f'[SOHBET] Router hatası: {e}')
            kategoriler = []
        kat_isimleri = [k for k, _ in kategoriler] if kategoriler and isinstance(kategoriler[0], tuple) else kategoriler
        logger.info(f'[SOHBET] ROUTER → kategoriler: {kategoriler}')

        # 3b. Dinamik Tool Yükleme
        secilen_tools = tools_yukle(kat_isimleri, _FUNCTIONS)
        tool_isimleri = [t['name'] for t in secilen_tools] if secilen_tools else []
        logger.info(f'[SOHBET] TOOLS → {len(tool_isimleri)} tool: {tool_isimleri}')

        # 3c. Katmanlı Prompt
        sistem = prompt_olustur(emlakci, kat_isimleri, metin)
        logger.info(f'[SOHBET] PROMPT → {len(sistem)} karakter | kategoriler: {kat_isimleri}')

        # 3d. LLM çağır
        try:
            openai_key = os.environ.get('OPENAI_API_KEY', '')
            gemini_key = os.environ.get('GEMINI_API_KEY', '')
            if openai_key:
                logger.info(f'[SOHBET] LLM → OpenAI seçildi | gecmis: {len(gecmis)} mesaj')
                from app.services.asistan import _openai_with_functions_v2 as owf
                ai_sonuc = owf(openai_key, sistem, gecmis, emlakci, secilen_tools)
                if isinstance(ai_sonuc, tuple):
                    cevap, nav_tab = ai_sonuc
                else:
                    cevap = ai_sonuc
                kullanilan_model = 'openai'
            elif gemini_key:
                logger.info(f'[SOHBET] LLM → Gemini seçildi | gecmis: {len(gecmis)} mesaj')
                from app.services.asistan import _gemini_with_functions_v2 as gwf
                try:
                    ai_sonuc = gwf(gemini_key, sistem, gecmis, emlakci, secilen_tools)
                    if isinstance(ai_sonuc, tuple):
                        cevap, nav_tab = ai_sonuc
                    else:
                        cevap = ai_sonuc
                    kullanilan_model = 'gemini'
                except Exception as e:
                    logger.error(f'[SOHBET] Gemini hatası, fallback: {e}')
                    cevap = _ai_cevap(metin, gecmis, sistem)
                    kullanilan_model = 'gemini'
            else:
                logger.info(f'[SOHBET] LLM → Claude fallback')
                cevap = _ai_cevap(metin, gecmis, sistem)
                kullanilan_model = 'claude'
        except Exception as e:
            logger.error(f'[SOHBET] AI hatası: {e}')
            cevap = 'Bir hata oluştu, lütfen tekrar deneyin.'
            kullanilan_model = 'hata'

        logger.info(f'[SOHBET] AI CEVAP → model={kullanilan_model} | cevap: "{str(cevap)[:120]}..."')
        kredi_dus(emlakci, 'ai_sohbet', aciklama=f'router:{",".join(kat_isimleri[:2])} {metin[:60]}', model=kullanilan_model)

    # Zeka motoru
    try:
        from app.services.zeka import mesaj_zenginlestir
        cevap_once = cevap
        cevap = mesaj_zenginlestir(emlakci, metin, cevap)
        if cevap != cevap_once:
            logger.info(f'[SOHBET] ZEKA zenginleştirdi: +{len(cevap) - len(cevap_once)} karakter')
    except Exception:
        pass

    # Eğitim verisi
    islem_adi = 'ai_sohbet'
    if kullanilan_model == 'pattern':
        islem_adi = 'pattern'
    elif kullanilan_model == 'ogrenilen':
        islem_adi = 'ogrenilen'
    diyalog_kaydet(emlakci.id, metin, metin_norm, islem_adi, model=kullanilan_model)

    try:
        from app.services.hafiza import konusma_ozeti_kaydet
        konusma_ozeti_kaydet(emlakci.id, gecmis)
    except Exception:
        pass

    # Kaydet ve dön
    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
    db.session.commit()

    logger.info(f'[SOHBET] ═══ SONUÇ: model={kullanilan_model} ═══')

    resp = {'cevap': cevap, 'kredi_kalan': emlakci.kredi, 'sohbet_id': sohbet.id}
    if nav_tab:
        resp['tab'] = nav_tab
    return jsonify(resp)


@bp.route('/sohbetler', methods=['GET'])
@jwt_required()
def sohbet_listesi():
    emlakci_id = get_jwt_identity()
    sohbetler = PanelSohbet.query.filter_by(emlakci_id=emlakci_id)\
        .order_by(PanelSohbet.guncelleme.desc()).limit(50).all()
    return jsonify({
        'sohbetler': [{
            'id': s.id,
            'baslik': s.baslik,
            'olusturma': s.olusturma.isoformat(),
        } for s in sohbetler]
    })


@bp.route('/sohbetler/<int:sid>', methods=['GET'])
@jwt_required()
def sohbet_detay(sid):
    emlakci_id = get_jwt_identity()
    sohbet = PanelSohbet.query.filter_by(id=sid, emlakci_id=emlakci_id).first()
    if not sohbet:
        return jsonify({'message': 'Sohbet bulunamadı'}), 404
    return jsonify({
        'mesajlar': [{
            'rol': m.rol,
            'icerik': m.icerik,
            'olusturma': m.olusturma.isoformat(),
        } for m in sohbet.mesajlar]
    })


@bp.route('/sohbetler/export', methods=['GET'])
@jwt_required()
def sohbet_export():
    """Tüm sohbet geçmişini JSON olarak export et."""
    emlakci_id = get_jwt_identity()
    sohbetler = PanelSohbet.query.filter_by(emlakci_id=emlakci_id).order_by(PanelSohbet.olusturma).all()
    data = []
    for s in sohbetler:
        mesajlar = PanelMesaj.query.filter_by(sohbet_id=s.id).order_by(PanelMesaj.olusturma).all()
        data.append({
            'baslik': s.baslik,
            'tarih': s.olusturma.isoformat() if s.olusturma else None,
            'mesajlar': [{'rol': m.rol, 'icerik': m.icerik, 'tarih': m.olusturma.isoformat() if m.olusturma else None} for m in mesajlar],
        })
    return jsonify({'sohbetler': data, 'toplam': len(data)})


@bp.route('/sohbetler/<int:sid>', methods=['DELETE'])
@jwt_required()
def sohbet_sil(sid):
    emlakci_id = get_jwt_identity()
    sohbet = PanelSohbet.query.filter_by(id=sid, emlakci_id=emlakci_id).first()
    if not sohbet:
        return jsonify({'message': 'Sohbet bulunamadı'}), 404
    PanelMesaj.query.filter_by(sohbet_id=sid).delete()
    db.session.delete(sohbet)
    db.session.commit()
    return jsonify({'ok': True})

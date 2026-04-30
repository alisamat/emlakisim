"""
PANEL SOHBET — Uygulama içi AI sohbet API + kredi sistemi
"""
import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Emlakci, PanelSohbet, PanelMesaj
from app.services.asistan import _ai_cevap, _sistem_prompt, _normalize, _pattern_isle, _komut_calistir, _openai_with_functions, _bekleyen_isle
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

    # 1. Bekleyen adımlı işlem
    bekleyen = _bekleyen_isle(session, emlakci, metin)
    if bekleyen:
        cevap = bekleyen
        islem = session.get('_son_islem', 'pattern')
        kredi_dus(emlakci, islem, aciklama=metin[:100])
        kullanilan_model = 'pattern'
    else:
        # 2. Öğrenilen pattern'lar (DB'den)
        ogrenilen = ogrenilen_pattern_esle(metin_norm)
        if ogrenilen:
            cevap = _komut_calistir(ogrenilen, emlakci, metin, session)
            kredi_dus(emlakci, ogrenilen, aciklama=metin[:100], model='ogrenilen')
            kullanilan_model = 'ogrenilen'
        else:
            # 3. Sabit pattern matching
            komut = _pattern_isle(metin_norm, emlakci, metin)
            if komut:
                cevap = _komut_calistir(komut, emlakci, metin, session)
                kredi_dus(emlakci, komut, aciklama=metin[:100], model='pattern')
                kullanilan_model = 'pattern'
            else:
                # 4. AI — önce kredi kontrolü
                if not kredi_kontrol(emlakci, 1):
                    cevap = '⚠️ *Krediniz yetersiz.*\n\nAI asistan kullanmak için kredi gereklidir.\nMevcut kredi: *0*'
                    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
                    db.session.commit()
                    return jsonify({
                        'cevap': cevap,
                        'kredi_kalan': emlakci.kredi,
                        'sohbet_id': sohbet.id,
                        'kredi_yetersiz': True,
                    }), 200

                sistem = _sistem_prompt(emlakci, metin)
                try:
                    openai_key = os.environ.get('OPENAI_API_KEY', '')
                    if openai_key:
                        cevap = _openai_with_functions(openai_key, sistem, gecmis, emlakci)
                    else:
                        cevap = _ai_cevap(metin, gecmis, sistem)
                except Exception as e:
                    logger.error(f'[Sohbet] AI hatası: {e}')
                    cevap = 'Bir hata oluştu, lütfen tekrar deneyin.'

                # AI kredi düş
                kredi_dus(emlakci, 'ai_sohbet', aciklama=metin[:100], model='gpt-4o-mini')
                kullanilan_model = 'openai'

    # Zeka motoru — cevabı zenginleştir
    try:
        from app.services.zeka import mesaj_zenginlestir
        cevap = mesaj_zenginlestir(emlakci, metin, cevap)
    except Exception:
        pass

    # Diyaloğu kaydet (eğitim verisi)
    islem_adi = 'ai_sohbet'
    if kullanilan_model == 'pattern':
        islem_adi = 'pattern'
    elif kullanilan_model == 'ogrenilen':
        islem_adi = 'ogrenilen'
    diyalog_kaydet(emlakci.id, metin, metin_norm, islem_adi, model=kullanilan_model)

    # Asistan mesajını kaydet
    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
    db.session.commit()

    return jsonify({
        'cevap': cevap,
        'kredi_kalan': emlakci.kredi,
        'sohbet_id': sohbet.id,
    })


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

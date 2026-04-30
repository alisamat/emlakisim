"""
WHATSAPP WEBHOOK — Gelen mesajları AI asistana yönlendir + mesai dışı otomatik yanıt
"""
import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Emlakci
from app.services import whatsapp as wa
from app.services import asistan

logger = logging.getLogger(__name__)
bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')

_SESSIONS: dict[str, dict] = {}


@bp.route('', methods=['GET'])
def verify():
    mode      = request.args.get('hub.mode')
    token     = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == current_app.config.get('META_WEBHOOK_VERIFY_TOKEN'):
        return challenge, 200
    return 'Forbidden', 403


@bp.route('', methods=['POST'])
def gelen():
    data = request.get_json(silent=True) or {}
    try:
        entry   = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value   = changes.get('value', {})
        msgs    = value.get('messages', [])
        if not msgs:
            return jsonify({'status': 'ok'}), 200

        meta    = value.get('metadata', {})
        pid     = meta.get('phone_number_id', '')
        tok     = os.environ.get('WA_ACCESS_TOKEN', '')
        mesaj   = msgs[0]
        telefon = mesaj.get('from', '')

        # Emlakçıyı bul
        emlakci = _emlakci_bul(telefon)
        if not emlakci:
            wa.mesaj_gonder(pid, tok, telefon,
                '👋 Merhaba! Emlakisim sistemine hoş geldiniz.\n\n'
                'Kayıt olmak için: https://emlakisim.com/kayit')
            return jsonify({'status': 'ok'}), 200

        # Mesai dışı kontrolü (21:00 - 08:00 arası)
        saat = datetime.utcnow().hour + 3  # UTC+3 Türkiye
        if saat >= 24: saat -= 24
        if saat >= 21 or saat < 8:
            mesai_disi = os.environ.get('MESAI_DISI_MESAJ', '')
            if not mesai_disi:
                mesai_disi = (f'🌙 Merhaba! Şu anda mesai saatleri dışındayız.\n\n'
                             f'Mesajınız alındı, en kısa sürede dönüş yapılacaktır.\n'
                             f'Mesai saatleri: 08:00 - 21:00\n\n'
                             f'_Emlakisim AI Asistanı_')
            wa.mesaj_gonder(pid, tok, telefon, mesai_disi)
            # Mesajı yine de işle (kayıt olsun)

        # Session al ve asistana ilet
        session = _SESSIONS.setdefault(telefon, {'gecmis': []})
        temizle = asistan.isle(emlakci, mesaj, session, pid, tok)
        if temizle:
            _SESSIONS.pop(telefon, None)

    except Exception as e:
        logger.error(f'[Webhook] Hata: {e}', exc_info=True)

    return jsonify({'status': 'ok'}), 200


@bp.route('/gonder', methods=['POST'])
def wa_mesaj_gonder():
    """Panel'den müşteriye WhatsApp mesajı gönder."""
    from flask_jwt_extended import jwt_required, get_jwt_identity
    # JWT kontrolü manuel
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        emlakci_id = int(get_jwt_identity())
    except Exception:
        return jsonify({'message': 'Yetki gerekli'}), 401

    d = request.get_json() or {}
    telefon = d.get('telefon', '').strip()
    metin = d.get('mesaj', '').strip()
    if not telefon or not metin:
        return jsonify({'message': 'Telefon ve mesaj gerekli'}), 400

    pid = os.environ.get('WA_PHONE_NUMBER_ID', '')
    tok = os.environ.get('WA_ACCESS_TOKEN', '')
    if not pid or not tok:
        return jsonify({'message': 'WhatsApp yapılandırması eksik'}), 500

    # Telefon formatı düzelt
    telefon = telefon.replace('+', '').replace(' ', '').replace('-', '')
    if telefon.startswith('0'):
        telefon = '90' + telefon[1:]
    if not telefon.startswith('90'):
        telefon = '90' + telefon

    basarili = wa.mesaj_gonder(pid, tok, telefon, metin)
    if basarili:
        # İletişim geçmişine kaydet
        try:
            from app.models import Musteri
            from app.models.iletisim_gecmisi import IletisimKayit
            musteri = Musteri.query.filter_by(emlakci_id=emlakci_id, telefon=d.get('telefon')).first()
            if musteri:
                k = IletisimKayit(emlakci_id=emlakci_id, musteri_id=musteri.id,
                                  tip='whatsapp', yon='giden', ozet=metin[:200])
                db.session.add(k); db.session.commit()
        except Exception:
            pass
        return jsonify({'ok': True})
    return jsonify({'message': 'Gönderilemedi'}), 500


def _emlakci_bul(telefon: str):
    t = telefon.strip().replace('+', '')
    formatlar = [t, '+' + t, '0' + t[2:] if t.startswith('90') else t]
    return Emlakci.query.filter(
        Emlakci.aktif == True,
        Emlakci.telefon.in_(formatlar)
    ).first()

"""
WHATSAPP WEBHOOK — Gelen mesajları AI asistana yönlendir
"""
import logging
import os
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
                'Kayıt olmak için: https://emlakisim.com.tr/kayit')
            return jsonify({'status': 'ok'}), 200

        # Session al ve asistana ilet
        session = _SESSIONS.setdefault(telefon, {'gecmis': []})
        temizle = asistan.isle(emlakci, mesaj, session, pid, tok)
        if temizle:
            _SESSIONS.pop(telefon, None)

    except Exception as e:
        logger.error(f'[Webhook] Hata: {e}', exc_info=True)

    return jsonify({'status': 'ok'}), 200


def _emlakci_bul(telefon: str):
    t = telefon.strip().replace('+', '')
    formatlar = [t, '+' + t, '0' + t[2:] if t.startswith('90') else t]
    return Emlakci.query.filter(
        Emlakci.aktif == True,
        Emlakci.telefon.in_(formatlar)
    ).first()

"""
ÖDEME — Kuveyt Türk 3D Secure kredi satın alma
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, IslemLog
from app.services.kuveytturk import PAKETLER, start_3d_secure_payment, verify_3d_callback, provision_payment

logger = logging.getLogger(__name__)
bp = Blueprint('odeme', __name__, url_prefix='/api/odeme')

# Bekleyen ödeme session'ları (RAM — production'da Redis kullanılmalı)
_odeme_sessions = {}


@bp.route('/paketler', methods=['GET'])
def paketler():
    """Kredi paketlerini listele."""
    return jsonify({'paketler': {k: {**v} for k, v in PAKETLER.items()}})


@bp.route('/kuveytturk/init', methods=['POST'])
@jwt_required()
def odeme_baslat():
    """Kuveyt Türk 3D Secure ödeme başlat."""
    emlakci = Emlakci.query.get(int(get_jwt_identity()))
    if not emlakci:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404

    d = request.get_json() or {}
    paket_id = d.get('paket_id', '')
    paket = PAKETLER.get(paket_id)
    if not paket:
        return jsonify({'message': 'Geçersiz paket'}), 400

    # Kart bilgileri
    kart_sahibi = d.get('kart_sahibi', '')
    kart_no = d.get('kart_no', '').replace(' ', '')
    kart_ay = d.get('kart_ay', '')
    kart_yil = d.get('kart_yil', '')
    kart_cvv = d.get('kart_cvv', '')

    if not all([kart_sahibi, kart_no, kart_ay, kart_yil, kart_cvv]):
        return jsonify({'message': 'Kart bilgileri eksik'}), 400

    if len(kart_no) != 16 or not kart_no.isdigit():
        return jsonify({'message': 'Geçersiz kart numarası'}), 400

    # Tutar (kuruş cinsinden)
    tutar_kurus = int(paket['fiyat_tl'] * 100)
    order_id = f'EML-{emlakci.id}-{uuid.uuid4().hex[:8]}'

    # Session kaydet
    _odeme_sessions[order_id] = {
        'emlakci_id': emlakci.id,
        'paket_id': paket_id,
        'kredi': paket['kredi'],
        'tutar_tl': paket['fiyat_tl'],
        'tutar_kurus': tutar_kurus,
        'olusturma': datetime.utcnow(),
    }

    # İstemci IP
    client_ip = request.remote_addr or '127.0.0.1'

    # 3D Secure başlat
    sonuc = start_3d_secure_payment(
        kart_sahibi, kart_no, kart_ay, kart_yil, kart_cvv,
        tutar_kurus, order_id, client_ip
    )

    if sonuc['success']:
        return jsonify({'html': sonuc['html_content'], 'order_id': order_id})
    return jsonify({'message': sonuc.get('error', 'Ödeme başlatılamadı')}), 500


@bp.route('/kuveytturk/callback', methods=['POST'])
def odeme_callback():
    """Kuveyt Türk 3D Secure callback — banka buraya POST yapar."""
    frontend_url = os.environ.get('FRONTEND_URL', 'https://emlakisim.vercel.app')

    try:
        auth_response = request.form.get('AuthenticationResponse', '')
        if not auth_response:
            return redirect(f'{frontend_url}/odeme-sonuc?status=fail&error=Boş yanıt')

        # 3D doğrulama
        dogrulama = verify_3d_callback(auth_response)
        if not dogrulama['success']:
            return redirect(f'{frontend_url}/odeme-sonuc?status=fail&error={dogrulama.get("error", "Doğrulama hatası")}')

        order_id = dogrulama['order_id']
        amount = dogrulama['amount']
        md = dogrulama['md']

        # Session bul
        session = _odeme_sessions.get(order_id)
        if not session:
            return redirect(f'{frontend_url}/odeme-sonuc?status=fail&error=Oturum bulunamadı')

        # Provizyon (final ödeme)
        provizyon = provision_payment(order_id, amount, md)
        if not provizyon['success']:
            return redirect(f'{frontend_url}/odeme-sonuc?status=fail&error={provizyon.get("error", "Ödeme alınamadı")}')

        # Başarılı — kredi ekle
        emlakci = Emlakci.query.get(session['emlakci_id'])
        if emlakci:
            emlakci.kredi = (emlakci.kredi or 0) + session['kredi']

            # Kredi son kullanma: +365 gün
            emlakci.kredi_son_kullanma = datetime.utcnow() + timedelta(days=365)

            # İşlem log
            log = IslemLog(
                emlakci_id=emlakci.id,
                islem_tipi='kredi_satin_alma',
                aciklama=f'{session["paket_id"]} — {session["kredi"]} kredi — {session["tutar_tl"]} TL',
                kredi_tutar=-session['kredi'],  # negatif = ekleme
                maliyet_usd=0,
            )
            db.session.add(log)
            db.session.commit()

            logger.info(f'[Ödeme] ✅ {emlakci.ad_soyad} — {session["kredi"]} kredi eklendi — {session["tutar_tl"]} TL')

        # Session temizle
        _odeme_sessions.pop(order_id, None)

        return redirect(f'{frontend_url}/odeme-sonuc?status=success&kredi={session["kredi"]}&tutar={session["tutar_tl"]}')

    except Exception as e:
        logger.error(f'[Ödeme] Callback hata: {e}')
        return redirect(f'{frontend_url}/odeme-sonuc?status=fail&error=İşlem hatası')

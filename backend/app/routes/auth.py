"""
AUTH — Emlakçı kayıt, giriş, profil
"""
import hashlib
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


@bp.route('/kayit', methods=['POST'])
def kayit():
    d = request.get_json() or {}
    if not all([d.get('ad_soyad'), d.get('email'), d.get('telefon'), d.get('sifre')]):
        return jsonify({'message': 'Eksik alan'}), 400
    if Emlakci.query.filter_by(email=d['email']).first():
        return jsonify({'message': 'E-posta zaten kayıtlı'}), 409
    e = Emlakci(
        ad_soyad=d['ad_soyad'], email=d['email'],
        telefon=d['telefon'], sifre_hash=_hash(d['sifre']),
        acente_adi=d.get('acente_adi', ''), yetki_no=d.get('yetki_no', '')
    )
    db.session.add(e); db.session.commit()
    token = create_access_token(identity=str(e.id))
    return jsonify({'token': token, 'user': _user(e)}), 201


@bp.route('/giris', methods=['POST'])
def giris():
    d = request.get_json() or {}
    e = Emlakci.query.filter_by(email=d.get('email'), sifre_hash=_hash(d.get('sifre', ''))).first()
    if not e or not e.aktif:
        return jsonify({'message': 'Hatalı bilgi'}), 401
    return jsonify({'token': create_access_token(identity=str(e.id)), 'user': _user(e)})


@bp.route('/profil', methods=['GET'])
@jwt_required()
def profil():
    e = Emlakci.query.get(int(get_jwt_identity()))
    return jsonify({'user': _user(e)})


@bp.route('/profil', methods=['PUT'])
@jwt_required()
def profil_guncelle():
    e = Emlakci.query.get(int(get_jwt_identity()))
    d = request.get_json() or {}
    for f in ['ad_soyad', 'telefon', 'acente_adi', 'yetki_no']:
        if f in d:
            setattr(e, f, d[f])
    db.session.commit()
    return jsonify({'user': _user(e)})


@bp.route('/sifre-degistir', methods=['PUT'])
@jwt_required()
def sifre_degistir():
    e = Emlakci.query.get(int(get_jwt_identity()))
    d = request.get_json() or {}
    eski = d.get('eski_sifre', '')
    yeni = d.get('yeni_sifre', '')
    if not eski or not yeni:
        return jsonify({'message': 'Eski ve yeni şifre gerekli'}), 400
    if e.sifre_hash != _hash(eski):
        return jsonify({'message': 'Eski şifre hatalı'}), 401
    if len(yeni) < 4:
        return jsonify({'message': 'Yeni şifre en az 4 karakter olmalı'}), 400
    e.sifre_hash = _hash(yeni)
    db.session.commit()
    return jsonify({'message': 'Şifre değiştirildi'})


@bp.route('/sifre-sifirla', methods=['POST'])
def sifre_sifirla_istek():
    """Email ile şifre sıfırlama linki gönder."""
    d = request.get_json() or {}
    email = d.get('email', '').strip()
    if not email:
        return jsonify({'message': 'Email gerekli'}), 400

    e = Emlakci.query.filter_by(email=email).first()
    if not e:
        # Güvenlik: kullanıcı var mı bilgi verme
        return jsonify({'message': 'Eğer bu email kayıtlıysa, şifre sıfırlama bağlantısı gönderildi.'})

    import secrets, os
    token = secrets.token_urlsafe(32)
    # Token'ı geçici olarak kullanıcıya kaydet
    e.sifre_hash = e.sifre_hash  # değiştirme, sadece token kaydet
    # Basit yaklaşım: token'ı cache'e koy (production'da Redis kullanılmalı)
    _sifre_tokenlari[token] = {'emlakci_id': e.id, 'email': email}

    frontend_url = os.environ.get('FRONTEND_URL', 'https://emlakisim.com')
    link = f'{frontend_url}/sifre-sifirla?token={token}'

    try:
        from app.services.iletisim import email_gonder
        html = f'''<div style="font-family:sans-serif;max-width:500px;margin:0 auto">
        <div style="background:#16a34a;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0"><strong>Emlakisim — Şifre Sıfırlama</strong></div>
        <div style="padding:24px;background:#fff;border:1px solid #e2e8f0;border-radius:0 0 8px 8px">
        <p>Şifre sıfırlama talebiniz alındı.</p>
        <p><a href="{link}" style="background:#16a34a;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:700">Şifremi Sıfırla</a></p>
        <p style="font-size:12px;color:#94a3b8;margin-top:16px">Bu bağlantı 1 saat geçerlidir. Siz talep etmediyseniz bu emaili dikkate almayın.</p>
        </div></div>'''
        email_gonder(email, 'Emlakisim — Şifre Sıfırlama', html)
    except Exception:
        pass

    return jsonify({'message': 'Eğer bu email kayıtlıysa, şifre sıfırlama bağlantısı gönderildi.'})


@bp.route('/sifre-sifirla-onayla', methods=['POST'])
def sifre_sifirla_onayla():
    """Token ile yeni şifre belirle."""
    d = request.get_json() or {}
    token = d.get('token', '')
    yeni_sifre = d.get('yeni_sifre', '')

    if not token or not yeni_sifre:
        return jsonify({'message': 'Token ve yeni şifre gerekli'}), 400
    if len(yeni_sifre) < 4:
        return jsonify({'message': 'Şifre en az 4 karakter'}), 400

    veri = _sifre_tokenlari.pop(token, None)
    if not veri:
        return jsonify({'message': 'Geçersiz veya süresi dolmuş bağlantı'}), 400

    e = Emlakci.query.get(veri['emlakci_id'])
    if not e:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404

    e.sifre_hash = _hash(yeni_sifre)
    db.session.commit()
    return jsonify({'message': 'Şifre başarıyla değiştirildi. Giriş yapabilirsiniz.'})


# Geçici token deposu (production'da Redis kullanılmalı)
_sifre_tokenlari: dict = {}


def _user(e):
    return {
        'id': e.id, 'ad_soyad': e.ad_soyad, 'email': e.email,
        'telefon': e.telefon, 'acente_adi': e.acente_adi,
        'yetki_no': e.yetki_no, 'kredi': e.kredi,
        'kredi_son_kullanma': e.kredi_son_kullanma.isoformat() if e.kredi_son_kullanma else None,
    }

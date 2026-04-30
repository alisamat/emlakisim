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


def _user(e):
    return {
        'id': e.id, 'ad_soyad': e.ad_soyad, 'email': e.email,
        'telefon': e.telefon, 'acente_adi': e.acente_adi,
        'yetki_no': e.yetki_no, 'kredi': e.kredi,
    }

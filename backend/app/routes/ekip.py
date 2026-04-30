"""
EKİP — Danışman yönetimi + müşteri atama API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.ofis_ekip import Danisман, MusteriAtama

bp = Blueprint('ekip', __name__, url_prefix='/api/panel/ekip')


def _eid():
    return int(get_jwt_identity())


@bp.route('/danismanlar', methods=['GET'])
@jwt_required()
def danisman_listesi():
    kayitlar = Danisман.query.filter_by(emlakci_id=_eid(), aktif=True).all()
    return jsonify({'danismanlar': [{
        'id': d.id, 'ad_soyad': d.ad_soyad, 'telefon': d.telefon,
        'email': d.email, 'uzmanlik': d.uzmanlik,
    } for d in kayitlar]})


@bp.route('/danismanlar', methods=['POST'])
@jwt_required()
def danisman_ekle():
    d = request.get_json() or {}
    dn = Danisман(
        emlakci_id=_eid(), ad_soyad=d.get('ad_soyad', ''),
        telefon=d.get('telefon'), email=d.get('email'),
        uzmanlik=d.get('uzmanlik'), detaylar=d.get('detaylar', {}),
    )
    db.session.add(dn); db.session.commit()
    return jsonify({'ok': True, 'id': dn.id}), 201


@bp.route('/danismanlar/<int:did>', methods=['DELETE'])
@jwt_required()
def danisman_sil(did):
    d = Danisман.query.filter_by(id=did, emlakci_id=_eid()).first_or_404()
    d.aktif = False
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/atama', methods=['POST'])
@jwt_required()
def musteri_ata():
    d = request.get_json() or {}
    a = MusteriAtama(
        emlakci_id=_eid(), musteri_id=d.get('musteri_id'),
        danisman_id=d.get('danisman_id'), notlar=d.get('notlar'),
    )
    db.session.add(a); db.session.commit()
    return jsonify({'ok': True}), 201


@bp.route('/atamalar', methods=['GET'])
@jwt_required()
def atama_listesi():
    kayitlar = MusteriAtama.query.filter_by(emlakci_id=_eid()).order_by(MusteriAtama.olusturma.desc()).all()
    return jsonify({'atamalar': [{
        'id': a.id, 'musteri_id': a.musteri_id,
        'danisman_id': a.danisman_id, 'notlar': a.notlar,
    } for a in kayitlar]})
